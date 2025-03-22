from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Serve the HTML file
@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')


# Database Connection
def get_db_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            passwd='divya1111',
            database='pantry_genie'
        )
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


con1 = get_db_connection()
cur1 = con1.cursor()


# Routes
@app.route('/register', methods=['POST'])
def register():
    try:
        # Debug: Print the incoming data
        data = request.json
        print("Received data:", data)

        # Extract required fields from the request
        newname = data['name']
        illness = data['illness']
        shoppref = data['shoppref']

        # Fetch the current maximum customer ID
        cur1.execute("SELECT MAX(custid) FROM Customers;")
        result = cur1.fetchone()
        max_custid = result[0] if result[0] is not None else 0

        # Insert a new customer
        new_custid = max_custid + 1
        cur1.execute(
            "INSERT INTO Customers (custid, name, illness, shop_pref, reward_points) VALUES (%s, %s, %s, %s, 0);",
            (new_custid, newname, illness, shoppref),
        )
        print("Inserted customer ID:", new_custid)

        # Create a table for the new customer's orders
        cur1.execute(
            f"CREATE TABLE `{new_custid}T` ("
            "CustName CHAR(30), "
            "Itemordered CHAR(20), "
            "Dateoforder DATE DEFAULT CURDATE(), "
            "Ordernumber INT, "
            "shop_name CHAR(20)"
            ");"
        )
        print(f"Created table for customer {new_custid}")

        con1.commit()

        return jsonify({"message": "Customer registered successfully!", "customer_id": new_custid})

    except mysql.connector.Error as err:
        print("Database error:", err)  # Log the error
        return jsonify({"error": f"Database error: {err}"}), 500

    except Exception as ex:
        print("Unexpected error:", ex)  # Log unexpected errors
        return jsonify({"error": f"Unexpected error: {ex}"}), 500


@app.route('/restock', methods=['POST'])
def restock():
    try:
        data = request.json
        product = data['product']
        shop = data['shop']

        cur1.execute(f"UPDATE `{shop}` SET quantity = quantity + 40 WHERE item_name = %s;", (product,))
        con1.commit()
        return jsonify({"message": f"Restocked {product} in {shop} successfully!"})

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500


@app.route('/order', methods=['POST'])
def order():
    try:
        data = request.json
        cust_id = data['customer_id']
        order_list = data['order_list']

        for item in order_list:
            cur1.execute(
                f"INSERT INTO `{cust_id}T` (Itemordered, Ordernumber, shop_name) VALUES (%s, %s, %s);",
                (item['item'], item['order_number'], item['shop']),
            )
        con1.commit()
        return jsonify({"message": "Order placed successfully!"})

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500


@app.route('/previous_orders/<int:cust_id>', methods=['GET'])
def previous_orders(cust_id):
    try:
        cur1.execute(
            f"SELECT * FROM `{cust_id}T` WHERE Dateoforder = (SELECT MAX(Dateoforder) FROM `{cust_id}T`);"
        )
        orders = cur1.fetchall()

        results = [
            {"item_no": order[3], "item_name": order[1], "date_of_order": order[2]}
            for order in orders
        ]
        return jsonify({"previous_orders": results})

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500


@app.route('/check_stock', methods=['POST'])
def check_stock():
    try:
        data = request.json
        product = data['product']
        shop = data['shop']

        cur1.execute(f"SELECT item_name, quantity, price FROM `{shop}` WHERE item_name = %s;", (product,))
        item = cur1.fetchone()

        if item:
            return jsonify({
                "message": f"The product {product} is available in {shop}.",
                "quantity_available": item[1],
                "price": item[2]
            })
        else:
            return jsonify({"message": "Product unavailable."})

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500


@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        data = request.json
        shop_name = data['shop_name']
        products = data['products']

        for product in products:
            cur1.execute(
                f"INSERT INTO `{shop_name}` (sno, item_name, quantity, price) VALUES (%s, %s, %s, %s);",
                (product['sno'], product['iname'], product['quantity'], product['price']),
            )
        con1.commit()
        return jsonify({"message": "Products added successfully!"})

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500


@app.route('/customers', methods=['GET'])
def get_customers():
    try:
        cur1.execute("SELECT * FROM Customers;")
        customers = cur1.fetchall()

        customer_list = [
            {"id": cust[0], "name": cust[1], "illness": cust[2], "shop_pref": cust[3]}
            for cust in customers
        ]
        return jsonify({"message": "Success", "data": customer_list})

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500


@app.route('/register_user', methods=['POST'])
def register_user():
    data = request.json
    username = data['username']
    password = data['password']
    role = data['role']  # 'user', 'shop_owner', or 'admin'

    # Validate the role
    if role not in ['customer', 'shop_owner', 'admin']:
        return jsonify({"error": "Invalid role"}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    try:
        cur1.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s);",
            (username, hashed_password, role)
        )
        con1.commit()
        return jsonify({"message": f"User '{username}' registered successfully as {role}!"})
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500


# Login User
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    try:
        cur1.execute("SELECT user_id, password, role FROM users WHERE username = %s;", (username,))
        user = cur1.fetchone()

        if user and check_password_hash(user[1], password):
            user_id, _, role = user
            return jsonify({"message": "Login successful!", "user_id": user_id, "role": role})
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500


# Example Admin-Only Route
@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    # Check user role (replace with session or token-based validation for production)
    user_role = request.headers.get('Role')  # Pass role in headers for simplicity
    if user_role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403

    return jsonify({"message": "Welcome to the Admin Dashboard!"})


# Example Shop Owner-Only Route
@app.route('/shop_dashboard', methods=['GET'])
def shop_dashboard():
    user_role = request.headers.get('Role')
    if user_role != 'shop_owner':
        return jsonify({"error": "Unauthorized access"}), 403

    return jsonify({"message": "Welcome to the Shop Owner Dashboard!"})


# Example User-Only Route
@app.route('/user_dashboard', methods=['GET'])
def user_dashboard():
    user_role = request.headers.get('Role')
    if user_role != 'user':
        return jsonify({"error": "Unauthorized access"}), 403

    return jsonify({"message": "Welcome to the User Dashboard!"})


if __name__ == '__main__':
    app.run(debug=True)
