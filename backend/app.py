from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB = "database.db"

# ================= DATABASE =================

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        amount REAL,
        description TEXT,
        category TEXT,
        date TEXT
    );

    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT UNIQUE,
        amount REAL
    );

    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        target REAL,
        saved REAL,
        deadline TEXT
    );

    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        amount REAL,
        due TEXT,
        category TEXT,
        paid INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS recurring (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        amount REAL,
        category TEXT,
        frequency TEXT,
        next_date TEXT
    );

    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        name TEXT,
        currency TEXT
    );
    """)

    conn.commit()
    conn.close()

init_db()

# ================= TRANSACTIONS =================

@app.route("/transactions", methods=["GET"])
def get_transactions():
    conn = get_db()
    data = conn.execute("SELECT * FROM transactions").fetchall()
    conn.close()
    return jsonify([dict(row) for row in data])

@app.route("/transactions", methods=["POST"])
def add_transaction():
    data = request.json

    conn = get_db()
    conn.execute("""
        INSERT INTO transactions (type, amount, description, category, date)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["type"],
        data["amount"],
        data["description"],
        data["category"],
        data["date"]
    ))
    conn.commit()
    conn.close()

    return jsonify({"msg": "Transaction added"})

@app.route("/transactions/<int:id>", methods=["DELETE"])
def delete_transaction(id):
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"msg": "Deleted"})

# ================= BUDGETS =================

@app.route("/budgets", methods=["GET"])
def get_budgets():
    conn = get_db()
    data = conn.execute("SELECT * FROM budgets").fetchall()
    conn.close()
    return jsonify([dict(row) for row in data])

@app.route("/budgets", methods=["POST"])
def set_budget():
    data = request.json

    conn = get_db()
    conn.execute("""
        INSERT INTO budgets (category, amount)
        VALUES (?, ?)
        ON CONFLICT(category) DO UPDATE SET amount=excluded.amount
    """, (data["category"], data["amount"]))

    conn.commit()
    conn.close()

    return jsonify({"msg": "Budget saved"})

# ================= GOALS =================

@app.route("/goals", methods=["GET"])
def get_goals():
    conn = get_db()
    data = conn.execute("SELECT * FROM goals").fetchall()
    conn.close()
    return jsonify([dict(row) for row in data])

@app.route("/goals", methods=["POST"])
def add_goal():
    data = request.json

    conn = get_db()
    conn.execute("""
        INSERT INTO goals (name, target, saved, deadline)
        VALUES (?, ?, ?, ?)
    """, (
        data["name"],
        data["target"],
        data["saved"],
        data["deadline"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"msg": "Goal added"})

@app.route("/goals/<int:id>", methods=["PUT"])
def update_goal(id):
    data = request.json

    conn = get_db()
    conn.execute("UPDATE goals SET saved=? WHERE id=?", (data["saved"], id))
    conn.commit()
    conn.close()

    return jsonify({"msg": "Goal updated"})

@app.route("/goals/<int:id>", methods=["DELETE"])
def delete_goal(id):
    conn = get_db()
    conn.execute("DELETE FROM goals WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"msg": "Goal deleted"})

# ================= BILLS =================

@app.route("/bills", methods=["GET"])
def get_bills():
    conn = get_db()
    data = conn.execute("SELECT * FROM bills").fetchall()
    conn.close()
    return jsonify([dict(row) for row in data])

@app.route("/bills", methods=["POST"])
def add_bill():
    data = request.json

    conn = get_db()
    conn.execute("""
        INSERT INTO bills (name, amount, due, category)
        VALUES (?, ?, ?, ?)
    """, (
        data["name"],
        data["amount"],
        data["due"],
        data["category"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"msg": "Bill added"})

@app.route("/bills/<int:id>/pay", methods=["PUT"])
def pay_bill(id):
    conn = get_db()
    conn.execute("UPDATE bills SET paid=1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"msg": "Bill marked as paid"})

# ================= RECURRING =================

@app.route("/recurring", methods=["GET"])
def get_recurring():
    conn = get_db()
    data = conn.execute("SELECT * FROM recurring").fetchall()
    conn.close()
    return jsonify([dict(row) for row in data])

@app.route("/recurring", methods=["POST"])
def add_recurring():
    data = request.json

    conn = get_db()
    conn.execute("""
        INSERT INTO recurring (description, amount, category, frequency, next_date)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["description"],
        data["amount"],
        data["category"],
        data["frequency"],
        data["next_date"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"msg": "Recurring added"})

# ================= INSIGHTS =================

@app.route("/insights", methods=["GET"])
def get_insights():
    conn = get_db()

    income = conn.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='income'"
    ).fetchone()[0] or 0

    expense = conn.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='expense'"
    ).fetchone()[0] or 0

    top_category = conn.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE type='expense'
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    return jsonify({
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "top_category": dict(top_category) if top_category else {}
    })

# ================= SETTINGS =================

@app.route("/settings", methods=["GET"])
def get_settings():
    conn = get_db()
    data = conn.execute("SELECT * FROM settings LIMIT 1").fetchone()
    conn.close()

    return jsonify(dict(data) if data else {})

@app.route("/settings", methods=["POST"])
def save_settings():
    data = request.json

    conn = get_db()
    conn.execute("DELETE FROM settings")
    conn.execute("""
        INSERT INTO settings (id, name, currency)
        VALUES (1, ?, ?)
    """, (data["name"], data["currency"]))

    conn.commit()
    conn.close()

    return jsonify({"msg": "Settings saved"})

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)