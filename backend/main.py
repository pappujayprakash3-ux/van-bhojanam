"""
Van Bhojanam — booking API

A small FastAPI service that accepts checkout submissions from the
frontend, keeps an in-memory record of bookings, and exposes a stats
endpoint so the frontend can show a live "tonight" dashboard.

Note: state is in-memory only. It resets whenever the service restarts
(e.g. on a Render free-tier spin-down/spin-up, or a redeploy). Swap the
in-memory store for a real database if you need it to persist.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Van Bhojanam Booking API", version="1.0.0")

# Comma-separated list of allowed origins, e.g.
#   FRONTEND_ORIGINS="https://van-bhojanam-web.onrender.com,http://localhost:5500"
# Defaults to "*" so it works out of the box; tighten this once your
# frontend URL is known.
_origins_env = os.getenv("FRONTEND_ORIGINS", "*")
allow_origins = ["*"] if _origins_env.strip() == "*" else [
    o.strip() for o in _origins_env.split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class OrderItem(BaseModel):
    id: str
    name: str
    qty: int = Field(gt=0)
    price: float = Field(ge=0)


class CheckoutRequest(BaseModel):
    guest_name: str
    phone: str
    guests: int = Field(gt=0)
    date: str
    time_slot: str
    zone_id: str
    zone_name: str
    items: List[OrderItem]
    subtotal: float = Field(ge=0)
    cover_charge: float = Field(ge=0)
    eco_levy: float = Field(ge=0)
    total: float = Field(ge=0)
    payment_method: str


class CheckoutResponse(BaseModel):
    booking_id: str
    status: str
    total: float
    message: str


class StatsResponse(BaseModel):
    booking_count: int
    total_revenue: float
    total_eco_levy_collected: float


class BookingRecord(BaseModel):
    booking_id: str
    created_at: str
    guest_name: str
    zone_name: str
    guests: int
    total: float
    payment_method: str


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

class Store:
    def __init__(self) -> None:
        self.bookings: List[BookingRecord] = []
        self.total_revenue: float = 0.0
        self.total_eco_levy: float = 0.0

    def add_booking(self, req: CheckoutRequest) -> BookingRecord:
        record = BookingRecord(
            booking_id=uuid.uuid4().hex[:8].upper(),
            created_at=datetime.utcnow().isoformat() + "Z",
            guest_name=req.guest_name,
            zone_name=req.zone_name,
            guests=req.guests,
            total=req.total,
            payment_method=req.payment_method,
        )
        self.bookings.append(record)
        self.total_revenue += req.total
        self.total_eco_levy += req.eco_levy
        return record


store = Store()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """Simple health check for Render's health-check probe."""
    return {"status": "ok"}


@app.post("/api/checkout", response_model=CheckoutResponse)
def checkout(req: CheckoutRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    computed_subtotal = sum(item.price * item.qty for item in req.items)
    computed_total = computed_subtotal + req.cover_charge + req.eco_levy
    # Basic sanity check against client-computed totals (informational —
    # we still trust the client's total for this demo, but this guards
    # against obviously malformed payloads).
    if abs(computed_total - req.total) > 1.0:
        raise HTTPException(
            status_code=400,
            detail="Total does not match items, cover charge, and eco levy.",
        )

    record = store.add_booking(req)

    return CheckoutResponse(
        booking_id=record.booking_id,
        status="confirmed",
        total=req.total,
        message=f"Table reserved in {req.zone_name} for {req.guests} guests.",
    )


@app.get("/api/stats", response_model=StatsResponse)
def stats():
    return StatsResponse(
        booking_count=len(store.bookings),
        total_revenue=round(store.total_revenue, 2),
        total_eco_levy_collected=round(store.total_eco_levy, 2),
    )


@app.get("/api/bookings", response_model=List[BookingRecord])
def list_bookings():
    """Recent bookings, most recent first. Useful for a back-office view."""
    return list(reversed(store.bookings))


@app.get("/")
def root():
    return {
        "service": "Van Bhojanam Booking API",
        "docs": "/docs",
        "endpoints": ["/health", "/api/checkout", "/api/stats", "/api/bookings"],
    }
