from supabase import Client
from app.modules.qa.models import QAPair, QuestionOnly, VerifyRequest, VerifyResponse, VerifyResult


def get_questions(db: Client, receipt_id: str) -> list[QuestionOnly]:
    """영수증의 질문 목록만 반환 (정답 제외)"""
    res = (
        db.table("qa_pairs")
        .select("id, receipt_id, question, order")
        .eq("receipt_id", receipt_id)
        .order("order")
        .execute()
    )
    return [QuestionOnly(**row) for row in res.data]


def get_qa_pairs(db: Client, receipt_id: str) -> list[QAPair]:
    """영수증의 전체 Q&A (정답 포함, 내부용)"""
    res = (
        db.table("qa_pairs")
        .select("*")
        .eq("receipt_id", receipt_id)
        .order("order")
        .execute()
    )
    return [QAPair(**row) for row in res.data]


def verify_answers(db: Client, receipt_id: str, request: VerifyRequest) -> VerifyResponse:
    """사용자 답변 검증"""
    qa_pairs = get_qa_pairs(db, receipt_id)
    qa_map = {qa.id: qa for qa in qa_pairs}

    results = []
    for submission in request.answers:
        qa = qa_map.get(submission.question_id)
        if qa is None:
            continue
        correct = qa.answer.strip().lower() == submission.answer.strip().lower()
        results.append(
            VerifyResult(
                question_id=submission.question_id,
                correct=correct,
                expected=qa.answer,
                submitted=submission.answer,
            )
        )

    correct_count = sum(1 for r in results if r.correct)
    return VerifyResponse(
        receipt_id=receipt_id,
        total=len(results),
        correct_count=correct_count,
        passed=correct_count == len(results) and len(results) > 0,
        results=results,
    )
