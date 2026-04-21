from flask import Blueprint, render_template, session, redirect, url_for
from models import get_db

admin = Blueprint('admin', __name__)

@admin.route('/admin')
def admin_dashboard():

    # 🔐 LOGIN CHECK
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # 🔐 ADMIN CHECK
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    db = get_db()

    # 👤 USERS
    users = db.execute("SELECT * FROM users").fetchall()

    # 💰 EXPENSES WITH CATEGORY
    expenses = db.execute("""
        SELECT u.username,
               e.amount,
               c.name AS category,
               e.date,
               e.description
        FROM expenses e
        JOIN users u ON u.id = e.user_id
        JOIN categories c ON c.id = e.category_id
        ORDER BY e.id DESC
    """).fetchall()

    return render_template("admin.html",
                           users=users,
                           expenses=expenses)