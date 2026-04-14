from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.modules.qa import service
from src.modules.qa.models import QuestionOnly, VerifyRequest, VerifyResponse

router = APIRouter(prefix="/receipts", tags=["qa"])


@router.get("/{receipt_id}/questions", response_model=list[QuestionOnly])
def get_questions(receipt_id: str, db: Session = Depends(get_db)):
    questions = service.get_questions(db, receipt_id)
    if not questions:
        raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다.")
    return questions


@router.post("/{receipt_id}/verify", response_model=VerifyResponse)
def verify_answers(
    receipt_id: str,
    request: VerifyRequest,
    db: Session = Depends(get_db),
):
    return service.verify_answers(db, receipt_id, request)
