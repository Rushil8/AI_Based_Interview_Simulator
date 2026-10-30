import math
import re
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import settings
from app.schemas.profile import StructuredProfile

# Try importing sentence_transformers, with graceful fallback to normalized TF-IDF vectorizer
try:
    from sentence_transformers import SentenceTransformer
    _SBERT_AVAILABLE = True
except ImportError:
    _SBERT_AVAILABLE = False


# Standard competency templates for roles
ROLE_COMPETENCY_CATALOG = {
    "software engineer": [
        {"name": "Data Structures & Algorithms", "category": "problem_solving", "weight": 1.0, "desc": "Understanding of algorithm complexity, arrays, trees, graphs, and dynamic programming."},
        {"name": "System Architecture & API Design", "category": "technical", "weight": 0.9, "desc": "Designing modular services, RESTful APIs, microservices, and database models."},
        {"name": "Database Management & Query Optimization", "category": "technical", "weight": 0.85, "desc": "Relational databases, indexing, transactions, NoSQL data stores, and query performance."},
        {"name": "Testing, Debugging & Code Quality", "category": "practical_application", "weight": 0.8, "desc": "Writing unit tests, integration testing, CI/CD pipelines, and root-cause debugging."},
        {"name": "Technical Communication & Collaboration", "category": "communication", "weight": 0.75, "desc": "Explaining trade-offs, documentation, code review etiquette, and cross-functional teamwork."},
    ],
    "full stack": [
        {"name": "Frontend Architecture & Modern Frameworks", "category": "technical", "weight": 1.0, "desc": "React, TypeScript, component lifecycles, state management, and modern CSS."},
        {"name": "Backend API Development", "category": "technical", "weight": 1.0, "desc": "FastAPI, Node.js, Express, REST APIs, asynchronous programming, and request validation."},
        {"name": "Database Design & ORM Integration", "category": "technical", "weight": 0.85, "desc": "PostgreSQL, SQLAlchemy, relational schema design, migrations, and query tuning."},
        {"name": "End-to-End Application Security & Auth", "category": "practical_application", "weight": 0.8, "desc": "JWT, OAuth2, session handling, CORS, input sanitization, and vulnerability prevention."},
        {"name": "Problem Solving & Deployment", "category": "problem_solving", "weight": 0.8, "desc": "Docker containerization, cloud deployment, monitoring, and resolving edge-case bugs."},
    ],
    "frontend": [
        {"name": "Core JavaScript & TypeScript Proficiency", "category": "technical", "weight": 1.0, "desc": "Deep knowledge of ES6+, TypeScript types, closures, event loop, and DOM APIs."},
        {"name": "UI Component Design & Responsive Layouts", "category": "practical_application", "weight": 0.95, "desc": "Tailwind CSS, responsive design, accessibility (WCAG), and modern UI patterns."},
        {"name": "Client-Side State Management & APIs", "category": "technical", "weight": 0.9, "desc": "State containers, caching, optimistic updates, and REST/GraphQL data fetching."},
        {"name": "Frontend Performance Optimization", "category": "problem_solving", "weight": 0.85, "desc": "Code splitting, lazy loading, Core Web Vitals, asset bundling, and rendering performance."},
        {"name": "UX Collaboration & Design Systems", "category": "communication", "weight": 0.75, "desc": "Translating Figma specs, reusable component libraries, and interactive animations."},
    ],
    "backend": [
        {"name": "Server-Side Architecture & Frameworks", "category": "technical", "weight": 1.0, "desc": "Python FastAPI, Django, Node.js, asynchronous I/O, and concurrent processing."},
        {"name": "Database Modeling, Indexing & Transactions", "category": "technical", "weight": 0.95, "desc": "ACID compliance, PostgreSQL, indexing strategies, query optimization, and sharding."},
        {"name": "Distributed Systems & Scalability", "category": "system_design", "weight": 0.9, "desc": "Caching with Redis, message brokers (Kafka/RabbitMQ), load balancing, and rate limiting."},
        {"name": "Security, Authentication & Authorization", "category": "practical_application", "weight": 0.85, "desc": "RBAC, JWT tokens, encryption, TLS, OWASP standards, and safe secret handling."},
        {"name": "API Testing, Profiling & Reliability", "category": "problem_solving", "weight": 0.8, "desc": "Unit/integration testing, mocking, profiling memory leaks, and logging/observability."},
    ],
    "data science": [
        {"name": "Machine Learning Fundamentals", "category": "technical", "weight": 1.0, "desc": "Supervised/unsupervised learning, scikit-learn, loss functions, and evaluation metrics."},
        {"name": "Data Processing & Feature Engineering", "category": "practical_application", "weight": 0.95, "desc": "Pandas, NumPy, data cleaning, outlier handling, and pipeline transformations."},
        {"name": "Deep Learning & NLP", "category": "technical", "weight": 0.9, "desc": "Neural networks, PyTorch, transformers, embeddings, and generative AI models."},
        {"name": "Statistical Modeling & Experimentation", "category": "problem_solving", "weight": 0.85, "desc": "Hypothesis testing, A/B testing, regression analysis, and probabilistic reasoning."},
        {"name": "Model Deployment & Evaluation", "category": "practical_application", "weight": 0.8, "desc": "Serving models via FastAPI, Docker, drift monitoring, and batch vs real-time inference."},
    ],
}


