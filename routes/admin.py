from flask import Blueprint, render_template, session, redirect, url_for
from models import get_db
from psycopg2.extras import RealDictCursor

admin = Blueprint('admin', __name__)


@admin.route('/admin')
def admin_dashboard():

    # 🔐 LOGIN CHECK
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # 🔐 ADMIN CHECK
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 👤 USERS
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    # 💰 EXPENSES WITH JOIN
    cur.execute("""
        SELECT u.username,
               e.amount,
               c.name AS category,
               e.date,
               e.description
        FROM expenses e
        JOIN users u ON u.id = e.user_id
        JOIN categories c ON c.id = e.category_id
        ORDER BY e.id DESC
    """)
    expenses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin.html",
        users=users,
        expenses=expenses
    )
