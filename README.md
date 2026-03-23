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

## Quick Start

### Step 1: Clone and set up the backend

```bash
git clone https://github.com/ittotoo/nexttrack.git
cd nexttrack/backend

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials (DB_NAME, DB_USER, DB_PASSWORD)
```

### Step 2: Set up the database

Make sure PostgreSQL is running, then:

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE nexttrack;"

# Load the schema
psql -U postgres -d nexttrack -f db/schema.sql

# Load the dataset (89,740 tracks)
python3 db/load_data.py

# Build the knowledge graph
psql -U postgres -d nexttrack -f db/migration_001_knowledge_graph.sql
python3 db/populate_knowledge_graph.py
```

### Step 3: Start the backend

```bash
source venv/bin/activate
python -m uvicorn app.main:app --port 8000
```

Verify it works: open http://localhost:8000/docs to see the interactive API docs.

### Step 4: Start the frontend

Open a **new terminal**:

```bash
cd nexttrack/frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser. You should see the NextTrack interface.

### Step 5: Try it out

1. Search for a song you like (e.g. "Bohemian Rhapsody")
2. Click to add it as a seed track
3. Click **Get Recommendations**
4. Browse results — each one shows a score breakdown and explanation
5. Click play to preview via Spotify

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/recommend` | POST | Generate recommendations from 1-5 seed tracks |
| `/search?q=` | GET | Search tracks by name or artist |
| `/track/{id}` | GET | Get track details |
| `/random` | GET | Random tracks (evaluation baseline) |
| `/health` | GET | Health check |

### Example

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

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Database connection error` | Check your `.env` credentials and that PostgreSQL is running |
| `No tracks found` | Make sure you ran `python3 db/load_data.py` to load the dataset |
| `Frontend shows connection error` | Make sure the backend is running on port 8000 |
| `Spotify client error` | Ignore — the system works without Spotify credentials |

## Project Structure

```
nexttrack/
├── backend/
│   ├── app/
│   │   ├── main.py              # API endpoints
│   │   ├── database.py          # PostgreSQL queries
│   │   ├── models/              # Data models (Track, AudioFeatures)
│   │   └── recommender/         # Hybrid engine, similarity, KG, popularity
│   ├── tests/                   # 64 unit tests
│   └── db/                      # Schema, migrations, data loader
├── frontend/
│   └── src/
│       ├── components/          # 9 React components
│       ├── hooks/               # Search + recommendation hooks
│       └── services/            # API client
├── Data/                        # Cleaned Kaggle dataset
└── notebooks/                   # Data exploration
```

## Licence

This project was developed for academic purposes as part of the University of London BSc Computer Science Final Project.
