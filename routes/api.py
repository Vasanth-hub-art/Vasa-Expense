from flask import Blueprint, jsonify, request, session
from models import get_db

api = Blueprint('api', __name__)

@api.route('/chart-data')
def chart():

    # 🔐 check login
    if 'user_id' not in session:
        return jsonify({"categories": [], "amounts": []})

    conn = get_db()
    cur = conn.cursor()

    filter_type = request.args.get('filter', 'month')

    # ✅ PostgreSQL query
    cur.execute("""
        SELECT c.name AS category, SUM(e.amount) AS total
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        WHERE e.user_id = %s
        GROUP BY c.name
    """, (session['user_id'],))

    data = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        "categories": [row['category'] for row in data],
        "amounts": [float(row['total']) for row in data]
    })
