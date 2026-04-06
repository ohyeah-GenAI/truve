from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.database import get_supabase
from app.modules.qa import service
from app.modules.qa.models import QuestionOnly, VerifyRequest, VerifyResponse

router = APIRouter(prefix="/receipts", tags=["qa"])


@router.get("/{receipt_id}/questions", response_model=list[QuestionOnly])
def get_questions(receipt_id: str, db: Client = Depends(get_supabase)):
    """영수증에 대한 질문 목록 반환 (정답 미포함)"""
    questions = service.get_questions(db, receipt_id)
    if not questions:
        raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다.")
    return questions


@router.post("/{receipt_id}/verify", response_model=VerifyResponse)
def verify_answers(
    receipt_id: str,
    request: VerifyRequest,
    db: Client = Depends(get_supabase),
):
    """사용자 답변 제출 및 정답 검증"""
    return service.verify_answers(db, receipt_id, request)
