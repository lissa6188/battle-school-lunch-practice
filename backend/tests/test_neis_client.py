import pytest
import asyncio

from backend import neis_client


async def fake_fetch_school(client, url, params):
    return {"schoolInfo": [{"head": []}, {"row": [{"SCHUL_NM": "서울초등학교", "SD_SCHUL_CODE": "1001", "LCTN_ADRES": "서울시 종로구"}]}]}


async def fake_fetch_meal(client, url, params):
    return {"mealServiceDietInfo": [{"head": []}, {"row": [{"MLSV_YMD": "20260817", "DDISH_NM": "김밥 / 된장국 / 샐러드"}]}]}


@pytest.mark.asyncio
async def test_search_schools_neis(monkeypatch):
    async def _fake(client, url, params):
        return await fake_fetch_school(client, url, params)

    monkeypatch.setattr(neis_client, "_fetch", _fake)
    res = await neis_client.search_schools_neis("서울", "dummy")
    assert isinstance(res, list)
    assert res and res[0]["code"] == "1001"


@pytest.mark.asyncio
async def test_get_meals_neis(monkeypatch):
    async def _fake(client, url, params):
        return await fake_fetch_meal(client, url, params)

    monkeypatch.setattr(neis_client, "_fetch", _fake)
    res = await neis_client.get_meals_neis("1001", "2026-08-17", "2026-08-18", "dummy")
    assert isinstance(res, list)
    assert res[0]["date"] == "2026-08-17"
    assert any("김밥" in item for item in res[0]["lunch"]) 
