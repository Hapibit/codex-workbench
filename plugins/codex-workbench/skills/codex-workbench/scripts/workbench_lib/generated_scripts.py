"""Project-side script generators for Codex Workbench.

These functions return standalone scripts that are written into generated
project workbenches. The generated scripts must not import this module.
"""

from __future__ import annotations

import json
from typing import Any


def quote_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def generate_quality_gate_py(
    commands: list[dict[str, Any]],
    feature_package_files: list[str],
    allowed_workbench_top_level_dirs: set[str] | list[str],
    workbench_version: str,
) -> str:
    command_json = quote_json(commands)
    feature_files_json = quote_json(feature_package_files)
    allowed_dirs_json = quote_json(sorted(allowed_workbench_top_level_dirs))
    version_json = json.dumps(workbench_version)
    return f'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

COMMANDS = {command_json}
FEATURE_PACKAGE_FILES = {feature_files_json}
ALLOWED_WORKBENCH_TOP_LEVEL_DIRS = set({allowed_dirs_json})
WORKBENCH_VERSION = {version_json}
WORKFLOW_STAGES = ["CLASSIFY", "BASELINE_CHECK", "CHANGE", "IMPACT", "ROUTE", "PLAN", "IMPLEMENT", "VERIFY", "REVIEW", "GATE", "LEARN", "DONE", "BLOCKED"]
WORKFLOW_PROFILES = {{"light", "standard", "strict", "unclassified"}}
QUALITY_PROFILES = {{"smoke", "standard", "full"}}
FEATURE_STATUSES = {{"active", "on_hold", "complete", "blocked", "failed", "repeated_issue"}}
WORKBENCH_UPGRADE_ASSESSMENTS = {{"required", "deferred", "not_required"}}
CONTROLLED_CODE_DIRS = ("src/", "app/", "server/", "backend/", "frontend/", "db/", "migrations/", "packages/", "services/")
CONTROLLED_CODE_FILES = (
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb",
    "pom.xml", "build.gradle", "settings.gradle", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod"
)
LIGHT_FORBIDDEN_PREFIXES = (
    "db/", "migrations/",
    "workbench/product/", "workbench/design/", "workbench/architecture/",
    "workbench/quality/", "workbench/runtime/", "workbench/feature-template/",
    "workbench/features/", "workbench/scorecard/", "workbench/review/",
)
LIGHT_FORBIDDEN_FILES = {{
    "PROJECT_INTAKE.md", "DEVELOPMENT_FLOW.md", "FEATURE_WORKFLOW.md", "PRODUCT_BASELINE.md",
    "workbench/delivery/TRACEABILITY.md", "workbench/delivery/RELEASE_PLAN.md", "workbench/delivery/RELEASE_CHECKLIST.md",
}}
STRICT_TRIGGER_NONE_VALUES = {{"", "none", "n/a", "na", "no", "false", "无", "无影响", "不需要", "not_required"}}
STRICT_TRIGGER_PATH_PREFIXES = (
    "db/", "migrations/",
    "workbench/architecture/", "workbench/quality/", "workbench/runtime/",
)
STRICT_TRIGGER_PATH_FILES = {{
    "workbench/delivery/TRACEABILITY.md",
    "workbench/delivery/RELEASE_PLAN.md",
    "workbench/delivery/RELEASE_CHECKLIST.md",
}}
STRICT_TRIGGER_TERMS = (
    "auth", "permission", "permissions", "security", "secret", "payment", "privacy",
    "release", "deploy", "migration", "schema", "tenant", "role", "credential",
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel_to(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def read_json(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
        if text.startswith("\\ufeff"):
            text = text.lstrip("\\ufeff")
        return json.loads(text)
    except Exception:
        return {{}}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return "sha256:" + digest.hexdigest()


def text_sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def command_output(root: Path, command: list[str]) -> str:
    try:
        result = subprocess.run(command, cwd=str(root), text=True, capture_output=True, timeout=20)
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.rstrip("\\r\\n")


def git_head(root: Path) -> str:
    return command_output(root, ["git", "rev-parse", "HEAD"]) or "unavailable"


def diff_hash(root: Path) -> str:
    try:
        result = subprocess.run(["git", "diff", "--binary", "HEAD"], cwd=str(root), capture_output=True, timeout=30)
        payload = result.stdout if result.returncode == 0 else b""
    except Exception:
        payload = b""
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def changed_paths(root: Path) -> list[str]:
    output = command_output(root, ["git", "status", "--porcelain", "-z"])
    if not output:
        return []
    paths: list[str] = []
    entries = [entry for entry in output.split("\\0") if entry]
    index = 0
    while index < len(entries):
        entry = entries[index]
        status = entry[:2]
        path = entry[3:] if len(entry) > 3 else ""
        if status.startswith("R") or status.startswith("C"):
            if index + 1 < len(entries):
                index += 1
                path = entries[index]
        if path:
            normalized = path.replace("\\\\", "/")
            candidate = root / normalized
            if normalized.endswith("/") and candidate.exists() and candidate.is_dir():
                for child in candidate.rglob("*"):
                    if child.is_file():
                        paths.append(child.relative_to(root).as_posix())
            else:
                paths.append(normalized)
        index += 1
    return paths


def is_controlled_path(path: str) -> bool:
    normalized = path.replace("\\\\", "/").lstrip("./")
    if not normalized or normalized.startswith(".workbench-validation/"):
        return False
    if normalized.startswith("workbench/"):
        return True
    if normalized in {{
        "AGENTS.md", "WORKBENCH.md", "REVIEW.md", "PROJECT_INTAKE.md", "PROJECT_STATE.md",
        "DEVELOPMENT_FLOW.md", "PRODUCT_BASELINE.md", "FEATURE_WORKFLOW.md",
    }}:
        return True
    if normalized in CONTROLLED_CODE_FILES:
        return True
    return normalized.startswith(CONTROLLED_CODE_DIRS)


def controlled_changed_paths(root: Path) -> list[str]:
    return [path for path in changed_paths(root) if is_controlled_path(path)]


def path_is_within(path: str, scope: str) -> bool:
    normalized_path = path.replace("\\\\", "/").lstrip("./")
    normalized_scope = scope.replace("\\\\", "/").lstrip("./").rstrip("/")
    if not normalized_path or not normalized_scope:
        return False
    return normalized_path == normalized_scope or normalized_path.startswith(normalized_scope + "/")


def declared_feature_paths(*texts: str) -> list[str]:
    candidates: set[str] = set()
    pattern = re.compile(r"`([^`]+)`|((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+|[A-Za-z0-9_.-]+\\.(?:json|toml|md|xml|lock|yaml|yml|py|js|ts|tsx|jsx|java|go|rs|sql))")
    allowed_prefixes = CONTROLLED_CODE_DIRS + (
        "workbench/product/", "workbench/design/", "workbench/architecture/", "workbench/delivery/",
        "workbench/quality/", "workbench/runtime/", "workbench/scorecard/", "workbench/review/", "workbench/feedback/",
    )
    allowed_files = set(CONTROLLED_CODE_FILES) | {{
        "AGENTS.md", "WORKBENCH.md", "REVIEW.md", "PROJECT_INTAKE.md", "PROJECT_STATE.md",
        "DEVELOPMENT_FLOW.md", "PRODUCT_BASELINE.md", "FEATURE_WORKFLOW.md",
    }}
    for text in texts:
        for match in pattern.finditer(text or ""):
            raw = match.group(1) or match.group(2) or ""
            normalized = raw.strip().strip(".,;)").replace("\\\\", "/").lstrip("./")
            if not normalized or is_placeholder_cell(normalized):
                continue
            if normalized in allowed_files or normalized.startswith(allowed_prefixes):
                candidates.add(normalized)
    return sorted(candidates)


def feature_covers_controlled_path(root: Path, package: Path, controlled_path: str) -> bool:
    package_prefix = rel_to(root, package).rstrip("/") + "/"
    normalized = controlled_path.replace("\\\\", "/").lstrip("./")
    if normalized.startswith(package_prefix):
        return True
    texts = []
    for filename in ("CHANGE_REQUEST.md", "IMPACT_ANALYSIS.md", "PLAN.md", "TASKS.md", "DESIGN.md"):
        path = package / filename
        if path.exists():
            texts.append(read_text(path))
    declared = declared_feature_paths(*texts)
    return any(path_is_within(normalized, scope) or path_is_within(scope, normalized) for scope in declared)


def feature_covered_controlled_paths(root: Path, checked_features: list[str], controlled_paths: list[str]) -> list[str]:
    covered: list[str] = []
    for checked_feature in checked_features:
        feature_rel = checked_feature.split(" ", 1)[0]
        package = root / feature_rel
        if not package.exists():
            continue
        for controlled_path in controlled_paths:
            if controlled_path in covered:
                continue
            if feature_covers_controlled_path(root, package, controlled_path):
                covered.append(controlled_path)
    return covered


def is_light_allowed_path(path: str) -> bool:
    normalized = path.replace("\\\\", "/").lstrip("./")
    if normalized in LIGHT_FORBIDDEN_FILES:
        return False
    if normalized.startswith(LIGHT_FORBIDDEN_PREFIXES):
        return False
    lowered = normalized.lower()
    if any(term in lowered for term in ("auth", "permission", "permissions", "security", "secret", "payment", "privacy", "release", "deploy")):
        return False
    return True


def load_light_change_records(root: Path) -> list[dict]:
    path = root / "workbench" / "delivery" / "CHANGE_LOG.md"
    if not path.exists():
        return []
    text = read_text(path)
    records: list[dict] = []
    for match in re.finditer(r"(?ms)^```(?:json|JSON)\\s*(\\{{.*?\\}})\\s*```", text):
        try:
            data = json.loads(match.group(1))
        except Exception:
            continue
        if isinstance(data, dict):
            records.append(data)
    return records


def has_valid_light_change_record(root: Path, controlled_paths: list[str]) -> bool:
    if not controlled_paths or any(not is_light_allowed_path(path) for path in controlled_paths):
        return False
    for record in load_light_change_records(root):
        if str(record.get("workflow_profile") or record.get("risk") or "").lower() != "light":
            continue
        if str(record.get("status") or "").lower() not in {{"ready", "verified", "passed", "complete"}}:
            continue
        required = ("change_id", "scope", "risk", "validation", "evidence", "reviewer", "gate_marker")
        if any(not valid_light_value(record.get(field)) for field in required if field != "scope"):
            continue
        if not str(record.get("gate_marker") or "").startswith(".workbench-validation/"):
            continue
        if valid_light_scope(record.get("scope") or record.get("paths"), controlled_paths):
            return True
    return False


def run_scorecard(root: Path, profile: str) -> dict:
    script = root / "workbench" / "scorecard" / "scorecard.py"
    if not script.exists():
        raise SystemExit("[quality] scorecard.py is missing. Generate or upgrade workbench/scorecard before trusting evidence reporting.")
    command = [sys.executable, str(script), "--profile", profile, "--write-report", "--called-from-quality-gate", "--enforce-blockers"]
    print("[quality] scorecard evidence report")
    result = subprocess.run(command, cwd=str(root), text=True)
    if result.returncode != 0:
        raise SystemExit(f"[quality] scorecard found blocking evidence gaps (exit {{result.returncode}})")
    report = read_json(root / ".workbench-validation" / "scorecard-report.json")
    return report if isinstance(report, dict) else {{}}


def run_step(root: Path, step: dict) -> None:
    name = step["name"]
    group = step.get("group", "default")
    cwd = root / step.get("cwd", ".")
    command = step["command"]
    exe = command[0]
    if shutil.which(exe) is None:
        raise SystemExit(f"[quality] missing command for {{name}}: {{exe}}")
    print(f"[quality] {{name}}")
    result = subprocess.run(command, cwd=str(cwd), text=True)
    if result.returncode != 0:
        raise SystemExit(f"[quality] failed: {{name}} (exit {{result.returncode}})")


def check_project_intake(root: Path) -> str | None:
    intake = root / "PROJECT_INTAKE.md"
    if not intake.exists():
        return None
    text = intake.read_text(encoding="utf-8", errors="replace")
    if re.search(r"(?im)^\\s*status\\s*:\\s*draft\\s*$", text):
        raise SystemExit("[quality] PROJECT_INTAKE.md is still draft. Confirm project intake before relying on this workbench for feature or high-risk work.")
    if re.search(r"(?im)^\\|\\s*P\\d+\\s*\\|.*\\|\\s*open\\s*\\|\\s*$", text):
        raise SystemExit("[quality] PROJECT_INTAKE.md has open blocking project-intake questions.")
    return str(intake.relative_to(root))


def check_directory_contract(root: Path) -> list[str]:
    workbench = root / "workbench"
    if not workbench.exists():
        return []
    for child in sorted(workbench.iterdir(), key=lambda item: item.name.lower()):
        if child.is_dir() and child.name not in ALLOWED_WORKBENCH_TOP_LEVEL_DIRS:
            raise SystemExit(
                f"[quality] undeclared workbench directory {{child.relative_to(root)}}. "
                "Move it under a declared directory, document it in WORKBENCH.md, or upgrade the workbench directory contract."
            )
        if child.is_file():
            raise SystemExit(
                f"[quality] unexpected file directly under workbench/: {{child.relative_to(root)}}. "
                "Put durable evidence in a declared subdirectory."
            )
    return ["workbench directory contract"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_field(text: str, name: str) -> str | None:
    match = re.search(rf"(?im)^\\s*{{re.escape(name)}}\\s*:\\s*(.+?)\\s*$", text)
    return match.group(1).strip() if match else None


def read_bool(text: str, name: str) -> bool:
    return (read_field(text, name) or "").lower() == "true"


def read_int(text: str, name: str) -> int | None:
    value = read_field(text, name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def is_placeholder_value(value: str | None) -> bool:
    return value is None or value.strip().lower() in {{"", "unclassified", "待填写", "todo", "tbd"}}


def is_placeholder_cell(value: str | None) -> bool:
    if value is None:
        return True
    normalized = value.strip().strip("`").lower()
    return normalized in ("", "todo", "tbd", "n/a", "na", "none", "unconfirmed", "unclassified", "unknown", "待填写", "无")


def valid_light_value(value: object) -> bool:
    return isinstance(value, str) and not is_placeholder_cell(value)


def valid_light_scope(scope: object, controlled_paths: list[str]) -> bool:
    if isinstance(scope, str):
        scope_items = [scope]
    elif isinstance(scope, list):
        scope_items = [str(item) for item in scope]
    else:
        return False
    normalized_scope = [item.replace("\\\\", "/").strip("./") for item in scope_items if not is_placeholder_cell(str(item))]
    if not normalized_scope:
        return False
    if any(item in ("*", "all", "**", ".") for item in [scope.lower() for scope in normalized_scope]):
        return False
    return all(any(path == item or path.startswith(item.rstrip("/") + "/") for item in normalized_scope) for path in controlled_paths)


def non_none_trigger_value(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().strip("`").lower()
    return normalized not in STRICT_TRIGGER_NONE_VALUES and not is_placeholder_cell(normalized)


def checked_strict_trigger_lines(spec_text: str) -> list[str]:
    section = section_between(spec_text, "流程强度", "风险分数")
    lines: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if re.match(r"(?i)^-\\s*\\[[xX]\\]", stripped):
            lines.append(stripped)
    return lines


def impact_route_value(text: str, name: str) -> str:
    value = read_field(text, name)
    if value:
        return value.strip()
    match = re.search(r"(?im)^[ \\t]*-[ \\t]*" + re.escape(name) + r"[ \\t]*[:：][ \\t]*([^\\r\\n]*)[ \\t]*$", text)
    return match.group(1).strip() if match else ""


def strict_trigger_reasons(root: Path, package: Path, spec_text: str, impact_text: str, controlled_paths: list[str]) -> list[str]:
    reasons: list[str] = []
    hard_triggers = read_field(spec_text, "hard_triggers")
    if non_none_trigger_value(hard_triggers):
        reasons.append("SPEC.md hard_triggers is not none")
    if checked_strict_trigger_lines(spec_text):
        reasons.append("SPEC.md has checked hard trigger items")
    for name in ("strict 触发器", "strict_triggers", "数据迁移", "权限", "AI/RAG/Agent", "CI/CD", "配置", "依赖"):
        if non_none_trigger_value(impact_route_value(impact_text, name)):
            reasons.append(f"IMPACT_ANALYSIS.md {{name}} is not none")
            break
    package_prefix = rel_to(root, package).rstrip("/") + "/"
    for raw_path in controlled_paths:
        normalized = raw_path.replace("\\\\", "/").lstrip("./")
        if normalized.startswith(package_prefix):
            continue
        if normalized in STRICT_TRIGGER_PATH_FILES or normalized.startswith(STRICT_TRIGGER_PATH_PREFIXES):
            reasons.append(f"changed high-risk path {{normalized}}")
            break
        lowered = normalized.lower()
        if any(term in lowered for term in STRICT_TRIGGER_TERMS):
            reasons.append(f"changed strict-trigger path {{normalized}}")
            break
    return sorted(set(reasons))


EVIDENCE_MARKERS = (
    "passed",
    "pass",
    "success",
    "ok",
    "通过",
    "成功",
    ".workbench-validation",
    ".json",
    ".xml",
    ".log",
    ".txt",
    ".png",
    ".jpg",
    ".webm",
    "pytest",
    "vitest",
    "jest",
    "playwright",
    "pa11y",
    "axe",
    "npm run",
    "pnpm",
    "mvn",
    "gradle",
    "curl",
    "ci",
)
RESULT_MARKERS = ("passed", "pass", "success", "ok", "通过", "成功")
LOCAL_EVIDENCE_RE = r"(?<![A-Za-z0-9_./-])((?:\\.workbench-validation|workbench|reports?|test-results?|playwright-report|coverage|screenshots?)/[^\\s|`<>\\x22\\x27]+)"
EXTERNAL_EVIDENCE_RE = r"https?://[^\\s|`<>\\x22\\x27]+"


def markdown_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if all(re.fullmatch(r"[-:]+", cell.replace(" ", "")) and "---" in cell for cell in cells):
            continue
        rows.append(cells)
    return rows


def checked_line(text: str, label: str) -> bool:
    return bool(re.search(r"(?im)^\\s*-\\s*\\[[xX]\\]\\s*" + re.escape(label), text))


def section_between(text: str, start_heading: str, end_heading: str | None = None) -> str:
    start = re.search(r"(?im)^##\\s+" + re.escape(start_heading) + r"\\s*$", text)
    if not start:
        return ""
    body = text[start.end():]
    if end_heading:
        end = re.search(r"(?im)^##\\s+" + re.escape(end_heading) + r"\\s*$", body)
        if end:
            return body[:end.start()]
    return body


def has_verification_evidence(verify_text: str) -> bool:
    for cells in markdown_table_rows(verify_text):
        if cells and cells[0] in ("命令", "场景", "项目", "问题"):
            continue
        non_placeholder = [cell for cell in cells if not is_placeholder_cell(cell)]
        if len(non_placeholder) < 3:
            continue
        joined = " ".join(non_placeholder).lower()
        has_result = any(marker in joined for marker in RESULT_MARKERS)
        has_local_artifact = bool(re.search(LOCAL_EVIDENCE_RE, joined))
        has_external_artifact = bool(re.search(EXTERNAL_EVIDENCE_RE, joined)) and any(term in joined for term in ("ci", "github", "actions", "jenkins", "build", "report", "log", "artifact", "run"))
        if has_result and (has_local_artifact or has_external_artifact):
            return True
    return False


def local_evidence_paths_from_text(text: str) -> list[str]:
    paths: list[str] = []
    for match in re.finditer(LOCAL_EVIDENCE_RE, text):
        value = match.group(1).strip().rstrip(".,;)")
        if value and not is_placeholder_cell(value):
            normalized = value.replace("\\\\", "/")
            if normalized.startswith("./"):
                normalized = normalized[2:]
            paths.append(normalized)
    return sorted(set(paths))


def local_evidence_paths(root: Path, verify_text: str) -> list[str]:
    paths: list[str] = []
    for cells in markdown_table_rows(verify_text):
        if cells and cells[0] in ("命令", "场景", "项目", "问题"):
            continue
        for cell in cells:
            paths.extend(local_evidence_paths_from_text(cell))
    return sorted(set(paths))


def missing_local_evidence_paths(root: Path, verify_text: str) -> list[str]:
    missing: list[str] = []
    for rel in local_evidence_paths(root, verify_text):
        target = root / rel
        if not target.exists():
            missing.append(rel)
    return missing


def verification_risk_issues(verify_text: str) -> list[str]:
    issues: list[str] = []
    for cells in markdown_table_rows(verify_text):
        if len(cells) < 7:
            continue
        if cells[0] == "项目" or re.fullmatch(r"[-:]+", cells[0].strip()) or all(is_placeholder_cell(cell) for cell in cells[:3]):
            continue
        accepted = cells[3].strip().lower()
        if accepted in ("true", "yes", "是", "accepted"):
            missing = []
            for index, label in ((4, "用户确认"), (5, "替代验证"), (6, "deferred_follow_up")):
                if is_placeholder_cell(cells[index] if len(cells) > index else ""):
                    missing.append(label)
            if missing:
                issues.append(f"{{cells[0]}}: accepted_risk true but missing {{', '.join(missing)}}")
            continue
        issues.append(f"{{cells[0]}}: accepted_risk is not true")
    return issues


def has_accepted_verification_risk(verify_text: str) -> bool:
    for cells in markdown_table_rows(verify_text):
        if len(cells) < 7:
            continue
        if cells[0] == "项目" or re.fullmatch(r"[-:]+", cells[0].strip()) or all(is_placeholder_cell(cell) for cell in cells[:3]):
            continue
        if cells[3].strip().lower() in ("true", "yes", "是", "accepted"):
            return True
    return False


def require_verify_evidence(package: Path, verify_text: str, workflow_profile: str) -> None:
    if (read_field(verify_text, "status") or "").lower() != "passed":
        return
    if not has_verification_evidence(verify_text):
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} VERIFY.md is marked passed but has no machine-readable command, report, screenshot, log, eval, CI, or acceptance evidence.")
    missing_paths = missing_local_evidence_paths(project_root(), verify_text)
    if missing_paths:
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} VERIFY.md references missing local evidence files: {{', '.join(missing_paths[:5])}}")
    if not (checked_line(verify_text, "可以交付。") or checked_line(verify_text, "可以交付")):
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} VERIFY.md is marked passed but delivery conclusion is not checked.")
    if workflow_profile == "strict":
        risk_issues = verification_risk_issues(verify_text)
        if risk_issues:
            raise SystemExit(f"[quality] strict feature {{package.relative_to(project_root())}} has incomplete verification risk acceptance: {{'; '.join(risk_issues[:3])}}")


def unresolved_review_blocker_lines(review_text: str) -> list[str]:
    blockers: list[str] = []
    for line in review_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not (
            re.match(r"(?i)^(?:[-*]\\s*)?P[01]\\b", stripped)
            or re.match(r"(?i)^\\|\\s*P[01]\\s*\\|", stripped)
        ):
            continue
        if "未发现" in stripped or "无未解决" in stripped or re.search(r"(?i)\\bno\\s+(unresolved\\s+)?P[01]\\b", stripped):
            continue
        if re.match(r"(?i)^-\\s*\\[ \\]\\s*存在\\s*P[01]", stripped):
            continue
        lowered = stripped.lower()
        if re.search(r"(?i)\\b(unresolved|not\\s+resolved|open|pending|blocked)\\b", stripped) or any(term in stripped for term in ("未解决", "未修复", "待处理", "阻塞")):
            blockers.append(stripped)
            continue
        if re.search(r"(?i)\\b(status|状态)\\s*[:：]\\s*(resolved|closed|fixed)\\b", stripped) or any(term in stripped for term in ("状态: 已解决", "状态：已解决", "状态: 已修复", "状态：已修复", "状态: 关闭", "状态：关闭")):
            continue
        blockers.append(stripped)
    return blockers


def require_review_evidence(package: Path, review_text: str) -> None:
    if (read_field(review_text, "status") or "").lower() != "passed":
        return
    if not (checked_line(review_text, "未发现 P0/P1。") or checked_line(review_text, "未发现 P0/P1")):
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} REVIEW.md is marked passed but does not check 'no P0/P1'.")
    if checked_line(review_text, "存在 P0/P1，不能交付。") or checked_line(review_text, "存在 P0/P1"):
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} REVIEW.md is marked passed while blocking P0/P1 is checked.")
    p0p1_section = section_between(review_text, "P0/P1 检查", "产品下限检查")
    if re.search(r"(?m)^\\s*-\\s*\\[ \\]", p0p1_section):
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} REVIEW.md is marked passed but P0/P1 checklist still has unchecked items.")
    blockers = unresolved_review_blocker_lines(review_text)
    if blockers:
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} REVIEW.md contains unresolved P0/P1 findings: {{'; '.join(blockers[:3])}}")


