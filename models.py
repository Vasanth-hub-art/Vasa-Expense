import sqlite3
from werkzeug.security import generate_password_hash


# 🔗 DATABASE CONNECTION
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# 🏗️ INITIALIZE DATABASE
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # ================= USERS =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    )
    """)

    # ================= CATEGORIES =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT CHECK(type IN ('income','expense'))
    )
    """)

    # ================= EXPENSES =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        category_id INTEGER,
        date TEXT,
        description TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )
    """)

    # ================= ADMIN USER =================
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("""
        INSERT INTO users(username,password,role)
        VALUES (?,?,?)
        """, (
            "admin",
            generate_password_hash("admin123"),
            "admin"
        ))

    # ================= DEFAULT CATEGORIES =================
    cur.executemany("""
    INSERT OR IGNORE INTO categories(name,type) VALUES (?,?)
    """, [
        ("Food","expense"),
        ("Travel","expense"),
        ("Shopping","expense"),
        ("Bills","expense"),
        ("Salary","income"),
        ("Freelance","income")
    ])

    conn.commit()
    conn.close()