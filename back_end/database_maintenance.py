from uuid import uuid4

from sqlalchemy import inspect, text


def ensure_sqlite_schema(app, db):
    if not str(db.engine.url).startswith("sqlite"):
        return

    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    with db.engine.begin() as connection:
        if "conversations" in table_names:
            _add_column(connection, inspector, "conversations", "public_id", "VARCHAR(36)")
            rows = connection.execute(text("SELECT id FROM conversations WHERE public_id IS NULL OR public_id = ''")).fetchall()
            for row in rows:
                connection.execute(
                    text("UPDATE conversations SET public_id = :public_id WHERE id = :id"),
                    {"public_id": uuid4().hex, "id": row.id},
                )

        if "messages" in table_names:
            _add_column(connection, inspector, "messages", "public_id", "VARCHAR(36)")
            _add_column(connection, inspector, "messages", "parent_message_id", "INTEGER")
            _add_column(connection, inspector, "messages", "is_deleted", "BOOLEAN DEFAULT 0")
            rows = connection.execute(text("SELECT id FROM messages WHERE public_id IS NULL OR public_id = ''")).fetchall()
            for row in rows:
                connection.execute(
                    text("UPDATE messages SET public_id = :public_id WHERE id = :id"),
                    {"public_id": uuid4().hex, "id": row.id},
                )


def _add_column(connection, inspector, table_name, column_name, column_type):
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name not in columns:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
