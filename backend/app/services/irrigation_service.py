"""Rule-based irrigation guidance and weather alerts.

Measured inputs : weather provider data (temperature, humidity, rain, ET0 forecast).
Estimated output: crop water demand using the FAO-56 single crop coefficient method
                  ETc = Kc x ET0  (Allen et al., 1998, FAO Irrigation and Drainage Paper 56).

This does NOT know the actual soil moisture of the field, so every number is an estimate
and the farmer should check soil moisture before irrigating.
"""

LITRES_PER_MM_PER_ACRE = 4046.86  # 1 mm of water over 1 acre (4046.86 m^2)

# FAO-56 Table 12 single crop coefficients: (initial, mid-season, late-season)
KC_VALUES: dict[str, tuple[float, float, float]] = {
    "rice": (1.05, 1.20, 0.75),
    "wheat": (0.30, 1.15, 0.30),
    "maize": (0.30, 1.20, 0.60),
    "cotton": (0.35, 1.18, 0.60),
    "sugarcane": (0.40, 1.25, 0.75),
    "potato": (0.50, 1.15, 0.75),
    "tomato": (0.60, 1.15, 0.80),
    "soybean": (0.40, 1.15, 0.50),
    "chickpea": (0.40, 1.00, 0.35),
    "lentil": (0.40, 1.10, 0.30),
    "groundnut": (0.40, 1.15, 0.60),
    "mustard": (0.35, 1.08, 0.35),
    "onion": (0.70, 1.05, 0.75),
    "pepper": (0.60, 1.05, 0.90),
    "banana": (0.50, 1.10, 1.00),
}
STAGES = ("initial", "mid", "late")

# Thresholds (India Meteorological Department categories where applicable)
HEAVY_RAIN_MM = 64.5  # IMD "heavy rainfall" lower limit (24 h)
VERY_HEAVY_RAIN_MM = 115.6  # IMD "very heavy rainfall" lower limit (24 h)
HEAT_C = 40.0
FROST_C = 4.0
SPRAY_WIND_KMH = 15.0
INEFFECTIVE_RAIN_MM = 5.0  # simplified assumption: light showers mostly evaporate
EFFECTIVE_RAIN_FRACTION = 0.8


def effective_rain(rain_mm: float) -> float:
    """Simplified effective rainfall: rain below 5 mm/day is ignored, 80% of the rest counts."""
    if rain_mm is None or rain_mm <= INEFFECTIVE_RAIN_MM:
        return 0.0
    return round(EFFECTIVE_RAIN_FRACTION * rain_mm, 1)


def weather_alerts(weather: dict) -> list[dict]:
    alerts = []
    cur = weather["current"]
    for day in weather["daily"][:3]:
        rain = day.get("rain_mm") or 0
        if rain >= VERY_HEAVY_RAIN_MM:
            alerts.append({"type": "very_heavy_rain", "severity": "high", "date": day["date"],
                           "message": f"Very heavy rain forecast ({rain:.0f} mm). Ensure field drainage; postpone spraying and fertiliser."})
        elif rain >= HEAVY_RAIN_MM:
            alerts.append({"type": "heavy_rain", "severity": "medium", "date": day["date"],
                           "message": f"Heavy rain forecast ({rain:.0f} mm). Clear drainage channels; avoid irrigation and spraying."})
        if (day.get("temp_max_c") or 0) >= HEAT_C:
            alerts.append({"type": "heat", "severity": "medium", "date": day["date"],
                           "message": f"High temperature forecast ({day['temp_max_c']:.0f}°C). Irrigate in early morning or evening; protect nurseries."})
        if day.get("temp_min_c") is not None and day["temp_min_c"] <= FROST_C:
            alerts.append({"type": "frost", "severity": "medium", "date": day["date"],
                           "message": f"Cold night forecast ({day['temp_min_c']:.0f}°C). Light irrigation in the evening can reduce frost damage."})
    if (cur.get("wind_speed_kmh") or 0) > SPRAY_WIND_KMH:
        alerts.append({"type": "wind", "severity": "low", "date": None,
                       "message": f"Wind is {cur['wind_speed_kmh']:.0f} km/h. Avoid spraying pesticides now (spray drift)."})
    hum, temp = cur.get("humidity_pct"), cur.get("temperature_c")
    if hum is not None and temp is not None and hum >= 85 and 15 <= temp <= 28:
        alerts.append({"type": "disease_risk", "severity": "low", "date": None,
                       "message": "Humid, mild weather favours fungal diseases (e.g. blights, mildews). Inspect leaves regularly."})
    return alerts


