"""Pydantic data models — the single source of truth for API contracts."""

from pydantic import BaseModel, Field
from typing import Optional


class ReceiptItem(BaseModel):
    """A single line item on the receipt."""
    product_name: str = Field(..., description="商品名称")
    price: float = Field(..., description="单价")


class ReceiptData(BaseModel):
    """Structured receipt data extracted by LLM."""
    date: str = Field(..., description="小票日期, format YYYY-MM-DD")
    store_name: str = Field(..., description="店名")
    items: list[ReceiptItem] = Field(..., description="商品列表")
    total_price: float = Field(..., description="总价")
    tax: float = Field(0.0, description="税费")


class ProcessResponse(BaseModel):
    """Response returned to the frontend after processing."""
    success: bool
    receipt_data: Optional[ReceiptData] = None
    drive_link: Optional[str] = None
    message: str = ""
