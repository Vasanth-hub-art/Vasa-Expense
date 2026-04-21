from flask import Blueprint, jsonify, request, session
from models import get_db

api = Blueprint('api', __name__)

@api.route('/chart-data')
def chart():

    # 🔐 check login
    if 'user_id' not in session:
        return jsonify({"categories": [], "amounts": []})

    db = get_db()
    cur = db.cursor()

    filter_type = request.args.get('filter', 'month')

    # ✅ PostgreSQL FIXED QUERY
    query = """
    SELECT c.name, SUM(e.amount)
    FROM expenses e
    JOIN categories c ON c.id = e.category_id
    WHERE e.user_id = %s
    GROUP BY c.name
    """

    cur.execute(query, (session['user_id'],))
    data = cur.fetchall()

    return jsonify({
        "categories": [row[0] for row in data],
        "amounts": [float(row[1]) for row in data]
    })
