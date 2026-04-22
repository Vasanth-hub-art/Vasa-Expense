from flask import Flask
import os
from models import init_db

app = Flask(__name__)
app.secret_key = "secret123"

# 🚀 SAFE INIT (DO NOT CRASH APP)
with app.app_context():
    try:
        init_db()
        print("DB initialized")
    except Exception as e:
        print("DB init error:", e)

@app.route("/")
def home():
    return "Vasa Expense Running 🚀"

if __name__ == "__main__":
    app.run()
