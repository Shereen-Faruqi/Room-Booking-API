import logging

import pytest


def booking_body(**overrides):
    body = {
        "room": "A1",
        "starts_at": "2026-11-02T09:00:00Z",
        "ends_at": "2026-11-02T10:00:00Z",
        "customer_email": "guest@example.com",
    }
    body.update(overrides)
    return body


# --- POST /bookings -------------------------------------------------------

@pytest.mark.parametrize("headers", [{}, {"X-User-Token": "not-a-real-token"}],
                         ids=["no-token", "unknown-token"])
def test_post_requires_a_valid_token(client, alice, headers):
    response = client.post("/bookings", json=booking_body(), headers=headers)

    assert response.status_code == 401
    assert client.get("/bookings", headers=alice).json() == []  # nothing was stored


def test_post_creates_a_booking_owned_by_the_caller(client, alice):
    # An "owner" field in the body must be ignored: the owner is the logged-in user.
    response = client.post("/bookings", json=booking_body(owner="bob"), headers=alice)

    assert response.status_code == 201
    data = response.json()
    assert data["owner"] == "alice"
    assert data["room"] == "A1"
    assert data["customer_email"] == "guest@example.com"


@pytest.mark.parametrize(
    "overrides",
    [
        {"ends_at": "2026-11-02T08:00:00Z"},
        {"customer_email": "not-an-email"},
        {"starts_at": "2026-11-02T09:00:00"},
        {"room": ""},
    ],
    ids=["ends-before-start", "bad-email", "no-timezone", "empty-room"],
)
def test_post_rejects_invalid_input(client, alice, overrides):
    response = client.post("/bookings", json=booking_body(**overrides), headers=alice)

    assert response.status_code == 422
    assert client.get("/bookings", headers=alice).json() == []  # nothing was stored


# --- GET /bookings --------------------------------------------------------

@pytest.mark.parametrize("headers", [{}, {"X-User-Token": "not-a-real-token"}],
                         ids=["no-token", "unknown-token"])
def test_get_requires_a_valid_token(client, headers):
    assert client.get("/bookings", headers=headers).status_code == 401


def test_get_returns_only_the_callers_bookings(client, alice, bob):
    client.post("/bookings", json=booking_body(room="A1"), headers=alice)
    client.post("/bookings", json=booking_body(room="B2"), headers=bob)

    alice_rooms = [b["room"] for b in client.get("/bookings", headers=alice).json()]
    bob_rooms = [b["room"] for b in client.get("/bookings", headers=bob).json()]

    assert alice_rooms == ["A1"]
    assert bob_rooms == ["B2"]


def test_a_user_cannot_see_another_users_bookings(client, alice, bob):
    secret = "alice.private@example.com"
    created = client.post("/bookings", json=booking_body(customer_email=secret),
                          headers=alice).json()

    plain = client.get("/bookings", headers=bob)
    # Naming another user in the query string must not widen the result either.
    sneaky = client.get("/bookings", params={"owner": "alice"}, headers=bob)

    for response in (plain, sneaky):
        assert response.status_code == 200
        assert response.json() == []
        assert secret not in response.text
        assert created["id"] not in [b["id"] for b in response.json()]


# --- Logging (policy 2) ---------------------------------------------------

def test_creating_a_booking_does_not_log_the_customer_email(client, alice, caplog):
    email = "secret.guest@example.com"

    with caplog.at_level(logging.INFO):
        response = client.post("/bookings", json=booking_body(customer_email=email),
                               headers=alice)

    assert response.status_code == 201
    assert "booking created" in caplog.text  # proves logging was captured at all
    assert email not in caplog.text
    assert "example.com" not in caplog.text
