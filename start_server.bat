@echo off
cd src
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 