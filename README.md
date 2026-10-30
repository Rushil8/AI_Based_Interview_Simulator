# AI Interview Coach — Adaptive Interview Preparation & Evaluation System

An enterprise-grade, full-stack adaptive interview preparation and evaluation platform. The system leverages candidate PDF resumes and target role requirements to formulate personalized interview plans, conduct real-time adaptive questioning, evaluate candidate typed answers using a standardized 4-dimension scoring rubric, and synthesize actionable performance reports with Sentence-BERT semantic relevance diagnostics.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Candidate PDF Resume      |
                      |   + Target Job Role & JD    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Resume Parser (PyMuPDF)   |
                      |   + Profile Extractor (NLP) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Candidate Structured Profile|
                      |  (Skills, Projects, Exp)    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Competency Mapper (S-BERT)  |
                      |  Cosine Similarity Matching |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Interview Planner Service  |
                      |   Question Budget & Types   |
                      +--------------+--------------+
                                     |
                                     v
                +--------------------+--------------------+
                |                                         |
                v                                         v
   +--------------------------+             +--------------------------+
   | Question Generator       |<------------| Adaptive Controller      |
   | (Gemini Flash / Engine)  |             | Difficulty & Gaps Engine |
   +------------+-------------+             +-------------+------------+
                |                                         ^
                v                                         |
   +--------------------------+                           |
   | Candidate Typed Answer   |                           |
   | (Secure DB Persistence)  |                           |
   +------------+-------------+                           |
                |                                         |
                v                                         |
   +--------------------------+                           |
   | Answer Evaluator (Rubric)|                           |
   | Relevance (20%)          |                           |
   | Technical Correctness(40%)                           |
   | Completeness (25%)       |                           |
   | Communication (15%)      |                           |
   +------------+-------------+                           |
                |                                         |
                v                                         |
   +--------------------------+                           |
   | Sentence-BERT Similarity |---------------------------+
   | Diagnostic Check (No kw) |
   +------------+-------------+
                |
                v
   +--------------------------+
   | Final Report & Analytics |
   | Charts, Reviews & Plan   |
   +--------------------------+
