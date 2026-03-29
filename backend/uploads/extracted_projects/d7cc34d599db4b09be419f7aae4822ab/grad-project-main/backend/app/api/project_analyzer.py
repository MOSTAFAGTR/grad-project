import os
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import openai

from .. import models
from ..db.database import get_db
from .auth import get_current_user
from .projects import EXTRACTED_PROJECTS_DIR, _assert_project_access, normalize_project_root


router = APIRouter()


def _detect_frameworks(file_name: str, content: str) -> set[str]:
    frameworks: set[str] = set()
    lower_name = file_name.lower()
    lower_content = content.lower()

    if "react" in lower_content and (lower_name.endswith(".tsx") or lower_name.endswith(".jsx") or "package.json" in lower_name):
        frameworks.add("React")
    if "fastapi" in lower_content:
        frameworks.add("FastAPI")
    if "flask" in lower_content:
        frameworks.add("Flask")
    if "django" in lower_content:
        frameworks.add("Django")
    if "express" in lower_content:
        frameworks.add("Express")
    if "flutter" in lower_content or lower_name == "pubspec.yaml":
        frameworks.add("Flutter")
    return frameworks


def _is_entry_point(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/").lower()
    candidates = {
        "main.py",
        "app.py",
        "manage.py",
        "server.js",
        "index.js",
        "index.ts",
        "src/main.tsx",
        "src/main.jsx",
        "main.dart",
        "lib/main.dart",
    }
    return any(normalized.endswith(c) for c in candidates)


def _safe_ai_summary(context: dict[str, Any]) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    openai.api_key = api_key
    prompt = (
        "Analyze this project structure and describe architecture, risks, and key components.\n"
        f"Data: {context}"
    )
    try:
        response = openai.ChatCompletion.create(
            model=os.getenv("AI_MENTOR_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a software architecture and AppSec reviewer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            timeout=20,
        )
        return str(response.choices[0].message["content"]).strip()
    except Exception:
        return None


@router.post("/project/analyze-structure")
def analyze_project_structure(
    project_id: str = Query(..., description="ID of extracted project folder"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _assert_project_access(db, project_id, current_user)
    project_dir = EXTRACTED_PROJECTS_DIR / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project folder does not exist")
    if len(list(project_dir.rglob("*"))) == 0:
        raise HTTPException(status_code=400, detail="Project folder is EMPTY after extraction")

    scan_root = normalize_project_root(project_dir)

    ext_to_lang = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".dart": "dart",
        ".java": "java",
        ".go": "go",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".kt": "kotlin",
        ".swift": "swift",
        ".sql": "sql",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".xml": "xml",
        ".html": "html",
        ".css": "css",
    }
    skip_dirs = {".git", "node_modules", "__pycache__", "venv", ".dart_tool"}

    languages: set[str] = set()
    frameworks: set[str] = set()
    entry_points: list[str] = []
    files_summary: list[dict[str, Any]] = []
    risk_indicators: set[str] = set()

    for root, dirs, files in os.walk(scan_root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file_name in files:
            full_path = Path(root) / file_name
            rel = str(full_path.relative_to(scan_root)).replace("\\", "/")
            ext = full_path.suffix.lower()
            lang = ext_to_lang.get(ext, "unknown")
            if lang != "unknown":
                languages.add(lang)

            files_summary.append({"path": rel, "language": lang, "size": full_path.stat().st_size})

            if _is_entry_point(rel):
                entry_points.append(rel)

            content = ""
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                content = ""

            if content:
                frameworks.update(_detect_frameworks(file_name, content))

                low = content.lower()
                if "@router." in content or "@app.route" in content or "app.get(" in content or "app.post(" in content:
                    risk_indicators.add("API routes detected")
                if "create_engine(" in content or "sqlalchemy" in low or "pymysql" in low or "sqlite3" in low:
                    risk_indicators.add("Database usage detected")
                if "docker.sock" in low:
                    risk_indicators.add("Docker socket exposure pattern found")
                if "os.system(" in content or "subprocess.run(" in content or "exec(" in content:
                    risk_indicators.add("Potential command execution sink detected")
                if "password=" in low or "api_key" in low or "secret" in low or "token" in low:
                    risk_indicators.add("Potential hardcoded secret patterns detected")

    files_summary_sorted = sorted(files_summary, key=lambda x: x["size"], reverse=True)[:25]
    context = {
        "languages": sorted(languages),
        "frameworks": sorted(frameworks),
        "entry_points": sorted(set(entry_points)),
        "risk_indicators": sorted(risk_indicators),
        "top_files": files_summary_sorted[:10],
    }
    ai_summary = _safe_ai_summary(context)

    return {
        "languages": context["languages"],
        "frameworks": context["frameworks"],
        "entry_points": context["entry_points"],
        "files_summary": files_summary_sorted,
        "risk_indicators": context["risk_indicators"],
        "ai_summary": ai_summary,
    }

