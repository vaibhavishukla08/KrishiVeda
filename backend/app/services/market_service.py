"""Mandi (market) prices.

Live source : AGMARKNET data published on data.gov.in — resource
              "Current Daily Price of Various Commodities from Various Markets (Mandi)"
              (id 9ef84268-d588-465a-a308-a864a43d0070). Requires a free API key
              (DATA_GOV_IN_API_KEY) from https://data.gov.in.
Fallback    : clearly labelled DEMO records from app/data/market_demo.json.
"""

import json
from datetime import date, datetime
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.orm import MarketPrice
from app.services.http_client import make_client

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
API_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
DEMO_FILE = Path(__file__).resolve().parent.parent / "data" / "market_demo.json"
LIVE_SOURCE = "AGMARKNET via data.gov.in"


def _parse_date(value: str) -> date:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date: {value}")


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _demo_records(commodity: str | None, state: str | None) -> list[dict]:
    records = json.loads(DEMO_FILE.read_text(encoding="utf-8"))["records"]
    if commodity:
        records = [r for r in records if r["commodity"].lower() == commodity.lower()]
    if state:
        records = [r for r in records if (r["state"] or "").lower() == state.lower()]
    for r in records:
        r.update(unit="Rs/quintal", source="DEMO sample data — not real prices", is_demo=True)
    return records


def _fetch_live(commodity: str | None, state: str | None, limit: int) -> list[dict]:
    params = {"api-key": get_settings().data_gov_in_api_key, "format": "json", "limit": limit}
    if commodity:
        params["filters[commodity]"] = commodity
    if state:
        params["filters[state]"] = state
    with make_client() as client:
        resp = client.get(API_URL, params=params)
        resp.raise_for_status()
        payload = resp.json()
    out = []
    for r in payload.get("records", []):
        out.append({
            "commodity": r.get("commodity"),
            "variety": r.get("variety"),
            "market": r.get("market"),
            "district": r.get("district"),
            "state": r.get("state"),
            "min_price": _to_float(r.get("min_price")),
            "max_price": _to_float(r.get("max_price")),
            "modal_price": _to_float(r.get("modal_price")),
            "unit": "Rs/quintal",
            "price_date": _parse_date(r["arrival_date"]).isoformat(),
            "source": LIVE_SOURCE,
            "is_demo": False,
        })
    return out


def _save(db: Session, records: list[dict]) -> None:
    for r in records:
        db.add(MarketPrice(**{**r, "price_date": date.fromisoformat(r["price_date"])}))
    db.commit()


def get_prices(db: Session, commodity: str | None = None, state: str | None = None, limit: int = 50) -> dict:
    live_error = None
    if get_settings().data_gov_in_api_key:
        try:
            records = _fetch_live(commodity, state, limit)
            _save(db, records)
            return {"mode": "live", "source": LIVE_SOURCE, "records": records, "notice": None}
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            live_error = type(exc).__name__

    records = _demo_records(commodity, state)[:limit]
    notice = "Showing DEMO sample prices. Set DATA_GOV_IN_API_KEY to load real AGMARKNET prices."
    if live_error:
        notice = f"Live price service failed ({live_error}). Showing DEMO sample prices instead."
    return {"mode": "demo", "source": "Demo sample data", "records": records, "notice": notice}


def demo_commodities() -> list[str]:
    records = json.loads(DEMO_FILE.read_text(encoding="utf-8"))["records"]
    return sorted({r["commodity"] for r in records})
