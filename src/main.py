"""
Demo Atlas - Simple task manager app backed by MySQL.
"""

import os
import mysql.connector
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "mysql"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "database": os.getenv("DB_NAME", "demo"),
}


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


# ── UI ─────────────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return render_template("index.html")


# ── Users ──────────────────────────────────────────────────────────────────────

@app.get("/users")
def list_users():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)


@app.post("/users")
def create_user():
    data = request.json
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email) VALUES (%s, %s)",
        (data["name"], data["email"]),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return jsonify({"id": user_id, "name": data["name"], "email": data["email"]}), 201


# ── Tasks ──────────────────────────────────────────────────────────────────────

@app.get("/tasks")
def list_tasks():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT t.*, u.name AS user_name FROM tasks t JOIN users u ON u.id = t.user_id ORDER BY t.id"
    )
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)


@app.post("/tasks")
def create_task():
    data = request.json
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (user_id, title) VALUES (%s, %s)",
        (data["user_id"], data["title"]),
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return jsonify({"id": task_id, "user_id": data["user_id"], "title": data["title"], "done": False}), 201


@app.patch("/tasks/<int:task_id>")
def complete_task(task_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET done = TRUE WHERE id = %s", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"id": task_id, "done": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)
