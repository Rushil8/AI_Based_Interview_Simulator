"""
Inference Module for Trained Adaptive Question Selector
Loads the saved ML pipeline and selects the optimal next question
from a question bank based on candidate state.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import joblib


class AdaptiveQuestionSelector:
    def __init__(self, model_path: Optional[Path] = None):
        if model_path is None:
            base_dir = Path(__file__).resolve().parent
            model_path = base_dir / "saved_models" / "question_ranker_pipeline.joblib"

        self.model_path = model_path
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        if self.model_path.exists():
            try:
                self.pipeline = joblib.load(self.model_path)
            except Exception as e:
                print(f"Warning: Could not load trained ML model: {e}")
                self.pipeline = None
        else:
            self.pipeline = None

    @property
    def is_available(self) -> bool:
        return self.pipeline is not None

    def rank_questions(
        self,
        role: str,
        competency: str,
        difficulty: str,
        previous_score: float,
        previous_weakness: str,
        candidate_skills: str,
        question_pool: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate questions from question_pool given the current candidate state.
        Returns sorted list with questions and predicted pedagogical match probability.
        """
        if not self.is_available or not question_pool:
            # Fallback uniform ranking
            return [{"question": q, "predicted_score": 1.0} for q in question_pool]

        model = self.pipeline["model"]
        vectorizer = self.pipeline["vectorizer"]

        state_text = (
            f"Role: {role} | "
            f"Competency: {competency} | "
            f"Difficulty: {difficulty} | "
            f"Previous Score: {previous_score} | "
            f"Weakness: {previous_weakness} | "
            f"Skills: {candidate_skills}"
        )

        cross_texts = [f"{state_text} [SEP] Question: {q}" for q in question_pool]
        X = vectorizer.transform(cross_texts)
        probs = model.predict_proba(X)[:, 1]

        ranked = []
        for q, p in zip(question_pool, probs):
            ranked.append({
                "question": q,
                "predicted_score": float(p)
            })

        # Sort descending by predicted probability
        ranked.sort(key=lambda x: x["predicted_score"], reverse=True)
        return ranked

    def select_best_question(
        self,
        role: str,
        competency: str,
        difficulty: str,
        previous_score: float,
        previous_weakness: str,
        candidate_skills: str,
        question_pool: List[str]
    ) -> Optional[Dict[str, Any]]:
        ranked = self.rank_questions(
            role=role,
            competency=competency,
            difficulty=difficulty,
            previous_score=previous_score,
            previous_weakness=previous_weakness,
            candidate_skills=candidate_skills,
            question_pool=question_pool
        )
        return ranked[0] if ranked else None

    def generate_question_seq2seq(
        self,
        role: str,
        competency: str,
        difficulty: str,
        previous_weakness: str,
        max_len: int = 35
    ) -> Optional[str]:
        """
        Uses the trained PyTorch Seq2Seq model with Attention to generate a question text.
        """
        import torch
        from ml.train_question_generator_pytorch import EncoderRNN, AttnDecoderRNN

        ckpt_path = Path(__file__).resolve().parent / "saved_models" / "pytorch_seq2seq_generator.pt"
        if not ckpt_path.exists():
            return None

        device = torch.device("cpu")
        checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)

        src_word2idx = checkpoint.get("src_word2idx", {})
        src_n_words = checkpoint.get("src_n_words", len(src_word2idx) + 4)
        tgt_idx2word = checkpoint.get("tgt_idx2word", {})
        tgt_n_words = checkpoint.get("tgt_n_words", len(tgt_idx2word) + 4)
        hidden_size = checkpoint.get("hidden_size", 128)

        # Convert str keys to int if necessary from JSON/pickle
        tgt_idx2word = {int(k): v for k, v in tgt_idx2word.items()}

        encoder = EncoderRNN(src_n_words, hidden_size).to(device)
        decoder = AttnDecoderRNN(hidden_size, tgt_n_words).to(device)

        encoder.load_state_dict(checkpoint["encoder_state"])
        decoder.load_state_dict(checkpoint["decoder_state"])

        encoder.eval()
        decoder.eval()

        input_str = f"{role} {competency} {difficulty} {previous_weakness}".lower().replace("?", " ?").replace(".", " .").replace(",", " ,")
        tokens = [1]  # <SOS>
        for word in input_str.split():
            tokens.append(src_word2idx.get(word, 3))
            if len(tokens) >= 24:
                break
        tokens.append(2)  # <EOS>
        while len(tokens) < 25:
            tokens.append(0)
        token_ids = tokens[:25]

        x_tensor = torch.tensor([token_ids], dtype=torch.long, device=device)

        with torch.no_grad():
            encoder_outputs, hidden = encoder(x_tensor)
            dec_in = torch.tensor([[1]], dtype=torch.long, device=device)  # <SOS>
            words = []

            for _ in range(max_len):
                output, hidden, _ = decoder(dec_in, hidden, encoder_outputs)
                top_id = output.argmax(dim=-1).item()

                if top_id == 2:  # <EOS>
                    break
                if top_id not in (0, 1, 3):
                    word = tgt_idx2word.get(top_id, "")
                    if word:
                        words.append(word)

                dec_in = torch.tensor([[top_id]], dtype=torch.long, device=device)

        if not words:
            return None

        # Reconstruct sentence with proper capitalization and punctuation
        result = " ".join(words)
        result = result.replace(" ?", "?").replace(" .", ".").replace(" ,", ",")
        return result[0].upper() + result[1:]



# Global singleton instance
adaptive_selector = AdaptiveQuestionSelector()

