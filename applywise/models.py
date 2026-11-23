"""Persistence helpers for job applications."""

import sqlite3
from datetime import date, datetime, timezone
from typing import Any


FIELDS = (
    "company",
    "role",
    "status",
    "location",
    "job_url",
    "source",
    "salary",
    "applied_on",
    "follow_up_on",
    "notes",
)


def serialize(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite row into the API's JSON-friendly shape."""
    item = dict(row)
    for field in ("applied_on", "follow_up_on"):
        if item[field]:
            item[field] = date.fromisoformat(item[field])
    for field in ("created_at", "updated_at"):
        item[field] = datetime.fromisoformat(item[field])
    return item


def create(connection: sqlite3.Connection, values: dict[str, Any]) -> dict[str, Any]:
    """Insert an application and return its serialized record."""
    data = {field: values.get(field) for field in FIELDS}
    columns = ", ".join(data)
    placeholders = ", ".join("?" for _ in data)
    parameters = [value.isoformat() if isinstance(value, date) else value for value in data.values()]
    cursor = connection.execute(
        f"INSERT INTO applications ({columns}) VALUES ({placeholders})", parameters
    )
    connection.commit()
    return serialize(connection.execute("SELECT * FROM applications WHERE id = ?", (cursor.lastrowid,)).fetchone())


def get(connection: sqlite3.Connection, application_id: int) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
    return serialize(row) if row else None


def list_all(
    connection: sqlite3.Connection,
    status_filter: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    parameters: list[str] = []
    if status_filter:
        clauses.append("status = ?")
        parameters.append(status_filter)
    if search:
        clauses.append("(company LIKE ? COLLATE NOCASE OR role LIKE ? COLLATE NOCASE OR location LIKE ? COLLATE NOCASE)")
        pattern = f"%{search.strip()}%"
        parameters.extend([pattern, pattern, pattern])
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = connection.execute(
        f"SELECT * FROM applications{where} ORDER BY updated_at DESC", parameters
    ).fetchall()
    return [serialize(row) for row in rows]


def update(
    connection: sqlite3.Connection, application_id: int, values: dict[str, Any]
) -> dict[str, Any] | None:
    current = get(connection, application_id)
    if current is None:
        return None
    changes = {key: value for key, value in values.items() if key in FIELDS}
    if changes:
        assignments = ", ".join(f"{field} = ?" for field in changes)
        parameters = [value.isoformat() if isinstance(value, date) else value for value in changes.values()]
        parameters.extend([datetime.now(timezone.utc).isoformat(), application_id])
        connection.execute(
            f"UPDATE applications SET {assignments}, updated_at = ? WHERE id = ?", parameters
        )
        connection.commit()
    return get(connection, application_id)


def delete(connection: sqlite3.Connection, application_id: int) -> bool:
    cursor = connection.execute("DELETE FROM applications WHERE id = ?", (application_id,))
    connection.commit()
    return cursor.rowcount > 0


def overview(connection: sqlite3.Connection) -> dict[str, Any]:
    """Aggregate counts, due follow-ups, and recently updated applications."""
    total = connection.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    grouped = dict(connection.execute("SELECT status, COUNT(*) FROM applications GROUP BY status").fetchall())
    today = date.today().isoformat()
    active = "'offer', 'rejected', 'withdrawn'"
    due_where = (
        f"follow_up_on IS NOT NULL AND follow_up_on <= ? AND status NOT IN ({active})"
    )
    follow_up_count = connection.execute(
        f"SELECT COUNT(*) FROM applications WHERE {due_where}", (today,)
    ).fetchone()[0]
    due_rows = connection.execute(
        f"SELECT * FROM applications WHERE {due_where} ORDER BY follow_up_on LIMIT 5", (today,)
    ).fetchall()
    recent_rows = connection.execute(
        "SELECT * FROM applications ORDER BY updated_at DESC LIMIT 5"
    ).fetchall()
    applied = sum(grouped.get(key, 0) for key in ("applied", "interview", "offer", "rejected"))
    responses = sum(grouped.get(key, 0) for key in ("interview", "offer", "rejected"))
    return {
        "total": total,
        "by_status": grouped,
        "response_rate": round(responses / applied * 100) if applied else 0,
        "follow_up_count": follow_up_count,
        "follow_ups": [serialize(row) for row in due_rows],
        "recent": [serialize(row) for row in recent_rows],
    }
