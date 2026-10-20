"""Farmer Advisory Assistant.

Provider is chosen by which key is configured in backend/.env:
  1. GEMINI_API_KEY    -> Google Gemini (REST generateContent API; has a free tier)
  2. ANTHROPIC_API_KEY -> Claude via the official Anthropic SDK
  3. neither           -> small offline knowledge base
If the AI call fails, the assistant falls back to the knowledge base and says so clearly —
it never pretends an AI answered.
"""

import json
import logging
import re
from pathlib import Path

from app.config import get_settings
from app.services.http_client import make_client

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

logger = logging.getLogger("krishiveda")
KB_FILE = Path(__file__).resolve().parent.parent / "data" / "knowledge_base.json"

# Models that accept the server-side refusal fallback parameter
_FALLBACK_MODELS = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}

SYSTEM_PROMPT = """You are KrishiVeda's farm advisory assistant for small and marginal farmers in India.
Answer questions about crops, irrigation, weather, soil, pests and disease prevention.

How to answer:
- Use simple words a farmer with little technical background understands. Keep answers short
  (about 80-150 words) and practical, with steps they can take.
- Reply in the language requested (English or Hindi in Devanagari script).
- For pesticide or fungicide use, give the general type of product and tell the farmer to follow
  the label dose and confirm with the local agriculture officer or Krishi Vigyan Kendra (KVK).
  Never invent brand-specific doses.
- If you are not sure, or the question needs a field visit or lab test, say so and suggest the
  Kisan Call Centre (1800-180-1551) or the nearest KVK.
- Do not claim to know live prices or today's weather; point to the app's Market Prices and Weather pages.
- Politely decline questions unrelated to farming."""


def _load_kb() -> list[dict]:
    return json.loads(KB_FILE.read_text(encoding="utf-8"))["entries"]


def active_provider() -> str:
    """'gemini', 'anthropic' or 'knowledge_base', depending on which key is configured."""
    settings = get_settings()
    if settings.gemini_api_key:
        return "gemini"
    if settings.anthropic_api_key:
        return "anthropic"
    return "knowledge_base"


def active_model() -> str | None:
    provider = active_provider()
    return {"gemini": get_settings().gemini_model, "anthropic": get_settings().advisory_model}.get(provider)


def ai_configured() -> bool:
    return active_provider() != "knowledge_base"


def _user_text(question: str, language: str, context: str | None) -> str:
    lang_name = "Hindi (Devanagari script)" if language == "hi" else "English"
    text = f"Answer in {lang_name}.\n"
    if context:
        text += f"Farmer context: {context}\n"
    return text + f"Question: {question}"


def knowledge_base_answer(question: str, language: str) -> tuple[str, str | None]:
    """Return (answer, matched_entry_id) using simple keyword scoring."""
    q = question.lower()
    words = set(re.findall(r"\w+", q))
    best, best_score = None, 0
    for entry in _load_kb():
        score = 0
        for kw in entry["keywords"]:
            kw_l = kw.lower()
            if " " in kw_l:
                score += 2 if kw_l in q else 0
            elif kw_l in words or (len(kw_l) > 3 and kw_l in q):
                score += 1
        if score > best_score:
            best, best_score = entry, score
    if not best:
        if language == "hi":
            return ("माफ़ कीजिए, इस प्रश्न का उत्तर ऑफ़लाइन ज्ञानकोष में नहीं है। सिंचाई, मिट्टी जाँच, कीट, रोग, पराली या "
                    "सरकारी योजनाओं के बारे में पूछें, या किसान कॉल सेंटर 1800-180-1551 पर कॉल करें।"), None
        return ("Sorry, the offline knowledge base does not cover this question. Try asking about irrigation, soil testing, "
                "pests, diseases, stubble management or government schemes, or call the Kisan Call Centre at 1800-180-1551."), None
    return best["answer_hi" if language == "hi" else "answer_en"], best["id"]


def _ask_claude(question: str, language: str, context: str | None, history: list[dict]) -> str:
    import anthropic

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=60.0)
    messages = [{"role": m["role"], "content": m["content"]} for m in history[-6:]]
    messages.append({"role": "user", "content": _user_text(question, language, context)})

    kwargs = {}
    if settings.advisory_model in _FALLBACK_MODELS:
        # If a safety classifier declines, the API retries on a fallback model automatically.
        kwargs = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
    response = client.beta.messages.create(
        model=settings.advisory_model,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        output_config={"effort": "low"},  # short conversational answers
        messages=messages,
        **kwargs,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("refusal")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise RuntimeError("empty response")
    return text


def _ask_gemini(question: str, language: str, context: str | None, history: list[dict]) -> str:
    """Call the Gemini generateContent REST API (uses the shared client: OS certificate store)."""
    settings = get_settings()
    contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in history[-6:]]
    contents.append({"role": "user", "parts": [{"text": _user_text(question, language, context)}]})
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 4096},  # room for the model's thinking + a short answer
    }
    with make_client(timeout=60.0) as client:
        resp = client.post(GEMINI_URL.format(model=settings.gemini_model), json=body,
                           headers={"x-goog-api-key": settings.gemini_api_key})
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini HTTP {resp.status_code}")  # bad key, quota, unknown model...
    data = resp.json()
    if data.get("promptFeedback", {}).get("blockReason"):
        raise RuntimeError("prompt blocked")
    parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    if not text:
        raise RuntimeError("empty response")
    return text


def answer(question: str, language: str = "en", context: str | None = None, history: list[dict] | None = None) -> dict:
    provider = active_provider()
    if provider != "knowledge_base":
        ask = _ask_gemini if provider == "gemini" else _ask_claude
        try:
            text = ask(question, language, context, history or [])
            return {"answer": text, "provider": provider, "model": active_model(), "notice": None}
        except Exception as exc:  # network errors, bad key, quota/rate limits, blocked or empty answers
            logger.warning("AI advisory (%s) failed, using knowledge base: %s", provider, exc)
            notice = "The AI assistant is unavailable right now, so this answer is from the offline knowledge base."
    else:
        notice = "AI assistant is not configured (no GEMINI_API_KEY). This answer is from the offline knowledge base."

    text, entry_id = knowledge_base_answer(question, language)
    return {"answer": text, "provider": "knowledge_base", "model": None, "matched_topic": entry_id, "notice": notice}
