from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.database import get_supabase
from app.modules.qa.models import CaptchaResponse
from app.modules.receipts import service
from app.modules.receipts.models import Receipt, ReceiptSummary

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.get("/random", response_model=CaptchaResponse)
def get_random_captcha(
    receipt_type: str | None = Query(None, description="영수증 종류 (restaurant 등)"),
    db: Client = Depends(get_supabase),
):
    captcha = service.get_random_captcha(db, receipt_type)
    if not captcha:
        raise HTTPException(status_code=404, detail="영수증 또는 질문을 찾을 수 없습니다.")
    return captcha


@router.get("", response_model=list[ReceiptSummary])
def list_receipts(
    batch_id: str | None = Query(None),
    receipt_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Client = Depends(get_supabase),
):
    return service.list_receipts(db, batch_id, receipt_type, limit, offset)


@router.get("/{receipt_id}", response_model=Receipt)
def get_receipt(receipt_id: str, db: Client = Depends(get_supabase)):
    receipt = service.get_receipt_by_id(db, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="영수증을 찾을 수 없습니다.")
    return receipt
