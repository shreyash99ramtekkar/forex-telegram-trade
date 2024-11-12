#!/bin/bash

cd /home/itachi/forex/MetaTrader5-Docker-Image; 
docker compose up &> /dev/null &
while [ $(ps aux | grep "docker compose" | grep -v grep | wc -l) -ne 1 ]; do
    echo "Waiting for service to come up" 
    sleep 10  # Wait for 1 second before checking again
done
echo "Sleeping 60 seconds"
sleep 60
cd /home/itachi/forex/forex-telegram-trade;
pwd
echo "Running the code"
.venv/bin/python main.py
