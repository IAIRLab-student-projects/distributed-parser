#!/bin/bash
# wait_and_start.sh

# Задержка в 11 секунд
sleep 15

# Запуск основного процесса (worker.py)
exec "$@"