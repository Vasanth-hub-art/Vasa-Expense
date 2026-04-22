from flask import Blueprint, render_template, request, redirect, session, flash, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import get_db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s",
                    (request.form['username'],))
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


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()

        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            flash("Username already exists ⚠️")
            return redirect(url_for('auth.register'))

        cur.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        """, (username, password, "user"))

        conn.commit()

        flash("Registration successful ✅")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@auth.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') == 'admin':
        return redirect('/admin')

    return render_template('analytics.html')
