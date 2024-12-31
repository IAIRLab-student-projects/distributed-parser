#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[ ]:


from pymongo import MongoClient

mongo_host = "mongodb"
mongo_port = 27017

mongo_client = MongoClient(host=mongo_host, port=mongo_port)
mongo_db = mongo_client["vk_data"]
mongo_collection = mongo_db["posts"]

def save_post(post_data):
    mongo_collection.update_one({"id": post_data["id"]}, {"$set": post_data}, upsert=True)

