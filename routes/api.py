from flask import Blueprint, jsonify, request, session
from models import get_db

api = Blueprint('api', __name__)

@api.route('/chart-data')
def chart():

    # 🔐 check login
    if 'user_id' not in session:
        return jsonify({"categories": [], "amounts": []})

    db = get_db()

    filter_type = request.args.get('filter', 'month')

    # ✅ FIXED QUERY WITH JOIN
    query = """
    SELECT c.name, SUM(e.amount)
    FROM expenses e
    JOIN categories c ON c.id = e.category_id
    WHERE e.user_id=?
    GROUP BY c.name
    """

    data = db.execute(query, (session['user_id'],)).fetchall()

    return jsonify({
        "categories": [row[0] for row in data],
        "amounts": [row[1] for row in data]
    })