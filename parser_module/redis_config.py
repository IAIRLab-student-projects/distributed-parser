#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[ ]:


import redis

redis_host = "redis"
redis_port = 6379

redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

def get_task_key(task_id):
    return f"task:{task_id}"