class CompetencyService:
    def __init__(self):
        self.sbert_model = None
        if _SBERT_AVAILABLE:
            try:
                self.sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self.sbert_model = None

    def compute_embedding(self, text: str) -> np.ndarray:
        """
        Computes normalized L2 embedding for a given text.
        """
        if self.sbert_model is not None:
            emb = self.sbert_model.encode([text])[0]
            norm = np.linalg.norm(emb)
            return emb / (norm + 1e-9)
        else:
            # Fallback to zero vector placeholder if TF-IDF pairwise is used
            return np.zeros(64)

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """
        Computes cosine similarity between two texts.
        Uses Sentence-BERT if loaded; otherwise uses L2-normalized char-wb n-gram TF-IDF.
        """
        if not text_a.strip() or not text_b.strip():
            return 0.0

        if self.sbert_model is not None:
            emb_a = self.sbert_model.encode([text_a])[0]
            emb_b = self.sbert_model.encode([text_b])[0]
            # Normalize embeddings before calculating cosine similarity
            norm_a = np.linalg.norm(emb_a)
            norm_b = np.linalg.norm(emb_b)
            if norm_a > 0 and norm_b > 0:
                sim = float(np.dot(emb_a / norm_a, emb_b / norm_b))
                return max(0.0, min(1.0, sim))

        # High-precision normalized sublinear TF-IDF fallback with character n-grams for morphological root matching
        try:
            vectorizer = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 4),
                sublinear_tf=True,
                norm="l2"
            )
            tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
            sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
            return max(0.0, min(1.0, round(sim, 4)))
        except Exception:
            return 0.0

    def generate_and_map_competencies(
        self,
        job_role: str,
        job_description: Optional[str],
        profile: StructuredProfile
    ) -> List[Dict[str, Any]]:
        """
        Maps candidate profile against target role competencies.
        Calculates:
        - Relevance to target role
        - Evidence found in resume
        - Coverage status: covered, partially_covered, uncovered
        - Initial evidence strength (0.0 to 1.0)
        - Importance weight
        """
        base_competencies = self._select_competency_templates(job_role, job_description)

        # Build candidate evidence corpus
        skills_corpus = " ".join(profile.technical_skills + profile.programming_languages + profile.frameworks_libraries + profile.tools_platforms)
        projects_corpus = " ".join(f"{p.title}: {p.description} {' '.join(p.technologies)}" for p in profile.projects)
        exp_corpus = " ".join(f"{e.role} at {e.company}: {' '.join(e.responsibilities)}" for e in profile.work_experience)
        candidate_full_corpus = f"{skills_corpus} {projects_corpus} {exp_corpus} {profile.summary or ''}"

        mapped_results = []
        similarity_threshold = settings.SEMANTIC_SIMILARITY_FLAG_THRESHOLD

        for comp in base_competencies:
            comp_name = comp["name"]
            comp_desc = comp["desc"]
            comp_category = comp.get("category", "technical")
            importance_weight = float(comp.get("weight", 1.0))

            # Find specific evidence snippets in candidate profile
            evidence_snippet = self._find_evidence_snippet(comp_name, comp_desc, profile)

            # Compute semantic similarity between competency requirement and candidate experience
            semantic_score = self.compute_similarity(f"{comp_name}: {comp_desc}", candidate_full_corpus)

            # Calculate coverage status and initial evidence strength
            # Rule: Do not treat semantic similarity alone as proof of technical competence!
            has_direct_evidence = bool(evidence_snippet)
            
            if has_direct_evidence and semantic_score >= similarity_threshold:
                coverage_status = "covered"
                initial_strength = min(1.0, round(0.65 + (semantic_score * 0.35), 2))
            elif has_direct_evidence or semantic_score >= (similarity_threshold - 0.15):
                coverage_status = "partially_covered"
                initial_strength = min(0.65, round(0.35 + (semantic_score * 0.30), 2))
            else:
                coverage_status = "uncovered"
                initial_strength = round(max(0.10, semantic_score * 0.3), 2)

            mapped_results.append({
                "name": comp_name,
                "category": comp_category,
                "importance_weight": importance_weight,
                "relevance_score": round(min(1.0, max(0.5, importance_weight * 0.95)), 2),
                "initial_strength": initial_strength,
                "evidence": evidence_snippet or "No direct evidence found in resume. Competency will be probed in interview.",
                "coverage_status": coverage_status,
            })

        return mapped_results

    def _select_competency_templates(self, job_role: str, job_description: Optional[str]) -> List[Dict[str, Any]]:
        role_lower = job_role.lower()

        # Find closest catalog match
        selected = None
        for key, comps in ROLE_COMPETENCY_CATALOG.items():
            if key in role_lower:
                selected = [dict(c) for c in comps]
                break

        if not selected:
            # Default to Software Engineer baseline
            selected = [dict(c) for c in ROLE_COMPETENCY_CATALOG["software engineer"]]

        # If job description provided, extract dynamic custom requirements
        if job_description and len(job_description.strip()) > 50:
            custom_comp = self._derive_competency_from_jd(job_description)
            if custom_comp:
                selected.insert(1, custom_comp)

        return selected[:6]

    def _derive_competency_from_jd(self, jd_text: str) -> Optional[Dict[str, Any]]:
        # Check for prominent technologies or domains in JD
        domains = [
            ("Cloud & DevOps Infrastructure", ["aws", "azure", "docker", "kubernetes", "ci/cd", "terraform"], "practical_application"),
            ("Distributed Messaging & Streaming", ["kafka", "rabbitmq", "redis", "pubsub", "microservices"], "system_design"),
            ("AI & LLM Application Engineering", ["llm", "langchain", "gemini", "rag", "embeddings", "openai"], "technical"),
            ("High Throughput Low Latency Systems", ["concurrency", "async", "caching", "websockets", "real-time"], "technical"),
        ]
        jd_lower = jd_text.lower()
        for name, keywords, category in domains:
            matches = [kw for kw in keywords if kw in jd_lower]
            if len(matches) >= 2:
                return {
                    "name": name,
                    "category": category,
                    "weight": 0.95,
                    "desc": f"Experience with {', '.join(matches)} as specified in the job description."
                }
        return None

    def _find_evidence_snippet(self, comp_name: str, comp_desc: str, profile: StructuredProfile) -> Optional[str]:
        # Search skills evidence map
        keywords = set(re.findall(r"\w+", f"{comp_name} {comp_desc}".lower()))
        for skill, snippet in profile.evidence_map.items():
            if skill.lower() in keywords:
                return f"Skill match '{skill}': {snippet}"

        # Search projects
        for proj in profile.projects:
            proj_text = f"{proj.title} {proj.description} {' '.join(proj.technologies)}".lower()
            matching_words = [w for w in keywords if len(w) > 3 and w in proj_text]
            if len(matching_words) >= 2:
                return f"Project '{proj.title}': {proj.description[:120]}..."

        # Search experience
        for exp in profile.work_experience:
            exp_text = f"{exp.role} {exp.company} {' '.join(exp.responsibilities)}".lower()
            matching_words = [w for w in keywords if len(w) > 3 and w in exp_text]
            if len(matching_words) >= 2:
                return f"Experience at {exp.company} ({exp.role}): {exp.responsibilities[0] if exp.responsibilities else ''}"

        return None


competency_service = CompetencyService()
