import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash


def get_db():
    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        raise Exception("DATABASE_URL not set")

    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    """)

    # CATEGORIES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            type TEXT CHECK(type IN ('income','expense'))
        )
    """)

    # EXPENSES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            category_id INTEGER,
            date TEXT,
            description TEXT
        )
    """)

    # ✅ ADMIN USER SAFE INSERT
    cur.execute("SELECT id FROM users WHERE username=%s", ("admin",))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        """, (
            "admin",
            generate_password_hash("admin123"),
            "admin"
        ))

    # DEFAULT CATEGORIES
    cur.executemany("""
        INSERT INTO categories (name, type)
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
