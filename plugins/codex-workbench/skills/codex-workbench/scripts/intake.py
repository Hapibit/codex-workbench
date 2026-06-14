#!/usr/bin/env python3
"""Project intake preflight helper.

Commands:
  init      Create PROJECT_INTAKE.md from the bundled template.
  audit     Check PROJECT_INTAKE.md readiness.
  blockers  List open blocking questions.
  confirm   Mark PROJECT_INTAKE.md confirmed only when blockers are closed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_STATUSES = {"draft", "confirmed"}
REPORT_DIR = ".workbench-validation"

REQUIRED_TEXT = [
    "项目预处理画像",
    "一句话项目目标",
    "用户和角色",
    "第一版范围",
    "核心业务流程",
    "数据和权限",
    "AI 使用边界",
    "质量和验收",
    "阻塞问题",
    "可默认假设",
    "生成下游文件前检查",
]

DEFAULT_PLACEHOLDERS = [
    "project owner",
    "unconfirmed",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_project(path: str | None) -> Path:
    project = Path(path or ".").expanduser().resolve()
    if not project.exists():
        raise SystemExit(f"Project path does not exist: {project}")
    if not project.is_dir():
        raise SystemExit(f"Project path is not a directory: {project}")
    return project


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def template_text() -> str:
    template = skill_root() / "assets" / "PROJECT_INTAKE.template.md"
    if not template.exists():
        raise SystemExit(f"Template not found: {template}")
    return read_text(template)


def render_template(project_name: str) -> str:
    return template_text().replace("{{PROJECT_NAME}}", project_name)


def status_from(text: str) -> str | None:
    match = re.search(r"(?im)^\s*status\s*:\s*([a-zA-Z_-]+)\s*$", text)
    return match.group(1).strip().lower() if match else None


def open_blocker_rows(text: str) -> list[str]:
    rows: list[str] = []
    for line in text.splitlines():
        if re.search(r"(?i)^\|\s*P\d+\s*\|.*\|\s*open\s*\|\s*$", line):
            rows.append(line)
    return rows


def make_issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def audit_project(project: Path) -> dict[str, Any]:
    target = project / "PROJECT_INTAKE.md"
    findings: list[dict[str, str]] = []
    blockers: list[str] = []
    status: str | None = None

    if not target.exists():
        findings.append(make_issue("P0", "missing-intake", "PROJECT_INTAKE.md is missing. Run init before planning or coding."))
    else:
        text = read_text(target)
        status = status_from(text)
        if status is None:
            findings.append(make_issue("P1", "missing-status", "PROJECT_INTAKE.md has no status field."))
        elif status not in VALID_STATUSES:
            findings.append(make_issue("P1", "invalid-status", f"Invalid intake status: {status}"))
        elif status == "draft":
            findings.append(make_issue("P1", "draft-intake", "PROJECT_INTAKE.md is still draft. Confirm intake before high-risk planning or coding."))

        for required in REQUIRED_TEXT:
            if required not in text:
                findings.append(make_issue("P2", "missing-section", f"Missing required text or section: {required}"))

        for placeholder in DEFAULT_PLACEHOLDERS:
            if placeholder in text:
                findings.append(make_issue("P2", "default-placeholder", f"Default placeholder remains: {placeholder}"))

        blockers = open_blocker_rows(text)
        if blockers:
            findings.append(make_issue("P1", "open-blockers", "PROJECT_INTAKE.md has open blocking questions."))

        flow = project / "DEVELOPMENT_FLOW.md"
        if flow.exists():
            flow_text = read_text(flow)
            flow_status = status_from(flow_text)
            if flow_status == "confirmed" and status != "confirmed":
                findings.append(make_issue("P1", "confirmed-flow-without-intake", "DEVELOPMENT_FLOW.md is confirmed while project intake is not confirmed."))

    summary = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for finding in findings:
        summary[finding["severity"]] = summary.get(finding["severity"], 0) + 1
    passed = summary["P0"] == 0 and summary["P1"] == 0
    return {
        "schema": "project-intake-preflight-audit/v1",
        "timestamp": utc_now(),
        "projectRoot": str(project),
        "intakePath": str(target),
        "status": status,
        "passed": passed,
        "summary": summary,
        "openBlockers": blockers,
        "findings": findings,
    }


def write_report(project: Path, name: str, data: dict[str, Any]) -> None:
    report_dir = project / REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    write_text(report_dir / name, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def command_init(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    target = project / "PROJECT_INTAKE.md"
    result: dict[str, Any] = {
        "schema": "project-intake-preflight-init/v1",
        "timestamp": utc_now(),
        "projectRoot": str(project),
        "intakePath": str(target),
        "dryRun": args.dry_run,
        "force": args.force,
    }
    if target.exists() and not args.force:
        result["action"] = "skipped-existing"
    else:
        result["action"] = "would-write" if args.dry_run else "written"
        if not args.dry_run:
            write_text(target, render_template(args.name or project.name))
            write_report(project, "project-intake-init-report.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_audit(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    report = audit_project(project)
    if args.write_report:
        write_report(project, "project-intake-audit-report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


def command_blockers(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    target = project / "PROJECT_INTAKE.md"
    if not target.exists():
        raise SystemExit(f"PROJECT_INTAKE.md is missing: {target}")
    rows = open_blocker_rows(read_text(target))
    print(json.dumps({"schema": "project-intake-preflight-blockers/v1", "openBlockers": rows}, ensure_ascii=False, indent=2))
    return 0 if not rows else 1


def command_confirm(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    target = project / "PROJECT_INTAKE.md"
    if not target.exists():
        raise SystemExit(f"PROJECT_INTAKE.md is missing: {target}")
    text = read_text(target)
    blockers = open_blocker_rows(text)
    if blockers:
        raise SystemExit("Cannot confirm intake while open blockers remain. Run blockers to inspect them.")
    if status_from(text) not in VALID_STATUSES:
        raise SystemExit("Cannot confirm intake because status is missing or invalid.")
    updated = re.sub(r"(?im)^\s*status\s*:\s*[a-zA-Z_-]+\s*$", "status: confirmed", text, count=1)
    if args.owner:
        updated = re.sub(r"(?im)^owner\s*:.*$", f"owner: {args.owner}", updated, count=1)
    updated = re.sub(r"(?im)^intake_updated_at\s*:.*$", f"intake_updated_at: {utc_now()}", updated, count=1)
    if not args.dry_run:
        write_text(target, updated)
    result = {
        "schema": "project-intake-preflight-confirm/v1",
        "timestamp": utc_now(),
        "projectRoot": str(project),
        "intakePath": str(target),
        "dryRun": args.dry_run,
        "status": "confirmed",
    }
    if not args.dry_run:
        write_report(project, "project-intake-confirm-report.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project intake preflight helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--project", default=None)
    p_init.add_argument("--name", default=None)
    p_init.add_argument("--force", action="store_true")
    p_init.add_argument("--dry-run", action="store_true")
    p_init.set_defaults(func=command_init)

    p_audit = sub.add_parser("audit")
    p_audit.add_argument("--project", default=None)
    p_audit.add_argument("--write-report", action="store_true")
    p_audit.set_defaults(func=command_audit)

    p_blockers = sub.add_parser("blockers")
    p_blockers.add_argument("--project", default=None)
    p_blockers.set_defaults(func=command_blockers)

    p_confirm = sub.add_parser("confirm")
    p_confirm.add_argument("--project", default=None)
    p_confirm.add_argument("--owner", default="")
    p_confirm.add_argument("--dry-run", action="store_true")
    p_confirm.set_defaults(func=command_confirm)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
