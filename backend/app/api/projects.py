from pathlib import Path
from uuid import uuid4
import shutil
import zipfile
import os
import re
import json
import subprocess
import tempfile
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
from typing import Optional, Any
from urllib.parse import urlparse

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..scanner.detector import scan_file_for_vulnerabilities_detailed
from ..scanner.semgrep_scanner import run_semgrep_scan
from ..scanner.scorer import calculate_risk
from ..scanner.fixer import attach_fixes
from ..scanner.report_generator import generate_security_report, generate_pdf_report
from ..ai.mentor import generate_ai_security_feedback
from ..db.database import get_db, SessionLocal
from .. import models
from .auth import get_current_user, get_current_admin
from ..security.security_logger import SecurityEventType, SecuritySeverity, log_security_event
from ..security.learning_tracker import recalculate_learning_progress
from ..ai.serper_helpers import serper_configured


router = APIRouter()
logger = logging.getLogger(__name__)

SCAN_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="scale_scan",
)


def _openai_key() -> str:
    return (os.getenv("OPENAI_API_KEY", "") or "").strip()


def _resolve_storage_root() -> Path:
    configured_root = os.getenv("PROJECT_STORAGE_ROOT", "").strip()
    if configured_root:
        return Path(configured_root).resolve()

    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "backend").exists() and (candidate / "frontend").exists():
            return candidate.resolve()

    app_root = Path("/app")
    if app_root.exists():
        return app_root.resolve()

    return Path.cwd().resolve()


STORAGE_ROOT = _resolve_storage_root()
PROJECTS_UPLOAD_DIR = STORAGE_ROOT / "uploads" / "projects"
EXTRACTED_PROJECTS_DIR = STORAGE_ROOT / "uploads" / "extracted_projects"
REPORTS_DIR = STORAGE_ROOT / "reports"


def _assert_project_access(
    db: Session,
    project_id: str,
    current_user: models.User,
) -> None:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return
    if current_user.role == "admin":
        return
    if project.owner_id and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this project")


