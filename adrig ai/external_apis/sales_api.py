"""External API exposing read-only endpoints for a `sales_db` MongoDB.

Endpoints:
- GET  /status                 -> health check
- GET  /customers              -> list customers (query param `q`, `limit`)
- GET  /customers/{id}         -> get customer by id
- GET  /orders                 -> list orders (filter by `customer_id`)
- GET  /orders/{id}            -> get order by id
- GET  /sales/summary          -> simple sales aggregation
"""
from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import os

try:
    from pymongo import MongoClient
    from bson.objectid import ObjectId
except Exception:
    MongoClient = None
    ObjectId = None

MONGO_URL = os.environ.get("SALES_DB_URL") or "mongodb://localhost:27017/sales_db"

app = FastAPI(title="Sales External API")


def _get_db():
    if MongoClient is None:
        raise RuntimeError("pymongo is not installed")
    client = MongoClient(MONGO_URL)
    # database name taken from URL path or default sales_db
    return client.get_default_database() if client is not None else None


def _build_order_filter(customer_id: Optional[str] = None, min_total: Optional[float] = None,
                        max_total: Optional[float] = None, amount: Optional[float] = None):
    filt = {}
    if customer_id:
        filt["customer_id"] = customer_id

    if amount is not None and min_total is None:
        min_total = amount

    if min_total is not None:
        filt["total"] = {"$gte": float(min_total)}
    if max_total is not None:
        filt.setdefault("total", {})["$lte"] = float(max_total)
    return filt


