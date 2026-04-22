import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash


def get_db():
    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        raise Exception("DATABASE_URL is not set")

    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # ⚠️ RESET TABLES (ONLY FIRST DEPLOY)
    cur.execute("DROP TABLE IF EXISTS expenses CASCADE;")
    cur.execute("DROP TABLE IF EXISTS categories CASCADE;")
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")

    # USERS
    cur.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)

    # CATEGORIES
    cur.execute("""
        CREATE TABLE categories (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            type TEXT CHECK(type IN ('income','expense'))
        )
    """)

    # EXPENSES
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

    # ADMIN USER
    cur.execute("SELECT * FROM users WHERE username=%s", ("admin",))
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
