"""Ask an Expert: farmer submits a question, expert answers it in the panel, farmer sees the reply."""

import pytest

CODE = "test-expert-code"


@pytest.fixture
def expert_code(settings, monkeypatch):
    monkeypatch.setattr(settings, "expert_access_code", CODE)
    return {"X-Expert-Code": CODE}


def ask(client, farmer_id=None, **overrides):
    body = {"farmer_id": farmer_id, "farmer_name": "Test Farmer", "phone": "9876543210", "crop": "wheat",
            "category": "disease", "question": "Yellow stripes are appearing on my wheat leaves. What should I do?",
            "language": "en", **overrides}
    return client.post("/api/expert/questions", json=body)


def test_contacts(client):
    body = client.get("/api/expert/contacts").json()
    assert body["helpline"]["phone"] == "1800-180-1551"
    assert body["kvk_portal"]["url"] == "https://kvk.icar.gov.in"


def test_full_question_and_answer_flow(client, farmer, expert_code):
    r = ask(client, farmer["id"])
    assert r.status_code == 201, r.text
    q = r.json()
    assert q["status"] == "open" and "phone" not in q  # phone is never echoed in farmer views

    inbox = client.get("/api/expert/inbox", headers=expert_code).json()
    item = next(i for i in inbox if i["id"] == q["id"])
    assert item["phone"] == "9876543210"  # experts can call back

    r = client.post(f"/api/expert/questions/{q['id']}/answer", headers=expert_code,
                    json={"expert_name": "Dr. Sharma, KVK", "answer": "This looks like yellow rust. Contact your KVK for a field visit."})
    assert r.status_code == 200
    assert r.json()["status"] == "answered" and r.json()["answered_at"]

    mine = client.get("/api/expert/questions", params={"farmer_id": farmer["id"]}).json()
    assert mine[0]["status"] == "answered" and mine[0]["expert_name"] == "Dr. Sharma, KVK"
    assert all(i["id"] != q["id"] for i in client.get("/api/expert/inbox", headers=expert_code).json())  # no longer open


def test_expert_endpoints_need_correct_code(client, expert_code):
    assert client.get("/api/expert/inbox").status_code == 401
    r = client.get("/api/expert/inbox", headers={"X-Expert-Code": "wrong"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "INVALID_EXPERT_CODE"
    assert client.get("/api/expert/verify", headers=expert_code).json() == {"ok": True}


def test_panel_disabled_without_code(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "expert_access_code", "")
    r = client.get("/api/expert/inbox", headers={"X-Expert-Code": "anything"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "EXPERT_PANEL_DISABLED"


def test_question_validation(client):
    r = ask(client, question="help", phone="12345", category="astrology")
    assert r.status_code == 422
    fields = {f["field"] for f in r.json()["error"]["details"]["fields"]}
    assert {"question", "phone", "category"} <= fields
    assert ask(client, farmer_id=999999).status_code == 404


def test_answer_unknown_question(client, expert_code):
    r = client.post("/api/expert/questions/999999/answer", headers=expert_code,
                    json={"expert_name": "Expert", "answer": "Some answer"})
    assert r.status_code == 404