def _count_by_type(findings: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in findings:
        v = str(f.get("vulnerability_type") or f.get("type") or "Unknown")
        out[v] = out.get(v, 0) + 1
    return out


def _count_by_severity(findings: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in findings:
        s = str(f.get("severity") or "Unknown")
        out[s] = out.get(s, 0) + 1
    return out


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """
    Safely extract a ZIP file to a target directory.

    - Only whitelisted source-code extensions are extracted.
    - Directory traversal (../ or absolute paths) is blocked so that
      nothing can escape the intended extraction folder.

    This function is the hook where later vulnerability scanners will be
    plugged in to walk the extracted tree and analyze code.
    """
    allowed_exts = {
        ".php", ".js", ".jsx", ".ts", ".tsx",
        ".py", ".java", ".go", ".rb", ".cs", ".kt", ".swift",
        ".html", ".htm", ".css", ".vue", ".svelte",
        ".sql", ".xml", ".json", ".yml", ".yaml", ".env", ".ini", ".cfg",
        ".c", ".cpp", ".h", ".hpp", ".sh", ".dart",
    }

    # Ensure target directory exists
    extract_to.mkdir(parents=True, exist_ok=True)
    base = extract_to.resolve()

    extracted_count = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            name = member.filename

            # Skip directories
            if name.endswith("/"):
                continue

            rel_path = Path(name)

            # Skip large/unwanted trees like node_modules early
            if "node_modules" in rel_path.parts:
                continue

            # Only allow specific source-code file extensions.
            # This reduces risk from binary payloads (.exe, .dll, etc.)
            # and keeps future scanning focused on code.
            if rel_path.suffix.lower() not in allowed_exts:
                continue

            # Prevent directory traversal / absolute paths:
            # an entry like "../../etc/passwd" must never escape our base folder.
            target_path = (base / rel_path).resolve()
            if not str(target_path).startswith(str(base)):
                # Instead of extracting, we fail fast as this indicates a malicious ZIP.
                raise HTTPException(status_code=400, detail="Unsafe path in zip archive")

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member, "r") as src, open(target_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted_count += 1

    # Mandatory extraction diagnostics for pipeline verification.
    print("=== EXTRACTION DEBUG START ===")
    for root, dirs, files in os.walk(extract_to):
        for f in files:
            print("EXTRACTED FILE:", os.path.join(root, f))
    print("=== EXTRACTION DEBUG END ===")
    print("TOTAL EXTRACTED FILES:", extracted_count)
    if extracted_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Scanner found 0 files — extraction or traversal failure",
        )


def normalize_project_root(path: Path) -> Path:
    """
    Handle nested archive structures like project/project/files...
    We keep descending while there is exactly one directory entry.
    """
    current = path
    while True:
        try:
            contents = [p for p in current.iterdir()]
        except FileNotFoundError:
            return current
        if len(contents) == 1 and contents[0].is_dir():
            current = contents[0]
            continue
        return current


def scan_project_files(project_folder: Path):
    """
    Walk the extracted project tree and return a list of source-code files
    with detected language based on file extension.

    - Recursive walking is important so we don't miss code buried several
      levels deep in nested folders.
    - We aggressively filter to known code extensions to avoid accidentally
      treating binaries, media, or dependency caches as code.
    """
    if not project_folder.is_dir():
        raise HTTPException(status_code=404, detail="Project folder not found")

    # Directories we never want to traverse for scanning purposes.
    skip_dirs = {".git", "node_modules", "venv", "__pycache__"}

    ext_to_lang = {
        ".php": "php",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".py": "python",
        ".java": "java",
        ".go": "go",
        ".rb": "ruby",
        ".cs": "csharp",
        ".kt": "kotlin",
        ".swift": "swift",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".vue": "vue",
        ".svelte": "svelte",
        ".sql": "sql",
        ".xml": "xml",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".env": "env",
        ".ini": "config",
        ".cfg": "config",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c_header",
        ".hpp": "cpp_header",
        ".sh": "shell",
        ".dart": "dart",
    }

    files_info = []
    base = project_folder.resolve()

    for root, dirs, files in os.walk(base):
        # Prune unwanted directories in-place so os.walk skips their contents.
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for fname in files:
            full_path = Path(root) / fname
            rel_path = full_path.relative_to(base)
            ext = Path(fname).suffix.lower()
            language = ext_to_lang.get(ext, "unknown")
            print("SCANNING FILE:", str(full_path))
            files_info.append(
                {
                    "file": str(rel_path).replace("\\", "/"),
                    "language": language,
                }
            )

    print("TOTAL FILES FOUND:", len(files_info))
    if len(files_info) == 0:
        raise HTTPException(
            status_code=400,
            detail="Scanner found 0 files — extraction or traversal failure",
        )

    return files_info


def _merge_findings(semgrep: list[dict], legacy: list[dict]) -> list[dict]:
    """
    Merge Semgrep and legacy regex findings.
    Deduplicate by (file, line, vulnerability_type).
    Semgrep findings take priority when there is a collision.
    """
    seen: set[tuple] = set()
    merged: list[dict] = []

    for f in semgrep:
        key = (
            str(f.get("file", "")),
            int(f.get("line") or 0),
            str(f.get("vulnerability_type", "")),
        )
        if key not in seen:
            seen.add(key)
            merged.append(f)

    for f in legacy:
        key = (
            str(f.get("file", "")),
            int(f.get("line") or 0),
            str(f.get("vulnerability_type", "")),
        )
        if key not in seen:
            seen.add(key)
            fc = dict(f)
            fc["engine"] = "regex"
            merged.append(fc)

    return merged


def _legacy_regex_findings_raw(project_folder: Path) -> list[dict]:
    files = scan_project_files(project_folder)
    all_findings: list[dict] = []
    for entry in files:
        rel_path = entry["file"]
        full_path = project_folder / rel_path
        detailed = scan_file_for_vulnerabilities_detailed(full_path)
        for f in detailed["findings"]:
            all_findings.append({"file": rel_path, **f})
    return all_findings


def run_merged_scan(
    project_folder: Path,
    extraction_root: Optional[Path] = None,
    semgrep_timeout_seconds: int = 45,
) -> dict:
    """
    Run Semgrep plus legacy regex scanner, merge findings, attach fixes.
    """
    semgrep_result = run_semgrep_scan(
        str(project_folder.resolve()),
        timeout_seconds=semgrep_timeout_seconds,
    )
    semgrep_findings = list(semgrep_result.get("findings") or [])
    semgrep_available = bool(semgrep_result.get("available", False))
    legacy_raw = _legacy_regex_findings_raw(project_folder)
    merged_findings = _merge_findings(semgrep_findings, legacy_raw)
    enhanced_findings = attach_fixes(merged_findings)

    summary: dict[str, int] = {}
    for f in enhanced_findings:
        vtype = f.get("vulnerability_type", "Unknown")
        summary[vtype] = summary.get(vtype, 0) + 1

    files = scan_project_files(project_folder)
    file_debug = []
    file_errors = []
    files_with_matches = 0
    for entry in files:
        rel_path = entry["file"]
        full_path = project_folder / rel_path
        detailed = scan_file_for_vulnerabilities_detailed(full_path)
        file_findings = detailed["findings"]
        if detailed.get("error"):
            file_errors.append({"file": rel_path, "error": detailed["error"]})
        if file_findings:
            files_with_matches += 1
        file_debug.append(
            {
                "file": rel_path,
                "matches": len(file_findings),
                "lines_scanned": detailed.get("lines_scanned", 0),
            }
        )

    logger.info(
        "scanner merged: semgrep=%s regex_raw=%s merged=%s",
        len(semgrep_findings),
        len(legacy_raw),
        len(merged_findings),
    )

    message = (
        "No vulnerabilities detected OR not supported by current scanner depth"
        if len(enhanced_findings) == 0
        else "Vulnerabilities detected"
    )

    debug_payload = {
        "files_scanned": len(files),
        "files_with_matches": files_with_matches,
        "file_details": file_debug,
        "file_errors": file_errors,
        "root_used_for_scan": str(project_folder.resolve()),
        "semgrep_errors": semgrep_result.get("errors") or [],
    }
    if extraction_root is not None:
        debug_payload["extracted_file_count"] = sum(1 for p in extraction_root.rglob("*") if p.is_file())

    scanner_engines = {
        "semgrep": semgrep_available,
        "semgrep_findings": len(semgrep_findings),
        "regex_findings": len(legacy_raw),
        "total_after_dedup": len(merged_findings),
    }

    return {
        "total_vulnerabilities": len(enhanced_findings),
        "findings": enhanced_findings,
        "summary": summary,
        "message": message,
        "debug": debug_payload,
        "scanner_engines": scanner_engines,
    }


def scan_project_for_vulnerabilities(project_folder: Path, extraction_root: Optional[Path] = None):
    """
    Run Semgrep (when available) plus the legacy rule-based detector, merge results,
    and attach fix guidance.
    """
    return run_merged_scan(project_folder, extraction_root, semgrep_timeout_seconds=45)


@router.post("/project/upload")
async def upload_project(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Accept a compressed project (.zip), save it, and extract safe files for later scanning.

    Validation here is critical:
    - to reduce risk of abusing this endpoint for arbitrary large uploads
      (basic DoS protection via size limit),
    - and to constrain the accepted file type before any future processing.
    """
    # 1) Enforce extension-based type check: only .zip files are allowed.
    filename = file.filename or ""
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are allowed")

    # 2) Read file content into memory to enforce a hard size cap (50 MB).
    #    This prevents extremely large uploads from being written to disk.
    content = await file.read()
    max_bytes = 50 * 1024 * 1024  # 50 MB
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    try:
        # 3) Ensure upload directory exists.
        PROJECTS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # 4) Generate a unique file name to avoid collisions.
        unique_name = f"{uuid4().hex}.zip"
        dest_path = PROJECTS_UPLOAD_DIR / unique_name

        # 5) Write the file to disk.
        dest_path.write_bytes(content)

        # 6) Extract whitelisted code files into a per-project folder.
        project_id = unique_name[:-4]  # strip ".zip"
        project_extract_dir = EXTRACTED_PROJECTS_DIR / project_id
        extract_zip(dest_path, project_extract_dir)

        # Persist uploaded project so scanner can restore ownership/history.
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not project:
            project = models.Project(
                id=project_id,
                name=filename,
                owner_id=current_user.id,
                created_at=datetime.utcnow(),
            )
            db.add(project)
            db.commit()

        relative_folder = f"uploads/extracted_projects/{project_id}/"
        log_security_event(
            db=db,
            event_type=SecurityEventType.FILE_UPLOAD,
            severity=SecuritySeverity.LOW,
            payload={"filename": filename, "size_bytes": len(content), "project_id": project_id},
            request=request,
            user_id=current_user.id,
            metadata={"status": "success"},
        )
        return {
            "message": "Upload and extraction successful",
            "project_id": project_id,
            "project_folder": relative_folder,
        }
        
    except HTTPException:
        # Bubble up known HTTP errors unchanged.
        raise
    except Exception:
        # Generic server-side failure.
        raise HTTPException(status_code=500, detail="Failed to save or extract project file")


@router.get("/project/files")
def list_project_files(
    project_id: str = Query(..., description="ID of extracted project folder"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List all source-code files for a previously extracted project, with
    a simple language label per file based on extension.

    This endpoint does *not* perform any vulnerability analysis; it only
    enumerates code files so a later step can run scanners on them.
    """
    _assert_project_access(db, project_id, current_user)
    project_dir = EXTRACTED_PROJECTS_DIR / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project folder does not exist")
    if len(list(project_dir.rglob("*"))) == 0:
        raise HTTPException(status_code=400, detail="Project folder is EMPTY after extraction")
    scan_root = normalize_project_root(project_dir)
    files_info = scan_project_files(scan_root)

    return {
        "project_id": project_id,
        "root_used_for_scan": str(scan_root),
        "total_files": len(files_info),
        "files": files_info,
    }


def _run_dep_scan_background(
    extracted_root: str,
    project_id: str,
    scan_id: Optional[int] = None,
) -> None:
    try:
        from ..scanner.dependency_scanner import scan_dependencies

        dep_result = scan_dependencies(extracted_root)
        db = SessionLocal()
        try:
            if scan_id is not None:
                scan_row = (
                    db.query(models.ScanHistory)
                    .filter(models.ScanHistory.id == scan_id)
                    .first()
                )
            else:
                scan_row = (
                    db.query(models.ScanHistory)
                    .filter(models.ScanHistory.project_id == project_id)
                    .order_by(models.ScanHistory.scan_date.desc())
                    .first()
                )
            if scan_row:
                existing = json.loads(scan_row.vuln_summary or "{}")
                existing["dependency_scan"] = dep_result
                scan_row.vuln_summary = json.dumps(existing)
                db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning("Background dep scan error: %s", e)


def _run_full_scan_background(
    scan_id: int,
    project_id: str,
    extracted_root_str: str,
    user_id: int,
) -> None:
    """Runs in a thread pool worker; opens its own DB session."""
    db = SessionLocal()
    scan_root = Path(extracted_root_str)
    project_dir = EXTRACTED_PROJECTS_DIR / project_id
    try:
        result = run_merged_scan(
            scan_root,
            extraction_root=project_dir,
            semgrep_timeout_seconds=45,
        )
        risk = calculate_risk(result["findings"])
        enhanced = result["findings"]
        type_counts = result["summary"]

        vuln_blob: dict[str, Any] = {
            "status": "complete",
            "project_id": project_id,
            "findings": enhanced,
            "summary": type_counts,
            "summary_detail": {
                "vulnerability_counts": _count_by_type(enhanced),
                "severity_counts": _count_by_severity(enhanced),
                "scanner_engines": result.get("scanner_engines", {}),
                "root_used_for_scan": str(scan_root.resolve()),
            },
            "debug": result.get("debug", {}),
            "message": result.get("message"),
            "scanner_engines": result.get("scanner_engines", {}),
        }

        scan_row = db.query(models.ScanHistory).filter(models.ScanHistory.id == scan_id).first()
        if scan_row:
            scan_row.total_vulnerabilities = len(enhanced)
            scan_row.vuln_summary = json.dumps(vuln_blob)
            scan_row.risk_score = risk["total_score"]
            scan_row.risk_level = risk["risk_level"]
            db.commit()

        proj = db.query(models.Project).filter(models.Project.id == project_id).first()
        if proj:
            proj.last_scan_date = datetime.utcnow()
            proj.latest_risk_score = risk["total_score"]
            proj.latest_risk_level = risk["risk_level"]
            proj.total_scans = (proj.total_scans or 0) + 1
            db.commit()

        recalculate_learning_progress(db, user_id)

        dep_thread = threading.Thread(
            target=_run_dep_scan_background,
            args=(str(scan_root), project_id, scan_id),
            daemon=True,
        )
        dep_thread.start()

    except Exception as e:
        logger.exception("Background scan failed")
        try:
            scan_row = db.query(models.ScanHistory).filter(models.ScanHistory.id == scan_id).first()
            if scan_row:
                scan_row.vuln_summary = json.dumps(
                    {
                        "status": "error",
                        "error": str(e)[:500],
                        "findings": [],
                    }
                )
                scan_row.risk_level = "Unknown"
                scan_row.risk_score = 0
                scan_row.total_vulnerabilities = 0
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/project/scan")
async def scan_project(
    project_id: str = Query(..., description="ID of extracted project folder"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    request: Request = None,
):
    """
    Start static analysis in a background thread. Returns immediately with scan_id.
    Poll GET /api/project/scan-status/{scan_id} for results.
    """
    _assert_project_access(db, project_id, current_user)

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = EXTRACTED_PROJECTS_DIR / project_id
    if not project_dir.exists():
        raise HTTPException(
            status_code=400,
            detail="Project files not found. Re-upload the project.",
        )
    if len(list(project_dir.rglob("*"))) == 0:
        raise HTTPException(status_code=400, detail="Project folder is EMPTY after extraction")

    scan_root = normalize_project_root(project_dir)

    if not project.owner_id:
        project.owner_id = current_user.id
        db.flush()

    pending_summary = {"status": "pending", "findings": [], "summary": {}}
    scan_row = models.ScanHistory(
        project_id=project_id,
        total_vulnerabilities=0,
        risk_score=0,
        risk_level="Unknown",
        vuln_summary=json.dumps(pending_summary),
    )
    db.add(scan_row)
    db.commit()
    db.refresh(scan_row)
    scan_id = scan_row.id

    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        SCAN_EXECUTOR,
        _run_full_scan_background,
        scan_id,
        project_id,
        str(scan_root.resolve()),
        current_user.id,
    )

    log_security_event(
        db=db,
        event_type=SecurityEventType.PROJECT_SCAN,
        severity=SecuritySeverity.LOW,
        payload={"project_id": project_id, "scan_id": scan_id},
        request=request,
        user_id=current_user.id,
        metadata={"status": "pending_async"},
    )

    return {
        "scan_id": scan_id,
        "project_id": project_id,
        "status": "pending",
        "message": "Scan started. Poll GET /api/project/scan-status/{scan_id} for results.",
        "estimated_seconds": 30,
    }


@router.get("/project/scan-status/{scan_id}")
def get_scan_status(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    scan_row = db.query(models.ScanHistory).filter(models.ScanHistory.id == scan_id).first()
    if not scan_row:
        raise HTTPException(status_code=404, detail="Scan not found")

    _assert_project_access(db, scan_row.project_id, current_user)

    summary = json.loads(scan_row.vuln_summary or "{}")
    status = summary.get("status", "pending")

    if status == "pending":
        return {
            "scan_id": scan_id,
            "status": "pending",
            "message": "Scan is running...",
            "progress": None,
        }

    if status == "error":
        return {
            "scan_id": scan_id,
            "status": "error",
            "error": summary.get("error", "Unknown error"),
        }

    dep_scan = summary.get("dependency_scan")
    dep_status = "complete" if dep_scan is not None else "pending"
    dep_note = (
        None
        if dep_status == "complete"
        else "Dependency scan is still running. Refresh in 15 seconds for dependency results."
    )

    scanner_engines = summary.get("scanner_engines") or (
        (summary.get("summary_detail") or {}).get("scanner_engines") or {}
    )

    return {
        "scan_id": scan_id,
        "status": "complete",
        "project_id": scan_row.project_id,
        "total_vulnerabilities": scan_row.total_vulnerabilities,
        "risk_level": scan_row.risk_level,
        "risk": {
            "total_score": scan_row.risk_score,
            "risk_level": scan_row.risk_level,
        },
        "findings": summary.get("findings", []),
        "summary": summary.get("summary", {}),
        "debug": summary.get("debug", {}),
        "scanner_engines": scanner_engines,
        "dependency_scan": dep_scan if dep_scan is not None else {},
        "dependency_scan_status": dep_status,
        "dependency_scan_note": dep_note,
        "message": summary.get("message"),
    }


class ScanFromGitBody(BaseModel):
    repo_url: str = Field(..., min_length=1)
    branch: str = "main"


def _validate_git_repo_url(repo_url: str) -> str:
    u = (repo_url or "").strip()
    forbidden = [";", "&&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r", "\\"]
    for ch in forbidden:
        if ch in u:
            raise HTTPException(
                status_code=400,
                detail="Invalid repository URL. Only HTTPS URLs to public repositories are supported.",
            )
    if not (u.startswith("https://") or u.startswith("git@")):
        raise HTTPException(
            status_code=400,
            detail="Invalid repository URL. Only HTTPS URLs to public repositories are supported.",
        )
    host = ""
    if u.startswith("https://"):
        parsed = urlparse(u)
        host = (parsed.hostname or "").lower()
    else:
        m = re.match(r"^git@([^:]+):", u)
        host = (m.group(1).lower() if m else "")
    allowed_hosts = {"github.com", "gitlab.com", "bitbucket.org"}
    if host in allowed_hosts:
        return u
    if host and re.search(r"\.[a-z]{2,}$", host):
        return u
    raise HTTPException(
        status_code=400,
        detail="Invalid repository URL. Only HTTPS URLs to public repositories are supported.",
    )


def _count_repo_files_and_size(repo_path: str) -> tuple[int, int]:
    total_size = 0
    nfiles = 0
    for dirpath, _, filenames in os.walk(repo_path):
        for fname in filenames:
            fp = os.path.join(dirpath, fname)
            try:
                total_size += os.path.getsize(fp)
            except OSError:
                pass
            nfiles += 1
    return nfiles, total_size


@router.post("/project/scan-from-git")
async def scan_from_git(
    body: ScanFromGitBody,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    request: Request = None,
):
    repo_url = _validate_git_repo_url(body.repo_url)
    branch_requested = (body.branch or "main").strip() or "main"
    branch_used = branch_requested

    temp_dir = tempfile.mkdtemp(prefix="scale_git_")
    repo_dest = os.path.join(temp_dir, "repo")
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}

    def _clone(br: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--single-branch",
                "--branch",
                br,
                "--no-tags",
                repo_url,
                repo_dest,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

    result = _clone(branch_requested)
    if result.returncode != 0:
        err = ((result.stderr or "") + (result.stdout or "")).lower()
        if branch_requested == "main" and (
            "not found" in err or "does not exist" in err
        ):
            branch_used = "master"
            result = _clone("master")
        if result.returncode != 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            error_msg = (result.stderr or result.stdout or "unknown error")[:300]
            raise HTTPException(status_code=400, detail=f"Git clone failed: {error_msg}")

    files_cloned, total_size = _count_repo_files_and_size(repo_dest)
    if total_size > 100 * 1024 * 1024:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=400,
            detail=(
                "Repository is too large (>100MB). Please upload a specific subdirectory as a ZIP instead."
            ),
        )

    git_dir = os.path.join(repo_dest, ".git")
    if os.path.isdir(git_dir):
        shutil.rmtree(git_dir, ignore_errors=True)

    PROJECTS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    zip_name = f"{uuid4().hex}.zip"
    zip_path = PROJECTS_UPLOAD_DIR / zip_name
    zip_base = str(zip_path.with_suffix(""))
    shutil.make_archive(zip_base, "zip", temp_dir, "repo")
    shutil.rmtree(temp_dir, ignore_errors=True)

    project_id = zip_name[:-4]
    project_extract_dir = EXTRACTED_PROJECTS_DIR / project_id
    try:
        extract_zip(zip_path, project_extract_dir)
    except HTTPException:
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)
        if project_extract_dir.exists():
            shutil.rmtree(project_extract_dir, ignore_errors=True)
        raise

    repo_name = repo_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    if repo_name.startswith("git@"):
        repo_name = repo_name.split(":")[-1].split("/")[-1]
    display_name = f"{repo_name} (git)"

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        project = models.Project(
            id=project_id,
            name=display_name,
            owner_id=current_user.id,
            created_at=datetime.utcnow(),
        )
        db.add(project)
        db.commit()

    scan_root = normalize_project_root(project_extract_dir)

    pending_summary = {"status": "pending", "findings": [], "summary": {}}
    scan_row = models.ScanHistory(
        project_id=project_id,
        total_vulnerabilities=0,
        risk_score=0,
        risk_level="Unknown",
        vuln_summary=json.dumps(pending_summary),
    )
    db.add(scan_row)
    db.commit()
    db.refresh(scan_row)
    new_scan_id = scan_row.id

    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        SCAN_EXECUTOR,
        _run_full_scan_background,
        new_scan_id,
        project_id,
        str(scan_root.resolve()),
        current_user.id,
    )

    log_security_event(
        db=db,
        event_type=SecurityEventType.FILE_UPLOAD,
        severity=SecuritySeverity.LOW,
        payload={
            "repo_url": repo_url[:200],
            "project_id": project_id,
            "branch": branch_used,
            "scan_id": new_scan_id,
        },
        request=request,
        user_id=current_user.id,
        metadata={"status": "git_clone_scan_async"},
    )

    return {
        "scan_id": new_scan_id,
        "project_id": project_id,
        "project_name": display_name,
        "repo_url": repo_url,
        "branch": branch_used,
        "files_cloned": files_cloned,
        "total_size_kb": max(1, total_size // 1024),
        "scan_started": True,
        "status": "pending",
        "message": "Repository cloned and scan initiated. Poll GET /api/project/scan-status/{scan_id} for results.",
        "estimated_seconds": 30,
    }


@router.get("/project/report")
def get_project_report(
    project_id: str = Query(..., description="ID of extracted project folder"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generate a structured security report JSON for a project.

    This is the reporting layer: it takes raw detection + scoring results
    and shapes them into something suitable for stakeholders and tooling.
    """
    _assert_project_access(db, project_id, current_user)
    project_dir = EXTRACTED_PROJECTS_DIR / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project folder does not exist")
    if len(list(project_dir.rglob("*"))) == 0:
        raise HTTPException(status_code=400, detail="Project folder is EMPTY after extraction")
    scan_root = normalize_project_root(project_dir)
    files = scan_project_files(scan_root)
    scan_result = scan_project_for_vulnerabilities(scan_root, extraction_root=project_dir)
    risk = calculate_risk(scan_result["findings"])

    report = generate_security_report(
        project_id=project_id,
        findings=scan_result["findings"],
        risk_data=risk,
        files=files,
    )

    return report


@router.get("/project/report/pdf")
def get_project_report_pdf(
    project_id: str = Query(..., description="ID of extracted project folder"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generate and download a PDF version of the security report.

    Detection and scoring happen first; this step is purely about formatting
    and export so that results can be shared with non-technical stakeholders.
    """
    _assert_project_access(db, project_id, current_user)
    project_dir = EXTRACTED_PROJECTS_DIR / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project folder does not exist")
    if len(list(project_dir.rglob("*"))) == 0:
        raise HTTPException(status_code=400, detail="Project folder is EMPTY after extraction")
    scan_root = normalize_project_root(project_dir)
    files = scan_project_files(scan_root)
    scan_result = scan_project_for_vulnerabilities(scan_root, extraction_root=project_dir)
    risk = calculate_risk(scan_result["findings"])

    report = generate_security_report(
        project_id=project_id,
        findings=scan_result["findings"],
        risk_data=risk,
        files=files,
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = REPORTS_DIR / f"{project_id}_security_report.pdf"
    generate_pdf_report(report, pdf_path)

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{project_id}_security_report.pdf",
    )


@router.post("/project/scan/ai")
def scan_project_with_ai(
    project_id: str = Query(..., description="ID of extracted project folder"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Run the normal rule-based scan, then enrich up to N findings with AI mentoring.

    The AI mentor is an optional, separate layer that:
    - explains findings in depth,
    - describes realistic attack scenarios,
    - and suggests secure refactorings.
    Detection and scoring logic remain rule-based and deterministic.
    """
    if not _openai_key() and not serper_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "AI scan is not available. Set OPENAI_API_KEY and/or SERPER_API_KEY in your .env file. "
                "Use the standard scan endpoint instead: POST /api/project/scan"
            ),
        )
    _assert_project_access(db, project_id, current_user)
    project_dir = EXTRACTED_PROJECTS_DIR / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project folder does not exist")
    if len(list(project_dir.rglob("*"))) == 0:
        raise HTTPException(status_code=400, detail="Project folder is EMPTY after extraction")
    scan_root = normalize_project_root(project_dir)
    scan_result = scan_project_for_vulnerabilities(scan_root, extraction_root=project_dir)

    findings = scan_result["findings"]
    enhanced = []

    # Limit AI calls to avoid excessive cost/latency.
    max_ai_findings = 5

    for idx, f in enumerate(findings):
        enriched = {
            "file": f.get("file"),
            "line": f.get("line"),
            "vulnerability_type": f.get("vulnerability_type"),
            "severity": f.get("severity"),
            "code_snippet": f.get("code_snippet"),
            "rule_based_fix": f.get("fix"),
        }

        if idx < max_ai_findings:
            ai_data = generate_ai_security_feedback(f)
            enriched["ai_analysis"] = ai_data or None
        else:
            enriched["ai_analysis"] = None

        enhanced.append(enriched)

    return {
        "project_id": project_id,
        "findings": enhanced,
    }


@router.get("/user/projects")
def list_user_projects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return a summary of projects for the current user.

    For now, ownership is optional; if projects have no owner_id set they
    will not appear here until a dedicated project-management flow assigns them.
    """
    projects = (
        db.query(models.Project)
        .filter(models.Project.owner_id == current_user.id)
        .order_by(models.Project.created_at.desc())
        .all()
    )

    result = []
    for p in projects:
        # Look up latest scan history for total vulnerabilities.
        last_scan = (
            db.query(models.ScanHistory)
            .filter(models.ScanHistory.project_id == p.id)
            .order_by(models.ScanHistory.scan_date.desc())
            .first()
        )
        result.append(
            {
                "project_id": p.id,
                "name": p.name,
                "latest_risk_level": p.latest_risk_level,
                "latest_risk_score": p.latest_risk_score,
                "total_vulnerabilities": last_scan.total_vulnerabilities if last_scan else 0,
                "last_scan_date": (p.last_scan_date.isoformat() if p.last_scan_date else None),
            }
        )

    return {
        "total_projects": len(projects),
        "projects": result,
    }


@router.get("/project/analytics")
def project_analytics(
    project_id: str = Query(..., description="ID of project"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return risk and vulnerability trends over time for a single project.
    """
    _assert_project_access(db, project_id, current_user)
    history = (
        db.query(models.ScanHistory)
        .filter(models.ScanHistory.project_id == project_id)
        .order_by(models.ScanHistory.scan_date.asc())
        .all()
    )

    risk_trend = [
        {"date": h.scan_date.date().isoformat(), "risk_score": h.risk_score} for h in history
    ]
    vulnerability_trend = [
        {"date": h.scan_date.date().isoformat(), "total": h.total_vulnerabilities} for h in history
    ]

    return {
        "project_id": project_id,
        "risk_trend": risk_trend,
        "vulnerability_trend": vulnerability_trend,
    }


@router.get("/project/{project_id}")
def get_project_by_id(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _assert_project_access(db, project_id, current_user)
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = EXTRACTED_PROJECTS_DIR / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project files not found")

    latest_scan = (
        db.query(models.ScanHistory)
        .filter(models.ScanHistory.project_id == project_id)
        .order_by(models.ScanHistory.scan_date.desc())
        .first()
    )

    return {
        "project_id": project.id,
        "name": project.name,
        "owner_id": project.owner_id,
        "created_at": project.created_at,
        "last_scan_date": project.last_scan_date,
        "latest_risk_score": project.latest_risk_score,
        "latest_risk_level": project.latest_risk_level,
        "total_scans": project.total_scans or 0,
        "last_scan_summary": json.loads(latest_scan.vuln_summary) if latest_scan and latest_scan.vuln_summary else {},
        "project_path_exists": True,
    }


@router.get("/project/{project_id}/dependencies")
def get_project_dependencies(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _assert_project_access(db, project_id, current_user)
    latest_scan = (
        db.query(models.ScanHistory)
        .filter(models.ScanHistory.project_id == project_id)
        .order_by(models.ScanHistory.scan_date.desc())
        .first()
    )
    if not latest_scan or not latest_scan.vuln_summary:
        raise HTTPException(status_code=404, detail="No scan found for this project.")
    try:
        summary = json.loads(latest_scan.vuln_summary)
    except Exception:
        raise HTTPException(status_code=404, detail="No scan found for this project.")
    return summary.get("dependency_scan", {})


@router.get("/admin/overview")
def admin_overview(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
):
    """
    Global admin analytics across all projects.

    This aggregates project and scan history data to give a high-level
    security posture view for the organization.
    """
    total_projects = db.query(models.Project).count()
    total_scans = db.query(models.ScanHistory).count()

    # Average risk score across all scans.
    avg_risk_row = db.query(func.avg(models.ScanHistory.risk_score)).one()
    average_risk_score = float(avg_risk_row[0] or 0.0)

    high_risk_projects = (
        db.query(models.Project)
        .filter(models.Project.latest_risk_level == "High")
        .count()
    )

    # Aggregate vulnerability types from stored summaries.
    top_vuln_types: dict[str, int] = {}
    all_summaries = db.query(models.ScanHistory.vuln_summary).all()
    for (summary_text,) in all_summaries:
        if not summary_text:
            continue
        try:
            data = json.loads(summary_text)
        except Exception:
            continue
        for vtype, count in data.items():
            top_vuln_types[vtype] = top_vuln_types.get(vtype, 0) + int(count)

    return {
        "total_projects": total_projects,
        "total_scans": total_scans,
        "average_risk_score": round(average_risk_score, 2),
        "high_risk_projects": high_risk_projects,
        "top_vulnerability_types": top_vuln_types,
    }

