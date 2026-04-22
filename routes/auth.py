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
        cur = db.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=%s",
            (request.form['username'],)
        )

        user = cur.fetchone()

        if not user:
            flash("Invalid username ❌")
            return redirect(url_for('auth.login'))

        if not check_password_hash(user['password'], request.form['password']):
            flash("Invalid password ❌")
            return redirect(url_for('auth.login'))

        session['user_id'] = user['id']
        session['role'] = user['role']

        if user['role'] == 'admin':
            return redirect('/admin')

        return redirect('/dashboard')

    return render_template('login.html')


# ---------------- REGISTER ----------------
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()

        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        cur.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        existing = cur.fetchone()

        if existing:
            flash("Username already exists ⚠️")
            return redirect(url_for('auth.register'))

        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, password, "user")
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


# ---------------- ANALYTICS ----------------
@auth.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') == 'admin':
        return redirect('/admin')

    return render_template('analytics.html')


# ---------------- CHART DATA ----------------
@auth.route('/chart-data')
def chart_data():
    if 'user_id' not in session:
        return jsonify({"categories": [], "amounts": []})

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT c.name, SUM(e.amount)
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        WHERE e.user_id=%s
        GROUP BY c.name
    """, (session['user_id'],))

    data = cur.fetchall()

    return jsonify({
        "categories": [row[0] for row in data],
        "amounts": [float(row[1]) for row in data]
    })
