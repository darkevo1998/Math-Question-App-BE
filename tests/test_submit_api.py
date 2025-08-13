import uuid
from http import HTTPStatus


def make_attempt_id():
    return str(uuid.uuid4())


def test_submit_success_and_idempotency(client):
    # First submit
    resp = client.post("/api/lessons/1/submit", json={
        "attempt_id": make_attempt_id(),
        "answers": [
            {"problem_id": 1, "option_id": 2},  # correct 4
            {"problem_id": 2, "value": "12"}   # correct
        ],
    })
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    assert data["correct_count"] == 2
    first_streak = data["streak"]["current"] if isinstance(data["streak"], dict) else data["streak"]["current"]

    # Duplicate attempt id
    dup_id = "fixed-id"
    resp2 = client.post("/api/lessons/1/submit", json={
        "attempt_id": dup_id,
        "answers": [
            {"problem_id": 1, "option_id": 2},
        ],
    })
    assert resp2.status_code == HTTPStatus.OK

    # Same attempt again returns 409
    resp3 = client.post("/api/lessons/1/submit", json={
        "attempt_id": dup_id,
        "answers": [
            {"problem_id": 1, "option_id": 2},
        ],
    })
    assert resp3.status_code == HTTPStatus.CONFLICT

    # New attempt same day should not increment streak further
    resp4 = client.post("/api/lessons/1/submit", json={
        "attempt_id": make_attempt_id(),
        "answers": [
            {"problem_id": 1, "option_id": 2},
        ],
    })
    assert resp4.status_code == HTTPStatus.OK
    d4 = resp4.get_json()
    assert d4["streak"]["current"] == first_streak


def test_submit_invalid_problem_returns_422(client):
    resp = client.post("/api/lessons/1/submit", json={
        "attempt_id": make_attempt_id(),
        "answers": [
            {"problem_id": 999, "option_id": 1},
        ],
    })
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY 