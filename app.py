from flask import Flask, redirect, session
import os

from models import init_db
from routes.auth import auth
from routes.expenses import expenses
from routes.admin import admin
from routes.api import api

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")

# ✅ REGISTER BLUEPRINTS
app.register_blueprint(auth)
app.register_blueprint(expenses)
app.register_blueprint(admin)
app.register_blueprint(api)


# ✅ INIT DB (SAFE)
def safe_init_db():
    try:
        with app.app_context():
            init_db()
        print("DB initialized")
    except Exception as e:
        print("DB init error:", e)


safe_init_db()


# ✅ ROOT ROUTE (IMPORTANT FOR RENDER)
@app.route("/")
def home():
    return "App Running 🚀"


# ✅ MUST EXIST FOR RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
