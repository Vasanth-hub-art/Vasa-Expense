from flask import Flask, render_template, request, redirect, session, flash, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")


# ================= DATABASE =================
def get_db():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )


# ================= INIT DB =================
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        type TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        category_id INTEGER,
        date DATE,
        description TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


init_db()


# ================= HOME =================
@app.route("/")
def home():
    return render_template("home.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            flash("Username already exists ❌")
            return redirect("/register")

        cur.execute(
            "INSERT INTO users (username,password,role) VALUES (%s,%s,%s)",
            (username, password, "user")
        )

        db.commit()
        return redirect("/login")

    return render_template("register.html")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s",
                    (request.form["username"],))
        user = cur.fetchone()

        if not user or not check_password_hash(user["password"], request.form["password"]):
            flash("Invalid credentials ❌")
            return redirect("/login")

        session["user_id"] = user["id"]
        session["role"] = user["role"]

        return redirect("/dashboard")

    return render_template("login.html")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT e.*, c.name AS category
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        WHERE e.user_id=%s
        ORDER BY e.id DESC
    """, (session["user_id"],))

    data = cur.fetchall()

    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    return render_template("dashboard.html",
                           data=data,
                           categories=categories)


# ================= ADD EXPENSE =================
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO expenses (user_id, amount, category_id, date, description)
        VALUES (%s,%s,%s,%s,%s)
    """, (
        session["user_id"],
        request.form["amount"],
        request.form["category_id"],
        request.form["date"],
        request.form["description"]
    ))

    db.commit()
    return redirect("/dashboard")


# ================= DELETE =================
@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM expenses WHERE id=%s", (id,))
    db.commit()

    return redirect("/dashboard")


# ================= EDIT =================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        cur.execute("""
            UPDATE expenses
            SET amount=%s, category_id=%s, date=%s, description=%s
            WHERE id=%s
        """, (
            request.form["amount"],
            request.form["category_id"],
            request.form["date"],
            request.form["description"],
            id
        ))

        db.commit()
        return redirect("/dashboard")

    cur.execute("SELECT * FROM expenses WHERE id=%s", (id,))
    e = cur.fetchone()

    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    return render_template("edit.html", e=e, categories=categories)


# ================= ANALYTICS PAGE =================
@app.route("/analytics")
def analytics():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("analytics.html")


# ================= ANALYTICS DATA (FIXED & CLEAN) =================
@app.route("/analytics-data")
def analytics_data():
    if "user_id" not in session:
        return jsonify({"total": 0, "categories": [], "amounts": []})

    db = get_db()
    cur = db.cursor()

    filter_type = request.args.get("filter", "month")

    if filter_type == "day":
        condition = "e.date::date = CURRENT_DATE"
    elif filter_type == "week":
        condition = "e.date::date >= CURRENT_DATE - INTERVAL '7 days'"
    elif filter_type == "month":
        condition = "e.date::date >= CURRENT_DATE - INTERVAL '30 days'"
    elif filter_type == "year":
        condition = "e.date::date >= CURRENT_DATE - INTERVAL '365 days'"
    else:
        condition = "1=1"

    # TOTAL EXPENSE
    cur.execute(f"""
        SELECT COALESCE(SUM(e.amount),0) AS total
        FROM expenses e
        WHERE e.user_id=%s AND {condition}
    """, (session["user_id"],))

    total = cur.fetchone()["total"]

    # CATEGORY DATA
    cur.execute(f"""
        SELECT c.name, COALESCE(SUM(e.amount),0) AS total
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        WHERE e.user_id=%s AND {condition}
        GROUP BY c.name
        ORDER BY total DESC
    """, (session["user_id"],))

    rows = cur.fetchall()

    return jsonify({
        "total": float(total),
        "categories": [r["name"] for r in rows],
        "amounts": [float(r["total"]) for r in rows]
    })


# ================= RUN =================
if __name__ == "__main__":
    app.run()