def impact_value(text: str, name: str) -> str:
    value = read_field(text, name)
    if value:
        return value.strip()
    match = re.search(r"(?im)^[ \\t]*-[ \\t]*" + re.escape(name) + r"[ \\t]*[:：][ \\t]*([^\\r\\n]*)[ \\t]*$", text)
    return match.group(1).strip() if match else ""


def has_nonimpact_traceability_reason(impact_text: str) -> bool:
    reason = impact_value(impact_text, "不需要更新的理由")
    if not is_placeholder_cell(reason):
        return True
    match = re.search(r"(?ims)^##\\s+后续同步\\s*(.+)$", impact_text)
    return bool(match and "不需要" in match.group(1) and not re.search(r"(?m)^\\s*-\\s*不需要更新的理由\\s*[:：]\\s*$", match.group(1)))


def expected_traceability_ids(impact_text: str) -> list[str]:
    ids: list[str] = []
    for cells in markdown_table_rows(impact_text):
        if len(cells) < 4:
            continue
        item_id = cells[0].strip().strip("`")
        if item_id.upper() == "ID" or is_placeholder_cell(item_id):
            continue
        action = cells[2].strip().lower() if len(cells) > 2 else ""
        if action in ("n/a", "na", "none", "不适用", "无影响"):
            continue
        if re.match(r"^[A-Z]+-[A-Z0-9-]*\\d+", item_id):
            ids.append(item_id)
    return sorted(set(ids))


