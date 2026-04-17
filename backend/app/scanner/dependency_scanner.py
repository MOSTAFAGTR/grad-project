"""
Dependency manifest discovery and OSV-based vulnerability lookup.
"""
from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

MAX_DEPS_TO_QUERY = 50
MAX_WORKERS = 10

# --- manifest parsers ---


def parse_requirements_txt(file_path: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("-r") or line.startswith("--"):
                continue
            if "==" in line:
                parts = line.split("==", 1)
                name = parts[0].strip()
                version = parts[1].strip()
            elif ">=" in line:
                name = line.split(">=", 1)[0].strip()
                version = "latest"
            elif "<=" in line:
                name = line.split("<=", 1)[0].strip()
                version = "latest"
            elif "~=" in line:
                name = line.split("~=", 1)[0].strip()
                version = "latest"
            elif "!=" in line:
                name = line.split("!=", 1)[0].strip()
                version = "latest"
            else:
                name = line.strip()
                version = "latest"
            if name:
                out.append({"package": name.lower(), "version": version, "ecosystem": "PyPI"})
    return out


def parse_package_json(file_path: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.loads(f.read())
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        block = data.get(key)
        if not isinstance(block, dict):
            continue
        for package_name, version_string in block.items():
            if not isinstance(version_string, str):
                continue
            cleaned = version_string.strip()
            for prefix in ("^", "~", ">=", "<=", ">", "<"):
                while cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix) :].lstrip()
            semver_ok = bool(re.match(r"^\d+\.\d+", cleaned))
            version = cleaned if semver_ok else "latest"
            out.append({"package": package_name, "version": version, "ecosystem": "npm"})
    return out


