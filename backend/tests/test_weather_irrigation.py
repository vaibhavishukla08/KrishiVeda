"""Weather provider parsing (mocked HTTP), failure fallback, and irrigation rules."""

import httpx
import pytest

from app.services import irrigation_service, weather_service


def open_meteo_handler(rain=(0, 0, 0, 0, 0), et0=(5.0, 5.0, 5.0, 5.0, 5.0), tmax=(32,) * 5, tmin=(18,) * 5,
                       humidity=55, wind=8.0, geocode_results=True):
    def handler(request: httpx.Request):
        if "geocoding" in request.url.host:
            results = [{"name": "Ludhiana", "admin1": "Punjab", "country": "India", "latitude": 30.9, "longitude": 75.85}]
            return httpx.Response(200, json={"results": results if geocode_results else []})
        return httpx.Response(200, json={
            "current": {"time": "2026-10-19T10:00", "temperature_2m": 28.4, "relative_humidity_2m": humidity,
                        "precipitation": 0.0, "weather_code": 1, "wind_speed_10m": wind},
            "daily": {"time": [f"2026-10-{19 + i}" for i in range(5)],
                      "temperature_2m_max": list(tmax), "temperature_2m_min": list(tmin),
                      "precipitation_sum": list(rain), "precipitation_probability_max": [80 if r else 5 for r in rain],
                      "et0_fao_evapotranspiration": list(et0), "weather_code": [1] * 5},
        })
    return handler


def use_mock(monkeypatch, handler):
    monkeypatch.setattr(weather_service, "make_client", lambda: httpx.Client(transport=httpx.MockTransport(handler)))


