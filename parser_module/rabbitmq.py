#!/usr/bin/env python
# coding: utf-8

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[ ]:


import pika
import logging

# Настройки RabbitMQ
rabbitmq_host = "localhost"  # Имя RabbitMQ из docker-compose.yml
rabbitmq_port = 5672
rabbitmq_queue = "vk_tasks"  # Имя очереди для задач
rabbitmq_user = "guest"  # Пользователь (указан в docker-compose.yml)
rabbitmq_password = "guest"  # Пароль (указан в docker-compose.yml)

def get_rabbitmq_channel():
    """
    Устанавливает соединение с RabbitMQ и возвращает канал.
    """
    try:
        logging.info(f"Connecting to RabbitMQ at {rabbitmq_host}...")
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_queue)  # Убедимся, что очередь существует
        logging.info("Successfully connected to RabbitMQ and declared the queue.")
        return channel
    except pika.exceptions.AMQPConnectionError as e:
        logging.error(f"Failed to connect to RabbitMQ: {e}")
        raise e

def send_task_to_queue(message):
    """
    Отправляет сообщение в очередь RabbitMQ.
    """
    try:
        channel = get_rabbitmq_channel()
        channel.basic_publish(exchange='', routing_key=rabbitmq_queue, body=message)
        logging.info(f"Message sent to queue '{rabbitmq_queue}': {message}")
    except Exception as e:
        logging.error(f"Failed to send message to RabbitMQ: {e}")
        raise e
