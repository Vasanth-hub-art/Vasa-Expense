from flask import Blueprint, render_template, request, redirect, session
from models import get_db

expenses = Blueprint('expenses', __name__)

def login_required():
    return 'user_id' in session


# 📊 DASHBOARD
@expenses.route('/dashboard')
def dashboard():
    if not login_required():
        return redirect('/')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT e.*, c.name as category
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id=%s
        ORDER BY e.id DESC
    """, (session['user_id'],))

    data = cur.fetchall()

    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('dashboard.html',
                           data=data,
                           categories=categories)


# ➕ ADD
@expenses.route('/add', methods=['POST'])
def add():
    if not login_required():
        return redirect('/')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO expenses(user_id, amount, category_id, date, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        session['user_id'],
        request.form['amount'],
        request.form['category_id'],
        request.form['date'],
        request.form['description']
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect('/dashboard')


# ❌ DELETE
@expenses.route('/delete/<int:id>')
def delete(id):
    if not login_required():
        return redirect('/')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM expenses WHERE id=%s", (id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect('/dashboard')


# ✏️ EDIT
@expenses.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if not login_required():
        return redirect('/')

    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute("""
            UPDATE expenses
            SET amount=%s, category_id=%s, date=%s, description=%s
            WHERE id=%s
        """, (
            request.form['amount'],
            request.form['category_id'],
            request.form['date'],
            request.form['description'],
            id
        ))

        conn.commit()
        cur.close()
        conn.close()
        return redirect('/dashboard')

    cur.execute("SELECT * FROM expenses WHERE id=%s", (id,))
    expense = cur.fetchone()

    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('edit.html',
                           e=expense,
                           categories=categories)
