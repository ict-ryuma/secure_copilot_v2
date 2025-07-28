#!/bin/bash
# Copy .env.example to .env if .env does not exist
if [ ! -f /app/.env ]; then
  echo "No .env file found. Copying .env.example to .env..."
  cp /app/.env.example /app/.env
fi
uvicorn backend.chat_secure_gpt:app --host 0.0.0.0 --port 8000 --reload &

streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 --reload

