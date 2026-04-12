"""
Centralized configuration for the AI Resume Generator.
All constants, paths, and settings are managed here.
"""

import os

# ─── LLM Configuration (Ollama — Local) ────────────────────────────────────────

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 4096
LLM_MAX_RETRIES = 3
LLM_RETRY_DELAY = 2  # seconds (base for exponential backoff)

# ─── Logging Configuration ─────────────────────────────────────────────────────

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# ─── Upload Limits ─────────────────────────────────────────────────────────────

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_PDF_PAGES = 20

# ─── Skill Categories ─────────────────────────────────────────────────────────

SKILL_CATEGORIES = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "ruby", "go", "rust", "kotlin", "swift", "php", "r", "matlab",
        "scala", "dart", "perl", "lua", "haskell", "elixir",
    ],
    "Web Development": [
        "html", "css", "react", "angular", "vue", "node.js", "nodejs",
        "express", "django", "flask", "fastapi", "spring", "next.js",
        "nextjs", "tailwind", "bootstrap", "sass", "webpack", "vite",
        "graphql", "rest api", "restful", "jquery", "svelte",
    ],
    "Data Science & AI": [
        "machine learning", "deep learning", "nlp",
        "natural language processing", "tensorflow", "pytorch", "keras",
        "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn",
        "data science", "data analysis", "data visualization",
        "computer vision", "opencv", "transformers", "hugging face",
        "langchain", "llm", "generative ai", "statistical modeling",
        "feature engineering", "model deployment",
    ],
    "Databases": [
        "sql", "mysql", "postgresql", "mongodb", "sqlite", "redis",
        "firebase", "oracle", "nosql", "elasticsearch", "dynamodb",
        "cassandra", "neo4j", "supabase",
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
        "ci/cd", "jenkins", "github actions", "terraform", "linux",
        "bash", "nginx", "apache", "ansible", "cloudformation",
        "serverless", "microservices", "devops",
    ],
    "Tools & Platforms": [
        "git", "github", "gitlab", "bitbucket", "jira", "figma",
        "postman", "vs code", "intellij", "jupyter", "colab",
        "slack", "confluence", "trello", "notion",
    ],
    "Soft Skills": [
        "communication", "teamwork", "leadership", "problem solving",
        "agile", "scrum", "project management", "critical thinking",
        "time management", "collaboration", "mentoring",
    ],
}

# Flatten all skills into one list for backward compatibility
ALL_SKILLS = []
for skills in SKILL_CATEGORIES.values():
    ALL_SKILLS.extend(skills)

# ─── Application Tracker Fields ────────────────────────────────────────────────

APPLICATION_FIELDS = ["company", "role", "date", "status", "link", "notes"]
APPLICATION_STATUSES = [
    "Applied", "Interview Scheduled", "Under Review",
    "Rejected", "Offer Received", "Accepted", "Withdrawn",
]
