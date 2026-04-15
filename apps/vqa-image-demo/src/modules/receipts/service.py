import random

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.modules.receipts.models import Receipt, ReceiptSummary


def get_receipt_by_id(db: Session, receipt_id: str) -> Receipt | None:
    result = db.execute(
        text("SELECT id, receipt_type, content, image_data, batch_id, created_at, updated_at "
             "FROM receipts WHERE id = :receipt_id"),
        {"receipt_id": receipt_id},
    )
    row = result.fetchone()
    if not row:
        return None
    return Receipt(
        id=row[0],
        receipt_type=row[1],
        content=row[2],
        image_data=row[3],
        batch_id=row[4],
        created_at=row[5],
        updated_at=row[6],
    )


def get_random_receipt(db: Session, receipt_type: str | None = None) -> Receipt | None:
    if receipt_type:
        result = db.execute(
            text("SELECT id FROM receipts WHERE receipt_type = :receipt_type"),
            {"receipt_type": receipt_type},
        )
    else:
        result = db.execute(text("SELECT id FROM receipts"))

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
        text("SELECT id, question FROM qa_pairs WHERE receipt_id = :receipt_id"),
        {"receipt_id": receipt.id},
    )
    qa_rows = result.fetchall()
    if not qa_rows:
        return None

    random_qa = random.choice(qa_rows)
    return CaptchaResponse(
        receipt_id=receipt.id,
        receipt_type=receipt.receipt_type,
        image_data=receipt.image_data,
        question_id=random_qa[0],
        question=random_qa[1],
    )


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
    query = text(
        f"SELECT id, receipt_type, batch_id, created_at FROM receipts "
        f"{where_sql} LIMIT :limit OFFSET :offset"
    )
    result = db.execute(query, params)
    return [
        ReceiptSummary(id=row[0], receipt_type=row[1], batch_id=row[2], created_at=row[3])
        for row in result.fetchall()
    ]
