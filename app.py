import os
from flask import Flask, render_template, request, redirect, session, flash, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")


# ================= DATABASE =================
def get_db():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL not set")
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # SAFE TABLES (no conflict with dictionary app)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expense_users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expense_categories (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            type TEXT CHECK(type IN ('income','expense'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expense_expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            category_id INTEGER,
            date TEXT,
            description TEXT
        )
    """)

    # ADMIN USER
    cur.execute("SELECT * FROM expense_users WHERE username=%s", ("admin",))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO expense_users (username, password, role)
            VALUES (%s, %s, %s)
        """, (
            "admin",
            generate_password_hash("admin123"),
            "admin"
        ))

    # DEFAULT CATEGORIES
    cur.executemany("""
        INSERT INTO expense_categories (name, type)
        VALUES (%s, %s)
        ON CONFLICT (name) DO NOTHING
    """, [
        ("Food", "expense"),
        ("Travel", "expense"),
        ("Shopping", "expense"),
        ("Bills", "expense"),
        ("Salary", "income"),
        ("Freelance", "income")
    ])

    conn.commit()
    cur.close()
    conn.close()


# INIT DB
try:
    init_db()
except Exception as e:
    print("DB init error:", e)


# ================= ROUTES =================

@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/admin" if session.get("role") == "admin" else "/dashboard")
    return redirect("/login")


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        cur.execute("SELECT * FROM expense_users WHERE username=%s", (username,))
        if cur.fetchone():
            flash("Username already exists")
            return redirect("/register")

        cur.execute("""
            INSERT INTO expense_users (username, password, role)
            VALUES (%s, %s, %s)
        """, (username, password, "user"))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM expense_users WHERE username=%s",
                    (request.form["username"],))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user or not check_password_hash(user["password"], request.form["password"]):
            flash("Invalid credentials")
            return redirect("/login")

        session["user_id"] = user["id"]
        session["role"] = user["role"]

        return redirect("/admin" if user["role"] == "admin" else "/dashboard")

    return render_template("login.html")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT e.*, c.name AS category
        FROM expense_expenses e
        JOIN expense_categories c ON e.category_id = c.id
        WHERE e.user_id=%s
        ORDER BY e.id DESC
    """, (session["user_id"],))
    data = cur.fetchall()

    cur.execute("SELECT * FROM expense_categories")
    categories = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("dashboard.html", data=data, categories=categories)


# ---------- ADD ----------
@app.route("/add", methods=["POST"])
def add():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO expense_expenses (user_id, amount, category_id, date, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        session["user_id"],
        request.form["amount"],
        request.form["category_id"],
        request.form["date"],
        request.form["description"]
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/dashboard")


# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM expense_expenses WHERE id=%s", (id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/dashboard")


# ---------- ADMIN ----------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM expense_users")
    users = cur.fetchall()

    cur.execute("""
        SELECT u.username, e.amount, c.name AS category, e.date, e.description
        FROM expense_expenses e
        JOIN expense_users u ON u.id = e.user_id
        JOIN expense_categories c ON c.id = e.category_id
    """)
    expenses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin.html", users=users, expenses=expenses)


# ---------- CHART API ----------
@app.route("/chart-data")
def chart():
    if "user_id" not in session:
        return jsonify({"categories": [], "amounts": []})

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.name, SUM(e.amount)
        FROM expense_expenses e
        JOIN expense_categories c ON c.id = e.category_id
        WHERE e.user_id=%s
        GROUP BY c.name
    """, (session["user_id"],))

    data = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        "categories": [row[0] for row in data],
        "amounts": [float(row[1]) for row in data]
    })


# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
