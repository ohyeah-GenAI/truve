from sqlalchemy import text
from sqlalchemy.orm import Session

from src.modules.qa.models import QAPair, QuestionOnly, VerifyRequest, VerifyResponse, VerifyResult


def verify_single_answer(db: Session, question_id: int, user_answer: str) -> bool:
    """단일 질문 ID와 사용자 답변을 검증. 정답이면 True 반환."""
    result = db.execute(
        text("SELECT answer FROM qa_pairs WHERE id = :question_id"),
        {"question_id": question_id},
    )
    row = result.fetchone()
    if not row:
        return False
    expected = row[0]
    return expected.strip().lower() == user_answer.strip().lower()


def get_questions(db: Session, receipt_id: str) -> list[QuestionOnly]:
    result = db.execute(
        text(
            "SELECT id, receipt_id, question, `order` FROM qa_pairs "
            "WHERE receipt_id = :receipt_id ORDER BY `order`"
        ),
        {"receipt_id": receipt_id},
    )
    return [
        QuestionOnly(id=row[0], receipt_id=row[1], question=row[2], order=row[3])
        for row in result.fetchall()
    ]


def get_qa_pairs(db: Session, receipt_id: str) -> list[QAPair]:
    result = db.execute(
        text("SELECT id, receipt_id, question, answer, `order`, created_at FROM qa_pairs "
             "WHERE receipt_id = :receipt_id ORDER BY `order`"),
        {"receipt_id": receipt_id},
    )
    return [
        QAPair(
            id=row[0],
            receipt_id=row[1],
            question=row[2],
            answer=row[3],
            order=row[4],
            created_at=row[5],
        )
        for row in result.fetchall()
    ]


def verify_answers(db: Session, receipt_id: str, request: VerifyRequest) -> VerifyResponse:
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