def test_weather_open_meteo_parsing(client, monkeypatch):
    use_mock(monkeypatch, open_meteo_handler())
    r = client.get("/api/weather", params={"city": "Ludhiana"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["location"]["name"] == "Ludhiana, Punjab, India"
    assert body["current"]["temperature_c"] == 28.4
    assert len(body["daily"]) == 5 and body["daily"][0]["et0_mm"] == 5.0
    assert body["source"]["provider"] == "open-meteo"
    assert body["alerts"] == []


def test_weather_location_not_found(client, monkeypatch):
    use_mock(monkeypatch, open_meteo_handler(geocode_results=False))
    r = client.get("/api/weather", params={"city": "Nowhereville"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "LOCATION_NOT_FOUND"


def test_weather_requires_location(client):
    r = client.get("/api/weather")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "LOCATION_REQUIRED"


def test_weather_provider_down_returns_503(client, monkeypatch):
    def down(request):
        raise httpx.ConnectError("no network", request=request)

    use_mock(monkeypatch, down)
    r = client.get("/api/weather", params={"city": "Ludhiana"})
    assert r.status_code == 503
    err = r.json()["error"]
    assert err["code"] == "WEATHER_UNAVAILABLE"
    assert "Traceback" not in err["message"]


def test_openweather_used_when_key_configured(client, settings, monkeypatch):
    seen = []

    def handler(request):
        seen.append(request.url.host)
        path = request.url.path
        if path.endswith("/geo/1.0/direct"):
            return httpx.Response(200, json=[{"name": "Pune", "state": "Maharashtra", "country": "IN", "lat": 18.5, "lon": 73.8}])
        if path.endswith("/weather"):
            return httpx.Response(200, json={"dt": 1760860800, "main": {"temp": 30.0, "humidity": 60},
                                             "wind": {"speed": 2.0}, "weather": [{"description": "few clouds"}]})
        items = [{"dt_txt": f"2026-10-{19 + i // 8} {(i % 8) * 3:02d}:00:00", "main": {"temp_max": 31, "temp_min": 20},
                  "rain": {"3h": 1.0}, "pop": 0.4, "weather": [{"description": "light rain"}]} for i in range(16)]
        return httpx.Response(200, json={"list": items})

    monkeypatch.setattr(settings, "openweather_api_key", "test-key")
    use_mock(monkeypatch, handler)
    body = client.get("/api/weather", params={"city": "Pune"}).json()
    assert body["source"]["provider"] == "openweather"
    assert body["current"]["wind_speed_kmh"] == 7.2  # 2 m/s -> km/h
    assert body["daily"][0]["rain_mm"] == 8.0  # 8 x 3-hour slots of 1 mm
    assert body["daily"][0]["et0_mm"] is None
    assert all(h == "api.openweathermap.org" for h in seen)


def test_openweather_invalid_key(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "openweather_api_key", "wrong-key")
    use_mock(monkeypatch, lambda request: httpx.Response(401, json={"message": "Invalid API key"}))
    r = client.get("/api/weather", params={"city": "Pune"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "WEATHER_KEY_INVALID"


def test_irrigation_endpoint(client, monkeypatch):
    use_mock(monkeypatch, open_meteo_handler())
    r = client.get("/api/irrigation/advice", params={"city": "Ludhiana", "crop": "wheat", "stage": "mid", "area_acres": 2})
    assert r.status_code == 200
    adv = r.json()["advice"]
    assert adv["action"] == "irrigate"
    est = adv["estimate"]
    assert est["kc"] == 1.15 and est["et0_mm"] == 15.0 and est["etc_mm"] == 17.2
    assert est["litres_for_farm"] == round(est["net_requirement_mm"] * irrigation_service.LITRES_PER_MM_PER_ACRE * 2)


def test_irrigation_endpoint_validation(client):
    r = client.get("/api/irrigation/advice", params={"city": "Ludhiana", "crop": "wheat", "stage": "flowering"})
    assert r.status_code == 422


# ---------------------------------------------------------------- pure rule tests
def make_weather(rain=(0, 0, 0), et0=(5, 5, 5), tmax=(32, 32, 32), tmin=(18, 18, 18), temp=28, humidity=55, wind=8):
    return {
        "current": {"temperature_c": temp, "humidity_pct": humidity, "wind_speed_kmh": wind},
        "daily": [{"date": f"d{i}", "rain_mm": rain[i], "rain_probability_pct": 80 if rain[i] else 5,
                   "et0_mm": et0[i] if et0 else None, "temp_max_c": tmax[i], "temp_min_c": tmin[i]} for i in range(3)],
    }


def test_delay_when_rain_expected():
    adv = irrigation_service.irrigation_advice(make_weather(rain=(12, 3, 0)), "wheat")
    assert adv["action"] == "delay"


def test_monitor_when_low_demand():
    adv = irrigation_service.irrigation_advice(make_weather(et0=(1, 1, 1)), "wheat", "initial")
    assert adv["action"] == "monitor"
    assert adv["estimate"]["net_requirement_mm"] == 0.9


def test_no_quantity_without_et0_or_unknown_crop():
    assert irrigation_service.irrigation_advice(make_weather(et0=None), "wheat")["estimate"] is None
    adv = irrigation_service.irrigation_advice(make_weather(), "dragonfruit")
    assert adv["estimate"] is None
    assert any("not in our table" in r for r in adv["reasons"])


def test_hot_dry_rule_without_et0():
    adv = irrigation_service.irrigation_advice(make_weather(et0=None, temp=38, humidity=30), "cotton")
    assert adv["action"] == "irrigate"


def test_rice_specific_note():
    adv = irrigation_service.irrigation_advice(make_weather(), "rice")
    assert any("standing water" in r for r in adv["reasons"])


@pytest.mark.parametrize("kwargs,alert", [
    ({"rain": (70, 0, 0)}, "heavy_rain"),
    ({"rain": (120, 0, 0)}, "very_heavy_rain"),
    ({"tmax": (42, 30, 30)}, "heat"),
    ({"tmin": (3, 10, 10)}, "frost"),
    ({"wind": 25}, "wind"),
    ({"humidity": 90, "temp": 22}, "disease_risk"),
])
def test_weather_alerts(kwargs, alert):
    types = {a["type"] for a in irrigation_service.weather_alerts(make_weather(**kwargs))}
    assert alert in types


def test_effective_rain():
    assert irrigation_service.effective_rain(4) == 0
    assert irrigation_service.effective_rain(10) == 8.0
