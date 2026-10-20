"""Health, farmer profile, persistence, crop recommendation, market prices, advisory and resources."""

import json

import httpx
import pytest

from app.services import advisory_service, crop_service, market_service

VALID_CROP_INPUT = {"N": 90, "P": 42, "K": 43, "temperature": 21, "humidity": 82, "ph": 6.5, "rainfall": 203}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"]["connected"] is True
    assert body["weather_provider"] == "open-meteo"  # no OpenWeather key in tests
    assert body["market_prices"] == "demo"
    assert body["advisory_provider"] == "knowledge_base"
    assert set(body["disease_model"]) == {"available", "version", "reason"}


def test_root_redirects_to_docs(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/docs"


def test_unknown_route_returns_json_error(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------- farmers
def test_create_and_read_farmer(client, farmer):
    assert farmer["name"] == "Test Farmer"
    assert farmer["farms"][0]["crops"][0]["crop_name"] == "wheat"  # normalised to lower case
    r = client.get(f"/api/farmers/{farmer['id']}")
    assert r.status_code == 200
    assert r.json()["farms"][0]["location_name"] == "Ludhiana"


def test_update_farmer_replaces_crops(client, farmer):
    payload = {"name": "Updated Name", "preferred_language": "en",
               "farm": {"name": "North field", "crops": [{"crop_name": "rice"}, {"crop_name": "potato"}]}}
    r = client.put(f"/api/farmers/{farmer['id']}", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Updated Name"
    assert sorted(c["crop_name"] for c in body["farms"][0]["crops"]) == ["potato", "rice"]


def test_farmer_validation_errors(client):
    r = client.post("/api/farmers", json={"name": "A", "phone": "12345"})
    assert r.status_code == 422
    fields = {f["field"] for f in r.json()["error"]["details"]["fields"]}
    assert {"name", "phone"} <= fields


def test_missing_farmer_404(client):
    r = client.get("/api/farmers/999999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "FARMER_NOT_FOUND"


# ---------------------------------------------------------------- crop recommendation
def test_crop_recommendation_valid_and_saved(client, farmer):
    r = client.post("/api/crops/recommend", json={**VALID_CROP_INPUT, "farmer_id": farmer["id"]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["recommended_crop"] == "rice"  # this input is a real row of the rice class
    assert 0 < body["confidence"] <= 1
    assert len(body["candidates"]) == 3
    assert len(body["candidates"][0]["comparison"]) == 7
    assert body["warnings"] == []

    history = client.get(f"/api/farmers/{farmer['id']}/history").json()
    assert history["crop_recommendations"][0]["recommended_crop"] == "rice"


def test_crop_recommendation_out_of_dataset_range_warns(client):
    r = client.post("/api/crops/recommend", json={**VALID_CROP_INPUT, "N": 250})
    assert r.status_code == 200
    assert any("Nitrogen" in w for w in r.json()["warnings"])


def test_crop_recommendation_low_confidence_warns(client):
    # Values that sit between several crops' typical ranges
    r = client.post("/api/crops/recommend", json={"N": 100, "P": 40, "K": 40, "temperature": 22.8,
                                                   "humidity": 60, "ph": 6.8, "rainfall": 80})
    body = r.json()
    assert body["confidence"] < 0.5
    assert any("Low confidence" in w for w in body["warnings"])


def test_crop_recommendation_invalid_inputs(client):
    r = client.post("/api/crops/recommend", json={**VALID_CROP_INPUT, "ph": 15, "humidity": -5})
    assert r.status_code == 422
    fields = {f["field"] for f in r.json()["error"]["details"]["fields"]}
    assert fields == {"ph", "humidity"}
    r = client.post("/api/crops/recommend", json={"N": 10})
    assert r.status_code == 422


def test_crop_model_missing_returns_503(client, settings, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "crop_model_path", tmp_path / "missing.joblib")
    crop_service.load_model(force=True)
    try:
        r = client.post("/api/crops/recommend", json=VALID_CROP_INPUT)
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "MODEL_NOT_AVAILABLE"
    finally:
        monkeypatch.undo()
        crop_service.load_model(force=True)


# ---------------------------------------------------------------- market prices
def test_market_prices_demo_mode_is_labelled(client):
    r = client.get("/api/market-prices", params={"commodity": "Wheat"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "demo"
    assert "DEMO" in body["notice"]
    assert body["records"] and all(rec["is_demo"] and rec["commodity"] == "Wheat" for rec in body["records"])


def _mock_client(handler):
    return lambda: httpx.Client(transport=httpx.MockTransport(handler))


def test_market_prices_live_mode_parses_agmarknet(client, settings, monkeypatch):
    def handler(request):
        assert request.url.params["filters[commodity]"] == "Tomato"
        return httpx.Response(200, json={"records": [{
            "state": "Maharashtra", "district": "Nashik", "market": "Pimpalgaon", "commodity": "Tomato",
            "variety": "Hybrid", "arrival_date": "17/10/2026", "min_price": "800", "max_price": "1500", "modal_price": "1200",
        }]})

    monkeypatch.setattr(settings, "data_gov_in_api_key", "test-key")
    monkeypatch.setattr(market_service, "make_client", _mock_client(handler))
    body = client.get("/api/market-prices", params={"commodity": "Tomato"}).json()
    assert body["mode"] == "live"
    rec = body["records"][0]
    assert rec["modal_price"] == 1200.0 and rec["price_date"] == "2026-10-17" and rec["is_demo"] is False


def test_market_prices_live_failure_falls_back_to_demo(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "data_gov_in_api_key", "test-key")
    monkeypatch.setattr(market_service, "make_client", _mock_client(lambda req: httpx.Response(500)))
    body = client.get("/api/market-prices").json()
    assert body["mode"] == "demo"
    assert "failed" in body["notice"]


# ---------------------------------------------------------------- advisory
def test_advisory_without_key_uses_knowledge_base(client, farmer):
    r = client.post("/api/advisory/ask", json={"question": "What can I do instead of burning parali?",
                                                "language": "en", "farmer_id": farmer["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "knowledge_base"
    assert body["matched_topic"] == "stubble"
    assert "not configured" in body["notice"]
    history = client.get(f"/api/farmers/{farmer['id']}/history").json()
    assert history["advisory"][0]["provider"] == "knowledge_base"


@pytest.mark.parametrize("profile,expected_context", [
    # Regression: a farmer with a state but no farm used to cause a 500 (misc.py read farm.location_name on None)
    ({"name": "No Farm", "state": "Punjab"}, "location Punjab"),
    ({"name": "No Farm", "district": "Karnal", "state": "Haryana"}, "location Karnal"),
    ({"name": "Nothing Set"}, None),
    ({"name": "Has Farm", "state": "Punjab", "farm": {"location_name": "Ludhiana", "soil_type": "alluvial",
                                                      "crops": [{"crop_name": "wheat"}]}},
     "location Ludhiana; crops: wheat; soil: alluvial"),
])
def test_advisory_context_with_and_without_farm(client, monkeypatch, profile, expected_context):
    seen = {}

    def fake_answer(question, language, context, history):
        seen["context"] = context
        return {"answer": "ok", "provider": "knowledge_base", "model": None, "notice": None}

    monkeypatch.setattr(advisory_service, "answer", fake_answer)
    farmer_id = client.post("/api/farmers", json=profile).json()["id"]
    r = client.post("/api/advisory/ask", json={"question": "When should I irrigate?", "farmer_id": farmer_id})
    assert r.status_code == 200, r.text
    assert seen["context"] == expected_context


def test_advisory_hindi_answer(client):
    body = client.post("/api/advisory/ask", json={"question": "गेहूँ में सिंचाई कब करें?", "language": "hi"}).json()
    assert body["matched_topic"] == "irrigation_time"
    assert "सिंचाई" in body["answer"]


def test_advisory_ai_failure_falls_back(client, settings, monkeypatch):
    def boom(*args, **kwargs):
        raise ConnectionError("network down")

    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(advisory_service, "_ask_claude", boom)
    body = client.post("/api/advisory/ask", json={"question": "How do I control aphids?"}).json()
    assert body["provider"] == "knowledge_base"
    assert "unavailable" in body["notice"]


def test_advisory_uses_gemini_when_key_set(client, settings, monkeypatch):
    seen = {}

    def handler(request):
        seen["url"], seen["key"] = str(request.url), request.headers["x-goog-api-key"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": [
            {"text": "thinking...", "thought": True}, {"text": "Irrigate early in the morning."}]}}]})

    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")
    monkeypatch.setattr(advisory_service, "make_client", lambda timeout=None: httpx.Client(transport=httpx.MockTransport(handler)))
    assert client.get("/api/advisory/status").json()["provider"] == "gemini"
    body = client.post("/api/advisory/ask", json={
        "question": "When should I irrigate?", "language": "en",
        "history": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}],
    }).json()
    assert body["provider"] == "gemini" and body["answer"] == "Irrigate early in the morning."  # thought part skipped
    assert seen["key"] == "test-gemini-key" and f"models/{settings.gemini_model}:generateContent" in seen["url"]
    assert [c["role"] for c in seen["body"]["contents"]] == ["user", "model", "user"]
    assert "KrishiVeda" in seen["body"]["systemInstruction"]["parts"][0]["text"]


def test_advisory_gemini_bad_key_falls_back(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "wrong-key")
    monkeypatch.setattr(advisory_service, "make_client", lambda timeout=None: httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(400, json={"error": {"message": "API key not valid"}}))))
    body = client.post("/api/advisory/ask", json={"question": "How do I control aphids?"}).json()
    assert body["provider"] == "knowledge_base"
    assert "unavailable" in body["notice"]


def test_advisory_validation(client):
    assert client.post("/api/advisory/ask", json={"question": "hi"}).status_code == 422
    assert client.post("/api/advisory/ask", json={"question": "valid question", "language": "fr"}).status_code == 422


# ---------------------------------------------------------------- resources & stats
def test_resources(client):
    schemes = client.get("/api/resources/schemes").json()
    assert any(s["id"] == "pmfby" for s in schemes["schemes"])
    assert all(s["url"].startswith("https://") for s in schemes["schemes"])
    assert len(client.get("/api/resources/stubble").json()["options"]) >= 4


def test_stats(client, farmer):
    client.post("/api/crops/recommend", json={**VALID_CROP_INPUT, "farmer_id": farmer["id"]})
    stats = client.get(f"/api/farmers/{farmer['id']}/stats").json()
    assert stats["recommendations"] == 1
    assert stats["recommended_crops"] == {"rice": 1}