def require_traceability_evidence(root: Path, package: Path, impact_text: str, workflow_profile: str) -> None:
    if workflow_profile != "strict":
        return
    decision = impact_value(impact_text, "traceability_update_required").lower()
    if is_placeholder_cell(decision):
        raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} must classify traceability_update_required in IMPACT_ANALYSIS.md.")
    requires_update = any(word in decision for word in ("true", "yes", "required", "update", "需要", "更新"))
    no_update = any(word in decision for word in ("false", "no", "not_required", "n/a", "不需要", "无影响"))
    if not requires_update and no_update:
        if not has_nonimpact_traceability_reason(impact_text):
            raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} says traceability is not updated but does not give a non-impact rationale.")
        return
    traceability = root / "workbench" / "delivery" / "TRACEABILITY.md"
    if not traceability.exists():
        raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} requires TRACEABILITY.md but it is missing.")
    rows: dict[str, dict[str, str]] = {{}}
    for cells in markdown_table_rows(read_text(traceability)):
        if len(cells) < 8 or cells[0].strip().lower() == "id":
            continue
        status = cells[6].strip().lower()
        if status in ("covered", "partial", "missing", "n/a"):
            rows[cells[0].strip()] = {{"status": status, "verification": cells[5].strip(), "note": cells[7].strip()}}
    if not rows:
        raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} requires TRACEABILITY.md rows with covered/partial/missing/n/a status.")
    expected_ids = expected_traceability_ids(impact_text)
    if expected_ids:
        absent = [item_id for item_id in expected_ids if item_id not in rows]
        if absent:
            raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} has impacted IDs missing from TRACEABILITY.md: {{', '.join(absent[:5])}}")
        scoped_rows = [(item_id, rows[item_id]["status"], rows[item_id]["verification"], rows[item_id]["note"]) for item_id in expected_ids]
    else:
        scoped_rows = [(item_id, row["status"], row["verification"], row["note"]) for item_id, row in rows.items()]
    missing_ids = [item_id for item_id, status, _, _ in scoped_rows if status == "missing"]
    if missing_ids:
        raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} has missing TRACEABILITY rows: {{', '.join(missing_ids[:5])}}")
    unverifiable_ids = [item_id for item_id, status, verification, _ in scoped_rows if status != "n/a" and is_placeholder_cell(verification)]
    if unverifiable_ids:
        raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} has TRACEABILITY rows without verification location: {{', '.join(unverifiable_ids[:5])}}")
    package_prefix = rel_to(root, package).rstrip("/") + "/"
    stale_feature_refs: list[str] = []
    missing_verification_paths: list[str] = []
    no_verification_artifact: list[str] = []
    for item_id, status, verification, _ in scoped_rows:
        if status == "n/a":
            continue
        local_paths = local_evidence_paths_from_text(verification)
        external_evidence = bool(re.search(EXTERNAL_EVIDENCE_RE, verification)) and any(term in verification.lower() for term in ("ci", "github", "actions", "jenkins", "build", "report", "log", "artifact", "run"))
        if not local_paths and not external_evidence:
            no_verification_artifact.append(item_id)
            continue
        for rel_path in local_paths:
            if rel_path.startswith("workbench/features/") and not rel_path.startswith(package_prefix):
                stale_feature_refs.append(item_id)
            if not (root / rel_path).exists():
                missing_verification_paths.append(f"{{item_id}} -> {{rel_path}}")
    if no_verification_artifact:
        raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} has TRACEABILITY rows without concrete verification artifact paths or CI URLs: {{', '.join(no_verification_artifact[:5])}}")
    if stale_feature_refs:
        raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} TRACEABILITY verification points at another feature package: {{', '.join(stale_feature_refs[:5])}}")
    if missing_verification_paths:
        raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} TRACEABILITY verification paths do not exist: {{', '.join(missing_verification_paths[:5])}}")
    weak_rows = [item_id for item_id, status, _, note in scoped_rows if status in ("partial", "n/a") and is_placeholder_cell(note)]
    if weak_rows:
        raise SystemExit(f"[quality] strict feature {{package.relative_to(root)}} has TRACEABILITY partial/n/a rows without rationale: {{', '.join(weak_rows[:5])}}")


