from flask import Blueprint, render_template, request, redirect, session, flash, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import get_db

auth = Blueprint('auth', __name__)


# ---------------- HOME ----------------
@auth.route('/')
def home():
    return render_template('home.html')


# ---------------- LOGIN ----------------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE username=?",
            (request.form['username'],)
        ).fetchone()

        # ❌ INVALID USER
        if not user:
            flash("Invalid username ❌")
            return redirect(url_for('auth.login'))

        # ❌ WRONG PASSWORD
        if not check_password_hash(user['password'], request.form['password']):
            flash("Invalid password ❌")
            return redirect(url_for('auth.login'))

        # ✅ LOGIN SUCCESS
        session['user_id'] = user['id']
        session['role'] = user['role']

        # 👉 ADMIN → ADMIN PAGE
        if user['role'] == 'admin':
            return redirect('/admin')

        return redirect('/dashboard')

    return render_template('login.html')


# ---------------- REGISTER ----------------
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()

        username = request.form['username']
        password = request.form['password']

        # ❗ CHECK EXISTING USER
        existing = db.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if existing:
            flash("Username already exists ⚠️")
            return redirect(url_for('auth.register'))

        db.execute(
            "INSERT INTO users(username,password,role) VALUES(?,?,?)",
            (username, generate_password_hash(password), "user")
        )
        db.commit()

        flash("Registration successful ✅ Please login")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ---------------- LOGOUT ----------------
@auth.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------- ANALYTICS PAGE ----------------
@auth.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect('/login')

    # ❌ ADMIN SHOULD NOT SEE ANALYTICS
    if session.get('role') == 'admin':
        return redirect('/admin')

    return render_template('analytics.html')


# ---------------- CHART DATA API ----------------
@auth.route('/chart-data')
def chart_data():
    if 'user_id' not in session:
        return jsonify({"categories": [], "amounts": []})

    db = get_db()

    data = db.execute("""
        SELECT c.name, SUM(e.amount) as total
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        WHERE e.user_id=?
        GROUP BY c.name
    """, (session['user_id'],)).fetchall()

    return jsonify({
        "categories": [row['name'] for row in data],
        "amounts": [row['total'] for row in data]
    })