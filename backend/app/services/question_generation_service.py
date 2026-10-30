import json
import re
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from app.config import settings
from app.schemas.question import EvaluationRubric
from app.prompts.question_prompt import QUESTION_SYSTEM_INSTRUCTION, build_question_prompt


class QuestionGenerationService:
    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY and not settings.MOCK_AI:
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                print(f"Failed to initialize Gemini Client: {e}")
                self.client = None

    def generate_question(
        self,
        job_role: str,
        job_description: Optional[str],
        competency_id: str,
        competency_name: str,
        competency_category: str,
        difficulty: str,
        question_type: str,
        sequence_number: int,
        candidate_profile_json: str,
        previous_questions: List[Dict[str, Any]],
        adaptation_reason: Optional[str] = None,
        previous_answer_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates an interview question using Gemini Flash or fallback intelligent engine.
        Considers candidate's previous answer and evaluation to provide true conversational continuity.
        """
        if self.client and not settings.MOCK_AI:
            try:
                return self._generate_with_gemini(
                    job_role,
                    job_description,
                    competency_id,
                    competency_name,
                    competency_category,
                    difficulty,
                    question_type,
                    sequence_number,
                    candidate_profile_json,
                    previous_questions,
                    adaptation_reason,
                    previous_answer_context=previous_answer_context
                )
            except Exception as e:
                print(f"Gemini Question Generation failed: {e}. Falling back to deterministic engine.")

        # Deterministic / Mock Generation
        return self._generate_mock_question(
            job_role,
            competency_id,
            competency_name,
            competency_category,
            difficulty,
            question_type,
            sequence_number,
            candidate_profile_json,
            adaptation_reason,
            previous_questions=previous_questions,
            previous_answer_context=previous_answer_context
        )

    def _generate_with_gemini(
        self,
        job_role: str,
        job_description: Optional[str],
        competency_id: str,
        competency_name: str,
        competency_category: str,
        difficulty: str,
        question_type: str,
        sequence_number: int,
        candidate_profile_json: str,
        previous_questions: List[Dict[str, Any]],
        adaptation_reason: Optional[str],
        previous_answer_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        prompt_content = build_question_prompt(
            job_role=job_role,
            job_description=job_description or "",
            competency_name=competency_name,
            competency_category=competency_category,
            difficulty=difficulty,
            question_type=question_type,
            candidate_profile_json=candidate_profile_json,
            previous_questions=[q.get("question_text", "") for q in previous_questions],
            adaptation_reason=adaptation_reason,
            previous_answer_context=previous_answer_context
        )

        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt_content,
            config=types.GenerateContentConfig(
                system_instruction=QUESTION_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.4,
            ),
        )

        raw_json = response.text
        parsed = self._clean_and_parse_json(raw_json)
        return self._normalize_question_dict(parsed, competency_id, sequence_number, difficulty, question_type)

    def _clean_and_parse_json(self, raw_str: str) -> Dict[str, Any]:
        if not raw_str:
            raise ValueError("Empty response received from LLM")
        # Strip potential markdown fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_str.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return json.loads(cleaned)

    def _normalize_question_dict(
        self,
        data: Dict[str, Any],
        competency_id: str,
        sequence_number: int,
        difficulty: str,
        question_type: str
    ) -> Dict[str, Any]:
        question_text = data.get("question_text") or "Can you explain your experience and approach to solving technical problems?"
        expected_elements = data.get("expected_elements") or ["Conceptual understanding", "Practical application", "Trade-offs"]
        rubric_data = data.get("rubric") or {}

        rubric = EvaluationRubric(
            relevance_criteria=rubric_data.get("relevance_criteria", "Directly addresses the question without deviation."),
            technical_criteria=rubric_data.get("technical_criteria", "Demonstrates accurate technical knowledge and sound reasoning."),
            completeness_criteria=rubric_data.get("completeness_criteria", "Covers expected concepts, architecture, and constraints."),
            communication_criteria=rubric_data.get("communication_criteria", "Clearly structured with precise technical terminology.")
        )

        return {
            "sequence_number": sequence_number,
            "competency_id": competency_id,
            "question_text": question_text,
            "question_type": data.get("question_type", question_type),
            "difficulty": data.get("difficulty", difficulty),
            "expected_elements": expected_elements,
            "rubric": rubric.model_dump(),
            "maximum_score": float(data.get("maximum_score", 100.0)),
            "follow_up_guidance": data.get("follow_up_guidance", "Assess depth of technical clarity and edge cases."),
        }

    def _generate_mock_question(
        self,
        job_role: str,
        competency_id: str,
        competency_name: str,
        competency_category: str,
        difficulty: str,
        question_type: str,
        sequence_number: int,
        candidate_profile_json: str,
        adaptation_reason: Optional[str],
        previous_questions: Optional[List[Dict[str, Any]]] = None,
        previous_answer_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deterministic, high-quality question catalog tailored by competency, difficulty, and type.
        Directly references and branches off the candidate's previous response when available.
        """
        # If candidate previously answered and missed concepts or showed specific weaknesses, formulate a direct follow-up!
        if previous_answer_context and sequence_number > 1:
            prev_ans_text = previous_answer_context.get("answer_text", "").strip()
            missing_concepts = previous_answer_context.get("missing_concepts", [])
            last_score = previous_answer_context.get("score", 70.0)
            last_q_text = previous_answer_context.get("question_text", "")

            # If candidate struggled or missed a key area in their previous answer
            if missing_concepts and last_score < 70:
                missing_topic = missing_concepts[0]
                q_text = f"In your previous response, you discussed your approach, but didn't touch on {missing_topic}. Can you dive deeper into how you would address {missing_topic} in this context?"
                expected = [f"Directly explains {missing_topic}", "Connects back to previous scenario", "Considers architectural constraints"]
                rubric = EvaluationRubric(
                    relevance_criteria=f"Directly elaborates on {missing_topic} following up on previous answer.",
                    technical_criteria=f"Demonstrates clear technical grasp of {missing_topic} and error handling.",
                    completeness_criteria="Covers underlying mechanisms, implementation details, and trade-offs.",
                    communication_criteria="Articulates the clarification concisely and coherently."
                )
                return {
                    "sequence_number": sequence_number,
                    "competency_id": competency_id,
                    "question_text": q_text,
                    "question_type": "technical",
                    "difficulty": difficulty,
                    "expected_elements": expected,
                    "rubric": rubric.model_dump(),
                    "maximum_score": 100.0,
                    "follow_up_guidance": f"Ensure candidate accurately clarifies {missing_topic}.",
                    "source": "adaptive_followup"
                }

            # If candidate did well, follow up with an architectural stress test or edge case on their previous answer
            elif last_score >= 80 and prev_ans_text:
                q_text = f"Building on your previous answer: what are the primary bottleneck edge cases or failure modes in that approach, and how would you scale or monitor it under 10x traffic?"
                expected = ["Identifies specific failure modes/bottlenecks", "Proposes caching/partitioning or resiliency strategies", "Outlines monitoring and health metrics"]
                rubric = EvaluationRubric(
                    relevance_criteria="Addresses high-scale bottlenecks and resiliency extending the prior solution.",
                    technical_criteria="Demonstrates deep architectural trade-off analysis under high concurrency.",
                    completeness_criteria="Provides concrete solutions for scaling, failover, and metrics.",
                    communication_criteria="Clearly structured engineering recommendations."
                )
                return {
                    "sequence_number": sequence_number,
                    "competency_id": competency_id,
                    "question_text": q_text,
                    "question_type": "scenario",
                    "difficulty": "senior",
                    "expected_elements": expected,
                    "rubric": rubric.model_dump(),
                    "maximum_score": 100.0,
                    "follow_up_guidance": "Assess if candidate can stress-test their own architectural decisions.",
                    "source": "adaptive_escalation_followup"
                }

        # Query vetted question dataset (HuggingFace Ankshi/interview)
        from app.services.question_dataset_service import question_dataset_service
        
        # Determine category / keywords for matching
        exclude_list = []
        if previous_questions:
            exclude_list = [q.get("question_text", "") for q in previous_questions if q.get("question_text")]

        matched = question_dataset_service.get_best_question(
            job_role=job_role,
            category=competency_name if question_type == "behavioral" else competency_category,
            difficulty=difficulty,
            keywords=[competency_name, job_role, question_type],
            exclude_texts=exclude_list
        )

        if matched and (question_type == "behavioral" or matched.get("difficulty", "").lower() == difficulty.lower() or not settings.MOCK_AI):
            q_text = matched["question"]
            ideal_ans = matched.get("ideal_answer", "")
            expected = [
                f"Directly addresses {matched.get('category', competency_name)}",
                "Applies STAR structure (Situation, Task, Action, Result)",
                ideal_ans[:100] if ideal_ans else "Provides relevant real-world examples",
                "Articulates key learning and impact"
            ]
            rubric = EvaluationRubric(
                relevance_criteria=f"Directly addresses {matched.get('category', competency_name)} and context of {job_role}.",
                technical_criteria=f"Demonstrates sound practical reasoning, alignment with {matched.get('category', 'industry standards')}, and key decision trade-offs.",
                completeness_criteria="Covers context, actions taken, trade-offs, and measurable results.",
                communication_criteria="Explanations are well-organized, articulate, and professional."
            )
            return {
                "sequence_number": sequence_number,
                "competency_id": competency_id,
                "question_text": q_text,
                "question_type": question_type,
                "difficulty": difficulty,
                "expected_elements": expected,
                "rubric": rubric.model_dump(),
                "maximum_score": 100.0,
                "follow_up_guidance": f"Assess depth in {matched.get('category', competency_name)} and candidate's practical contribution.",
                "source": "hf_ankshi_dataset"
            }

        comp_lower = competency_name.lower()
        
        # Select tailored question template based on competency keywords
        if "data structures" in comp_lower or "algorithm" in comp_lower:
            if difficulty == "senior":
                q_text = "When designing an in-memory caching system like Redis, how would you implement an LRU cache with O(1) get and put operations? Discuss concurrency handling and memory fragmentation trade-offs."
                expected = ["Hash map coupled with doubly linked list", "O(1) lookup and O(1) eviction mechanics", "Read-write locks or mutexes for concurrent thread safety", "Memory overhead of node pointers"]
            elif difficulty == "junior":
                q_text = "Can you explain the difference between an Array and a Linked List in terms of time complexity for insertion, deletion, and random lookup? When would you choose one over the other?"
                expected = ["Array O(1) index lookup vs Linked List O(N)", "Array O(N) arbitrary insertion vs Linked List O(1) insertion if pointer is known", "Contiguous memory locality benefits of arrays vs dynamic sizing of linked lists"]
            else:
                q_text = "Suppose you need to find the top K most frequent elements in a large real-time stream of data. How would you design this algorithm efficiently? What are the time and space complexities?"
                expected = ["Min-heap of size K or Count-Min Sketch", "O(N log K) time complexity", "Memory trade-offs between exact counts and streaming approximations"]
        elif "frontend" in comp_lower or "javascript" in comp_lower or "react" in comp_lower:
            if difficulty == "senior":
                q_text = "Explain the mechanics of React's Concurrent Mode and Fiber reconciler. How do priority scheduling and time-slicing prevent main thread blocking during heavy state updates?"
                expected = ["Fiber tree structure (child, sibling, return pointers)", "Two-phase reconciliation (render/reconciliation vs commit)", "useTransition and useDeferredValue priority lanes", "Avoiding waterfalls and micro-task starvation"]
            elif difficulty == "junior":
                q_text = "What is the difference between state and props in React? How do useEffect dependencies work, and how do you prevent unintentional infinite re-rendering loops?"
                expected = ["Props are immutable parent inputs; state is component-managed mutable data", "Dependency array comparison via Object.is", "Setting state unconditionally inside useEffect causes infinite loops"]
            else:
                q_text = "How would you optimize a large data grid or list in a web application with 50,000 items that is causing UI lag and slow scrolling?"
                expected = ["Virtualization / windowing (react-window or react-virtualized)", "Rendering only DOM nodes in visible viewport", "Debouncing/throttling search filters", "Memoization with useMemo/useCallback"]
        elif "backend" in comp_lower or "api" in comp_lower:
            if difficulty == "senior":
                q_text = "Design an idempotent distributed payment API endpoint. How do you prevent double-charging during network timeouts, client retries, and concurrent requests across multiple server instances?"
                expected = ["Client-generated idempotency key in HTTP headers", "Atomic reservation with distributed lock (Redis) or unique DB constraint", "State machine (pending, processing, succeeded, failed)", "Safe replay of cached response for duplicate requests"]
            elif difficulty == "junior":
                q_text = "What are the key differences between HTTP GET, POST, PUT, and PATCH? When should an API return status codes 400, 401, 403, and 404?"
                expected = ["GET is idempotent and safe; POST is non-idempotent; PUT replaces; PATCH updates partially", "400 Bad Request, 401 Unauthorized (unauthenticated), 403 Forbidden, 404 Not Found"]
            else:
                q_text = "In a microservices architecture, how do you manage distributed transactions across multiple databases without creating tight coupling? Explain the Saga pattern."
                expected = ["Two-phase commit (2PC) bottlenecks vs Saga eventual consistency", "Choreography vs Orchestration based Sagas", "Compensating transactions on failure", "Outbox pattern for reliable event publishing"]
        elif "database" in comp_lower or "query" in comp_lower:
            if difficulty == "senior":
                q_text = "Explain PostgreSQL transaction isolation levels (Read Committed, Repeatable Read, Serializable). What are phantom reads, and how does MVCC implement snapshot isolation under high write concurrency?"
                expected = ["MVCC xmin/xmax tuple versioning without read-blocking-writes", "Difference between dirty reads, non-repeatable reads, and phantom reads", "Serialization anomalies and write skew", "Optimistic concurrency control with retry loops"]
            else:
                q_text = "How do B-Tree indexes work in relational databases? When might adding an index hurt performance rather than help it?"
                expected = ["Balanced tree hierarchy with log(N) lookup", "Index selectivity and cardinality", "Write amplification (slower INSERT/UPDATE/DELETE)", "Covering indexes avoiding heap lookups"]
        elif "security" in comp_lower or "auth" in comp_lower:
            q_text = "How would you architect a secure authentication and session management system using JWTs and refresh tokens? How do you defend against XSS and CSRF attacks?"
            expected = ["Short-lived access token + long-lived rotating refresh token", "HttpOnly, Secure, SameSite cookies to protect from XSS", "CSRF tokens or custom request headers", "Token revocation / blacklisting strategies"]
        else:
            # Fallback to general dataset question or tailored prompt
            dataset_fallback = question_dataset_service.get_best_question(
                job_role=job_role,
                category="Behavioral" if question_type == "behavioral" else "Work Style",
                difficulty=difficulty,
                exclude_texts=exclude_list
            )
            if dataset_fallback:
                q_text = dataset_fallback["question"]
                expected = ["Clear structured explanation", "Actionable examples", "Reflection on outcome and learnings"]
            else:
                if question_type == "behavioral":
                    q_text = f"Describe a situation in your previous projects where you encountered an unexpected technical roadblock or conflicting architectural decision. How did you resolve it and communicate with stakeholders?"
                    expected = ["STAR method (Situation, Task, Action, Result)", "Objective evaluation of trade-offs", "Clear communication and proactive resolution", "Key lessons learned"]
                else:
                    q_text = f"Regarding {competency_name}, can you walk through a complex system or feature you implemented? What architectural challenges did you encounter and how did you validate correctness?"
                    expected = ["Clear structural explanation of the system", "Identification of bottlenecks or edge cases", "Testing and verification approach", "Reflections on performance and maintainability"]

        rubric = EvaluationRubric(
            relevance_criteria=f"Directly addresses {competency_name} and answers the specific prompt scenarios.",
            technical_criteria="Demonstrates sound architectural reasoning, accurate terminology, and awareness of performance/security implications.",
            completeness_criteria="Covers core mechanics, trade-offs, edge cases, and practical implementation details.",
            communication_criteria="Explanations are well-organized, articulate, and use precise technical phrasing."
        )

        return {
            "sequence_number": sequence_number,
            "competency_id": competency_id,
            "question_text": q_text,
            "question_type": question_type,
            "difficulty": difficulty,
            "expected_elements": expected,
            "rubric": rubric.model_dump(),
            "maximum_score": 100.0,
            "follow_up_guidance": "Examine if the candidate understands underlying runtime mechanics and edge cases.",
        }


question_generation_service = QuestionGenerationService()
