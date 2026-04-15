from datetime import datetime

from pydantic import BaseModel


class Receipt(BaseModel):
    id: str
    receipt_type: str | None = "restaurant"
    content: str
    image_data: str | None = None
    batch_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ReceiptSummary(BaseModel):
    id: str
    receipt_type: str | None = "restaurant"
    batch_id: str | None = None
    created_at: datetime | None = None
