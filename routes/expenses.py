from flask import Blueprint, render_template, request, redirect, session
from models import get_db

expenses = Blueprint('expenses', __name__)

# 🔐 LOGIN CHECK
def login_required():
    return 'user_id' in session


# 📊 DASHBOARD
@expenses.route('/dashboard')
def dashboard():
    if not login_required():
        return redirect('/')

    db = get_db()

    # ✅ JOIN WITH CATEGORY TABLE
    data = db.execute("""
        SELECT e.*, c.name as category
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id=?
        ORDER BY e.id DESC
    """, (session['user_id'],)).fetchall()

    # ✅ FETCH CATEGORIES FOR DROPDOWN
    categories = db.execute("SELECT * FROM categories").fetchall()

    return render_template('dashboard.html',
                           data=data,
                           categories=categories)


# ➕ ADD EXPENSE
@expenses.route('/add', methods=['POST'])
def add():
    if not login_required():
        return redirect('/')

    db = get_db()

    db.execute("""
        INSERT INTO expenses(user_id, amount, category_id, date, description)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session['user_id'],
        request.form['amount'],
        request.form['category_id'],   # ✅ FIXED
        request.form['date'],
        request.form['description']
    ))

    db.commit()
    return redirect('/dashboard')


# ❌ DELETE
@expenses.route('/delete/<int:id>')
def delete(id):
    if not login_required():
        return redirect('/')

    db = get_db()
    db.execute("DELETE FROM expenses WHERE id=?", (id,))
    db.commit()
    return redirect('/dashboard')


# ✏️ EDIT
@expenses.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    if not login_required():
        return redirect('/')

    db = get_db()

    if request.method == 'POST':
        db.execute("""
            UPDATE expenses
            SET amount=?, category_id=?, date=?, description=?
            WHERE id=?
        """, (
            request.form['amount'],
            request.form['category_id'],   # ✅ FIXED
            request.form['date'],
            request.form['description'],
            id
        ))

        db.commit()
        return redirect('/dashboard')

    # GET DATA + CATEGORIES
    expense = db.execute("SELECT * FROM expenses WHERE id=?", (id,)).fetchone()
    categories = db.execute("SELECT * FROM categories").fetchall()

    return render_template('edit.html',
                           e=expense,
                           categories=categories)