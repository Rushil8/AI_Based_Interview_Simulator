"""
Adaptive Interview Question Selection & Generation Dataset Generator
Creates annotated training, validation, and test datasets for training NLP models:
1. Question Ranking & Selection Model (State + Candidate Question -> Match Score)
2. Question Generation Model (State -> Question Text + Rubric)
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any

def load_hf_dataset_questions() -> List[Dict[str, Any]]:
    """Loads questions from the Hugging Face Ankshi/interview dataset."""
    base_dir = Path(__file__).resolve().parent.parent
    ds_path = base_dir / "app" / "data" / "dataset_questions.json"
    if ds_path.exists():
        with open(ds_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

HF_DATASET_QUESTIONS = load_hf_dataset_questions()

ROLES_COMPETENCIES = {
    "Full Stack Engineer": [
        {
            "competency": "Frontend State Management & React Internals",
            "junior_questions": [
                "Explain the difference between props and state in React with an example.",
                "How does the useState hook work and when would you use useEffect?",
                "What is the Virtual DOM and why is it faster than direct DOM manipulation?"
            ],
            "mid_questions": [
                "How do React 18 concurrent features like startTransition and useDeferredValue improve UI responsiveness?",
                "Compare Redux Toolkit, Zustand, and React Context API for complex application state.",
                "Explain how React reconciliation and the diffing algorithm handle keys in dynamic lists."
            ],
            "senior_questions": [
                "How would you architect a micro-frontend architecture with module federation and cross-app state synchronization?",
                "Explain React Fiber architecture, render vs commit phases, and how you prevent frame drops in 60fps UIs.",
                "Design a client-side offline-first sync engine with IndexedDB, conflict resolution, and optimistic UI updates."
            ],
            "remediation_questions": [
                "Let's review the basics: what triggers a component re-render in React and how do you prevent unnecessary renders?",
                "Can you walk through what happens when an event handler calls setState multiple times?",
                "What are pure components in React and how does useMemo help optimize performance?"
            ]
        },
        {
            "competency": "RESTful & Real-Time API Architecture",
            "junior_questions": [
                "What are the primary HTTP methods and how do idempotency rules apply to GET vs POST vs PUT?",
                "Explain the purpose of HTTP status codes: 200, 201, 400, 401, 403, and 500.",
                "What is CORS and why does the browser enforce it?"
            ],
            "mid_questions": [
                "How do you design a robust idempotency-key mechanism for financial payment API endpoints?",
                "Compare WebSockets, Server-Sent Events (SSE), and Long Polling for real-time notifications.",
                "How would you implement rate limiting with Redis sliding-window counter in an API gateway?"
            ],
            "senior_questions": [
                "Architect a zero-downtime blue-green API deployment pipeline handling breaking database schema migrations.",
                "Design an event-driven microservices architecture using Apache Kafka with outbox pattern for distributed consistency.",
                "How do you handle distributed tracing, latency budgets, and cascading failures in a high-throughput API mesh?"
            ],
            "remediation_questions": [
                "Let's take a step back: what makes an API truly RESTful and what is statelessness?",
                "How do query parameters differ from path parameters and request body in REST design?",
                "What headers are involved in content negotiation and pre-flight CORS requests?"
            ]
        },
        {
            "competency": "Database Optimization & SQL Internals",
            "junior_questions": [
                "What is the difference between an INNER JOIN, LEFT JOIN, and FULL OUTER JOIN?",
                "What is database normalization and what are 1NF, 2NF, and 3NF?",
                "What is a primary key versus a unique foreign key constraint?"
            ],
            "mid_questions": [
                "Explain how B-Tree indexes work internally in PostgreSQL and why index selectivity matters.",
                "How do connection pooling engines like PgBouncer prevent thread exhaustion under high concurrency?",
                "What are ACID transactions and how do database isolation levels (Read Committed vs Serializable) prevent anomalies?"
            ],
            "senior_questions": [
                "Design a horizontally partitioned (sharded) relational database architecture handling millions of queries per second.",
                "How do you resolve distributed deadlocks in two-phase commit (2PC) versus Saga orchestration?",
                "Explain Write-Ahead Logging (WAL), MVCC vacuuming, and lock contention optimization under high write throughput."
            ],
            "remediation_questions": [
                "Let's review foundational concepts: why can unindexed WHERE clauses cause full table scans?",
                "What is an index scan versus an index-only scan in SQL query execution plans?",
                "Why should you avoid SELECT * in production database queries?"
            ]
        },
        {
            "competency": "Application Security & Authentication",
            "junior_questions": [
                "What is the difference between authentication and authorization?",
                "Why should passwords never be stored in plain text and what is password salting?",
                "What is SQL injection and how do parameterized queries prevent it?"
            ],
            "mid_questions": [
                "How do you architect a secure JWT authentication flow with short-lived access tokens and HttpOnly refresh tokens?",
                "Explain Cross-Site Scripting (XSS) versus Cross-Site Request Forgery (CSRF) and how to mitigate both.",
                "How do Content Security Policy (CSP) headers protect modern Single Page Applications?"
            ],
            "senior_questions": [
                "Design an enterprise Role-Based and Attribute-Based Access Control (RBAC/ABAC) engine with distributed token revocation.",
                "How would you detect and mitigate automated credential stuffing and distributed DDoS attacks at layer 7?",
                "Explain zero-trust architecture principles and how mTLS ensures secure service-to-service communication."
            ],
            "remediation_questions": [
                "Let's clarify the fundamentals: where should sensitive API tokens be stored in a web browser?",
                "What is the role of HTTPS / TLS and what attacks occur if traffic is unencrypted?",
                "How does the Same-Origin Policy (SOP) protect web applications?"
            ]
        }
    ],
    "Backend Engineer": [
        {
            "competency": "Distributed Systems & Scalability",
            "junior_questions": [
                "What is vertical scaling versus horizontal scaling?",
                "What is the purpose of a load balancer in web architecture?",
                "What is a cache and why is Redis used alongside databases?"
            ],
            "mid_questions": [
                "Explain the CAP theorem and the trade-offs between consistency and availability during network partitions.",
                "How does consistent hashing work and how does it prevent hot spots in distributed cache clusters?",
                "How do you design an asynchronous background worker pool with Celery / Redis and handle worker crash retries?"
            ],
            "senior_questions": [
                "Design a distributed consensus mechanism comparing Raft and Paxos for replicated state machines.",
                "How do you design a globally distributed leaderboard handling 100k updates/second with event-driven streaming?",
                "Architect a multi-region active-active database failover system with conflict-free replicated data types (CRDTs)."
            ],
            "remediation_questions": [
                "Let's review the basics: what is latency versus throughput in backend systems?",
                "What happens when a cache expires (cache stampede / thundering herd) and how do you prevent it?",
                "Why are idempotent API retries critical when network timeouts occur?"
            ]
        },
        {
            "competency": "Concurrency, Async IO & Multi-Threading",
            "junior_questions": [
                "What is the difference between a process and a thread?",
                "What does synchronous execution mean compared to asynchronous execution?",
                "What is a deadlock in concurrent programming?"
            ],
            "mid_questions": [
                "How does the Python asyncio event loop work internally and how does cooperative multitasking differ from OS threads?",
                "What is the Global Interpreter Lock (GIL) in CPython and how do you achieve true CPU parallelism?",
                "Explain race conditions, mutex locks, and semaphores when sharing state across threads."
            ],
            "senior_questions": [
                "How do you build a lock-free ring buffer for ultra-low latency inter-process communication?",
                "Explain actor-model concurrency versus communicating sequential processes (CSP) in distributed engines.",
                "How do you profile and debug memory leaks, coroutine starvation, and thread contention in high-scale async services?"
            ],
            "remediation_questions": [
                "Let's step back: why does blocking code inside an async coroutine freeze the entire event loop?",
                "What is the difference between I/O bound tasks and CPU bound tasks?",
                "How do thread pools prevent the overhead of spawning new threads for every request?"
            ]
        }
    ]
}

SKILL_SETS = [
    ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
    ["JavaScript", "TypeScript", "React", "Node.js", "MongoDB"],
    ["Go", "Kubernetes", "gRPC", "PostgreSQL", "AWS"],
    ["Java", "Spring Boot", "Kafka", "MySQL", "Microservices"],
    ["Python", "Django", "Celery", "Redis", "SQLite"]
]

WEAKNESS_SNIPPETS = [
    "Struggled with SQL indexing and query execution plan details",
    "Confused JWT refresh token rotation with session cookies",
    "Missed concurrency race conditions and thread safety principles",
    "Could not explain the difference between WebSockets and polling",
    "Did not mention connection pooling or database lock contention",
    "Incomplete explanation of React reconciliation and keys",
    "Confused horizontal scaling with vertical hardware upgrades",
    "Overlooked distributed transaction rollback with Saga pattern"
]


def generate_dataset(num_samples: int = 1200, random_seed: int = 42) -> List[Dict[str, Any]]:
    random.seed(random_seed)
    samples = []

    for idx in range(num_samples):
        role = random.choice(list(ROLES_COMPETENCIES.keys()))
        competency_obj = random.choice(ROLES_COMPETENCIES[role])
        competency_name = competency_obj["competency"]

        # Simulate previous score to test adaptive escalation / remediation
        # Low scores (<55) -> remediation
        # High scores (>=80) -> senior / escalate
        # Mid scores (55-79) -> mid
        prev_score = random.randint(30, 95)
        skills = random.choice(SKILL_SETS)
        weakness = random.choice(WEAKNESS_SNIPPETS) if prev_score < 75 else "None identified - solid fundamental answer"

        # If HF dataset is available, integrate behavioral/leadership questions directly from Ankshi/interview dataset
        use_hf_sample = HF_DATASET_QUESTIONS and (idx % 3 == 0)
        if use_hf_sample:
            # Pick a question from HF dataset
            hf_item = random.choice(HF_DATASET_QUESTIONS)
            optimal_question = hf_item["question"]
            competency_name = f"{hf_item.get('category', 'Professional Skills')} ({hf_item.get('source_type', 'STAR')})"
            target_difficulty = "junior" if hf_item.get("difficulty", "").lower() == "easy" else ("senior" if hf_item.get("difficulty", "").lower() == "hard" else "mid")
            reason = f"Dataset benchmark: Evaluates {hf_item.get('category', 'competency')} sourced from HF Ankshi/interview dataset."
            # Distractors from other HF categories
            other_hf = [q for q in HF_DATASET_QUESTIONS if q.get("category") != hf_item.get("category")]
            distractor_wrong_topic = random.choice(other_hf)["question"] if other_hf else "Describe an unrelated project challenge."
            distractor_wrong_diff = random.choice([q["question"] for q in HF_DATASET_QUESTIONS if q.get("difficulty") != hf_item.get("difficulty")] or [optimal_question])
        elif prev_score < 55:
            target_difficulty = "junior"
            optimal_question = random.choice(competency_obj["remediation_questions"])
            reason = "Remediation: Low previous score requires reinforcing core foundational concepts."
            wrong_competency = random.choice([c for c in ROLES_COMPETENCIES[role] if c["competency"] != competency_name])
            distractor_wrong_topic = random.choice(wrong_competency["mid_questions"])
            distractor_wrong_diff = random.choice(competency_obj["senior_questions"])
        elif prev_score >= 80:
            target_difficulty = "senior"
            optimal_question = random.choice(competency_obj["senior_questions"])
            reason = "Escalation: High previous performance triggers advanced system design question."
            wrong_competency = random.choice([c for c in ROLES_COMPETENCIES[role] if c["competency"] != competency_name])
            distractor_wrong_topic = random.choice(wrong_competency["mid_questions"])
            distractor_wrong_diff = random.choice(competency_obj["junior_questions"])
        else:
            target_difficulty = "mid"
            optimal_question = random.choice(competency_obj["mid_questions"])
            reason = "Standard progression: Balanced mid-level question assessing practical engineering trade-offs."
            wrong_competency = random.choice([c for c in ROLES_COMPETENCIES[role] if c["competency"] != competency_name])
            distractor_wrong_topic = random.choice(wrong_competency["mid_questions"])
            distractor_wrong_diff = random.choice(competency_obj["junior_questions"])

        sample = {
            "id": f"q_sample_{idx:05d}",
            "role": role,
            "target_competency": competency_name,
            "candidate_skills": ", ".join(skills),
            "previous_score": prev_score,
            "previous_weakness": weakness,
            "target_difficulty": target_difficulty,
            "optimal_question": optimal_question,
            "pedagogical_reason": reason,
            # Ranking candidates with binary label (1 = optimal, 0 = non-optimal)
            "ranking_candidates": [
                {"question": optimal_question, "label": 1.0, "type": "optimal"},
                {"question": distractor_wrong_topic, "label": 0.0, "type": "wrong_topic"},
                {"question": distractor_wrong_diff, "label": 0.0, "type": "wrong_difficulty"}
            ]
        }
        samples.append(sample)

    return samples


def save_splits(output_dir: Path, num_samples: int = 1200):
    output_dir.mkdir(parents=True, exist_ok=True)
    all_data = generate_dataset(num_samples=num_samples)

    random.shuffle(all_data)
    n_train = int(len(all_data) * 0.8)
    n_val = int(len(all_data) * 0.1)

    train_data = all_data[:n_train]
    val_data = all_data[n_train:n_train + n_val]
    test_data = all_data[n_train + n_val:]

    with open(output_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2)

    with open(output_dir / "val.json", "w", encoding="utf-8") as f:
        json.dump(val_data, f, indent=2)

    with open(output_dir / "test.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2)

    print(f"Dataset generated successfully at: {output_dir}")
    print(f"  - Train: {len(train_data)} samples")
    print(f"  - Val:   {len(val_data)} samples")
    print(f"  - Test:  {len(test_data)} samples")


if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    data_dir = current_dir / "data"
    save_splits(data_dir, num_samples=1200)
