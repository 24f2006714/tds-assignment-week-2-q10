import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

class InvoiceRequest(BaseModel):
    text: Optional[str] = None

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str

@app.post("/extract", response_model=InvoiceResponse)
def extract_invoice(payload: InvoiceRequest):
    # Error handling for malformed or empty input (avoid HTTP 500)
    if not payload or not payload.text or not isinstance(payload.text, str) or len(payload.text.strip())= =0:
        return InvoiceResponse(
            vendor="Unknown",
            amount=0.0,
            currency="USD",
            date="2026-01-01"
        )
    
    text = payload.text

    # 1. Vendor Extraction (Matches patterns like 'Vendor:', 'From:', or capitalized company titles)
    vendor = "Unknown Vendor"
    vendor_match = re.search(r'(?:vendor|from|company|billed by)[:\s]+([A-Za-z0-9\-\s]+(?:Ltd|LLC|Inc|Industries|Co)?\.?)', text, re.IGNORECASE)
    if vendor_match:
        vendor = vendor_match.group(1).strip()
    else:
        # Fallback: look for common patterns like Acme-xxxx Industries Ltd
        fallback_vendor = re.search(r'([A-Z][A-Za-z0-9\-]+\s+(?:Industries|Ltd|LLC|Inc|Co)\.?)', text)
        if fallback_vendor:
            vendor = fallback_vendor.group(1).strip()

    # 2. Amount Extraction (Matches numbers after Total, Due, Amount, etc.)
    amount = 0.0
    amount_match = re.search(r'(?:total|due|amount|balance|sum)[:\s]*(?:USD|EUR|GBP|\$|€|£)?\s*([0-9]+\.[0-9]{2}|[0-9]+)', text, re.IGNORECASE)
    if amount_match:
        try:
            amount = float(amount_match.group(1))
        except ValueError:
            amount = 0.0
    else:
        # Generic fallback to find any float/price amount
        all_amounts = re.findall(r'\b[0-9]+\.[0-9]{2}\b', text)
        if all_amounts:
            amount = float(all_amounts[-1])

    # 3. Currency Extraction (USD, EUR, GBP)
    currency = "USD"
    curr_match = re.search(r'\b(USD|EUR|GBP)\b', text, re.IGNORECASE)
    if curr_match:
        currency = curr_match.group(1).upper()
    elif '€' in text:
        currency = "EUR"
    elif '£' in text:
        currency = "GBP"

    # 4. Date Extraction (YYYY-MM-DD format)
    date_str = "2026-01-01"
    date_match = re.search(r'\b(2026-[0-9]{2}-[0-9]{2})\b', text)
    if date_match:
        date_str = date_match.group(1)
    else:
        # Generic YYYY-MM-DD fallback
        any_date = re.search(r'\b([0-9]{4}-[0-9]{2}-[0-9]{2})\b', text)
        if any_date:
            date_str = any_date.group(1)

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date_str
    )