@app.get("/status")
def status():
    try:
        db = _get_db()
        # quick ping
        db.client.admin.command("ping")
        return {"status": "ok", "db": str(MONGO_URL)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/customers")
def list_customers(q: Optional[str] = Query(None), limit: int = Query(20)):
    try:
        db = _get_db()
        coll = db.customers
        filt = {}
        if q:
            regex = {"$regex": q, "$options": "i"}
            filt = {"$or": [{"name": regex}, {"email": regex}]}
        cursor = coll.find(filt, {"name": 1, "email": 1}).limit(int(limit))
        out = []
        for d in cursor:
            out.append({"id": str(d.get("_id")), "name": d.get("name"), "email": d.get("email")})
        return {"customers": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    try:
        if ObjectId is None:
            raise RuntimeError("bson is not available")
        db = _get_db()
        coll = db.customers
        doc = coll.find_one({"_id": ObjectId(customer_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"id": str(doc.get("_id")), "name": doc.get("name"), "email": doc.get("email")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/orders")
def list_orders(
    customer_id: Optional[str] = None,
    limit: int = Query(50),
    min_total: Optional[float] = None,
    max_total: Optional[float] = None,
    amount: Optional[float] = None,
):
    try:
        db = _get_db()
        coll = db.orders
        filt = _build_order_filter(customer_id, min_total, max_total, amount)

        cursor = coll.find(filt).limit(int(limit))
        out = []
        for d in cursor:
            out.append({"id": str(d.get("_id")), "customer_id": d.get("customer_id"), "total": d.get("total")})
        return {"orders": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    try:
        if ObjectId is None:
            raise RuntimeError("bson is not available")
        db = _get_db()
        coll = db.orders
        doc = coll.find_one({"_id": ObjectId(order_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Order not found")
        return {"id": str(doc.get("_id")), "customer_id": doc.get("customer_id"), "items": doc.get("items"), "total": doc.get("total")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/customers/high-value")
def high_value_customers(min_total: float = Query(20000), limit: int = Query(50)):
    """Return customer name + customer id for orders whose total is >= min_total."""
    try:
        db = _get_db()
        coll = db.orders
        pipeline = [
            {"$match": {"total": {"$gte": float(min_total)}}},
            {
                "$lookup": {
                    "from": "customers",
                    "let": {"cid": "$customer_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$or": [
                                        {"$eq": ["$_id", "$$cid"]},
                                        {"$eq": [{"$toString": "$_id"}, "$$cid"]},
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "customer",
                }
            },
            {"$unwind": {"path": "$customer", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": 1,
                    "customer_id": 1,
                    "customer_name": "$customer.name",
                    "customer_email": "$customer.email",
                    "total": 1,
                }
            },
            {"$limit": int(limit)},
        ]
        out = []
        for d in coll.aggregate(pipeline):
            out.append({
                "order_id": str(d.get("_id")),
                "customer_id": str(d.get("customer_id")),
                "customer_name": d.get("customer_name"),
                "customer_email": d.get("customer_email"),
                "total": d.get("total"),
            })
        return {"customers": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/count")
def orders_count(customer_id: Optional[str] = None, min_total: Optional[float] = None,
                 max_total: Optional[float] = None, amount: Optional[float] = None):
    try:
        db = _get_db()
        coll = db.orders
        filt = _build_order_filter(customer_id, min_total, max_total, amount)
        return {"count": coll.count_documents(filt)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/total")
def orders_total(customer_id: Optional[str] = None, min_total: Optional[float] = None,
                 max_total: Optional[float] = None, amount: Optional[float] = None):
    try:
        db = _get_db()
        coll = db.orders
        filt = _build_order_filter(customer_id, min_total, max_total, amount)
        pipeline = [{"$match": filt}, {"$group": {"_id": None, "total_sales": {"$sum": "$total"}}}]
        res = list(coll.aggregate(pipeline))
        return {"total_sales": res[0].get("total_sales", 0) if res else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/average")
def orders_average(customer_id: Optional[str] = None, min_total: Optional[float] = None,
                   max_total: Optional[float] = None, amount: Optional[float] = None):
    try:
        db = _get_db()
        coll = db.orders
        filt = _build_order_filter(customer_id, min_total, max_total, amount)
        pipeline = [{"$match": filt}, {"$group": {"_id": None, "average_total": {"$avg": "$total"}, "count": {"$sum": 1}}}]
        res = list(coll.aggregate(pipeline))
        return {"average_total": res[0].get("average_total", 0) if res else 0, "count": res[0].get("count", 0) if res else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/recent")
def recent_orders(limit: int = Query(10)):
    try:
        db = _get_db()
        coll = db.orders
        cursor = coll.find({}, {"_id": 1, "customer_id": 1, "total": 1}).sort("_id", -1).limit(int(limit))
        return {"orders": [{"id": str(d.get("_id")), "customer_id": d.get("customer_id"), "total": d.get("total")} for d in cursor]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/customers/count")
def customers_count():
    try:
        db = _get_db()
        return {"count": db.customers.count_documents({})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/customers/top-spenders")
def top_spenders(limit: int = Query(10)):
    try:
        db = _get_db()
        coll = db.orders
        pipeline = [
            {"$group": {"_id": "$customer_id", "total_spent": {"$sum": "$total"}, "orders": {"$sum": 1}}},
            {"$sort": {"total_spent": -1}},
            {"$limit": int(limit)},
        ]
        return {"top_spenders": list(coll.aggregate(pipeline))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/customers/with-orders")
def customers_with_orders(limit: int = Query(20)):
    try:
        db = _get_db()
        orders = db.orders
        customers = db.customers
        pipeline = [
            {"$group": {"_id": "$customer_id", "order_count": {"$sum": 1}, "total_spent": {"$sum": "$total"}}},
            {"$sort": {"order_count": -1}},
            {"$limit": int(limit)},
        ]
        out = []
        for row in orders.aggregate(pipeline):
            customer = customers.find_one({"_id": row.get("_id")}) if isinstance(row.get("_id"), str) else None
            out.append({
                "customer_id": str(row.get("_id")),
                "customer_name": customer.get("name") if customer else None,
                "customer_email": customer.get("email") if customer else None,
                "order_count": row.get("order_count", 0),
                "total_spent": row.get("total_spent", 0),
            })
        return {"customers": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sales/summary")
def sales_summary():
    try:
        db = _get_db()
        coll = db.orders
        pipeline = [
            {"$group": {"_id": None, "total_sales": {"$sum": "$total"}, "count": {"$sum": 1}}}
        ]
        res = list(coll.aggregate(pipeline))
        if not res:
            return {"total_sales": 0, "count": 0}
        r = res[0]
        return {"total_sales": r.get("total_sales", 0), "count": r.get("count", 0)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
