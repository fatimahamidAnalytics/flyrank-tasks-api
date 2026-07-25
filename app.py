import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_NAME = "tasks.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)

    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()[0]

    if count == 0:
        cur.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Buy groceries", 0))
        cur.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Finish assignment", 0))
        cur.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Read a book", 0))

    conn.commit()
    conn.close()


init_db()


def row_to_dict(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.route("/tasks", methods=["GET"])
def get_tasks():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return jsonify([row_to_dict(row) for row in rows])


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(row_to_dict(row))


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    title = data.get("title") if data else None

    if not title:
        return jsonify({"error": "Title is required"}), 400

    conn = get_db_connection()
    cur = conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (title, 0))
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()
    conn.close()

    return jsonify(row_to_dict(row)), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()

    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    new_title = data.get("title", row["title"])
    new_done = data.get("done", bool(row["done"]))

    conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, int(new_done), task_id)
    )
    conn.commit()
    updated_row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()

    return jsonify(row_to_dict(updated_row))


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return "", 204


if __name__ == "__main__":
    app.run(debug=True, port=3000)