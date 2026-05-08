from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client['affiliatetracker']
users_collection = db["user"]
affiliate_links = db["affiliate_links"]
products_collection = db['products_collection']
click_collection = db['click_collection']
sales_collection = db['sales_collection']