import urllib.request
import json
import re
from pathlib import Path

def download_and_extract():
    url = "https://huggingface.co/datasets/Ankshi/interview/resolve/main/hr_interview.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    print("Connecting to Hugging Face dataset stream...")
    with urllib.request.urlopen(req) as res:
        buffer = ""
        unique_questions = {}
        target_file = Path("app/data/dataset_questions.json")
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Read stream in chunks (up to ~6MB is plenty to see all unique questions & roles multiple times)
        chunk_count = 0
        while chunk_count < 100:
            chunk = res.read(65536)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="ignore")
            chunk_count += 1
            
            # Simple scanner for JSON objects in array
            # Look for "{" and "}"
            while True:
                start = buffer.find("{")
                if start == -1:
                    break
                # Find matching "}"
                end = buffer.find("}", start)
                if end == -1:
                    # Incomplete object in buffer, wait for more chunks
                    break
                
                json_str = buffer[start:end+1]
                buffer = buffer[end+1:]
                
                try:
                    obj = json.loads(json_str)
                    q = obj.get("question", "").strip()
                    if q and q not in unique_questions:
                        unique_questions[q] = {
                            "question": q,
                            "category": obj.get("category", "General"),
                            "role": obj.get("role", "Software Engineer"),
                            "experience": obj.get("experience", "fresher"),
                            "difficulty": obj.get("difficulty", "Medium"),
                            "source_type": obj.get("source_type", "Open-Ended"),
                            "ideal_answer": obj.get("ideal_answer", ""),
                            "keywords": obj.get("keywords", [])
                        }
                except Exception:
                    pass

        print(f"Extraction complete! Found {len(unique_questions)} unique questions.")
        question_list = list(unique_questions.values())
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(question_list, f, indent=2)
            
        print(f"Saved {len(question_list)} questions to {target_file}")

if __name__ == "__main__":
    download_and_extract()
