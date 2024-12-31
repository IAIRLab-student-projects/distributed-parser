#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[2]:


import os
import time
import json
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import pika
import requests
from pymongo import MongoClient

def load_token():
    try:
        with open("token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError("Token file 'token.txt' not found. Please ensure the file exists and contains the API token.")

VK_API_TOKEN = load_token()

app = Flask(__name__)
CORS(app)

redis_host = "localhost"
redis_port = 6379
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

rabbitmq_host = "localhost"
rabbitmq_queue = "vk_tasks"
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
channel = connection.channel()
channel.queue_declare(queue=rabbitmq_queue)

mongo_host = "localhost"
mongo_port = 27017
mongo_client = MongoClient(host=mongo_host, port=mongo_port)
mongo_db = mongo_client["vk_data"]
mongo_collection = mongo_db["posts"]

DEFAULT_GROUP_ID = "lilgarage"

@app.route("/monitor", methods=["POST"])
def create_monitor_task():
    data = request.json
    group_ids = data.get("group_ids", [DEFAULT_GROUP_ID])

    task_id = redis_client.incr("task_id")
    task_key = f"task:{task_id}"

    redis_client.hmset(task_key, {
        "status": "pending",
        "groups": json.dumps(group_ids)
    })

    task_message = json.dumps({
        "task_id": task_id,
        "groups": group_ids
    })
    channel.basic_publish(exchange='', routing_key=rabbitmq_queue, body=task_message)

    return jsonify({"task_id": task_id, "status": "pending"}), 201

@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_status(task_id):
    task_key = f"task:{task_id}"
    if not redis_client.exists(task_key):
        return jsonify({"error": "Task not found"}), 404

    task = redis_client.hgetall(task_key)
    task["groups"] = json.loads(task["groups"])
    return jsonify(task), 200

def process_task(ch, method, properties, body):
    try:
        task = json.loads(body)
        task_id = task["task_id"]
        group_ids = task["groups"]

        for group_id in group_ids:
            base_url = "https://api.vk.com/method/wall.get"
            params = {
                "owner_id": group_id,
                "access_token": VK_API_TOKEN,
                "v": "5.131",
                "count": 10,
                "filter": "owner"
            }

            response = requests.get(base_url, params=params).json()

            if "error" in response:
                print("Error from VK API:", response["error"].get("error_msg", "Unknown error"))
                redis_client.hset(f"task:{task_id}", "status", "error")
                continue

            items = response.get("response", {}).get("items", [])

            for item in items:
                post_data = {
                    "id": item.get("id"),
                    "date": item.get("date"),
                    "text": item.get("text", ""),
                    "owner_id": group_id
                }
                mongo_collection.update_one({"id": post_data["id"]}, {"$set": post_data}, upsert=True)

        redis_client.hset(f"task:{task_id}", "status", "completed")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing task: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def run_worker():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()
    channel.queue_declare(queue=rabbitmq_queue)
    channel.basic_consume(queue=rabbitmq_queue, on_message_callback=process_task)
    print("Worker is running and waiting for tasks...")
    channel.start_consuming()

def periodic_parsing(group_id=DEFAULT_GROUP_ID):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()
    channel.queue_declare(queue=rabbitmq_queue)
    while True:
        task_message = json.dumps({
            "task_id": redis_client.incr("task_id"),
            "groups": [group_id]
        })
        print(f"Sending periodic parsing task: {task_message}")
        channel.basic_publish(exchange='', routing_key=rabbitmq_queue, body=task_message)
        time.sleep(120)  # Wait 2 minutes

def start_all():
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False), daemon=True).start()

    threading.Thread(target=run_worker, daemon=True).start()

    threading.Thread(target=periodic_parsing, daemon=True).start()

if __name__ == "__main__":
    start_all()


# In[ ]:




