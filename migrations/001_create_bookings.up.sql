CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    owner TEXT NOT NULL,
    CHECK (ends_at > starts_at)
);

CREATE INDEX idx_bookings_owner ON bookings(owner);
