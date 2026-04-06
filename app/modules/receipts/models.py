from pydantic import BaseModel
from datetime import datetime


class Receipt(BaseModel):
    id: str
    receipt_type: str | None = "restaurant"
    content: str
    image_data: str | None = None
    batch_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ReceiptSummary(BaseModel):
    """이미지 없이 기본 정보만 반환 (목록 조회용)"""
    id: str
    receipt_type: str | None = "restaurant"
    batch_id: str | None = None
    created_at: datetime | None = None
