import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class QuestionDatasetService:
    """
    Manages loading, filtering, and querying questions from the Hugging Face dataset
    (Ankshi/interview) to ensure questions come from an external vetted dataset repository
    rather than hardcoded values in code.
    """
    def __init__(self, dataset_path: Optional[Path] = None):
        if dataset_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            dataset_path = base_dir / "data" / "dataset_questions.json"
            
        self.dataset_path = dataset_path
        self._questions: List[Dict[str, Any]] = []
        self._load_dataset()

    def _load_dataset(self):
        if self.dataset_path.exists():
            try:
                with open(self.dataset_path, "r", encoding="utf-8") as f:
                    self._questions = json.load(f)
                logger.info(f"Loaded {len(self._questions)} questions from dataset: {self.dataset_path}")
            except Exception as e:
                logger.error(f"Failed to load questions dataset from {self.dataset_path}: {e}")
                self._questions = []
        else:
            logger.warning(f"Dataset file not found at {self.dataset_path}")
            self._questions = []

    @property
    def total_count(self) -> int:
        return len(self._questions)

    def get_all_questions(self) -> List[Dict[str, Any]]:
        return list(self._questions)

    def find_matching_questions(
        self,
        job_role: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        exclude_texts: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filters and scores dataset questions based on role, category, difficulty, and keywords.
        Returns matched questions ordered by relevance.
        """
        exclude_set = set(t.strip().lower() for t in (exclude_texts or []))
        role_lower = (job_role or "").lower()
        cat_lower = (category or "").lower()
        diff_lower = (difficulty or "").lower()
        
        # Difficulty normalization: "junior" -> "easy", "mid" -> "medium", "senior" -> "hard"
        diff_map = {
            "junior": "easy",
            "entry": "easy",
            "easy": "easy",
            "mid": "medium",
            "intermediate": "medium",
            "medium": "medium",
            "senior": "hard",
            "advanced": "hard",
            "hard": "hard"
        }
        target_diff = diff_map.get(diff_lower, diff_lower)

        candidates = []
        for item in self._questions:
            q_text = item.get("question", "").strip()
            if not q_text or q_text.lower() in exclude_set:
                continue

            score = 0
            # Category match (e.g. Adaptability, Leadership, Team Collaboration, Conflict Resolution, etc.)
            item_cat = item.get("category", "").lower()
            if cat_lower and (cat_lower in item_cat or item_cat in cat_lower):
                score += 4
            elif any(w in item_cat for w in ["collaboration", "communication", "team"]) and any(w in cat_lower for w in ["collaboration", "communication", "team"]):
                score += 3
            elif any(w in item_cat for w in ["leadership", "management"]) and any(w in cat_lower for w in ["lead", "manage"]):
                score += 3

            # Role match
            item_role = item.get("role", "").lower()
            if role_lower and (role_lower in item_role or item_role in role_lower):
                score += 3
            elif ("engineer" in role_lower and "engineer" in item_role) or ("developer" in role_lower and "engineer" in item_role):
                score += 2

            # Difficulty match
            item_diff = item.get("difficulty", "").lower()
            if target_diff and item_diff == target_diff:
                score += 2

            # Keyword matches
            item_keywords = [k.lower() for k in item.get("keywords", [])]
            if keywords:
                for kw in keywords:
                    kw_low = kw.lower()
                    if kw_low in item_keywords or kw_low in q_text.lower():
                        score += 1

            candidates.append((score, item))

        # Sort descending by match score
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in candidates]

    def get_best_question(
        self,
        job_role: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        exclude_texts: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        matches = self.find_matching_questions(
            job_role=job_role,
            category=category,
            difficulty=difficulty,
            keywords=keywords,
            exclude_texts=exclude_texts
        )
        return matches[0] if matches else None


question_dataset_service = QuestionDatasetService()
