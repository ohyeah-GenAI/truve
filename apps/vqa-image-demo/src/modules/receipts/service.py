import random

from supabase import Client

from src.modules.receipts.models import Receipt, ReceiptSummary


def get_receipt_by_id(db: Client, receipt_id: str) -> Receipt | None:
    res = db.table("receipts").select("*").eq("id", receipt_id).single().execute()
    if res.data:
        return Receipt(**res.data)
    return None


def get_random_receipt(db: Client, receipt_type: str | None = None) -> Receipt | None:
    query = db.table("receipts").select("id")
    if receipt_type:
        query = query.eq("receipt_type", receipt_type)
    id_res = query.execute()
    if not id_res.data:
        return None
    random_id = random.choice(id_res.data)["id"]
    res = db.table("receipts").select("*").eq("id", random_id).single().execute()
    if res.data:
        return Receipt(**res.data)
    return None


def get_random_captcha(db: Client, receipt_type: str | None = None):
    from src.modules.qa.models import CaptchaResponse

    receipt = get_random_receipt(db, receipt_type)
    if not receipt:
        return None

    qa_res = db.table("qa_pairs").select("id, question").eq("receipt_id", receipt.id).execute()
    if not qa_res.data:
        return None

    random_qa = random.choice(qa_res.data)
    return CaptchaResponse(
        receipt_id=receipt.id,
        receipt_type=receipt.receipt_type,
        image_data=receipt.image_data,
        question_id=random_qa["id"],
        question=random_qa["question"],
    )


def list_receipts(
    db: Client,
    batch_id: str | None = None,
    receipt_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[ReceiptSummary]:
    query = db.table("receipts").select("id, receipt_type, batch_id, created_at")
    if batch_id:
        query = query.eq("batch_id", batch_id)
    if receipt_type:
        query = query.eq("receipt_type", receipt_type)
    res = query.range(offset, offset + limit - 1).execute()
    return [ReceiptSummary(**row) for row in res.data]
