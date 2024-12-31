#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[ ]:


import os
import time
import json
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from redis_config import redis_client, get_task_key
from rabbitmq_config import get_channel, rabbitmq_queue
from mongodb_config import save_post

VK_API_TOKEN = os.getenv("VK_API_TOKEN", "your_default_token")

app = Flask(__name__)
CORS(app)

DEFAULT_GROUP_ID = "lilgarage"

@app.route("/monitor", methods=["POST"])
def create_monitor_task():
    data = request.json
    group_ids = data.get("group_ids", [DEFAULT_GROUP_ID])

    task_id = redis_client.incr("task_id")
    task_key = get_task_key(task_id)

    redis_client.hset(task_key, mapping={
        "status": "pending",
        "groups": json.dumps(group_ids)
    })

    _, channel = get_channel()
    task_message = json.dumps({
        "task_id": task_id,
        "groups": group_ids
    })
    channel.basic_publish(exchange='', routing_key=rabbitmq_queue, body=task_message)

    return jsonify({"task_id": task_id, "status": "pending"}), 201

@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_status(task_id):
    task_key = get_task_key(task_id)
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
                redis_client.hset(get_task_key(task_id), "status", "error")
                continue

            items = response.get("response", {}).get("items", [])

            for item in items:
                post_data = {
                    "id": item.get("id"),
                    "date": item.get("date"),
                    "text": item.get("text", ""),
                    "owner_id": group_id
                }
                save_post(post_data)

        redis_client.hset(get_task_key(task_id), "status", "completed")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing task: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def run_worker():
    _, channel = get_channel()
    channel.basic_consume(queue=rabbitmq_queue, on_message_callback=process_task)
    print("Worker is running and waiting for tasks...")
    channel.start_consuming()

def periodic_parsing(group_id=DEFAULT_GROUP_ID):
    _, channel = get_channel()
    while True:
        task_message = json.dumps({
            "task_id": redis_client.incr("task_id"),
            "groups": [group_id]
        })
        print(f"Sending periodic parsing task: {task_message}")
        channel.basic_publish(exchange='', routing_key=rabbitmq_queue, body=task_message)
        time.sleep(120)

def start_all():
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False), daemon=True).start()
    threading.Thread(target=run_worker, daemon=True).start()
    threading.Thread(target=periodic_parsing, daemon=True).start()

if __name__ == "__main__":
    start_all()

