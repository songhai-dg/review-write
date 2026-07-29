#!/usr/bin/env python3
"""Route host-agent tasks to ReviewWrite without changing task content."""

from __future__ import annotations

import argparse
import json
from typing import Any

HIGH_RISK_GENRES = frozenset({
    "academic-paper", "grant-proposal", "policy-brief", "policy-document",
    "official-document", "research-report", "executive-memo", "public-article",
    "technical-commentary", "marketing-copy",
})
FORMAL_TASKS = frozenset({"write", "rewrite", "translate", "summarize", "long_document"})
LOW_TASKS = frozenset({"chat", "fact", "concept", "command", "format-only", "office-audit"})


def route(*, task_type: str, genre: str | None = None, characters: int = 0,
          formal: bool = False, has_preserve_constraints: bool = False,
          has_evidence_boundary: bool = False, explicit_skip: bool = False) -> dict[str, Any]:
    """Return a deterministic, local-only routing decision."""
    if characters < 0:
        raise ValueError("characters 不能为负数")
    if explicit_skip:
        return {"policy_version": 1, "tier": "skipped", "invoke": "skipped_by_user",
                "final_gate": "not_run", "repair_max_attempts": 0,
                "reason": "用户明确要求跳过审写", "warning": "不得声称正文已经过 ReviewWrite 审核"}
    high = (formal or genre in HIGH_RISK_GENRES or characters >= 100_000
            or has_preserve_constraints or has_evidence_boundary)
    if high and (task_type in FORMAL_TASKS or formal or genre or characters >= 100_000):
        return {"policy_version": 1, "tier": "high", "invoke": "required",
                "final_gate": "required", "repair_max_attempts": 2,
                "review_stage": "preflight-and-final-gate",
                "reason": "正式交付、证据/保留约束或超长文本需要完整审写闭环"}
    if task_type in FORMAL_TASKS or genre or has_preserve_constraints or has_evidence_boundary:
        return {"policy_version": 1, "tier": "medium", "invoke": "suggested",
                "final_gate": "required-if-invoked", "repair_max_attempts": 2,
                "review_stage": "preflight-and-final-gate-if-invoked",
                "reason": "任务涉及正文生成，建议接入审写以保护事实和交付边界"}
    return {"policy_version": 1, "tier": "low", "invoke": "not-needed",
            "final_gate": "not-needed", "repair_max_attempts": 0,
            "reason": "普通问答、事实查询、命令或格式操作不产生正式正文"}


def main() -> int:
    parser = argparse.ArgumentParser(description="ReviewWrite 宿主智能体风险自适应路由")
    parser.add_argument("--task-type", required=True)
    parser.add_argument("--genre")
    parser.add_argument("--characters", type=int, default=0)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--preserve-constraints", action="store_true")
    parser.add_argument("--evidence-boundary", action="store_true")
    parser.add_argument("--skip-review", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()
    try:
        decision = route(task_type=args.task_type, genre=args.genre, characters=args.characters,
                         formal=args.formal, has_preserve_constraints=args.preserve_constraints,
                         has_evidence_boundary=args.evidence_boundary, explicit_skip=args.skip_review)
    except ValueError as exc:
        parser.error(str(exc))
    if args.format == "json":
        print(json.dumps(decision, ensure_ascii=False, sort_keys=True))
    else:
        print(f"{decision['tier']}: {decision['invoke']}；终检={decision['final_gate']}；{decision['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
