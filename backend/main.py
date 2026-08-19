import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import date, timedelta

# Optional NEIS integration
NEIS_API_KEY = os.environ.get("NEIS_API_KEY")

try:
    from .neis_client import search_schools_neis, get_meals_neis
    HAS_NEIS_CLIENT = True
except Exception:
    HAS_NEIS_CLIENT = False

app = FastAPI(title="School Lunch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class School(BaseModel):
    code: str
    name: str
    address: str | None = None


class MealDay(BaseModel):
    date: date
    lunch: List[str] | None = None
    school_code: str
    school_name: str


# Sample in-memory school list. Replace with NEIS-backed lookup in production.
SCHOOLS = [
    {"code": "1001", "name": "서울초등학교", "address": "서울시 종로구"},
    {"code": "1002", "name": "한빛중학교", "address": "서울시 서초구"},
    {"code": "1003", "name": "동산고등학교", "address": "경기도 성남시"},
]


@app.get("/api/schools", response_model=List[School])
async def search_schools(query: str = Query(..., min_length=2)):
    q = query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="query is required")

    # If NEIS configured and client available, use it
    if NEIS_API_KEY and HAS_NEIS_CLIENT:
        try:
            results = await search_schools_neis(q, NEIS_API_KEY)
            # map to School model
            return [School(code=r.get("code", ""), name=r.get("name", ""), address=r.get("address")) for r in results]
        except Exception:
            # fall back to in-memory list on errors
            pass

    matches = [s for s in SCHOOLS if q.lower() in s["name"].lower()]
    return matches


@app.get("/api/meals", response_model=List[MealDay])
async def get_meals(school_code: str = Query(...), start_date: date = Query(...), end_date: date = Query(...)):
    # Basic validation
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
    delta = (end_date - start_date).days
    if delta > 60:
        raise HTTPException(status_code=400, detail="date range too large (max 60 days)")

    # Try NEIS when configured
    if NEIS_API_KEY and HAS_NEIS_CLIENT:
        try:
            # convert dates to iso strings for neis client
            sd = start_date.isoformat()
            ed = end_date.isoformat()
            neis_results = await get_meals_neis(school_code, sd, ed, NEIS_API_KEY)
            out = []
            for r in neis_results:
                # r: {date: 'YYYY-MM-DD', lunch: [items]}
                out.append(MealDay(date=r.get("date"), lunch=r.get("lunch"), school_code=school_code, school_name=""))
            return out
        except Exception:
            # fall back to mock
            pass

    school = next((s for s in SCHOOLS if s["code"] == school_code), None)
    if not school:
        raise HTTPException(status_code=404, detail="school not found")

    results: List[MealDay] = []
    for i in range(delta + 1):
        d = start_date + timedelta(days=i)
        # Mock: no meals on weekends
        if d.weekday() >= 5:
            lunch = None
        else:
            lunch = [f"메뉴 {d.isoformat()} - 김밥", "된장국", "샐러드"]
        results.append(MealDay(date=d, lunch=lunch, school_code=school["code"], school_name=school["name"]))

    return results
