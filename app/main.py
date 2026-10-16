"""Room-booking API: create bookings and list your own."""
import logging
from contextlib import asynccontextmanager, closing
from datetime import date, datetime

from fastapi import Depends, FastAPI, Query

from app import migrate
from app.auth import current_user
from app.db import connect
from app.schemas import BookingCreate, BookingOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bookings")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with closing(connect()) as conn:
        migrate.up(conn)
    yield


app = FastAPI(title="room-booking-api", lifespan=lifespan)


def _utc_text(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


@app.post("/bookings", response_model=BookingOut, status_code=201)
def create_booking(body: BookingCreate, user: str = Depends(current_user)):
    with closing(connect()) as conn:
        cursor = conn.execute(
            "INSERT INTO bookings (room, starts_at, ends_at, customer_email, owner) "
            "VALUES (?, ?, ?, ?, ?)",
            (body.room, _utc_text(body.starts_at), _utc_text(body.ends_at),
             body.customer_email, user),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM bookings WHERE id = ?", (cursor.lastrowid,)).fetchone()
    log.info("booking created id=%s", row["id"])
    return dict(row)


@app.get("/bookings", response_model=list[BookingOut])
def list_bookings(
    on_date: date | None = Query(
        default=None, alias="date",
        description="Only bookings that start on this UTC date (YYYY-MM-DD)."),
    user: str = Depends(current_user),
):
    wanted = on_date.isoformat() if on_date else None
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM bookings WHERE owner = ? "
            "AND (? IS NULL OR date(starts_at) = ?) ORDER BY starts_at, id",
            (user, wanted, wanted),
        ).fetchall()
    return [dict(row) for row in rows]
