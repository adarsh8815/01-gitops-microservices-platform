from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
import structlog
import uuid
import httpx
import os
from datetime import datetime
from typing import Optional, List

# Structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
log = structlog.get_logger()

app = FastAPI(title="Order Service", version="1.0.0", docs_url="/docs")

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:3001")

# In-memory store
orders_db: dict = {}

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItem]
    shipping_address: str

class Order(BaseModel):
    id: str
    user_id: str
    items: List[OrderItem]
    shipping_address: str
    status: str
    total_amount: float
    created_at: datetime
    updated_at: Optional[datetime] = None

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "order-service", 
            "version": os.getenv("APP_VERSION", "v1.0.0"), "timestamp": datetime.utcnow()}

@app.get("/ready")
async def ready():
    # Check dependency: user-service
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{USER_SERVICE_URL}/health")
            if resp.status_code != 200:
                return {"status": "not_ready", "reason": "user-service unhealthy"}
    except Exception as e:
        log.warning("dependency_check_failed", service="user-service", error=str(e))
        return {"status": "degraded", "reason": f"user-service unreachable: {str(e)}"}
    return {"status": "ready"}

@app.post("/api/v1/orders", response_model=Order, status_code=201)
async def create_order(order_data: OrderCreate):
    # Validate user exists
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{USER_SERVICE_URL}/api/v1/users/{order_data.user_id}")
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        log.error("user_service_call_failed", error=str(e))
        raise HTTPException(status_code=503, detail="User service unavailable")

    total = sum(item.price * item.quantity for item in order_data.items)
    order = Order(
        id=f"order_{uuid.uuid4().hex[:8]}",
        user_id=order_data.user_id,
        items=order_data.items,
        shipping_address=order_data.shipping_address,
        status="pending",
        total_amount=round(total, 2),
        created_at=datetime.utcnow()
    )
    orders_db[order.id] = order
    log.info("order_created", order_id=order.id, user_id=order_data.user_id, total=total)
    return order

@app.get("/api/v1/orders", response_model=List[Order])
async def list_orders(user_id: Optional[str] = None):
    orders = list(orders_db.values())
    if user_id:
        orders = [o for o in orders if o.user_id == user_id]
    return orders

@app.get("/api/v1/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.patch("/api/v1/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    order.updated_at = datetime.utcnow()
    log.info("order_status_updated", order_id=order_id, new_status=status)
    return order
