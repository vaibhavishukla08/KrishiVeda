"""Ask a human expert: farmers send questions, experts answer them in the Expert Panel.

Until farmer/expert login is built, the expert endpoints are protected by a shared access
code (EXPERT_ACCESS_CODE in backend/.env) sent in the X-Expert-Code header.
"""

import hmac
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import AppError
from app.api.farmers import get_farmer_or_404
from app.config import get_settings
from app.database.session import get_db
from app.models.orm import ExpertQuestion
from app.schemas.expert import ExpertAnswerIn, ExpertInboxItem, ExpertQuestionIn, ExpertQuestionOut

router = APIRouter(prefix="/api/expert", tags=["ask an expert"])

CONTACTS = {
    "helpline": {"name": "Kisan Call Centre", "phone": "1800-180-1551", "hours": "6 AM – 10 PM, all days",
                 "note": "Toll-free; agriculture experts answer in local languages"},
    "kvk_portal": {"name": "Krishi Vigyan Kendra (KVK) portal — find your district KVK", "url": "https://kvk.icar.gov.in"},
}


def require_expert(x_expert_code: str | None = Header(default=None)) -> None:
    code = get_settings().expert_access_code
    if not code:
        raise AppError(503, "EXPERT_PANEL_DISABLED",
                       "The Expert Panel is not set up. Add EXPERT_ACCESS_CODE to backend/.env and restart the backend.")
    if not x_expert_code or not hmac.compare_digest(x_expert_code.encode(), code.encode()):
        raise AppError(401, "INVALID_EXPERT_CODE", "Wrong expert access code.")


@router.get("/contacts")
def contacts():
    return {**CONTACTS, "panel_enabled": bool(get_settings().expert_access_code)}


@router.post("/questions", response_model=ExpertQuestionOut, status_code=201)
def ask_expert(payload: ExpertQuestionIn, db: Session = Depends(get_db)):
    if payload.farmer_id is not None:
        get_farmer_or_404(db, payload.farmer_id)
    q = ExpertQuestion(**payload.model_dump(), status="open")
    db.add(q)
    db.commit()
    return q


@router.get("/questions", response_model=list[ExpertQuestionOut])
def my_questions(farmer_id: int = Query(...), db: Session = Depends(get_db)):
    get_farmer_or_404(db, farmer_id)
    return db.execute(
        select(ExpertQuestion).where(ExpertQuestion.farmer_id == farmer_id)
        .order_by(ExpertQuestion.created_at.desc(), ExpertQuestion.id.desc()).limit(50)
    ).scalars().all()


# ---------------------------------------------------------------- expert side
@router.get("/verify", dependencies=[Depends(require_expert)])
def verify_code():
    return {"ok": True}


@router.get("/inbox", response_model=list[ExpertInboxItem], dependencies=[Depends(require_expert)])
def inbox(status: Literal["open", "answered", "all"] = "open", db: Session = Depends(get_db)):
    stmt = select(ExpertQuestion)
    if status != "all":
        stmt = stmt.where(ExpertQuestion.status == status)
    # Oldest open questions first so nobody waits too long; answered ones newest first
    order = ExpertQuestion.created_at.asc() if status == "open" else ExpertQuestion.created_at.desc()
    return db.execute(stmt.order_by(order, ExpertQuestion.id).limit(200)).scalars().all()


@router.post("/questions/{question_id}/answer", response_model=ExpertInboxItem, dependencies=[Depends(require_expert)])
def answer_question(question_id: int, payload: ExpertAnswerIn, db: Session = Depends(get_db)):
    q = db.get(ExpertQuestion, question_id)
    if not q:
        raise AppError(404, "QUESTION_NOT_FOUND", f"Question {question_id} was not found.")
    q.answer = payload.answer.strip()
    q.expert_name = payload.expert_name.strip()
    q.status = "answered"
    q.answered_at = datetime.now(timezone.utc)
    db.commit()
    return q
