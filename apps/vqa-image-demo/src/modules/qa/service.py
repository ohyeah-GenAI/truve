from sqlalchemy import text
from sqlalchemy.orm import Session

from src.modules.qa.models import QAPair, QuestionOnly, VerifyRequest, VerifyResponse, VerifyResult
from src.session_store import pop_session


def normalize_answer(value: str) -> str:
    return value.strip().lower()


def _fetch_answer_by_question_id(db: Session, question_id: int) -> str | None:
    row = db.execute(
        text("SELECT answer FROM qa_pairs WHERE qa_id = :question_id"),
        {"question_id": question_id},
    ).fetchone()
    if not row:
        return None
    return row[0]


def verify_single_answer(db: Session, question_id: int, user_answer: str) -> bool:
    """단일 질문 ID와 사용자 답변을 검증. 정답이면 True 반환."""
    expected = _fetch_answer_by_question_id(db, question_id)
    if expected is None:
        return False
    return normalize_answer(expected) == normalize_answer(user_answer)


def verify_session_answer(session_id: str, user_answer: str) -> bool:
    session = pop_session(session_id)
    if not session:
        return False
    expected = session.get("expected_answer")
    if expected is None:
        return False
    expected = str(expected)
    return normalize_answer(expected) == normalize_answer(user_answer)


def get_questions(db: Session, receipt_id: str) -> list[QuestionOnly]:
    result = db.execute(
        text(
            "SELECT qa_id, receipt_id, question, 1 AS display_order "
            "FROM qa_pairs WHERE receipt_id = :receipt_id"
        ),
        {"receipt_id": receipt_id},
    )
    return [
        QuestionOnly(id=row[0], receipt_id=row[1], question=row[2], order=row[3])
        for row in result.fetchall()
    ]


def get_qa_pairs(db: Session, receipt_id: str) -> list[QAPair]:
    result = db.execute(
        text(
            "SELECT qa_id, receipt_id, question, answer, 1 AS display_order, NULL AS created_at "
            "FROM qa_pairs WHERE receipt_id = :receipt_id"
        ),
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
        correct = normalize_answer(qa.answer) == normalize_answer(submission.answer)
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
