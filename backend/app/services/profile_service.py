import re
from typing import Dict, List, Any, Optional, Tuple
from app.schemas.profile import (
    StructuredProfile,
    ProjectItem,
    EducationItem,
    ExperienceItem,
)

# Curated Technical Taxonomies for precise matching and normalization
KNOWN_LANGUAGES = {
    "python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "sql", "html", "css",
    "bash", "shell", "dart", "perl", "matlab"
}

KNOWN_FRAMEWORKS = {
    "react", "react.js", "next.js", "vue", "vue.js", "angular", "node.js", "express",
    "express.js", "fastapi", "flask", "django", "spring", "spring boot", "asp.net",
    "laravel", "ruby on rails", "tailwindcss", "bootstrap", "pytorch", "tensorflow",
    "keras", "scikit-learn", "pandas", "numpy", "graphql", "redux", "prisma", "sqlalchemy"
}

KNOWN_TOOLS_PLATFORMS = {
    "git", "github", "gitlab", "docker", "kubernetes", "aws", "gcp", "azure", "linux",
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch", "kafka",
    "rabbitmq", "jenkins", "terraform", "ci/cd", "postman", "nginx", "vite", "webpack"
}


class ProfileService:
    @classmethod
    def parse_profile_from_text(cls, text: str) -> StructuredProfile:
        """
        Extracts candidate profile from resume text using section boundary analysis,
        regex extraction, date calculation, and skill taxonomy mapping.
        Preserves evidence snippets and avoids inventing missing info.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # 1. Contact Info & Name
        email = cls._extract_email(text)
        phone = cls._extract_phone(text)
        name = cls._extract_name(lines, email)

        # 2. Section Segmentation
        sections = cls._segment_sections(text)

        # 3. Skills Extraction & Categorization
        skills_dict, evidence_map = cls._extract_skills(text, sections)

        # 4. Experience & Projects Extraction
        work_experience = cls._extract_experience(sections.get("experience", ""))
        projects = cls._extract_projects(sections.get("projects", ""))
        education = cls._extract_education(sections.get("education", ""))
        achievements = cls._extract_achievements(sections.get("achievements", "") or sections.get("awards", ""))

        # 5. Experience Duration Calculation
        years_of_experience = cls._calculate_years_experience(text)

        summary = sections.get("summary") or sections.get("objective") or None
        if summary and len(summary) > 500:
            summary = summary[:497] + "..."

        return StructuredProfile(
            full_name=name or "Candidate",
            email=email,
            phone=phone,
            summary=summary,
            technical_skills=skills_dict.get("all_skills", []),
            programming_languages=skills_dict.get("languages", []),
            frameworks_libraries=skills_dict.get("frameworks", []),
            tools_platforms=skills_dict.get("tools", []),
            projects=projects,
            education=education,
            work_experience=work_experience,
            achievements=achievements,
            years_of_experience=years_of_experience,
            evidence_map=evidence_map,
        )

    @staticmethod
    def _extract_email(text: str) -> Optional[str]:
        match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_phone(text: str) -> Optional[str]:
        match = re.search(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}", text)
        return match.group(0).strip() if match else None

    @staticmethod
    def _extract_name(lines: List[str], email: Optional[str]) -> str:
        for line in lines[:5]:
            # Avoid headers or contact lines
            if "@" in line or "http" in line or len(line) > 50:
                continue
            if re.search(r"resume|curriculum|vitae|page", line, re.IGNORECASE):
                continue
            # Typical name: 2 to 4 capitalized words
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
                return line.strip()
        if email:
            # Fallback to email username
            clean_email_name = email.split("@")[0].replace(".", " ").replace("_", " ").title()
            return clean_email_name
        return "Candidate"

    @classmethod
    def _segment_sections(cls, text: str) -> Dict[str, str]:
        """
        Identifies common section headings and splits resume text into sections.
        """
        heading_patterns = {
            "summary": r"(?:summary|professional summary|about me|profile|objective)",
            "experience": r"(?:experience|work experience|employment history|professional experience|work history)",
            "projects": r"(?:projects|technical projects|academic projects|key projects)",
            "education": r"(?:education|academic background|qualifications)",
            "skills": r"(?:skills|technical skills|skills & expertise|core competencies)",
            "achievements": r"(?:achievements|awards|honors|certifications|publications)",
        }

        pattern = r"\n\s*(?:[#\-*]+\s*)?(" + "|".join(heading_patterns.values()) + r")[:\s]*\n"
        splits = re.split(pattern, "\n" + text, flags=re.IGNORECASE)

        sections: Dict[str, str] = {}
        if len(splits) > 1:
            for i in range(1, len(splits), 2):
                heading = splits[i].strip().lower()
                content = splits[i + 1].strip() if i + 1 < len(splits) else ""
                
                # Normalize section name
                matched_sec = None
                for sec_key, sec_pat in heading_patterns.items():
                    if re.match(sec_pat, heading, re.IGNORECASE):
                        matched_sec = sec_key
                        break
                if matched_sec:
                    sections[matched_sec] = sections.get(matched_sec, "") + "\n" + content
        else:
            sections["skills"] = text

        return sections

    @classmethod
    def _extract_skills(cls, full_text: str, sections: Dict[str, str]) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
        found_skills = set()
        languages = set()
        frameworks = set()
        tools = set()
        evidence_map = {}

        skills_content = sections.get("skills", "") + "\n" + full_text
        lower_content = skills_content.lower()

        # Helper to search words and find surrounding snippet
        def search_terms(term_set: set, target_set: set, category_name: str):
            for term in term_set:
                # Word boundary check
                pattern = r"(?<![a-zA-Z0-9])" + re.escape(term) + r"(?![a-zA-Z0-9])"
                match = re.search(pattern, lower_content)
                if match:
                    display_term = term.capitalize() if len(term) > 3 else term.upper()
                    if term in {"react", "react.js", "next.js", "vue.js", "node.js"}:
                        display_term = term.title()
                    elif term == "sql":
                        display_term = "SQL"
                    elif term == "aws":
                        display_term = "AWS"
                    elif term == "gcp":
                        display_term = "GCP"
                    elif term == "ci/cd":
                        display_term = "CI/CD"

                    target_set.add(display_term)
                    found_skills.add(display_term)

                    # Extract ~80 chars around evidence
                    start = max(0, match.start() - 30)
                    end = min(len(skills_content), match.end() + 50)
                    snippet = skills_content[start:end].replace("\n", " ").strip()
                    evidence_map[display_term] = snippet

        search_terms(KNOWN_LANGUAGES, languages, "language")
        search_terms(KNOWN_FRAMEWORKS, frameworks, "framework")
        search_terms(KNOWN_TOOLS_PLATFORMS, tools, "tool")

        # Also parse comma-separated items in the skills section
        if "skills" in sections:
            for line in sections["skills"].split("\n"):
                if ":" in line:
                    _, items_str = line.split(":", 1)
                else:
                    items_str = line
                for item in items_str.split(","):
                    clean_item = item.strip().strip("•-*")
                    if clean_item and 2 <= len(clean_item) <= 25 and not clean_item.lower().startswith("http"):
                        found_skills.add(clean_item)

        return {
            "all_skills": sorted(list(found_skills)),
            "languages": sorted(list(languages)),
            "frameworks": sorted(list(frameworks)),
            "tools": sorted(list(tools)),
        }, evidence_map

    @classmethod
    def _extract_projects(cls, projects_text: str) -> List[ProjectItem]:
        if not projects_text:
            return []
        
        projects = []
        blocks = re.split(r"\n(?=[A-Z0-9][\w\s\-]{2,40}(?:\s*\||\s*\(|\s*\n))", projects_text.strip())
        
        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue
            title_line = lines[0]
            # Clean title
            title = re.sub(r"[•\-*|]+", " ", title_line).strip()
            desc_lines = lines[1:] if len(lines) > 1 else [title_line]
            desc = " ".join(desc_lines)
            
            # Detect technologies mentioned in project
            techs = []
            for t in KNOWN_LANGUAGES.union(KNOWN_FRAMEWORKS).union(KNOWN_TOOLS_PLATFORMS):
                if re.search(r"(?<![a-zA-Z0-9])" + re.escape(t) + r"(?![a-zA-Z0-9])", desc.lower()):
                    techs.append(t.capitalize())

            projects.append(
                ProjectItem(
                    title=title[:80],
                    description=desc[:400] if desc else "Project details provided in resume.",
                    technologies=techs[:8],
                    highlights=desc_lines[:3],
                )
            )

        return projects[:6]

    @classmethod
    def _extract_experience(cls, exp_text: str) -> List[ExperienceItem]:
        if not exp_text or len(exp_text.strip()) < 15:
            return []
        
        items = []
        blocks = re.split(r"\n(?=[A-Z][\w\s,]{2,45}\s+(?:at|@|–|-|\|)\s+[\w\s]{2,40})", exp_text.strip())
        
        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue
            header = lines[0]
            role = header
            company = "Company"
            
            # Match Role at Company
            match = re.search(r"^(.*?)\s*(?:at|@|–|-|\|)\s*(.*?)(?:\s*\(|\s*$)", header, re.IGNORECASE)
            if match:
                role = match.group(1).strip()
                company = match.group(2).strip()
            else:
                # If neither 'at' nor duration found, skip non-experience lines
                duration_test = re.search(r"\b(20\d{2}|Present)\b", block, re.IGNORECASE)
                if not duration_test:
                    continue

            duration_match = re.search(r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4}).*?(?:Present|Current|\d{4}))", block, re.IGNORECASE)
            duration = duration_match.group(0).strip() if duration_match else None

            bullets = [l.strip("•-* ") for l in lines[1:] if len(l) > 10]

            if len(role) > 2 and company != role:
                items.append(
                    ExperienceItem(
                        role=role[:80],
                        company=company[:80],
                        duration=duration,
                        responsibilities=bullets[:5],
                    )
                )

        return items[:6]

    @classmethod
    def _extract_education(cls, edu_text: str) -> List[EducationItem]:
        if not edu_text:
            return []
        
        items = []
        lines = [l.strip() for l in edu_text.split("\n") if l.strip()]
        for line in lines:
            if re.search(r"bachelor|master|b\.tech|m\.tech|b\.s\.|m\.s\.|ph\.d|degree|diploma|university|college|institute", line, re.IGNORECASE):
                degree = line
                institution = "University / College"
                
                parts = re.split(r",|–|-|\|", line)
                if len(parts) >= 2:
                    degree = parts[0].strip()
                    institution = parts[1].strip()

                year_match = re.search(r"\b(20\d{2}|19\d{2})\b", line)
                year = year_match.group(0) if year_match else None

                items.append(
                    EducationItem(
                        degree=degree[:100],
                        institution=institution[:100],
                        year=year,
                        details=line,
                    )
                )

        return items[:3]

    @classmethod
    def _extract_achievements(cls, ach_text: str) -> List[str]:
        if not ach_text:
            return []
        lines = [l.strip("•-* ") for l in ach_text.split("\n") if len(l.strip()) > 15]
        return lines[:5]

    @classmethod
    def _calculate_years_experience(cls, text: str) -> float:
        """
        Estimates total years of experience by scanning date spans (e.g. 2020 - 2023 or 2021 - Present).
        """
        # Look for patterns like 2019 - 2023 or 2021 - Present
        year_ranges = re.findall(r"\b(20\d{2})\s*(?:-|–|to)\s*(20\d{2}|Present|Current)\b", text, re.IGNORECASE)
        current_year = 2026

        total_years = 0.0
        intervals = []
        for start_str, end_str in year_ranges:
            try:
                start_yr = int(start_str)
                if end_str.lower() in ["present", "current"]:
                    end_yr = current_year
                else:
                    end_yr = int(end_str)
                if 1990 <= start_yr <= current_year and start_yr <= end_yr <= current_year + 1:
                    intervals.append((start_yr, end_yr))
            except ValueError:
                continue

        if not intervals:
            return 1.0  # Default entry-level estimate

        # Merge overlapping intervals
        intervals.sort()
        merged = [intervals[0]]
        for curr in intervals[1:]:
            prev_start, prev_end = merged[-1]
            if curr[0] <= prev_end:
                merged[-1] = (prev_start, max(prev_end, curr[1]))
            else:
                merged.append(curr)

        total_years = sum(end - start for start, end in merged)
        return float(max(round(total_years, 1), 0.5))


profile_service = ProfileService()