def irrigation_advice(weather: dict, crop: str, stage: str = "mid", area_acres: float | None = None) -> dict:
    crop = crop.lower().strip()
    stage = stage if stage in STAGES else "mid"
    kc = KC_VALUES[crop][STAGES.index(stage)] if crop in KC_VALUES else None

    days = weather["daily"][:3]
    rain_next_2d = sum((d.get("rain_mm") or 0) for d in days[:2])
    max_prob_2d = max(((d.get("rain_probability_pct") or 0) for d in days[:2]), default=0)
    cur = weather["current"]
    reasons: list[str] = []

    # --- FAO-56 estimate (only when the provider gives ET0 and we know the crop's Kc)
    estimate = None
    et0_values = [d.get("et0_mm") for d in days]
    if kc is not None and all(v is not None for v in et0_values):
        et0 = round(sum(et0_values), 1)
        etc = round(kc * et0, 1)
        rain = round(sum((d.get("rain_mm") or 0) for d in days), 1)
        eff = round(sum(effective_rain(d.get("rain_mm") or 0) for d in days), 1)
        net = round(max(0.0, etc - eff), 1)
        estimate = {
            "method": "FAO-56 single crop coefficient: ETc = Kc × ET0",
            "period_days": len(days),
            "kc": kc,
            "et0_mm": et0,
            "etc_mm": etc,
            "forecast_rain_mm": rain,
            "effective_rain_mm": eff,
            "net_requirement_mm": net,
            "litres_per_acre": round(net * LITRES_PER_MM_PER_ACRE),
            "litres_for_farm": round(net * LITRES_PER_MM_PER_ACRE * area_acres) if area_acres else None,
            "assumptions": [
                "Soil moisture is unknown; the estimate assumes the root zone is not already wet.",
                "Effective rain: rain under 5 mm/day ignored, 80% of the rest counted (simplified).",
                "Irrigation system losses are not included (add ~10–40% depending on method).",
            ],
        }

    # --- Decision rules
    if rain_next_2d >= 10 or (max_prob_2d >= 70 and rain_next_2d >= 5):
        action = "delay"
        headline = "Postpone irrigation — rain is expected"
        reasons.append(f"About {rain_next_2d:.0f} mm of rain forecast in the next 2 days (max chance {max_prob_2d:.0f}%).")
    elif estimate and estimate["net_requirement_mm"] >= 15:
        action = "irrigate"
        headline = "Irrigation likely needed in the next 3 days"
        reasons.append(f"Estimated crop water use ({estimate['etc_mm']} mm) is higher than useful rain ({estimate['effective_rain_mm']} mm).")
    elif not estimate and (cur.get("temperature_c") or 0) >= 35 and (cur.get("humidity_pct") or 100) < 50:
        action = "irrigate"
        headline = "Hot and dry — check soil and irrigate if dry"
        reasons.append("High temperature and low humidity increase water loss from soil and leaves.")
    else:
        action = "monitor"
        headline = "No urgent irrigation — keep monitoring soil moisture"
        if estimate:
            reasons.append(f"Estimated net need is small ({estimate['net_requirement_mm']} mm over 3 days).")
        else:
            reasons.append("No strong signal from the weather forecast.")

    if crop == "rice":
        reasons.append("For transplanted paddy, keep 2–5 cm standing water during early growth; drain 10–15 days before harvest. "
                       "Percolation losses in paddy are not included in the estimate.")
    if kc is None:
        reasons.append(f"Crop coefficient for '{crop}' is not in our table, so no water-quantity estimate is shown.")
    reasons.append("Best time to irrigate is early morning or evening to reduce evaporation.")

    return {
        "crop": crop,
        "stage": stage,
        "action": action,
        "headline": headline,
        "reasons": reasons,
        "estimate": estimate,
        "alerts": weather_alerts(weather),
        "disclaimer": "Estimated guidance from weather data and FAO-56 crop coefficients. "
                      "Check soil moisture (e.g. squeeze a handful of soil from root depth) before irrigating.",
    }