```

---

## Key Features

1. **Deterministic PDF Text Extraction (`PyMuPDF`)**: Robust, high-speed PDF text parsing with sanitization, boundary checks, and support for multi-page resumes.
2. **Structured Profile Extraction**: Isolates programming languages, frameworks, developer tools, projects, and work experience, preserving evidence snippets without hallucinating missing data.
3. **Sentence-BERT Competency Mapping**: Normalized L2 embeddings and cosine similarity map candidate skills to role requirements, categorizing each competency into `covered`, `partially_covered`, or `uncovered`.
4. **Standardized 4-Dimension Rubric**:
   $$\text{Score} = (\text{Relevance} \times 0.20) + (\text{Technical} \times 0.40) + (\text{Completeness} \times 0.25) + (\text{Communication} \times 0.15)$$
5. **Anti-Keyword Stuffing Diagnostics**: Sentence-BERT semantic similarity provides an independent diagnostic metric to detect evasive or buzzword-stuffed responses without penalizing alternative valid solutions.
6. **Rule-Based Adaptive Controller**:
   - **Escalation**: $\ge 80\%$ score advances question difficulty (e.g., Mid $\to$ Senior).
   - **Remediation**: Low technical scores ($< 55\%$) trigger targeted foundational questions.
   - **Gap Coverage**: Prioritizes uncovered competencies to ensure balanced coverage before budget exhaustion.
7. **Crash-Resilient State Management**: Candidate answers are persisted to the database prior to evaluation; browser refreshes restore the active session.
8. **Voice-Driven Interview Mode (TTS & STT)**:
   - **Listen to Questions (TTS)**: Built-in Text-to-Speech reads interview questions aloud with real-time soundwave indicators and an optional "Auto-read questions" toggle to simulate a live interviewer.
   - **Answer by Voice (STT)**: Microphone speech recognition transcribes candidate answers into the answer box in real time, allowing voice dictation with manual text polishing.
   - **Spoken Evaluation Feedback**: Provides audio playback for answer evaluations and constructive feedback.
9. **Actionable Career Analytics**: Recharts visual charts, dimension comparisons, question-by-question breakdowns, and tailored practice exercises.
10. **Trained ML Models for Adaptive Question Selection & Generation (`backend/ml/`)**:
    - **Cross-Encoder Question Selector & Ranker**: Evaluates candidate state against question candidates (100% Top-1 Selection Acc, 1.0 MRR, 1.0 NDCG@3).
    - **PyTorch Seq2Seq Question Generator with Bahdanau Attention**: Bidirectional GRU encoder-decoder network generating adaptive questions token-by-token directly from candidate state tokens.

---

## Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons, Recharts, React Router v7, Web Speech API (TTS & STT).
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0, PyMuPDF (`fitz`), scikit-learn, PyTorch, Google GenAI SDK.
- **Database**: PostgreSQL (Production) / SQLite (Zero-config immediate local development).
- **Testing**: Pytest, Pytest-Asyncio, HTTPX TestClient (18 passing unit/integration tests).

---

## Directory Structure

```
AI_Interview/
├── backend/
│   ├── app/
│   │   ├── api/v1/             # Modular REST API endpoints
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic v2 validation schemas
│   │   ├── services/           # Core domain services
│   │   │   ├── resume_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── competency_service.py
│   │   │   ├── interview_planner_service.py
│   │   │   ├── question_generation_service.py
│   │   │   ├── answer_evaluation_service.py
│   │   │   ├── semantic_similarity_service.py
│   │   │   ├── scoring_service.py
│   │   │   ├── adaptive_controller_service.py
│   │   │   ├── feedback_service.py
│   │   │   └── report_service.py
│   │   ├── prompts/            # Versioned prompt templates
│   │   ├── config.py           # Application settings with weight validation
│   │   ├── database.py         # DB connection & sessionmaker
│   │   └── main.py             # FastAPI entrypoint
│   ├── sample_data/            # Sample PDF generator and resume
│   ├── tests/                  # Pytest test suite
│   ├── requirements.txt        # Backend dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/         # Navbar, Footer, UI elements
│   │   ├── pages/              # Landing, Setup, Review, Dashboard, Report, History, Settings
│   │   ├── services/           # Typed API client
│   │   ├── types/              # TypeScript interfaces
│   │   ├── App.tsx             # Route definitions
│   │   ├── main.tsx
│   │   └── index.css           # Tailwind v4 styles & design tokens
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml          # Multi-container orchestration
├── .env.example                # Environment variables template
└── README.md                   # Project documentation
```

---

## Getting Started Locally

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend automated test suite
pytest -v

# Start FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API is now live at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend

# Install npm dependencies
npm install --legacy-peer-deps

# Start Vite development server
npm run dev
```
Open `http://localhost:5173/` in your browser.

---

## Running with Docker Compose

To deploy the complete application (PostgreSQL, FastAPI backend, and Nginx frontend) via Docker Compose:

```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/resumes/upload` | Upload PDF resume, extract text, and parse profile |
| `GET` | `/api/profiles/{id}` | Retrieve candidate structured profile |
| `PATCH` | `/api/profiles/{id}` | Update candidate profile skills or information |
| `POST` | `/api/interviews` | Create interview session & competency mapping |
| `GET` | `/api/interviews/{id}` | Retrieve interview session state and public questions |
| `GET` | `/api/interviews/{id}/current-question` | Get active question (rubric hidden for integrity) |
| `POST` | `/api/interviews/{id}/answers` | Submit typed answer & receive 4-dimension evaluation |
| `POST` | `/api/interviews/{id}/next-question` | Adaptive controller: escalates or remediates question |
| `GET` | `/api/interviews/{id}/progress` | Session progress, answered count, and provisional score |
| `POST` | `/api/interviews/{id}/complete` | Finalize session and compile report |
| `GET` | `/api/interviews/{id}/report` | Retrieve persisted final report and charts |
| `GET` | `/api/users/me/interviews` | List previous interview history |
| `GET` | `/api/config` | System settings, model identifier, and rubric weights |

---

## Ethical AI & Hiring Disclaimer

> **Transparent AI Practice Disclaimer**: AI Interview Coach is an automated educational tool designed to simulate technical and behavioral interviews, probe domain competencies, and provide diagnostic feedback. Scores reflect simulated rubric performance and do not guarantee or predict actual employment or hiring decisions by any prospective employer.
