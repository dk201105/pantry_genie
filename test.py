from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return "Home"

@app.route("/get-user/<user_id>") #user_id is a path parameter
def get_user(user_id):
    user_data = {
        "user_id": user_id,
        "name" : "John Doe",
        "email" : "john@example.com"
    }

    extra = request.args.get("extra")
    if extra:
        user_data["extra"] = extra
    return jsonify(user_data), 200 #200 http success code - status

@app.route("/create-user", methods=["POST"])
def create_user():
    data = request.get_json()

    return jsonify(data),201

'''
GET #retrieve data
POST #create 
PUT #update
DELETE #delete
'''

if __name__ == "__main__": #flask framework
    app.run(debug=True)