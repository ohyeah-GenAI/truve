from supabase import Client
from app.modules.receipts.models import Receipt, ReceiptSummary


def get_receipt_by_id(db: Client, receipt_id: str) -> Receipt | None:
    res = db.table("receipts").select("*").eq("id", receipt_id).single().execute()
    if res.data:
        return Receipt(**res.data)
    return None


def get_random_receipt(db: Client, receipt_type: str | None = None) -> Receipt | None:
    query = db.table("receipts").select("*")
    if receipt_type:
        query = query.eq("receipt_type", receipt_type)
    # Supabase에서 랜덤 1개 가져오기
    res = query.limit(1).execute()
    if res.data:
        return Receipt(**res.data[0])
    return None


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