def workflow_stage_index(stage: str) -> int:
    try:
        return WORKFLOW_STAGES.index(stage.upper())
    except ValueError:
        return -1


def stage_reached(current_stage: str, expected_stage: str) -> bool:
    current = workflow_stage_index(current_stage)
    expected = workflow_stage_index(expected_stage)
    return current >= expected and expected >= 0


def require_feature_field(package: Path, filename: str, field: str, expected: str | bool) -> None:
    text = read_text(package / filename)
    value = read_bool(text, field) if isinstance(expected, bool) else (read_field(text, field) or "").lower()
    if value != expected:
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} is not complete: {{filename}} {{field}} must be {{expected}}")


def require_feature_status(package: Path, filename: str, allowed: set[str]) -> str:
    text = read_text(package / filename)
    status = (read_field(text, "status") or "").lower()
    if status not in allowed:
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} has invalid {{filename}} status: {{status or 'missing'}}")
    return status


def check_feature_packages(root: Path) -> list[str]:
    feature_root = root / "workbench" / "features"
    if not feature_root.exists():
        return []
    packages = [item for item in sorted(feature_root.iterdir()) if item.is_dir()]
    controlled_paths = controlled_changed_paths(root)
    checked: list[str] = []
    for package in packages:
        missing = [rel for rel in FEATURE_PACKAGE_FILES if not (package / rel).exists()]
        if missing:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} is missing files: {{', '.join(missing)}}")
        status_json = read_json(package / "FEATURE_STATUS.json")
        if status_json.get("schema") != "codex-workbench-feature-status/v2":
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has missing or invalid FEATURE_STATUS.json schema")
        feature_status = str(status_json.get("feature_status") or "active").lower()
        current_stage = str(status_json.get("current_stage") or "CHANGE").upper()
        workflow_profile = str(status_json.get("workflow_profile") or "unclassified").lower()
        required_artifacts = status_json.get("required_artifacts") if isinstance(status_json.get("required_artifacts"), list) else []
        missing_required_artifacts = [rel for rel in FEATURE_PACKAGE_FILES if rel != "FEATURE_STATUS.json" and rel not in required_artifacts]
        if missing_required_artifacts:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} FEATURE_STATUS.json is missing required_artifacts: {{', '.join(missing_required_artifacts)}}")
        if feature_status not in FEATURE_STATUSES:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid feature_status: {{feature_status}}")
        if current_stage not in set(WORKFLOW_STAGES):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid current_stage: {{current_stage}}")
        if workflow_profile not in WORKFLOW_PROFILES:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid workflow_profile: {{workflow_profile}}")
        if feature_status == "on_hold":
            checked.append(str(package.relative_to(root)) + " (on_hold)")
            continue

        change_text = read_text(package / "CHANGE_REQUEST.md")
        impact_text = read_text(package / "IMPACT_ANALYSIS.md")
        spec_text = read_text(package / "SPEC.md")
        design_text = read_text(package / "DESIGN.md")
        plan_text = read_text(package / "PLAN.md")
        tasks_text = read_text(package / "TASKS.md")
        verify_text = read_text(package / "VERIFY.md")
        review_text = read_text(package / "REVIEW.md")
        change_status = (read_field(change_text, "status") or "draft").lower()
        impact_status = (read_field(impact_text, "status") or "draft").lower()
        spec_status = require_feature_status(package, "SPEC.md", {{"draft", "approved", "blocked"}})
        design_status = require_feature_status(package, "DESIGN.md", {{"draft", "approved", "blocked"}})
        plan_status = require_feature_status(package, "PLAN.md", {{"draft", "approved", "blocked"}})
        tasks_status = require_feature_status(package, "TASKS.md", {{"draft", "ready", "blocked"}})
        verify_status = require_feature_status(package, "VERIFY.md", {{"missing", "partial", "passed", "failed", "blocked"}})
        review_status = require_feature_status(package, "REVIEW.md", {{"pending", "passed", "failed", "blocked"}})
        workbench_upgrade_assessment = (read_field(review_text, "workbench_upgrade_assessment") or "unassessed").lower()
        if workbench_upgrade_assessment == "unassessed" and (verify_status in {{"failed", "blocked"}} or review_status in {{"failed", "blocked"}} or current_stage == "DONE" or feature_status in {{"complete", "failed", "blocked", "repeated_issue"}}):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} must set REVIEW.md workbench_upgrade_assessment before passing quality gate")
        if workbench_upgrade_assessment != "unassessed" and workbench_upgrade_assessment not in WORKBENCH_UPGRADE_ASSESSMENTS:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid workbench_upgrade_assessment: {{workbench_upgrade_assessment}}")
        risk_level = (read_field(spec_text, "risk_level") or "unclassified").lower()
        spec_profile = (read_field(spec_text, "workflow_profile") or "unclassified").lower()
        impact_score = read_int(spec_text, "impact_score")
        uncertainty_score = read_int(spec_text, "uncertainty_score")
        rollback_score = read_int(spec_text, "rollback_score")
        risk_score = read_int(spec_text, "risk_score")
        hard_triggers = read_field(spec_text, "hard_triggers")
        classification_reason = read_field(spec_text, "classification_reason")
        if risk_level not in WORKFLOW_PROFILES:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid risk_level: {{risk_level}}")
        if spec_profile not in WORKFLOW_PROFILES:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid SPEC.md workflow_profile: {{spec_profile}}")
        component_scores = [impact_score, uncertainty_score, rollback_score]
        if any(score is None or score < 0 or score > 3 for score in component_scores):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid impact/uncertainty/rollback risk scores")
        if risk_score is None or risk_score < 0 or risk_score > 9:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid risk_score")
        if risk_score != sum(component_scores):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} risk_score must equal impact_score + uncertainty_score + rollback_score")
        if is_placeholder_value(hard_triggers) or is_placeholder_value(classification_reason):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} is missing risk classification evidence in SPEC.md")
        strict_reasons = strict_trigger_reasons(root, package, spec_text, impact_text, controlled_paths)
        if strict_reasons and (workflow_profile != "strict" or spec_profile != "strict" or risk_level != "strict"):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} hits strict hard triggers but is not classified strict: {{'; '.join(strict_reasons[:3])}}")
        if risk_score >= 6 and workflow_profile != "strict":
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} workflow_profile is too low for risk_score >= 6")
        if risk_score >= 3 and workflow_profile == "light":
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} workflow_profile is too low for risk_score >= 3")
        if stage_reached(current_stage, "PLAN") and change_status not in {{"ready", "approved"}}:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached PLAN before CHANGE_REQUEST.md was ready")
        if stage_reached(current_stage, "PLAN") and impact_status not in {{"ready", "approved"}}:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached PLAN before IMPACT_ANALYSIS.md was ready")
        if stage_reached(current_stage, "PLAN") and (spec_status != "approved" or not read_bool(spec_text, "approved_for_plan")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached PLAN before SPEC was approved")
        if stage_reached(current_stage, "PLAN") and (design_status != "approved" or not read_bool(design_text, "approved_for_plan")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached PLAN before DESIGN was approved")
        if stage_reached(current_stage, "IMPLEMENT") and (plan_status != "approved" or not read_bool(plan_text, "approved_for_tasks")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached TASKS before PLAN was approved for tasks")
        if stage_reached(current_stage, "IMPLEMENT") and (not read_bool(plan_text, "approved_for_implementation") or tasks_status != "ready" or not read_bool(tasks_text, "ready_for_implementation")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached IMPLEMENT before PLAN/TASKS allowed implementation")
        if stage_reached(current_stage, "REVIEW") and verify_status != "passed":
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached REVIEW before VERIFY passed")
        if current_stage == "DONE" and review_status != "passed":
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached complete before REVIEW passed")
        if feature_status != "complete":
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} is {{feature_status}}. Set feature_status to on_hold for paused work, or complete it before passing the final quality gate.")
        if bool(status_json.get("implementation_allowed")) and (not read_bool(plan_text, "approved_for_implementation") or not read_bool(tasks_text, "ready_for_implementation")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} FEATURE_STATUS.json allows implementation before PLAN/TASKS allow it")
        if bool(status_json.get("delivery_allowed")) and (verify_status != "passed" or review_status != "passed"):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} FEATURE_STATUS.json allows delivery before VERIFY/REVIEW pass")
        require_feature_field(package, "SPEC.md", "approved_for_plan", True)
        require_feature_field(package, "DESIGN.md", "approved_for_plan", True)
        require_feature_field(package, "PLAN.md", "approved_for_tasks", True)
        require_feature_field(package, "PLAN.md", "approved_for_implementation", True)
        require_feature_field(package, "TASKS.md", "ready_for_implementation", True)
        require_feature_field(package, "VERIFY.md", "status", "passed")
        require_feature_field(package, "REVIEW.md", "status", "passed")
        require_verify_evidence(package, verify_text, workflow_profile)
        require_review_evidence(package, review_text)
        require_traceability_evidence(root, package, impact_text, workflow_profile)
        if not bool(status_json.get("implementation_allowed")) or not bool(status_json.get("delivery_allowed")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} is complete but FEATURE_STATUS.json has not allowed implementation and delivery")
        if re.search(r"(?m)^- \\[ \\]", tasks_text):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} still has unchecked task items")
        checked.append(str(package.relative_to(root)))
    return checked


def infer_workflow_profile(root: Path, checked_features: list[str], controlled_paths: list[str]) -> str:
    if len(checked_features) == 1:
        package = root / checked_features[0]
        status = read_json(package / "FEATURE_STATUS.json")
        if isinstance(status, dict):
            value = str(status.get("workflow_profile") or "unclassified").lower()
            if value in WORKFLOW_PROFILES:
                return value
    if controlled_paths:
        if has_valid_light_change_record(root, controlled_paths):
            return "light"
        return "unclassified"
    return "unclassified"


def generate_workflow_state(root: Path, active_feature: str | None, current_stage: str, workflow_profile: str, quality_profile: str, gate_status: str, checks_run: list[str], controlled_paths: list[str], scorecard_report: dict) -> dict:
    source_hashes = {{}}
    for rel in [
        "PROJECT_INTAKE.md",
        "PROJECT_STATE.md",
        "workbench/delivery/TRACEABILITY.md",
        "workbench/delivery/CHANGE_LOG.md",
    ]:
        path = root / rel
        if path.exists():
            source_hashes[rel] = file_sha256(path)
    return {{
        "schema": "codex-workbench-workflow-state/v2",
        "workbench_version": WORKBENCH_VERSION,
        "generated_by": "quality_gate.py",
        "created_at": utc_now(),
        "project_root": str(root),
        "git_head": git_head(root),
        "diff_hash": diff_hash(root),
        "active_feature": active_feature,
        "current_stage": current_stage,
        "workflow_profile": workflow_profile,
        "quality_profile": quality_profile,
        "implementation_allowed": False,
        "delivery_allowed": False,
        "source_hashes": source_hashes,
        "last_gate_status": gate_status,
        "branch_protection": "unverified",
        "unverified_paths": ["branch_protection"],
        "controlled_changed_paths": controlled_paths,
        "scorecard_decision": scorecard_report.get("decision"),
        "scorecard_confidence": scorecard_report.get("confidence"),
        "checks_run": checks_run,
    }}


def stale_marker_reason(root: Path) -> str | None:
    marker = root / ".workbench-validation" / "quality-gate-ok.json"
    if not marker.exists():
        return None
    data = read_json(marker)
    if not data:
        return "marker is not valid json"
    current_diff = diff_hash(root)
    current_head = git_head(root)
    if data.get("schema") != "codex-workbench-quality-gate-marker/v2":
        return "marker schema is invalid"
    if data.get("status") not in {{"passed", "passed_with_risk"}}:
        return "marker status is not passed or passed_with_risk"
    if data.get("git_head") and data.get("git_head") != current_head:
        return "git_head changed since last quality gate"
    if data.get("diff_hash") and data.get("diff_hash") != current_diff:
        return "diff_hash changed since last quality gate"
    if not isinstance(data.get("checks_run"), list) or not data.get("checks_run"):
        return "marker checks_run is missing"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--profile", choices=["smoke", "standard", "full"], default="standard")
    parser.add_argument("--skip", action="append", default=[], help="Skip a command group such as docker, node, or maven.")
    args = parser.parse_args()

    root = project_root()
    if args.profile in ("standard", "full") and args.skip:
        raise SystemExit("[quality] --skip is not allowed for standard/full quality gates. Use smoke for local narrowing, or document accepted risk and run the full required gate.")
    if args.profile in ("standard", "full") and args.allow_empty:
        raise SystemExit("[quality] --allow-empty is not allowed for standard/full quality gates. Configure real checks or use smoke only for docs-only preview.")
    selected = [
        cmd
        for cmd in COMMANDS
        if cmd.get("group") not in set(args.skip)
        and args.profile in set(cmd.get("profiles", ["standard"]))
    ]
    print(f"[quality] profile={{args.profile}}")
    checks_run: list[str] = []
    checked_intake = check_project_intake(root)
    if checked_intake:
        print(f"[quality] checked project intake: {{checked_intake}}")
        checks_run.append("project intake blockers")
    for checked_contract in check_directory_contract(root):
        print(f"[quality] checked {{checked_contract}}")
        checks_run.append(checked_contract)
    marker_reason = stale_marker_reason(root)
    if marker_reason:
        print(f"[quality] previous marker is stale: {{marker_reason}}")
        checks_run.append("stale marker invalidated")
    checked_features = check_feature_packages(root)
    if checked_features:
        print(f"[quality] checked 2.0 feature packages: {{', '.join(checked_features)}}")
        checks_run.append("2.0 feature package structure")
    controlled_paths = controlled_changed_paths(root)
    if controlled_paths:
        print(f"[quality] controlled changed paths: {{', '.join(controlled_paths)}}")
        feature_covered_paths = feature_covered_controlled_paths(root, checked_features, controlled_paths)
        uncovered_paths = [path for path in controlled_paths if path not in feature_covered_paths]
        if uncovered_paths and not has_valid_light_change_record(root, uncovered_paths):
            raise SystemExit("[quality] controlled changes require a completed feature package or a machine-readable light CHANGE_LOG record with validation evidence.")
        checks_run.append("controlled diff linked to feature or light change")
    if not selected and not args.allow_empty:
        raise SystemExit(f"[quality] no checks configured for profile {{args.profile}}. Update workbench/quality/quality_gate.py or pass --allow-empty only for docs-only projects.")
    for step in selected:
        run_step(root, step)
        checks_run.append(step["name"])
    scorecard_report = run_scorecard(root, args.profile)
    checks_run.append("scorecard evidence report")
    scorecard_decision = str(scorecard_report.get("decision") or "UNKNOWN")
    accepted_risk_features: list[str] = []
    for checked_feature in checked_features:
        package = root / checked_feature.split(" ", 1)[0]
        verify_path = package / "VERIFY.md"
        if verify_path.exists() and has_accepted_verification_risk(read_text(verify_path)):
            accepted_risk_features.append(checked_feature)
    gate_status = "passed_with_risk" if scorecard_decision == "PASS_WITH_RISK" or accepted_risk_features else "passed"
    if args.profile == "full" and "branch_protection" in ["branch_protection"]:
        gate_status = "passed_with_risk"

    marker_dir = root / ".workbench-validation"
    marker_dir.mkdir(parents=True, exist_ok=True)
    active_feature = checked_features[0] if len(checked_features) == 1 else None
    workflow_profile = infer_workflow_profile(root, checked_features, controlled_paths)
    workflow_state = generate_workflow_state(root, active_feature, "GATE", workflow_profile, args.profile, gate_status, checks_run, controlled_paths, scorecard_report)
    workflow_state_path = marker_dir / ("quality-workflow-state-smoke.json" if args.profile == "smoke" else "quality-workflow-state.json")
    workflow_state_text = json.dumps(workflow_state, ensure_ascii=False, indent=2) + "\\n"
    workflow_state_path.write_text(workflow_state_text, encoding="utf-8")
    marker = marker_dir / ("quality-gate-smoke-ok.json" if args.profile == "smoke" else "quality-gate-ok.json")
    marker.write_text(json.dumps({{
        "schema": "codex-workbench-quality-gate-marker/v2",
        "workbench_version": WORKBENCH_VERSION,
        "gate": "quality-gate",
        "status": gate_status,
        "created_at": utc_now(),
        "projectRoot": str(root),
        "git_head": workflow_state["git_head"],
        "diff_hash": workflow_state["diff_hash"],
        "feature_id": active_feature,
        "workflow_profile": workflow_profile,
        "quality_profile": args.profile,
        "commands_run": [step["name"] for step in selected],
        "skipped_groups": list(args.skip),
        "allow_empty": bool(args.allow_empty),
        "checks_run": checks_run,
        "report_id": "qg-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "workflow_state": str(workflow_state_path),
        "workflow_state_hash": text_sha256(workflow_state_text),
        "controlled_changed_paths": controlled_paths,
        "scorecard_decision": scorecard_report.get("decision"),
        "scorecard_confidence": scorecard_report.get("confidence"),
        "accepted_risk_features": accepted_risk_features,
        "accepted_risk_required": gate_status == "passed_with_risk",
        "branch_protection": "unverified",
        "unverified_paths": ["branch_protection"],
    }}, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    print(f"[quality] wrote {{workflow_state_path}}")
    print(f"[quality] wrote {{marker}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

def generate_scorecard_py(feature_package_files: list[str], required_adapter_files: list[str]) -> str:
    feature_files_json = quote_json(feature_package_files)
    required_adapter_files_json = quote_json(required_adapter_files)
    script = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

FEATURE_PACKAGE_FILES = __FEATURE_PACKAGE_FILES__
REQUIRED_ADAPTER_FILES = __REQUIRED_ADAPTER_FILES__

WEIGHTS = {
    "intake": 15,
    "product": 15,
    "design": 10,
    "architecture": 15,
    "delivery": 10,
    "features": 20,
    "verification": 10,
    "feedback": 5,
}

PROFILE_RULES = {
    "smoke": {
        "reference_score": 60,
        "max_blockers": 0,
        "min_component_percent": 20,
        "require_calibration": False,
        "require_semantic_review": False,
        "component_floor_is_blocker": False,
        "score_is_gate": False,
    },
    "standard": {
        "reference_score": 75,
        "max_blockers": 0,
        "min_component_percent": 50,
        "require_calibration": False,
        "require_semantic_review": False,
        "component_floor_is_blocker": False,
        "score_is_gate": False,
    },
    "full": {
        "reference_score": 85,
        "max_blockers": 0,
        "min_component_percent": 60,
        "require_calibration": True,
        "require_semantic_review": True,
        "component_floor_is_blocker": False,
        "score_is_gate": False,
    },
}

STATUS_PATTERN = re.compile(r"(?im)^\s*status\s*:\s*([a-zA-Z_-]+)\s*$")
ACCEPTED_REVIEW_STATUSES = {"passed", "accepted_with_risk", "not_required"}
ACCEPTED_CALIBRATION_STATUSES = {"calibrated", "reviewed", "accepted_with_risk"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def field(text: str, name: str) -> str | None:
    match = re.search(rf"(?im)^\s*{re.escape(name)}\s*:\s*(.+?)\s*$", text)
    return match.group(1).strip() if match else None


def status_of(path: Path) -> str | None:
    text = read_text(path)
    match = STATUS_PATTERN.search(text)
    return match.group(1).strip().lower() if match else None


def has_open_blockers(text: str, prefix: str) -> bool:
    return bool(re.search(rf"(?im)^\|\s*{prefix}\d+\s*\|.*\|\s*open\s*\|\s*$", text))


def is_placeholder_cell(cell: str, placeholder_values: set[str]) -> bool:
    normalized = cell.strip()
    if normalized in placeholder_values:
        return True
    if not normalized:
        return True
    if normalized.startswith("`") and normalized.endswith("`"):
        return True
    if normalized.lower() in {"pending", "draft", "open", "unconfirmed", "project owner", "must"}:
        return True
    if re.fullmatch(r"[A-Z]{1,4}\d{3,}", normalized):
        return True
    if re.fullmatch(r"(FP|FN|I|B)\d{3,}", normalized):
        return True
    if normalized.endswith(".md") or normalized.endswith(".json"):
        return True
    if "待补充" in normalized or "作为..." in normalized or "Given/When/Then" in normalized:
        return True
    if "/" in normalized and any(part.strip().lower() in {"low", "medium", "high", "prototype-only", "usable-with-known-risks", "release-ready"} for part in normalized.split("/")):
        return True
    return False


def contains_filled_table_row(text: str) -> bool:
    placeholder_values = {
        "",
        "\u7f16\u53f7", "\u6765\u6e90", "\u95ee\u9898", "\u5904\u7406\u72b6\u6001", "\u4fee\u590d\u4f4d\u7f6e",
        "\u9879\u76ee", "\u7ed3\u8bba", "\u8bc1\u636e\u4f4d\u7f6e", "\u98ce\u9669/\u52a8\u4f5c",
        "\u7ef4\u5ea6", "\u6863\u4f4d", "\u603b\u5206", "\u7b49\u7ea7", "\u786c\u963b\u585e\u6570", "\u4e3b\u8981\u98ce\u9669",
        "\u6837\u4f8b", "\u9884\u671f\u8bc4\u5206", "\u7406\u7531",
        "\u62bd\u67e5\u4eba", "\u6837\u672c", "\u4eba\u5de5\u7ed3\u8bba", "\u811a\u672c\u7ed3\u8bba",
        "\u5dee\u5f02", "\u540e\u7eed\u52a8\u4f5c", "\u65e5\u671f", "\u8c03\u6574", "\u4f9d\u636e",
        "\u9879\u76ee\u72b6\u6001", "\u9884\u671f\u7b49\u7ea7", "\u9884\u671f\u53ef\u4fe1\u5ea6", "\u590d\u6838\u4eba",
        "\u9700\u6c42", "\u7528\u6237/\u89d2\u8272", "\u4f18\u5148\u7ea7", "\u72b6\u6001",
        "\u7528\u6237\u6545\u4e8b", "\u9a8c\u6536\u6807\u51c6", "\u5931\u8d25\u8def\u5f84", "\u5bf9\u5e94\u529f\u80fd\u5305",
    }
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        meaningful = [cell for cell in cells if not is_placeholder_cell(cell, placeholder_values)]
        if len(cells) >= 3 and meaningful:
            return True
    return False


def section_between(text: str, heading: str) -> str:
    match = re.search(rf"(?ms)^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)", text)
    return match.group(1) if match else ""


def has_unchecked_item(path: Path) -> bool:
    return bool(re.search(r"(?m)^- \[ \]", read_text(path)))


def score_file_status(root: Path, rel: str, accepted: set[str], full_points: int, partial_points: int = 1) -> tuple[int, list[str], list[str]]:
    path = root / rel
    if not path.exists():
        return 0, [f"missing {rel}"], []
    status = status_of(path)
    if status in accepted:
        return full_points, [], []
    if status == "draft":
        return partial_points, [], [f"{rel} is still draft"]
    return 0, [f"{rel} has invalid or missing status"], []


def component_result(name: str, score: int, max_score: int, blockers: list[str], warnings: list[str]) -> dict:
    score = max(0, min(score, max_score))
    return {
        "name": name,
        "score": score,
        "maxScore": max_score,
        "percent": round(score * 100 / max_score, 1) if max_score else 0,
        "blockers": blockers,
        "warnings": warnings,
    }


def profile_rules(profile: str) -> dict:
    return PROFILE_RULES.get(profile, PROFILE_RULES["standard"])


def score_intake(root: Path) -> dict:
    rel = "PROJECT_INTAKE.md"
    text = read_text(root / rel)
    score, blockers, warnings = score_file_status(root, rel, {"confirmed"}, WEIGHTS["intake"], 5)
    required_terms = ["\u9879\u76ee\u76ee\u6807", "\u7b2c\u4e00\u7248\u8303\u56f4", "AI \u4f7f\u7528\u8fb9\u754c", "\u9a8c\u6536", "\u963b\u585e\u95ee\u9898"]
    missing_terms = [term for term in required_terms if term not in text]
    score -= len(missing_terms) * 2
    warnings.extend([f"PROJECT_INTAKE.md missing section cue: {term}" for term in missing_terms])
    if has_open_blockers(text, "P"):
        blockers.append("PROJECT_INTAKE.md has open blocking questions")
    return component_result("intake", score, WEIGHTS["intake"], blockers, warnings)


def score_product(root: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 0
    for rel in ("workbench/product/PRODUCT_BRIEF.md", "workbench/product/PRD.md", "workbench/product/ROADMAP.md"):
        part, part_blockers, part_warnings = score_file_status(root, rel, {"approved", "confirmed"}, 4, 1)
        score += part
        blockers.extend(part_blockers)
        warnings.extend(part_warnings)
    prd = read_text(root / "workbench/product/PRD.md")
    if contains_filled_table_row(prd):
        score += 3
    else:
        warnings.append("PRD.md has no filled requirement/story evidence")
    return component_result("product", score, WEIGHTS["product"], blockers, warnings)


def score_design(root: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 0
    for rel in ("workbench/design/UX_SPEC.md", "workbench/design/PROTOTYPE.md", "workbench/design/USER_FLOW.md"):
        part, part_blockers, part_warnings = score_file_status(root, rel, {"approved", "confirmed"}, 3, 1)
        score += part
        blockers.extend(part_blockers)
        warnings.extend(part_warnings)
    ux = read_text(root / "workbench/design/UX_SPEC.md")
    if all(term in ux for term in ("\u5931\u8d25", "\u6743\u9650", "\u53ef\u8bbf\u95ee\u6027")):
        score += 1
    else:
        warnings.append("UX_SPEC.md should cover failure, permission, and accessibility states")
    return component_result("design", score, WEIGHTS["design"], blockers, warnings)


def score_architecture(root: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 0
    for rel in (
        "workbench/architecture/ARCHITECTURE.md",
        "workbench/architecture/DATA_MODEL.md",
        "workbench/architecture/API_DESIGN.md",
        "workbench/architecture/AI_DESIGN.md",
    ):
        part, part_blockers, part_warnings = score_file_status(root, rel, {"approved", "confirmed"}, 3, 1)
        score += part
        blockers.extend(part_blockers)
        warnings.extend(part_warnings)
    arch = read_text(root / "workbench/architecture/ARCHITECTURE.md")
    if all(term in arch for term in ("\u8d28\u91cf\u5c5e\u6027", "\u98ce\u9669", "\u9a8c\u8bc1\u65b9\u5f0f")):
        score += 3
    else:
        warnings.append("ARCHITECTURE.md should include quality attributes, risks, and verification method")
    return component_result("architecture", score, WEIGHTS["architecture"], blockers, warnings)


def score_delivery(root: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 0
    for rel in ("workbench/delivery/RELEASE_PLAN.md", "workbench/delivery/ITERATION_PLAN.md", "workbench/delivery/TASK_BREAKDOWN.md"):
        part, part_blockers, part_warnings = score_file_status(root, rel, {"approved", "confirmed", "active"}, 3, 1)
        score += part
        blockers.extend(part_blockers)
        warnings.extend(part_warnings)
    release = read_text(root / "workbench/delivery/RELEASE_PLAN.md")
    if "\u56de\u6eda" in release:
        score += 1
    else:
        warnings.append("RELEASE_PLAN.md should include rollback evidence")
    return component_result("delivery", score, WEIGHTS["delivery"], blockers, warnings)


def score_features(root: Path) -> dict:
    feature_root = root / "workbench" / "features"
    blockers: list[str] = []
    warnings: list[str] = []
    if not feature_root.exists():
        return component_result("features", 8, WEIGHTS["features"], blockers, ["No feature packages yet; acceptable before feature development"])
    packages = [item for item in sorted(feature_root.iterdir()) if item.is_dir()]
    if not packages:
        return component_result("features", 8, WEIGHTS["features"], blockers, ["workbench/features exists but has no feature package"])
    package_scores: list[int] = []
    for package in packages:
        rel_package = package.relative_to(root).as_posix()
        missing = [filename for filename in FEATURE_PACKAGE_FILES if not (package / filename).exists()]
        if missing:
            blockers.append(f"{rel_package} missing files: {', '.join(missing)}")
            package_scores.append(0)
            continue
        status_data = {}
        try:
            status_data = json.loads(read_text(package / "FEATURE_STATUS.json"))
        except Exception:
            blockers.append(f"{rel_package} FEATURE_STATUS.json is not valid json")
            package_scores.append(0)
            continue
        feature_status = str(status_data.get("feature_status") or "active").lower()
        current_stage = str(status_data.get("current_stage") or "CHANGE").upper()
        if feature_status == "on_hold":
            package_scores.append(12)
            continue
        if feature_status != "complete":
            warnings.append(f"{rel_package} is {feature_status} at {current_stage}")
            package_scores.append(8)
            continue
        verify_status = (field(read_text(package / "VERIFY.md"), "status") or "missing").lower()
        review_status = (field(read_text(package / "REVIEW.md"), "status") or "pending").lower()
        if verify_status == "passed" and review_status == "passed" and not has_unchecked_item(package / "TASKS.md") and bool(status_data.get("delivery_allowed")):
            package_scores.append(20)
        else:
            blockers.append(f"{rel_package} complete but VERIFY/REVIEW/status gates are not consistent")
            package_scores.append(12)
    score = min(package_scores) if package_scores else 8
    return component_result("features", score, WEIGHTS["features"], blockers, warnings)


def score_verification(root: Path, called_from_quality_gate: bool) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    marker = root / ".workbench-validation" / "quality-gate-ok.json"
    score = 0
    if marker.exists():
        score += 4
    elif called_from_quality_gate:
        warnings.append(".workbench-validation/quality-gate-ok.json is not expected yet because scorecard is running inside the current quality gate")
        score += 2
    else:
        warnings.append(".workbench-validation/quality-gate-ok.json is missing; treat this as historical gate evidence, not current proof")
    quality_gate = root / "workbench" / "quality" / "quality_gate.py"
    gate_text = read_text(quality_gate)
    if quality_gate.exists() and "run_scorecard" in gate_text and "--called-from-quality-gate" in gate_text:
        score += 6
    elif quality_gate.exists() and "run_scorecard" in gate_text:
        score += 4
        warnings.append("quality_gate.py calls scorecard.py but does not pass --called-from-quality-gate")
    else:
        blockers.append("quality_gate.py does not call scorecard.py for evidence reporting")
    return component_result("verification", score, WEIGHTS["verification"], blockers, warnings)


def score_feedback(root: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 0
    for rel in ("workbench/feedback/FAILURE_LOG.md", "workbench/feedback/ITERATION_LOG.md", "workbench/feedback/AI_EFFECTIVENESS.md"):
        if (root / rel).exists():
            score += 1
        else:
            blockers.append(f"missing {rel}")
    effectiveness = read_text(root / "workbench/feedback/AI_EFFECTIVENESS.md")
    if "\u8fd4\u5de5" in effectiveness and "\u8d28\u91cf\u95e8" in effectiveness:
        score += 2
    else:
        warnings.append("AI_EFFECTIVENESS.md should track rework and quality-gate failures")
    return component_result("feedback", score, WEIGHTS["feedback"], blockers, warnings)


def score_calibration(root: Path) -> tuple[dict, list[str], list[str]]:
    path = root / "workbench" / "scorecard" / "CALIBRATION.md"
    scorecard_path = root / "workbench" / "scorecard" / "SCORECARD.md"
    text = read_text(path)
    scorecard = read_text(scorecard_path)
    blockers: list[str] = []
    warnings: list[str] = []
    status = (field(text, "calibration_status") or field(scorecard, "calibration_status") or "missing").lower()
    has_anchor_examples = contains_filled_table_row(section_between(text, "\u951a\u5b9a\u6837\u4f8b"))
    has_human_spotcheck = contains_filled_table_row(section_between(text, "\u4eba\u5de5\u62bd\u67e5"))
    has_false_positive_record = "\u8bef\u62a5" in text
    has_false_negative_record = "\u6f0f\u62a5" in text
    has_reference_line_change_log = "\u53c2\u8003\u7ebf\u8c03\u6574" in text
    has_threshold_change_log = has_reference_line_change_log or "\u9608\u503c\u8c03\u6574" in text
    if not path.exists():
        blockers.append("CALIBRATION.md is missing")
    if status == "missing":
        warnings.append("CALIBRATION.md missing calibration_status")
    elif status not in ACCEPTED_CALIBRATION_STATUSES:
        warnings.append(f"CALIBRATION.md calibration_status is {status}, not calibrated/reviewed/accepted_with_risk")
    if not has_anchor_examples:
        warnings.append("CALIBRATION.md has no filled anchor-example evidence")
    if not has_human_spotcheck:
        warnings.append("CALIBRATION.md has no filled human spot-check evidence")
    return {
        "status": status,
        "acceptedStatuses": sorted(ACCEPTED_CALIBRATION_STATUSES),
        "hasAnchorExamples": has_anchor_examples,
        "hasHumanSpotcheck": has_human_spotcheck,
        "tracksFalsePositives": has_false_positive_record,
        "tracksFalseNegatives": has_false_negative_record,
        "hasReferenceLineChangeLog": has_reference_line_change_log,
        "hasThresholdChangeLog": has_threshold_change_log,
        "isCalibrated": status in ACCEPTED_CALIBRATION_STATUSES and has_anchor_examples and has_human_spotcheck,
    }, blockers, warnings


def score_semantic_review(root: Path, require_semantic_review: bool) -> tuple[dict, list[str], list[str]]:
    scorecard = read_text(root / "workbench" / "scorecard" / "SCORECARD.md")
    blockers: list[str] = []
    warnings: list[str] = []
    semantic_status = (field(scorecard, "semantic_review_status") or "missing").lower()
    if semantic_status not in ACCEPTED_REVIEW_STATUSES:
        message = "SCORECARD.md semantic_review_status is not passed, accepted_with_risk, or not_required"
        if require_semantic_review:
            blockers.append(message)
        else:
            warnings.append(message)
    architecture_status = (field(scorecard, "architecture_review_status") or "missing").lower()
    if architecture_status not in ACCEPTED_REVIEW_STATUSES:
        message = "SCORECARD.md architecture_review_status is not passed, accepted_with_risk, or not_required"
        if require_semantic_review:
            blockers.append(message)
        else:
            warnings.append(message)
    if "\u786c\u963b\u585e" not in scorecard or "\u67b6\u6784\u5408\u7406\u6027" not in scorecard:
        blockers.append("SCORECARD.md is missing scorecard structure cues")
    return {
        "semanticReviewStatus": semantic_status,
        "architectureReviewStatus": architecture_status,
        "acceptedStatuses": sorted(ACCEPTED_REVIEW_STATUSES),
        "required": require_semantic_review,
    }, blockers, warnings


def component_floor_violations(components: list[dict], min_percent: int) -> list[dict]:
    return [
        {
            "component": component["name"],
            "percent": component["percent"],
            "minPercent": min_percent,
        }
        for component in components
        if component["percent"] < min_percent
    ]


def confidence_level(blockers: list[str], warnings: list[str], calibration: dict, semantic_review: dict, floor_violations: list[dict]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if blockers:
        reasons.append("Blockers exist; the score cannot be used as pass evidence.")
        return "low", reasons
    if floor_violations:
        reasons.append("A component floor violation may hide local risk behind a good total score.")
    if not calibration["isCalibrated"]:
        reasons.append("The scoring rubric has not been calibrated with anchor examples and human spot checks.")
    if semantic_review["semanticReviewStatus"] not in ACCEPTED_REVIEW_STATUSES:
        reasons.append("Semantic review is incomplete or failed.")
    if semantic_review["architectureReviewStatus"] not in ACCEPTED_REVIEW_STATUSES:
        reasons.append("Architecture review is incomplete or failed.")
    if len(warnings) >= 10:
        reasons.append("Too many warnings; manually review score confidence.")
    if not reasons:
        return "high", ["No obvious blockers, component floor gaps, calibration gaps, or semantic-review gaps."]
    if len(reasons) >= 3 or floor_violations:
        return "low", reasons
    return "medium", reasons


def calculate(root: Path, profile: str, called_from_quality_gate: bool = False) -> dict:
    rules = profile_rules(profile)
    components = [
        score_intake(root),
        score_product(root),
        score_design(root),
        score_architecture(root),
        score_delivery(root),
        score_features(root),
        score_verification(root, called_from_quality_gate),
        score_feedback(root),
    ]
    semantic_review, semantic_blockers, semantic_warnings = score_semantic_review(root, rules["require_semantic_review"])
    calibration, calibration_blockers, calibration_warnings = score_calibration(root)
    total = sum(component["score"] for component in components)
    max_total = sum(component["maxScore"] for component in components)
    floor_violations = component_floor_violations(components, rules["min_component_percent"])
    blockers = semantic_blockers[:] + calibration_blockers[:]
    warnings = semantic_warnings[:] + calibration_warnings[:]
    for component in components:
        blockers.extend(component["blockers"])
        warnings.extend(component["warnings"])
    if rules["require_calibration"] and not calibration["isCalibrated"]:
        blockers.append("full profile requires calibrated scorecard evidence in CALIBRATION.md")
    for violation in floor_violations:
        message = f"{violation['component']} component {violation['percent']}% is below {violation['minPercent']}% floor for {profile}"
        if rules["component_floor_is_blocker"]:
            blockers.append(message)
        else:
            warnings.append(message)
    percentage = round(total * 100 / max_total, 1) if max_total else 0
    confidence, confidence_reasons = confidence_level(blockers, warnings, calibration, semantic_review, floor_violations)
    if blockers:
        level = "blocked"
    elif percentage >= 90:
        level = "release-ready"
    elif percentage >= 75:
        level = "usable-with-known-risks"
    elif percentage >= 60:
        level = "prototype-only"
    else:
        level = "not-ready"
    if blockers:
        decision = "BLOCKED"
    elif confidence == "high":
        decision = "PASS"
    else:
        decision = "PASS_WITH_RISK"
    return {
        "schema": "codex-workbench-scorecard/v1",
        "timestamp": utc_now(),
        "projectRoot": str(root),
        "profile": profile,
        "calledFromQualityGate": called_from_quality_gate,
        "profileRules": rules,
        "scoreMeaning": "evidence_maturity_and_process_consistency_only",
        "decision": decision,
        "decisionMeaning": "BLOCKED blocks delivery; PASS_WITH_RISK requires human review of warnings, confidence, calibration, and semantic review before treating the work as done.",
        "totalScore": total,
        "maxScore": max_total,
        "percentage": percentage,
        "level": level,
        "confidence": confidence,
        "confidenceReasons": confidence_reasons,
        "calibration": calibration,
        "semanticReview": semantic_review,
        "componentFloorViolations": floor_violations,
        "components": components,
        "blockers": blockers,
        "warnings": warnings,
        "limitations": [
            "Scorecard does not prove product correctness, architecture suitability, security/privacy acceptance, or AI eval quality.",
            "High scores must not override blockers, low confidence, missing calibration, missing semantic review, or failed quality gates.",
            "Reference scores and component floors are triage signals, not release gates by themselves.",
            "Treat score changes as signals for review and improvement, not as a target to game.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["smoke", "standard", "full"], default="standard")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--called-from-quality-gate", action="store_true")
    parser.add_argument("--enforce-blockers", action="store_true", help="Return non-zero only for hard blockers, not for low evidence score.")
    args = parser.parse_args()
    root = project_root()
    report = calculate(root, args.profile, args.called_from_quality_gate)
    rules = profile_rules(args.profile)
    report["referenceRules"] = rules
    if args.write_report:
        out_dir = root / ".workbench-validation"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "scorecard-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": report["decision"],
        "score": report["totalScore"],
        "maxScore": report["maxScore"],
        "percentage": report["percentage"],
        "level": report["level"],
        "confidence": report["confidence"],
        "blockers": len(report["blockers"]),
        "warnings": len(report["warnings"]),
        "componentFloorViolations": len(report["componentFloorViolations"]),
        "calibrationStatus": report["calibration"]["status"],
    }, ensure_ascii=False))
    if args.enforce_blockers and len(report["blockers"]) > rules["max_blockers"]:
        print("[scorecard] blockers exist", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    return script.replace("__FEATURE_PACKAGE_FILES__", feature_files_json).replace("__REQUIRED_ADAPTER_FILES__", required_adapter_files_json)

def generate_py_wrapper(script_name: str) -> str:
    return f'''param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "{script_name}"

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {{
  & $python.Source $script @Args
  exit $LASTEXITCODE
}}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {{
  & $python.Source $script @Args
  exit $LASTEXITCODE
}}

$python = Get-Command python3 -ErrorAction SilentlyContinue
if ($python) {{
  & $python.Source $script @Args
  exit $LASTEXITCODE
}}

throw "Python was not found. Install Python 3 and retry."
'''

def generate_sh_wrapper(script_name: str) -> str:
    return f'''#!/usr/bin/env sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/{script_name}" "$@"
fi
if command -v python >/dev/null 2>&1; then
  exec python "$SCRIPT_DIR/{script_name}" "$@"
fi
echo "Python 3 was not found. Install Python 3 and retry." >&2
exit 127
'''

def generate_runtime_gate_py(workbench_version: str) -> str:
    version_json = json.dumps(workbench_version)
    return f'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

WORKBENCH_VERSION = {version_json}
WORKFLOW_STAGES = ["CLASSIFY", "BASELINE_CHECK", "CHANGE", "IMPACT", "ROUTE", "PLAN", "IMPLEMENT", "VERIFY", "REVIEW", "GATE", "LEARN", "DONE", "BLOCKED"]
WORKFLOW_PROFILES = ["light", "standard", "strict", "unclassified"]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def command_output(root: Path, command: list[str]) -> str:
    try:
        result = subprocess.run(command, cwd=str(root), text=True, capture_output=True, timeout=20)
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def git_head(root: Path) -> str:
    return command_output(root, ["git", "rev-parse", "HEAD"]) or "unavailable"


def diff_hash(root: Path) -> str:
    try:
        result = subprocess.run(["git", "diff", "--binary", "HEAD"], cwd=str(root), capture_output=True, timeout=30)
        payload = result.stdout if result.returncode == 0 else b""
    except Exception:
        payload = b""
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return "sha256:" + digest.hexdigest()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {{}}


def generate_workflow_state(root: Path, stage: str, profile: str, active_feature: str | None) -> dict:
    source_hashes = {{}}
    for rel in [
        "PROJECT_INTAKE.md",
        "PROJECT_STATE.md",
        "workbench/delivery/TRACEABILITY.md",
        "workbench/delivery/CHANGE_LOG.md",
    ]:
        path = root / rel
        if path.exists():
            source_hashes[rel] = file_sha256(path)
    return {{
        "schema": "codex-workbench-workflow-state/v2",
        "workbench_version": WORKBENCH_VERSION,
        "generated_by": "runtime_gate.py",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "git_head": git_head(root),
        "diff_hash": diff_hash(root),
        "active_feature": active_feature,
        "current_stage": stage,
        "workflow_profile": profile,
        "implementation_allowed": stage == "IMPLEMENT",
        "delivery_allowed": stage == "DONE",
        "source_hashes": source_hashes,
        "last_gate_status": "unknown",
        "branch_protection": "unverified",
        "unverified_paths": ["branch_protection"],
    }}


def check_url(url: str, name: str) -> None:
    with urllib.request.urlopen(url, timeout=10) as response:
        status = getattr(response, "status", 200)
        if status >= 400:
            raise SystemExit(f"[runtime] {{name}} returned HTTP {{status}}: {{url}}")
        print(f"[runtime] {{name}} ok: HTTP {{status}} {{url}}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Run checks. Without this flag, print the plan only.")
    parser.add_argument("--frontend-url", default="")
    parser.add_argument("--backend-health-url", default="")
    parser.add_argument("--stage", choices=WORKFLOW_STAGES, default="CLASSIFY")
    parser.add_argument("--profile", choices=WORKFLOW_PROFILES, default="unclassified")
    parser.add_argument("--active-feature", default="")
    parser.add_argument("--write-state", action="store_true", help="Write .workbench-validation/runtime-state.json.")
    args = parser.parse_args()

    root = project_root()
    print("[runtime] dry-run by default. Pass --apply to run URL smoke checks.")
    if args.write_state:
        state = generate_workflow_state(root, args.stage, args.profile, args.active_feature or None)
        report_dir = root / ".workbench-validation"
        report_dir.mkdir(parents=True, exist_ok=True)
        target = report_dir / "runtime-state.json"
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        print(f"[runtime] wrote {{target}}")
    if not args.apply:
        if args.frontend_url:
            print(f"[runtime] planned frontend check: {{args.frontend_url}}")
        if args.backend_health_url:
            print(f"[runtime] planned backend health check: {{args.backend_health_url}}")
        if not args.frontend_url and not args.backend_health_url:
            print("[runtime] no URLs configured. Provide --frontend-url or --backend-health-url.")
        return 0

    if args.frontend_url:
        check_url(args.frontend_url, "frontend")
    if args.backend_health_url:
        check_url(args.backend_health_url, "backend")
    if not args.frontend_url and not args.backend_health_url:
        raise SystemExit("[runtime] no URL checks were provided.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

def generate_api_smoke_py() -> str:
    return '''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Health or smoke URL to request.")
    args = parser.parse_args()
    with urllib.request.urlopen(args.url, timeout=10) as response:
        status = getattr(response, "status", 200)
        if status >= 400:
            raise SystemExit(f"[smoke] HTTP {status}: {args.url}")
        print(f"[smoke] ok: HTTP {status} {args.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
