#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[ ]:


from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from redis_manager import create_task_in_redis, get_task_status_from_redis
from rabbitmq import send_task_to_queue

app = Flask(__name__)
CORS(app)

DEFAULT_GROUP_ID = "lentach"

@app.route("/monitor", methods=["POST"])
def create_monitor_task():
    data = request.json
    group_ids = data.get("group_ids", [DEFAULT_GROUP_ID])
    task_id, task_key = create_task_in_redis(group_ids)
    send_task_to_queue(task_id, group_ids)
    return jsonify({"task_id": task_id, "status": "pending"}), 201

@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_status(task_id):
    task = get_task_status_from_redis(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

