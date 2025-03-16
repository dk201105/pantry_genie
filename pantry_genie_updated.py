from flask import Flask, request, jsonify
import mysql.connector
from prettytable import PrettyTable
import threading
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to Pantry Genie!"
    

# Database Connections
def get_db_connection(db_name):
    return mysql.connector.connect(
        host='localhost',
        user='root',
        passwd='divya1111',
        database='pantry_genie'
    )

con1 = get_db_connection('Customer')
cur1 = con1.cursor()
con2 = get_db_connection('Shops')
cur2 = con2.cursor()
con3 = get_db_connection('Illness')
cur3 = con3.cursor()
con4 = get_db_connection('INDCUST')
cur4 = con4.cursor()
con5 = get_db_connection('Restocking')
cur5 = con5.cursor()
con6 = get_db_connection('Payment_and_delivery')
cur6 = con6.cursor()

List_of_restocking_info = []

# New Customer Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    newname = data['name']
    illness = data['illness']
    shoppref = data['shoppref']
    
    cur1.execute("SELECT * FROM Customers;")
    V = cur1.fetchall()
    
    if len(V) != 0:
        cur1.execute("INSERT INTO Customers VALUES ((SELECT MAX(custid) FROM Customers)+1, %s, %s, %s, 0);", (newname, illness, shoppref))
    else:
        cur1.execute("INSERT INTO Customers VALUES (1, %s, %s, %s, 0);", (newname, illness, shoppref))
    
    cur1.execute("SELECT MAX(custid) FROM Customers;")
    cid = cur1.fetchone()[0]
    cur4.execute(f"CREATE TABLE `{cid}T` (CustName CHAR(30) DEFAULT '{newname}', Itemordered CHAR(20), Dateoforder DATE DEFAULT CURDATE(), Ordernumber INT, shop_name CHAR(20));")
    con1.commit()
    con4.commit()
    
    return jsonify({"message": "Customer registered successfully!", "customer_id": cid})

# Restocking Items
@app.route('/restock', methods=['POST'])
def restock():
    data = request.json
    prod = data['product']
    shop = data['shop']
    
    cur2.execute(f"UPDATE `{shop}` SET QUANTITY = QUANTITY + 40 WHERE ITEM_NAME = %s;", (prod,))
    con2.commit()
    
    for removal in List_of_restocking_info:
        if removal[:2] == [shop, prod]:
            List_of_restocking_info.remove(removal)
    
    return jsonify({"message": f"Restocked {prod} in {shop} successfully!"})

# Getting Grocery List
@app.route('/order', methods=['POST'])
def order():
    data = request.json
    custid = data['customer_id']
    order_list = data['order_list']
    
    for item in order_list:
        cur4.execute(f"INSERT INTO `{custid}T` (Itemordered, Ordernumber, shop_name) VALUES (%s, %s, %s);", (item['item'], item['order_number'], item['shop']))
    con4.commit()
    
    return jsonify({"message": "Order placed successfully!"})

# Getting Previous Orders
@app.route('/previous_orders/<int:custid>', methods=['GET'])
def previous_orders(custid):
    cur4.execute(f"SELECT * FROM `{custid}T` WHERE Dateoforder = (SELECT MAX(Dateoforder) FROM `{custid}T`);")
    buy_details = cur4.fetchall()
    
    orders = []
    for pbuy in buy_details:
        orders.append({
            "item_no": pbuy[3],
            "item_name": pbuy[1],
            "date_of_order": pbuy[2]
        })
    
    return jsonify({"previous_orders": orders})

# Checking Stock Availability
@app.route('/check_stock', methods=['POST'])
def check_stock():
    data = request.json
    prodn = data['product']
    shopn = data['shop']
    
    cur2.execute(f"SELECT item_name, quantity, price FROM `{shopn}` WHERE item_name = %s;", (prodn,))
    prod = cur2.fetchone()
    
    if prod:
        return jsonify({
            "message": f"The product {prodn} is available in {shopn}.",
            "quantity_available": prod[1],
            "price": prod[2]
        })
    else:
        return jsonify({"message": "Product unavailable."})

# Shop Owner Functions
@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.json
    sname = data['shop_name']
    products = data['products']
    
    for product in products:
        cur2.execute(f"INSERT INTO `{sname}` VALUES (%s, %s, %s, %s);", (product['sno'], product['iname'], product['quantity'], product['price']))
    con2.commit()
    
    return jsonify({"message": "Records added successfully!"})

if __name__ == '__main__':
    app.run(debug=True)