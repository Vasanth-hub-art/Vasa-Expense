from flask import Flask, redirect, session
import os

from models import init_db
from routes.auth import auth
from routes.expenses import expenses
from routes.admin import admin
from routes.api import api

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")

# Blueprints
app.register_blueprint(auth)
app.register_blueprint(expenses)
app.register_blueprint(admin)
app.register_blueprint(api)

# DB INIT (SAFE)
def safe_init_db():
    try:
        with app.app_context():
            init_db()
        print("DB initialized successfully")
    except Exception as e:
        print("DB init failed:", e)

safe_init_db()

# ROOT ROUTE
@app.route("/")
def home():
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect("/admin")
        return redirect("/dashboard")
    return redirect("/login")

# HEALTH CHECK
@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run()
