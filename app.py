from flask import Flask
import os

from models import init_db
from routes.auth import auth
from routes.expenses import expenses
from routes.admin import admin
from routes.api import api

app = Flask(__name__)
app.secret_key = "secret123"


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
        print("DB init skipped/failed:", e)


safe_init_db()


# ================= RENDER ENTRY POINT =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
