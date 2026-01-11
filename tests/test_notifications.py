from datetime import datetime, timedelta

from sqlalchemy import text

from app.database import engine


def _insert_notification(schema: str, user_id: str, title: str, is_read: bool, created_at):
    with engine.begin() as conn:
        conn.execute(text(f'SET search_path TO "{schema}"'))
        conn.execute(
            text(
                """
                INSERT INTO notifications (user_id, type, title, message, meta, is_read, created_at)
                VALUES (:user_id, :type, :title, :message, :meta, :is_read, :created_at)
                RETURNING id
                """
            ),
            {
                "user_id": user_id,
                "type": "INFO",
                "title": title,
                "message": f"msg-{title}",
                "meta": None,
                "is_read": is_read,
                "created_at": created_at,
            },
        ).scalar_one()


def test_list_notifications_orders_and_limits(client):
    base = datetime.utcnow()
    _insert_notification("tenant1", "u1", "old", False, base - timedelta(minutes=10))
    _insert_notification("tenant1", "u1", "new", False, base)
    _insert_notification("tenant1", "u2", "other-user", False, base)

    r = client.get(
        "/notifications/",
        params={"user_id": "u1", "limit": 50},
        headers={"X-Tenant-Id": "tenant1"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["title"] == "new"
    assert data[1]["title"] == "old"

    r2 = client.get(
        "/notifications/",
        params={"user_id": "u1", "limit": 1},
        headers={"X-Tenant-Id": "tenant1"},
    )
    assert r2.status_code == 200
    assert len(r2.json()) == 1
    assert r2.json()[0]["title"] == "new"


def test_list_notifications_unread_only(client):
    base = datetime.utcnow()
    _insert_notification("tenant1", "u1", "unread", False, base)
    _insert_notification("tenant1", "u1", "read", True, base - timedelta(minutes=1))

    r = client.get(
        "/notifications/",
        params={"user_id": "u1", "unread_only": "true"},
        headers={"X-Tenant-Id": "tenant1"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["title"] == "unread"
    assert data[0]["is_read"] is False


def test_mark_read_success(client):
    base = datetime.utcnow()
    with engine.begin() as conn:
        conn.execute(text('SET search_path TO "tenant1"'))
        nid = conn.execute(
            text(
                """
                INSERT INTO notifications (user_id, type, title, message, meta, is_read, created_at)
                VALUES ('u1', 'INFO', 't', 'm', NULL, false, :created_at)
                RETURNING id
                """
            ),
            {"created_at": base},
        ).scalar_one()

    r = client.post(f"/notifications/{nid}/read", headers={"X-Tenant-Id": "tenant1"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == nid
    assert body["is_read"] is True


def test_mark_read_404(client):
    r = client.post("/notifications/999999/read", headers={"X-Tenant-Id": "tenant1"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Notification not found"


def test_tenant_isolation(client):
    base = datetime.utcnow()
    _insert_notification("public", "u1", "public-note", False, base)
    _insert_notification("tenant1", "u1", "tenant-note", False, base)

    r_public = client.get("/notifications/", params={"user_id": "u1"}, headers={"X-Tenant-Id": "public"})
    r_tenant = client.get("/notifications/", params={"user_id": "u1"}, headers={"X-Tenant-Id": "tenant1"})

    assert [n["title"] for n in r_public.json()] == ["public-note"]
    assert [n["title"] for n in r_tenant.json()] == ["tenant-note"]
