# netra-refund-agent

A fully containerized refund agent application with FastAPI backend and Next.js frontend.

## Prerequisites

- Docker and Docker Compose

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the root directory from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
NETRA_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
LITELLM_API_KEY=your_key_here
```

### 2. Start All Services

Build and start all services (PostgreSQL, backend, and frontend) with Docker Compose:

```bash
docker compose up --build
```

This will:
- Start PostgreSQL database on port 5432
- Build and start the FastAPI backend on port 8000
- Build and start the Next.js frontend on port 3000

All services run in production mode and are connected on the same Docker network.

### 3. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

To stop all services, press `Ctrl+C` or run:

```bash
docker compose down
```

## Development Setup

For local development without Docker:

### Backend
```bash
cd backend
# Install dependencies
uv sync
# Run migrations
uv run push.py
# Start development server
uv run fastapi dev
```

### Frontend
```bash
cd frontend
# Install dependencies
npm install
# Start development server
npm run dev
```

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
