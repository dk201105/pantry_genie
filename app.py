from flask import Flask, request, jsonify, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from prisma import Prisma

app = Flask(__name__)
app.secret_key = "your_secret_key"
CORS(app)

db = Prisma()
db.connect()

@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

@app.route('/register_user', methods=['POST'])
def register_user():
    data = request.json
    username = data['username']
    password = data['password']
    role = data['role']

    if role not in ['customer', 'shop_owner', 'admin']:
        return jsonify({"error": "Invalid role"}), 400

    hashed_password = generate_password_hash(password)

    try:
        user = db.user.create(
            data={
                "username": username,
                "password": hashed_password,
                "role": role,
            }
        )
        return jsonify({"message": f"User '{username}' registered successfully as {role}!"})
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    try:
        user = db.user.find_unique(
            where={"username": username}
        )

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            return jsonify({"message": "Login successful!", "role": user.role})
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/restock', methods=['POST'])
def restock():
    data = request.json
    product_name = data['product']
    shop_name = data['shop']

    try:
        product = db.product.update_many(
            where={"itemName": product_name, "shop": {"shopName": shop_name}},
            data={"quantity": {"increment": 40}}
        )
        return jsonify({"message": f"Restocked {product_name} in {shop_name} successfully!"})
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/admin_dashboard', methods=['GET'])
@role_required('admin')
def admin_dashboard():
    try:
        users = db.user.find_many(where={"role": "customer"})
        return jsonify({"message": "Welcome to the Admin Dashboard!", "users": users})
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
