import random

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.modules.receipts.models import Receipt, ReceiptSummary
from src.session_store import create_session


def _to_data_url(image_data: str | None) -> str | None:
    if not image_data:
        return None
    if image_data.startswith("data:image"):
        return image_data
    if image_data.startswith(("http://", "https://")):
        return image_data
    return f"data:image/png;base64,{image_data}"


def get_receipt_by_id(db: Session, receipt_id: str) -> Receipt | None:
    result = db.execute(
        text(
            "SELECT receipt_id, category AS receipt_type, '' AS content, image_data, "
            "NULL AS batch_id, NULL AS created_at, NULL AS updated_at "
            "FROM receipts WHERE receipt_id = :receipt_id"
        ),
        {"receipt_id": receipt_id},
    )
    row = result.fetchone()
    if not row:
        return None
    return Receipt(
        id=str(row[0]),
        receipt_type=row[1],
        content=row[2],
        image_data=_to_data_url(row[3]),
        batch_id=row[4],
        created_at=row[5],
        updated_at=row[6],
    )


def get_random_receipt(db: Session, receipt_type: str | None = None) -> Receipt | None:
    if receipt_type:
        result = db.execute(
            text(
                "SELECT receipt_id FROM receipts "
                "WHERE category = :receipt_type "
                "AND receipt_id IS NOT NULL "
                "AND image_data IS NOT NULL "
                "AND TRIM(image_data) <> '' "
                "AND EXISTS ("
                "  SELECT 1 FROM qa_pairs "
                "  WHERE qa_pairs.receipt_id = receipts.receipt_id "
                "  AND qa_pairs.answer IS NOT NULL "
                "  AND TRIM(qa_pairs.answer) <> ''"
                ")"
            ),
            {"receipt_type": receipt_type},
        )
    else:
        result = db.execute(
            text(
                "SELECT receipt_id FROM receipts "
                "WHERE receipt_id IS NOT NULL "
                "AND image_data IS NOT NULL "
                "AND TRIM(image_data) <> '' "
                "AND EXISTS ("
                "  SELECT 1 FROM qa_pairs "
                "  WHERE qa_pairs.receipt_id = receipts.receipt_id "
                "  AND qa_pairs.answer IS NOT NULL "
                "  AND TRIM(qa_pairs.answer) <> ''"
                ")"
            )
        )

    ids = [row[0] for row in result.fetchall()]
    if not ids:
        return None

    random_id = random.choice(ids)
    return get_receipt_by_id(db, random_id)


def get_random_captcha(db: Session, receipt_type: str | None = None):
    from src.modules.qa.models import CaptchaResponse

    receipt = get_random_receipt(db, receipt_type)
    if not receipt:
        return None

    result = db.execute(
        text(
            "SELECT qa_id, question FROM qa_pairs "
            "WHERE receipt_id = :receipt_id "
            "AND answer IS NOT NULL "
            "AND TRIM(answer) <> ''"
        ),
        {"receipt_id": receipt.id},
    )
    qa_rows = result.fetchall()
    if not qa_rows:
        return None

    random_qa = random.choice(qa_rows)
    return CaptchaResponse(
        receipt_id=receipt.id,
        receipt_type=receipt.receipt_type,
        image_data=_to_data_url(receipt.image_data),
        question_id=random_qa[0],
        question=random_qa[1],
    )


def generate_challenge_puzzle(db: Session, receipt_type: str | None = None) -> dict | None:
    captcha = get_random_captcha(db, receipt_type)
    if not captcha:
        return None
    if not captcha.image_data:
        return None

    answer_row = db.execute(
        text("SELECT answer FROM qa_pairs WHERE qa_id = :question_id"),
        {"question_id": captcha.question_id},
    ).fetchone()
    if not answer_row or answer_row[0] is None or str(answer_row[0]).strip() == "":
        return None

    session_id = create_session(captcha.receipt_id, captcha.question_id, answer_row[0])
    return {
        "session_id": session_id,
        "puzzle_type": "vqa-image",
        "puzzle_config": {
            "question": captcha.question,
            "image_data": captcha.image_data,
            "answer_schema": {
                "type": "text",
                "placeholder": "정답을 입력하세요",
            },
        },
    }


def list_receipts(
    db: Session,
    batch_id: str | None = None,
    receipt_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[ReceiptSummary]:
    where_clauses = []
    params: dict = {"limit": limit, "offset": offset}

    if batch_id:
        where_clauses.append("batch_id = :batch_id")
        params["batch_id"] = batch_id
    if receipt_type:
        where_clauses.append("receipt_type = :receipt_type")
        params["receipt_type"] = receipt_type

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    result = db.execute(
        text(
            f"SELECT receipt_id, category AS receipt_type, NULL AS batch_id, NULL AS created_at FROM receipts "
            f"{where_sql.replace('receipt_type', 'category')} LIMIT :limit OFFSET :offset"
        ),
        params,
    )
    return [
        ReceiptSummary(id=str(row[0]), receipt_type=row[1], batch_id=row[2], created_at=row[3])
        for row in result.fetchall()
    ]
