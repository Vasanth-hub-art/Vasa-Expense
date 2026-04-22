from flask import Blueprint, render_template, request, redirect, session
from models import get_db

expenses = Blueprint('expenses', __name__)

def login_required():
    return 'user_id' in session


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

    return render_template('dashboard.html',
                           data=data,
                           categories=categories)


@expenses.route('/add', methods=['POST'])
def add():
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
    return redirect('/dashboard')


@expenses.route('/delete/<int:id>')
def delete(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM expenses WHERE id=%s", (id,))
    conn.commit()

    return redirect('/dashboard')
