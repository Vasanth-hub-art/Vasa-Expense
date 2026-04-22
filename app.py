from flask import Flask
import os

from models import init_db
from routes.auth import auth
from routes.expenses import expenses
from routes.admin import admin
from routes.api import api

app = Flask(__name__)
app.secret_key = "secret123"


# ================= BLUEPRINTS =================
app.register_blueprint(auth)
app.register_blueprint(expenses)
app.register_blueprint(admin)
app.register_blueprint(api)


# ================= SAFE INIT =================
def safe_init():
    try:
        with app.app_context():
            init_db()
        print("DB initialized")
    except Exception as e:
        print("DB error:", e)


safe_init()


@app.route("/")
def home():
    return "Vasa Expense Running 🚀"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
