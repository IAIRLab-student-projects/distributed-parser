#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[ ]:


import redis
import json

redis_host = "redis"
redis_port = 6379
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

def create_task_in_redis(group_ids):
    task_id = redis_client.incr("task_id")
    task_key = f"task:{task_id}"
    redis_client.hmset(task_key, {
        "status": "pending",
        "groups": json.dumps(group_ids)
    })
    return task_id, task_key

def update_task_status(task_id, status):
    redis_client.hset(f"task:{task_id}", "status", status)

def get_task_status_from_redis(task_id):
    task_key = f"task:{task_id}"
    if not redis_client.exists(task_key):
        return None
    task = redis_client.hgetall(task_key)
    task["groups"] = json.loads(task["groups"])
    return task

