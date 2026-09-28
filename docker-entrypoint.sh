#!/bin/bash
set -e

cd /app

python api_server.py &
PID_API=$!

cd /app/comic-encryption-app-design
npm run start -- --hostname 0.0.0.0 --port 3000 &
PID_NEXT=$!

trap 'kill $PID_API $PID_NEXT' EXIT

wait $PID_API $PID_NEXT
