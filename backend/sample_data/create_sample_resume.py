import fitz  # PyMuPDF


def generate_sample_pdf(output_path: str = "sample_data/sample_resume.pdf"):
    doc = fitz.open()
    page = doc.new_page()

    text = """Alex Morgan
alex.morgan@example.com | +1 (555) 234-5678 | San Francisco, CA | github.com/alexmorgan

PROFESSIONAL SUMMARY
Senior Full Stack Engineer with 4 years of experience building high-scale web applications, distributed REST APIs, and responsive frontends using React, TypeScript, Python, and PostgreSQL. Experienced in Docker containerization and cloud architectures.

TECHNICAL SKILLS
Languages: Python, TypeScript, JavaScript, SQL, HTML, CSS, Bash
Frameworks & Libraries: React, Node.js, FastAPI, Express, Tailwind CSS, Next.js, Redux, SQLAlchemy
Databases & Cloud: PostgreSQL, Redis, Docker, AWS, Git, CI/CD, Linux

WORK EXPERIENCE
Senior Full Stack Developer at CloudScale Solutions | 2022 - Present
- Architected and deployed microservices backend using Python FastAPI and PostgreSQL handling 15M daily requests.
- Built responsive client dashboard using React, TypeScript, and Tailwind CSS, improving Core Web Vitals by 42%.
- Designed redis caching layer reducing P99 API response times from 350ms to 45ms.
- Mentored junior engineers and led code reviews focusing on modular design and automated unit testing.

Software Engineer at Apex Innovations | 2020 - 2022
- Developed RESTful APIs using Node.js and Express for an enterprise SaaS platform.
- Integrated JWT authentication and role-based access control protecting customer data.
- Automated testing pipelines using Pytest and Jest, achieving 88% test coverage.

PROJECTS
Adaptive Code Review Platform | React, TypeScript, FastAPI, PostgreSQL
- Built an open-source collaborative code review tool with syntax highlighting and real-time diffing.
- Implemented asynchronous background tasks for static analysis and linting.

Distributed Key-Value Store | Python, Docker
- Implemented a lightweight distributed key-value store with Raft consensus and write-ahead logging.

EDUCATION
Bachelor of Science in Computer Science
State University of California | 2016 - 2020
Graduated Magna Cum Laude, GPA 3.85/4.0
"""
    # Insert text into page
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, text, fontsize=9, fontname="helv", align=0)
    doc.save(output_path)
    doc.close()
    print(f"Sample PDF resume created at {output_path}")


if __name__ == "__main__":
    generate_sample_pdf()
