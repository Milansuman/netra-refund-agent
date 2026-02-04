#!/bin/bash
docker-compose up postgres -d
cd backend && uv run evaluate.py