# netra-refund-agent

A refund agent application with FastAPI backend and Next.js frontend.

## Prerequisites

- Docker and Docker Compose
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Node.js and npm

## Setup Instructions

### 1. Start Docker Services

First, start the required services using Docker Compose:

```bash
docker compose up
```

This will start the necessary database and other services defined in your docker-compose.yml.

### 2. Backend Setup

Navigate to the backend directory and run the database migrations:

```bash
cd backend
uv run push.py
```

Then start the FastAPI development server:

```bash
uv run fastapi dev
```

The backend API will be available at the default FastAPI port.

### 3. Frontend Setup

In a new terminal, navigate to the frontend directory:

```bash
cd frontend
```

Install the dependencies:

```bash
npm i
```

Start the Next.js development server:

```bash
npm run dev
```

The frontend will be available at the default Next.js port (typically http://localhost:3000).

## Project Structure

- `backend/` - FastAPI backend application
  - `agent.py` - Agent logic
  - `main.py` - FastAPI application entry point
  - `push.py` - Database migration script
  - `models/` - Database models
  - `migrations/` - SQL migration files
  - `policy/` - Policy documents

- `frontend/` - Next.js frontend application
  - `app/` - Next.js app directory
  - `components/` - React components
  - `lib/` - Utility functions
