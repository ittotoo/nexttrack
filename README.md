# NextTrack: Privacy-Preserving Music Recommendation API

A stateless music recommendation system that generates personalised recommendations without tracking users. Built as a final project for the University of London BSc Computer Science (Template 7.2).

## How It Works

Users provide 1-5 seed tracks and optional preferences. The system returns ranked recommendations using a hybrid 40/30/30 weighted ensemble:

- **Content-Based Filtering (40%)** — Cosine similarity across 8 audio features
- **Knowledge Graph (30%)** — BFS traversal of artist collaboration networks + genre taxonomy
- **Popularity Scoring (30%)** — Seed-aligned popularity matching

All computation is discarded after each response. No user accounts, no session state, no tracking.

## Tech Stack

- **Backend:** Python, FastAPI, PostgreSQL
- **Frontend:** React 18, TypeScript, Tailwind CSS, Vite
- **Data:** 89,740 tracks from Kaggle Spotify dataset
- **Testing:** 64 unit tests (pytest), 88-100% coverage

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/nexttrack.git
cd nexttrack
```

### 2. Database setup

Create a PostgreSQL database and load the schema:

```bash
psql -U postgres -c "CREATE DATABASE nexttrack;"
psql -U postgres -d nexttrack -f backend/db/schema.sql
```

Load the dataset:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 db/load_data.py
```

Run the knowledge graph migration:

```bash
psql -U postgres -d nexttrack -f db/migration_001_knowledge_graph.sql
python3 db/populate_knowledge_graph.py
```

### 3. Backend configuration

Copy the environment template and fill in your database credentials:

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 4. Start the backend

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --port 8000
```

The API is now running at http://localhost:8000. Interactive docs at http://localhost:8000/docs.

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/recommend` | POST | Generate recommendations from 1-5 seed tracks |
| `/search` | GET | Search tracks by name or artist |
| `/track/{id}` | GET | Get track details |
| `/random` | GET | Random tracks (evaluation baseline) |
| `/health` | GET | Health check |

### Example request

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "seed_track_ids": ["4u7EnebtmKWzUH433cf5Qv"],
    "limit": 5,
    "diversity_weight": 0.3
  }'
```

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

## Project Structure

```
nexttrack/
├── backend/          # FastAPI application
│   ├── app/          # Application code
│   │   ├── models/   # Pydantic data models
│   │   ├── recommender/  # Hybrid recommendation engine
│   │   └── external/ # External API clients
│   ├── tests/        # 64 unit tests
│   └── db/           # Database schema and migrations
├── frontend/         # React/TypeScript application
│   └── src/
│       ├── components/   # 9 React components
│       ├── hooks/        # Custom hooks (search, recommendations)
│       ├── services/     # API client
│       └── types/        # TypeScript interfaces
├── Data/             # Kaggle dataset (cleaned)
└── notebooks/        # Data exploration notebooks
```

## Licence

This project was developed for academic purposes as part of the University of London BSc Computer Science Final Project.
