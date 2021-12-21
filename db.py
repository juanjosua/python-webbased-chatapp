from pymongo import MongoClient
from werkzeug.security import generate_password_hash

from user import User

client = MongoClient(
    'mongodb+srv://test:test@chatapp.qs3uy.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')

# connect to the database in mongodb
chat_db = client.get_database('ChatDB')

# connect to the collections
users_collection = chat_db.get_collection('users')

# create new user entry


def save_user(username, email, password):
    password_hash = generate_password_hash(password)
    users_collection.insert_one({
        '_id': username,
        'email': email,
        'password': password_hash
    })


def get_user(username):
    user_data = users_collection.find_one({
        '_id': username
    })
    return User(user_data['_id'], user_data['email'], user_data['password']) if user_data else None