def parse_pipfile(file_path: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    section: str | None = None
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if re.match(r"^\[packages\]", line, re.I):
                section = "packages"
                continue
            if re.match(r"^\[dev-packages\]", line, re.I):
                section = "dev-packages"
                continue
            if line.startswith("["):
                section = None
                continue
            if section not in ("packages", "dev-packages"):
                continue
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*=\s*(.+)$", line)
            if not m:
                continue
            pkg = m.group(1).strip()
            rhs = m.group(2).strip().strip('"').strip("'")
            if rhs == "*":
                ver = "latest"
            else:
                rhs_clean = rhs
                for op in ("==", ">=", "<=", "~=", "!=", ">"):
                    if op in rhs_clean:
                        rhs_clean = rhs_clean.split(op, 1)[-1].strip()
                ver = rhs_clean if rhs_clean else "latest"
            out.append({"package": pkg.lower(), "version": ver, "ecosystem": "PyPI"})
    return out


def parse_pom_xml(file_path: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    for block in re.findall(r"<dependency>[\s\S]*?</dependency>", text, re.I):
        gid_m = re.search(r"<groupId>([^<]+)</groupId>", block, re.I)
        aid_m = re.search(r"<artifactId>([^<]+)</artifactId>", block, re.I)
        ver_m = re.search(r"<version>([^<]+)</version>", block, re.I)
        if not gid_m or not aid_m:
            continue
        group = gid_m.group(1).strip()
        artifact = aid_m.group(1).strip()
        version = ver_m.group(1).strip() if ver_m else "latest"
        name = f"{group}:{artifact}"
        out.append({"package": name, "version": version, "ecosystem": "Maven"})
    return out


def parse_composer_json(file_path: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.loads(f.read())
    for key in ("require", "require-dev"):
        block = data.get(key)
        if not isinstance(block, dict):
            continue
        for package_name, version_string in block.items():
            if package_name == "php" or not isinstance(version_string, str):
                continue
            cleaned = version_string.strip()
            for prefix in ("^", "~", ">=", "<=", ">", "<", "!"):
                while cleaned.startswith(prefix):
                    cleaned = cleaned[1:].lstrip()
            semver_ok = bool(re.match(r"^\d+\.\d+", cleaned))
            version = cleaned if semver_ok else "latest"
            out.append({"package": package_name, "version": version, "ecosystem": "Packagist"})
    return out


def find_manifests(extracted_root: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    skip_dir_parts = {"node_modules", ".git", "venv", "__pycache__"}
    basenames = {
        "package.json",
        "requirements.txt",
        "pipfile",
        "pom.xml",
        "build.gradle",
        "composer.json",
    }
    for root, dirs, files in os.walk(extracted_root):
        dirs[:] = [d for d in dirs if d not in skip_dir_parts]
        root_l = root.replace("\\", "/").lower()
        if any(part in skip_dir_parts for part in root_l.split("/")):
            continue
        for fname in files:
            low = fname.lower()
            if low not in basenames:
                continue
            full = os.path.join(root, fname)
            results.append((full, low))
    return results


def _map_severity_rating(rating: str) -> str:
    r = (rating or "").upper()
    if r == "CRITICAL":
        return "Critical"
    if r == "HIGH":
        return "High"
    if r == "MEDIUM":
        return "Medium"
    if r == "LOW":
        return "Low"
    return "Unknown"


def query_osv(package: str, version: str, ecosystem: str) -> list[dict[str, Any]]:
    if not version or version == "latest":
        return []
    payload = {"version": version, "package": {"name": package, "ecosystem": ecosystem}}
    try:
        r = requests.post(
            "https://api.osv.dev/v1/query",
            json=payload,
            timeout=4,
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 200:
            return []
        response = r.json()
    except (requests.Timeout, requests.RequestException, Exception) as exc:
        print(f"OSV query failed for {package}@{version}: {exc}")
        return []

    if not isinstance(response, dict):
        return []
    vulns = response.get("vulns")
    if not isinstance(vulns, list):
        return []

    results: list[dict[str, Any]] = []
    for vuln in vulns:
        if not isinstance(vuln, dict):
            continue
        cve_id = ""
        for alias in vuln.get("aliases") or []:
            if isinstance(alias, str) and alias.startswith("CVE-"):
                cve_id = alias
                break
        if not cve_id:
            cve_id = str(vuln.get("id") or "")

        severity = "Unknown"
        sev_list = vuln.get("severity")
        if isinstance(sev_list, list) and sev_list:
            first = sev_list[0]
            if isinstance(first, dict) and first.get("type") == "CVSS_V3":
                score = first.get("score")
                if isinstance(score, (int, float)):
                    if score >= 9.0:
                        severity = "Critical"
                    elif score >= 7.0:
                        severity = "High"
                    elif score >= 4.0:
                        severity = "Medium"
                    else:
                        severity = "Low"
            elif isinstance(first, dict):
                severity = _map_severity_rating(str(first.get("score") or first.get("rating") or ""))
        if severity == "Unknown":
            db_spec = vuln.get("database_specific") or {}
            if isinstance(db_spec, dict):
                sev_raw = db_spec.get("severity")
                if isinstance(sev_raw, str):
                    severity = _map_severity_rating(sev_raw)

        description = str(vuln.get("summary") or "No description.")

        fixed_in = ""
        for aff in vuln.get("affected") or []:
            if not isinstance(aff, dict):
                continue
            pkg = aff.get("package") or {}
            if isinstance(pkg, dict) and pkg.get("ecosystem") == ecosystem:
                for ev in aff.get("ranges") or []:
                    for event in ev.get("events") or []:
                        if isinstance(event, dict) and "fixed" in event:
                            fixed_in = str(event["fixed"])
                            break
                    if fixed_in:
                        break
            if fixed_in:
                break

        vid = str(vuln.get("id") or "")
        osv_url = f"https://osv.dev/vulnerability/{vid}"
        results.append(
            {
                "package": package,
                "version": version,
                "ecosystem": ecosystem,
                "cve_id": cve_id,
                "severity": severity,
                "description": description,
                "fixed_in": fixed_in,
                "osv_url": osv_url,
            }
        )
    return results


def scan_dependencies(extracted_root: str) -> dict[str, Any]:
    """
    Run the full dependency vulnerability scan on an extracted
    project directory. Returns a dict with dependency findings.
    """
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    manifests_found: list[str] = []

    manifest_files = find_manifests(extracted_root)
    all_deps: list[dict[str, str]] = []

    for file_path, basename in manifest_files:
        manifests_found.append(file_path)
        deps: list[dict[str, str]] = []
        try:
            if basename == "requirements.txt":
                deps = parse_requirements_txt(file_path)
            elif basename == "package.json":
                deps = parse_package_json(file_path)
            elif basename == "pipfile":
                deps = parse_pipfile(file_path)
            elif basename == "pom.xml":
                deps = parse_pom_xml(file_path)
            elif basename == "composer.json":
                deps = parse_composer_json(file_path)
            else:
                deps = []
        except Exception as e:
            errors.append({"file": file_path, "error": str(e)})
            deps = []

        all_deps.extend(deps)

    if len(all_deps) > MAX_DEPS_TO_QUERY:
        all_deps = all_deps[:MAX_DEPS_TO_QUERY]

    def _query_single(dep: dict[str, str]) -> list[dict[str, Any]]:
        try:
            return query_osv(dep["package"], dep["version"], dep["ecosystem"])
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_query_single, dep): dep for dep in all_deps}
        for future in as_completed(futures):
            try:
                vulns = future.result()
                results.extend(vulns)
            except Exception:
                pass

    return {
        "dependency_vulns": results,
        "manifests_scanned": manifests_found,
        "total_dependency_vulns": len(results),
        "errors": errors,
    }
