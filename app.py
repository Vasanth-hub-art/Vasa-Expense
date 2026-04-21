from flask import Flask
from models import init_db

from routes.auth import auth
from routes.expenses import expenses
from routes.admin import admin
from routes.api import api

app = Flask(__name__)
app.secret_key = "secret123"

init_db()

app.register_blueprint(auth)
app.register_blueprint(expenses)
app.register_blueprint(admin)
app.register_blueprint(api)

if __name__ == "__main__":
    app.run(debug=True)