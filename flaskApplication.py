from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection configuration
app.config['MONGO_URI'] = 'mongodb+srv://tylerlian2021:CytaQbiGsjwFwe8k@bfgsafespace.tnob2zh.mongodb.net/'
mongo_client = MongoClient(app.config['MONGO_URI'])
db = mongo_client['mydatabase']  # Replace 'mydatabase' with your desired database name

# Sample route to retrieve data from MongoDB
@app.route('/users', methods=['GET'])
def get_users():
    users_collection = db.users  # Replace "users" with your desired collection name
    users = list(users_collection.find())
    return jsonify(users)

if __name__ == '__main__':
    app.run(debug=True)

