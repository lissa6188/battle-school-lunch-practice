import os
import asyncio
import httpx
from datetime import datetime
from typing import List, Optional

NEIS_BASE = os.environ.get("NEIS_BASE_URL", "https://open.neis.go.kr")
DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3


async def _fetch(client: httpx.AsyncClient, url: str, params: dict) -> Optional[dict]:
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = await client.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_exc = exc
            await asyncio.sleep(0.2 * attempt)
    raise last_exc


async def search_schools_neis(query: str, api_key: str) -> List[dict]:
    """Search schools via NEIS schoolInfo endpoint and return list of {code,name,address}.
    NEIS supports filtering by SCHUL_NM; results are filtered client-side for partial matches.
    """
    url = f"{NEIS_BASE}/hub/schoolInfo"
    params = {
        "Key": api_key,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "SCHUL_NM": query,
    }
    async with httpx.AsyncClient() as client:
        payload = await _fetch(client, url, params)

    if not payload:
        return []

    # NEIS response shape: { 'schoolInfo': [ { 'head': [...], 'row': [ {...}, ... ] } ] }
    rows = []
    try:
        top = payload.get("schoolInfo")
        if top and isinstance(top, list) and len(top) > 0:
            rows = top[1].get("row") if len(top) > 1 and isinstance(top[1], dict) and "row" in top[1] else top[0].get("row", [])
    except Exception:
        rows = []

    results = []
    q = query.strip().lower()
    for r in rows or []:
        name = r.get("SCHUL_NM") or r.get("SCHUL_NM")
        code = r.get("SD_SCHUL_CODE") or r.get("SCHUL_CODE") or r.get("ATPT_OFCDC_SC_CODE", "")
        addr = r.get("LCTN_ADRES") or r.get("LCTN_SC_NM") or None
        # do partial match defensively
        if q in (name or "").lower():
            results.append({"code": code, "name": name, "address": addr})
    return results


def _parse_menu_text(text: str) -> List[str]:
    # NEIS often returns menu like "잡곡밥 / 미역국 / 김치" or with <br/>; normalize
    if not text:
        return []
    # remove html tags
    import re

    clean = re.sub(r"<[^>]+>", "\n", text)
    # split on common separators
    parts = [p.strip() for p in re.split(r"\n|/|,|;|·", clean) if p.strip()]
    # filter out numeric annotations like (1), ② etc
    parts = [re.sub(r"\(.*?\)|[①-⑨]", "", p).strip() for p in parts]
    return [p for p in parts if p]


async def get_meals_neis(school_code: str, start_date: str, end_date: str, api_key: str) -> List[dict]:
    """Get meals from NEIS for given school_code and date-range.
    start_date/end_date are ISO 'YYYY-MM-DD' strings; NEIS expects YYYYMMDD.
    Returns list of {date: 'YYYY-MM-DD', lunch: [items]}
    """
    url = f"{NEIS_BASE}/hub/mealServiceDietInfo"

    def to_neis(d: str) -> str:
        return datetime.fromisoformat(d).strftime("%Y%m%d")

    params = {
        "Key": api_key,
        "Type": "json",
        "pIndex": 1,
        "pSize": 1000,
        "SD_SCHUL_CODE": school_code,
        "MLSV_FROM_YMD": to_neis(start_date),
        "MLSV_TO_YMD": to_neis(end_date),
    }

    async with httpx.AsyncClient() as client:
        payload = await _fetch(client, url, params)

    if not payload:
        return []

    rows = []
    try:
        top = payload.get("mealServiceDietInfo")
        if top and isinstance(top, list) and len(top) > 0:
            rows = top[1].get("row") if len(top) > 1 and isinstance(top[1], dict) and "row" in top[1] else top[0].get("row", [])
    except Exception:
        rows = []

    results = []
    for r in rows or []:
        ymd = r.get("MLSV_YMD") or r.get("MLSV_YMD")
        # try to parse YYYYMMDD
        try:
            dt = datetime.strptime(ymd, "%Y%m%d").date()
            date_iso = dt.isoformat()
        except Exception:
            # fallback to given
            date_iso = ymd
        dish = r.get("DDISH_NM") or r.get("DDISH_NM")
        menu = _parse_menu_text(dish)
        results.append({"date": date_iso, "lunch": menu})
    # dedupe by date keeping first
    dedup = {}
    for item in results:
        dedup.setdefault(item["date"], item)
    # return sorted by date
    out = [dedup[k] for k in sorted(dedup.keys())]
    return out
