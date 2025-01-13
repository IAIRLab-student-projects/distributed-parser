#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[ ]:


import json
import requests
from redis_manager import update_task_status
from mongodb import save_post_to_mongo
from rabbitmq import get_rabbitmq_channel

def load_token():
    try:
        with open("token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError("Token file 'token.txt' not found. Please ensure the file exists and contains the API token.")

VK_API_TOKEN = load_token()

def fetch_posts(group_id, access_token, count=100):
    base_url = "https://api.vk.com/method/wall.get"
    params = {
        "owner_id": group_id,
        "access_token": access_token,
        "v": "5.131",
        "count": count,
        "filter": "owner"
    }
    response = requests.get(base_url, params=params).json()
    if "error" in response:
        raise Exception(response["error"].get("error_msg", "Unknown error"))
    return response.get("response", {}).get("items", [])

def process_task(ch, method, properties, body):
    try:
        task = json.loads(body)
        task_id = task["task_id"]
        group_ids = task["groups"]

        for group_id in group_ids:
            try:
                posts = fetch_posts(group_id, access_token=VK_API_TOKEN)
                for post in posts:
                    save_post_to_mongo(post)
            except Exception as e:
                print(f"Error fetching posts for group {group_id}: {e}")
                update_task_status(task_id, "error")
                continue

        update_task_status(task_id, "completed")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing task: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":
    channel = get_rabbitmq_channel()
    channel.basic_consume(queue="vk_tasks", on_message_callback=process_task)
    print("Worker is running and waiting for tasks...")
    channel.start_consuming()

