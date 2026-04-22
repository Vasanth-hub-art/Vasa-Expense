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

    cur.execute("DROP TABLE IF EXISTS expenses CASCADE;")
    cur.execute("DROP TABLE IF EXISTS categories CASCADE;")
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")

    cur.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)

    cur.execute("""
        CREATE TABLE categories (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            type TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            category_id INTEGER,
            date TEXT,
            description TEXT
        )
    """)

    # ADMIN
    cur.execute("""
        INSERT INTO users (username, password, role)
        VALUES (%s, %s, %s)
    """, ("admin", generate_password_hash("admin123"), "admin"))

    # DEFAULT CATEGORIES
    cur.executemany("""
        INSERT INTO categories (name, type)
        VALUES (%s, %s)
    """, [
        ("Food", "expense"),
        ("Travel", "expense"),
        ("Shopping", "expense"),
        ("Salary", "income")
    ])

    conn.commit()
    cur.close()
    conn.close()

try:
    init_db()
    print("DB READY")
except Exception as e:
    print("DB ERROR:", e)


# ================= ROOT =================
@app.route("/")
def home():
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect("/admin")
        return redirect("/dashboard")
    return redirect("/login")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s",
                    (request.form["username"],))
        user = cur.fetchone()

        if not user:
            flash("Invalid username")
            return redirect("/login")

        if not check_password_hash(user["password"], request.form["password"]):
            flash("Invalid password")
            return redirect("/login")

        session["user_id"] = user["id"]
        session["role"] = user["role"]

        return redirect("/")

    return render_template("login.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            flash("User exists")
            return redirect("/register")

        cur.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        """, (username, password, "user"))

        conn.commit()
        return redirect("/login")

    return render_template("register.html")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT e.id, e.amount, e.date, c.name as category
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id=%s
        ORDER BY e.id DESC
    """, (session["user_id"],))
    data = cur.fetchall()

    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    return render_template("dashboard.html", data=data, categories=categories)


# ================= ADD =================
@app.route("/add", methods=["POST"])
def add():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO expenses(user_id, amount, category_id, date, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        session["user_id"],
        request.form["amount"],
        request.form["category_id"],
        request.form["date"],
        request.form["description"]
    ))

    conn.commit()
    return redirect("/dashboard")


# ================= DELETE =================
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM expenses WHERE id=%s", (id,))
    conn.commit()

    return redirect("/dashboard")


# ================= ADMIN =================
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    cur.execute("""
        SELECT u.username, e.amount, c.name, e.date
        FROM expenses e
        JOIN users u ON u.id = e.user_id
        JOIN categories c ON c.id = e.category_id
    """)
    expenses = cur.fetchall()

    return render_template("admin.html", users=users, expenses=expenses)


# ================= API =================
@app.route("/chart-data")
def chart():
    if "user_id" not in session:
        return jsonify({"categories": [], "amounts": []})

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.name, SUM(e.amount)
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        WHERE e.user_id=%s
        GROUP BY c.name
    """, (session["user_id"],))

    data = cur.fetchall()

    return jsonify({
        "categories": [row[0] for row in data],
        "amounts": [float(row[1]) for row in data]
    })


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= RUN =================
if __name__ == "__main__":
    app.run()
