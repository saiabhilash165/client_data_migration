import os
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


from db.database import (
    init_db,
    create_sales_deal,
    update_sales_deal,
    get_all_sales_deals,
    get_sales_deal_by_key,
    get_sales_deals_by_deal_id,
    delete_sales_deals_by_deal_id,
    clear_sales_deals
)


app = FastAPI(title="Mock Sales Deals API")


class SalesDeal(BaseModel):
    country: str
    deal_id: str
    company_name: str
    contact_email: Optional[str] = None
    deal_value_usd: float
    sales_stage: str
    expected_close_date: str
    customer_segment: Optional[str] = None
    tax_id: Optional[str] = None
    source_file: Optional[str] = ""


def model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def home():
    return {
        "message": "Mock Sales Deals API is running",
        "storage": "SQLite",
        "database": "migration.db",
        "table": "sales_deals"
    }


@app.post("/sales-deals")
def create_sales_deal_endpoint(record: SalesDeal):
    record_dict = model_to_dict(record)

    existing = get_sales_deal_by_key(
        country=record_dict.get("country"),
        deal_id=record_dict.get("deal_id")
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Sales deal already exists in sales_deals table"
        )

    result = create_sales_deal(record_dict)

    if not result.get("created"):
        raise HTTPException(
            status_code=409,
            detail="Sales deal already exists in sales_deals table"
        )

    return {
        "status": "success",
        "action": "created",
        "storage": "SQLite",
        "table": "sales_deals",
        "record_key": result.get("record_key"),
        "record": result.get("record")
    }


@app.put("/sales-deals/{deal_id}")
def update_sales_deal_endpoint(deal_id: str, record: SalesDeal):
    record_dict = model_to_dict(record)
    record_dict["deal_id"] = str(deal_id)

    result = update_sales_deal(record_dict)

    if not result.get("updated"):
        raise HTTPException(
            status_code=404,
            detail="Sales deal not found in sales_deals table"
        )

    return {
        "status": "success",
        "action": "updated",
        "storage": "SQLite",
        "table": "sales_deals",
        "record_key": result.get("record_key"),
        "record": result.get("record")
    }


@app.get("/sales-deals")
def get_sales_deals_endpoint():
    records = get_all_sales_deals()

    clean_records = []

    for record in records:
        clean_records.append(
            {
                "id": record.get("id"),
                "record_key": record.get("record_key"),
                "country": record.get("country"),
                "deal_id": record.get("deal_id"),
                "company_name": record.get("company_name"),
                "contact_email": record.get("contact_email"),
                "deal_value_usd": record.get("deal_value_usd"),
                "sales_stage": record.get("sales_stage"),
                "expected_close_date": record.get("expected_close_date"),
                "customer_segment": record.get("customer_segment"),
                "tax_id": record.get("tax_id"),
                "source_file": record.get("source_file"),
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at")
            }
        )

    return {
        "storage": "SQLite",
        "database": "migration.db",
        "table": "sales_deals",
        "count": len(clean_records),
        "records": clean_records
    }


@app.get("/sales-deals/{deal_id}")
def get_sales_deal_endpoint(deal_id: str):
    records = get_sales_deals_by_deal_id(deal_id)

    if not records:
        raise HTTPException(
            status_code=404,
            detail="Sales deal not found in sales_deals table"
        )

    clean_records = []

    for record in records:
        clean_records.append(
            {
                "id": record.get("id"),
                "record_key": record.get("record_key"),
                "country": record.get("country"),
                "deal_id": record.get("deal_id"),
                "company_name": record.get("company_name"),
                "contact_email": record.get("contact_email"),
                "deal_value_usd": record.get("deal_value_usd"),
                "sales_stage": record.get("sales_stage"),
                "expected_close_date": record.get("expected_close_date"),
                "customer_segment": record.get("customer_segment"),
                "tax_id": record.get("tax_id"),
                "source_file": record.get("source_file"),
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at")
            }
        )

    return {
        "storage": "SQLite",
        "table": "sales_deals",
        "count": len(clean_records),
        "records": clean_records
    }


@app.delete("/sales-deals/{deal_id}")
def delete_sales_deal_endpoint(deal_id: str):
    deleted_count = delete_sales_deals_by_deal_id(deal_id)

    if deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Sales deal not found in sales_deals table"
        )

    return {
        "status": "success",
        "action": "deleted",
        "storage": "SQLite",
        "table": "sales_deals",
        "deal_id": deal_id,
        "deleted_count": deleted_count
    }


@app.delete("/sales-deals")
def clear_sales_deals_endpoint():
    clear_sales_deals()

    return {
        "status": "success",
        "action": "cleared_all_sales_deals",
        "storage": "SQLite",
        "table": "sales_deals"
    }


if __name__ == "__main__":
    import uvicorn

    init_db()

    uvicorn.run(
        "mock_api.main:app",
        host="127.0.0.1",
        port=8010,
        reload=True
    )