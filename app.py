from flask import Flask, redirect, session, os

from models import init_db
from routes.auth import auth
from routes.expenses import expenses
from routes.admin import admin
from routes.api import api

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")

# ================= BLUEPRINT REGISTRATION =================
app.register_blueprint(auth)
app.register_blueprint(expenses)
app.register_blueprint(admin)
app.register_blueprint(api)


# ================= SAFE DB INIT =================
def safe_init_db():
    try:
        with app.app_context():
            init_db()
        print("DB initialized successfully")
    except Exception as e:
        print("DB init failed/skipped:", e)


safe_init_db()


# ================= ROOT ROUTE =================
@app.route("/")
def home():
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect("/admin")
        return redirect("/dashboard")
    return redirect("/login")


# ================= HEALTH CHECK (Render-friendly) =================
@app.route("/health")
def health():
    return "OK", 200


# ================= RUN APP =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
