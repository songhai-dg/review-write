#!/usr/bin/env python3
"""ReviewWrite deterministic preflight for public-facing prose.

The linter catches likely prompt, reasoning, workflow, editor, and chat residue,
plus a small set of contextual, composite signals for technical commentary. It
does not estimate whether text was AI-generated and does not replace semantic or
citation review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    category: str
    message: str
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    category: str
    message: str
    line: int
    column: int
    excerpt: str
    applied_profile: str | None = None
    original_severity: str | None = None


SURFACES: tuple[str, ...] = (
    "review_report",
    "revision_plan",
    "deliverable_body",
    "verification_report",
)


class ProtocolError(ValueError):
    """Raised when a structured ReviewWrite response cannot be safely parsed."""


def parse_surfaces(
    text: str,
    required: Iterable[str] = SURFACES,
    *,
    strict_envelope: bool = True,
) -> dict[str, str]:
    """Parse the stable output envelope without interpreting its prose.

    Tags are deliberately the only hard-coded output contract.  The content of
    each surface remains model-generated and can adapt to language, genre, and
    user intent.  A strict envelope prevents commentary from being silently
    treated as part of a deliverable.
    """
    required_set = tuple(required)
    unknown = set(required_set) - set(SURFACES)
    if unknown:
        raise ProtocolError(f"未知 surface: {sorted(unknown)}")

    pattern = re.compile(
        r"<(?P<name>review_report|revision_plan|deliverable_body|verification_report)\s*>"
        r"(?P<body>.*?)"
        r"</(?P=name)\s*>",
        re.IGNORECASE | re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        raise ProtocolError("未找到 ReviewWrite surface 标签")

    surfaces: dict[str, str] = {}
    cursor = 0
    for match in matches:
        outside = text[cursor : match.start()]
        if strict_envelope and outside.strip():
            raise ProtocolError("surface 标签外存在未结构化文本")
        name = match.group("name").lower()
        if name in surfaces:
            raise ProtocolError(f"surface 重复: {name}")
        body = match.group("body").strip()
        if not body:
            raise ProtocolError(f"surface 为空: {name}")
        surfaces[name] = body
        cursor = match.end()

    if strict_envelope and text[cursor:].strip():
        raise ProtocolError("surface 标签外存在未结构化文本")

    missing = [name for name in required_set if name not in surfaces]
    if missing:
        raise ProtocolError(f"缺少 surface: {', '.join(missing)}")
    return surfaces


def extract_surface(text: str, surface: str, *, strict: bool = True) -> str:
    """Return one surface from a tagged response.

    ``full`` preserves the historical API for callers that already pass a
    body-only file.  Named surfaces require tags so a mixed response cannot be
    linted accidentally as if it were a publication-ready body.
    """
    if surface == "full":
        return text
    if surface not in SURFACES:
        raise ProtocolError(f"未知 surface: {surface}")
    return parse_surfaces(text, required=(surface,), strict_envelope=strict)[surface]


RULES: tuple[Rule, ...] = (
    Rule(
        "RW-F-001",
        "fail",
        "prompt-leakage",
        "正文疑似包含系统、开发者或提示模板内容。",
        r"(?:system\s+prompt|developer\s+(?:message|prompt)|you\s+are\s+chatgpt|"
        r"ignore\s+(?:all\s+|the\s+)?previous\s+instructions?|\[/?INST\]|"
        r"<\s*/?\s*(?:system|developer|assistant|user)\s*>|系统提示(?:词)?|"
        r"开发者(?:消息|提示)|忽略(?:此前|之前|以上|所有)[^。\n]{0,20}(?:指令|要求))",
    ),
    Rule(
        "RW-F-002",
        "fail",
        "reasoning-leakage",
        "正文疑似暴露隐藏推理、思考过程或分析通道。",
        r"(?:chain[ -]of[ -]thought|internal\s+reasoning|analysis\s+channel|"
        r"(?:我的|以下是|展示)(?:完整)?(?:思考|推理)(?:过程|链)|"
        r"逐步展示[^。\n]{0,10}(?:推理|思考))",
    ),
    Rule(
        "RW-F-003",
        "fail",
        "model-leakage",
        "正文疑似包含模型身份或能力免责声明。",
        r"(?:作为(?:一个|一名)?\s*(?:AI|人工智能|语言模型)|"
        r"as\s+an?\s+(?:AI|artificial\s+intelligence|language\s+model)|"
        r"I\s+am\s+(?:an?\s+)?(?:AI|language\s+model))",
    ),
    Rule(
        "RW-F-004",
        "fail",
        "instruction-leakage",
        "正文疑似复述用户任务、提示词或角色指令。",
        r"(?:(?:根据|按照)(?:用户|系统|开发者)(?:给出|提供|输入)?的?"
        r"(?:要求|提示|提示词|指令)|用户要求(?:我|我们)|"
        r"based\s+on\s+(?:the\s+)?user(?:'s)?\s+(?:prompt|instructions?)|"
        r"the\s+user\s+(?:asked|requested)\s+(?:me|us)\s+to)",
    ),
    Rule(
        "RW-F-005",
        "fail",
        "tool-leakage",
        "正文疑似包含工具调用、运行时或内部模块信息。",
        r"(?:我(?:调用|使用)了?[^。\n]{0,20}(?:搜索|浏览|代码|文件)?工具|"
        r"tool\s+call|tool\s+returned|工具调用|(?:SKILL|AGENTS)\.md|"
        r"working\s+tree|内部(?:skill|agent|route|模块|路由))",
    ),
    Rule(
        "RW-W-101",
        "warn",
        "process-narration",
        "用事实、方法或结论直接开头，不要在正文预告写作过程。",
        r"^[ \t]*(?:(?:本章|本节|下文|下面|接下来)(?:将|会|主要|首先)?"
        r"(?:介绍|讨论|分析|说明|探讨|展示)|(?:首先|接下来|下面)我(?:将|会|先)|"
        r"(?:in\s+this\s+(?:section|chapter)|this\s+(?:section|chapter)\s+will|"
        r"let\s+me\s+(?:explain|walk\s+you\s+through|analy[sz]e)))",
    ),
    Rule(
        "RW-W-102",
        "warn",
        "editorial-residue",
        "正文疑似包含编辑待办、改稿说明或版本过程。",
        r"(?:\bTODO\b|待(?:补充|修改|润色|核验)(?:[:：]|\b)|"
        r"(?:这段|本段|本节)[^。\n]{0,18}(?:需要|应当)[^。\n]{0,18}"
        r"(?:润色|补充|改写|引用)|当前版本[^。\n]{0,20}(?:下一轮|后续|提交前)|"
        r"(?:needs?|should\s+be)\s+(?:rewritten|polished|expanded|cited))",
    ),
    Rule(
        "RW-W-103",
        "warn",
        "chat-residue",
        "正式稿中疑似残留助手交接语或聊天式结尾。",
        r"(?:希望这对(?:你|您).{0,8}帮助|如果(?:你|您)?需要[^。\n]{0,20}"
        r"(?:我可以|可以继续)|如需[^。\n]{0,20}(?:请告诉我|我可以)|"
        r"let\s+me\s+know\s+if|hope\s+this\s+helps|happy\s+to\s+help|"
        r"here(?:'s|\s+is)\s+the\s+revised\s+version)",
    ),
    Rule(
        "RW-W-201",
        "warn",
        "formulaic-opening",
        "开场可能使用了空泛时代背景，建议直接进入具体问题。",
        r"(?:在(?:当今|这个|当前)[^，。\n]{0,12}(?:时代|背景|格局|环境)下?|"
        r"in\s+today(?:'s)?[^,.\n]{0,20}(?:world|landscape|environment))",
    ),
    Rule(
        "RW-W-202",
        "warn",
        "unsupported-significance",
        "文本可能只宣称重要性，建议补充具体影响或依据。",
        r"(?:具有(?:十分|非常|极其|重大)?(?:重要|重大|深远|关键)的?"
        r"(?:意义|价值|影响)|(?:意义|影响|价值)(?:十分|非常|极其)?(?:重大|深远)|"
        r"the\s+(?:implications?|stakes?|significance)\s+(?:are|is)\s+"
        r"(?:significant|important|profound|high))",
    ),
    Rule(
        "RW-W-203",
        "warn",
        "formulaic-contrast",
        "二元反转可能过于公式化；确认对比是否真的必要。",
        r"(?:不仅[^。\n]{1,50}而且|不是[^。\n]{1,50}而是|"
        r"not\s+(?:just|only)?[^.\n]{1,60}(?:but|it's)\s+)",
    ),
    Rule(
        "RW-W-204",
        "warn",
        "promotional-jargon",
        "政策或专业文本可能使用空泛宣传词，建议改为主体、行动和结果。",
        r"(?:(?:全面|深度)?(?:赋能|助力)[^。\n]{0,30}|"
        r"打造[^。\n]{0,18}(?:新格局|新生态|新引擎|新高地)|"
        r"(?:navigate|leverage|unlock)[^.\n]{0,30}(?:landscape|ecosystem|potential))",
    ),
    Rule(
        "RW-W-205",
        "warn",
        "formatting-pattern",
        "连续使用粗体标签式列表可能显得模板化；确认列表是否必要。",
        r"^[ \t]*[-*+]\s+\*\*[^*\n]{1,40}\*\*[：:]",
    ),
    Rule(
        "RW-W-206",
        "warn",
        "local-path",
        "公开正文疑似包含本地文件路径。",
        r"(?:/Users/[^\s)\]>'\"]+|/home/[^\s)\]>'\"]+|[A-Z]:\\Users\\[^\s)\]>'\"]+)",
    ),
    Rule(
        "RW-W-207",
        "warn",
        "abstract-intensifier",
        "强化词可能与抽象价值判断或空泛动作相邻；请补充主体、标准、范围或证据，不要机械删词。",
        r"(?:真正(?:的)?(?:价值|意义|影响|改变|突破|创新|能力|潜力|关键|核心)|"
        r"(?:真正)?值得(?:关注|重视|期待|借鉴|推广|信赖|投资)|"
        r"(?:真正|全面|深度|高度)(?:地)?(?:改变|影响|提升|推动|促进)[^。！？\n]{0,24}(?:未来|世界|格局|生活|行业|时代|发展))",
    ),
    Rule(
        "RW-W-208",
        "warn",
        "formulaic-bridge",
        "公式化转折或悬念可能替代了具体论点；确认它是否引入新信息，不能则直接写事实、判断或因果关系。",
        r"(?:换句话说|也就是说|简单来说|答案(?:很)?可能不是|"
        r"这(?:件事|一点|个问题)?最(?:吸引人|令人(?:兴奋|关注))的地方在于|"
        r"这(?:也)?是(?:最)?(?:危险|可怕|关键)的地方(?:在于)?|"
        r"in\s+other\s+words|the\s+answer\s+is\s+probably\s+not|"
        r"the\s+most\s+(?:appealing|interesting)\s+part\s+(?:is|is\s+that)|"
        r"this\s+is\s+(?:also\s+)?the\s+most\s+(?:dangerous|concerning)\s+part)",
    ),
)


# These are intentionally interaction rules rather than a larger forbidden-word
# list.  A single contrast or emphasis phrase can be useful; the signal appears
# when several of them are packed into a short technical argument.
TECHNICAL_TERMS = re.compile(
    r"(?:模型|参数|token|MoE|GPU|端侧|推理|内存|权重|芯片|算子|量化|带宽|"
    r"model|parameter|inference|memory|weights?|kernel|quantiz|bandwidth)",
    re.IGNORECASE,
)
COMPOSITE_CONTRASTS = re.compile(
    r"(?:不是[^。！？\n]{1,80}而是|不只是[^。！？\n]{1,80}更是|"
    r"未必[^。！？\n]{1,80}而更可能|not\s+(?:just|only)[^.?!\n]{1,90}(?:but|rather))",
    re.IGNORECASE,
)
IMPORTANCE_SIGNALS = re.compile(
    r"(?:这个细节很关键|这比[^。！？\n]{1,40}更重要|更重要的是|"
    r"(?:至少)?把方向拨正|真正(?:的)?关键(?:在于)?|the\s+key\s+point\s+is)",
    re.IGNORECASE,
)
AUDIENCE_SIGNALS = re.compile(
    r"(?:大多数用户|很多用户|普通用户|用户并不关心|"
    r"most\s+users|many\s+users|ordinary\s+users)",
    re.IGNORECASE,
)
FORECAST_SIGNALS = re.compile(
    r"(?:未必|更可能|有望|将(?:会)?|可能先|更有可能|"
    r"may\s+well|more\s+likely|is\s+likely\s+to|will\s+likely)",
    re.IGNORECASE,
)
TECHNICAL_NUMBER = re.compile(
    r"(?:\b\d+(?:\.\d+)?\s*[BMK]?\b|\b\d+(?:\.\d+)?%|"
    r"\d+(?:\.\d+)?\s*(?:B|M|G)参数)",
    re.IGNORECASE,
)


def _first_match(matches: list[re.Match[str]]) -> re.Match[str] | None:
    return matches[0] if matches else None


def _composite_findings(text: str, profiles: frozenset[str]) -> list[Finding]:
    """Find stacked signals without treating individual phrases as errors.

    Composite findings are enabled only for technical prose. This keeps a
    legitimate contrast in a policy or academic text from being penalized while
    catching the short, high-density pattern found in AI-generated tech posts.
    """
    if not TECHNICAL_TERMS.search(text):
        return []
    if not ({"public-article", "technical-commentary"} & profiles):
        return []

    contrasts = list(COMPOSITE_CONTRASTS.finditer(text))
    importance = list(IMPORTANCE_SIGNALS.finditer(text))
    audience = list(AUDIENCE_SIGNALS.finditer(text))
    forecasts = list(FORECAST_SIGNALS.finditer(text))
    findings: list[Finding] = []

    def add(
        rule_id: str,
        category: str,
        message: str,
        match: re.Match[str],
    ) -> None:
        line, column = _line_and_column(text, match.start())
        findings.append(
            Finding(
                rule_id=rule_id,
                severity="warn",
                category=category,
                message=message,
                line=line,
                column=column,
                excerpt=_excerpt_for(text, match.start()),
            )
        )

    if len(contrasts) >= 2:
        add(
            "RW-W-209",
            "stacked-formulaic-signal",
            "技术评论中短距离内连续出现多个二元反转；单个反转可以有功能，叠加时容易形成模板节奏。",
            contrasts[0],
        )
    if importance and contrasts:
        add(
            "RW-W-210",
            "empty-importance-stacking",
            "重要性提示与二元反转或总结判断叠加，但没有增加可验证信息；建议直接写机制、指标或条件。",
            _first_match(sorted(importance + contrasts, key=lambda item: item.start())) or importance[0],
        )
    if audience and forecasts:
        add(
            "RW-W-211",
            "unsupported-audience-generalization",
            "文本把用户群体、设备需求和行业方向连续概括；请补充样本、场景或适用范围。",
            _first_match(sorted(audience + forecasts, key=lambda item: item.start())) or audience[0],
        )
    if TECHNICAL_NUMBER.search(text) and (contrasts or forecasts):
        add(
            "RW-W-212",
            "technical-claim-scope",
            "技术数字、瓶颈或预测需要核对统计口径、测量对象、来源和适用条件；不要用流畅的结论替代技术限定。",
            TECHNICAL_NUMBER.search(text) or contrasts[0],
        )
    return findings


@dataclass(frozen=True)
class Exemption:
    """One authorized relaxation of a rule inside a declared genre or context.

    ReviewWrite's philosophy is fixed boundaries with contextual judgment, not a
    genre-blind blacklist.  A term like ``system prompt`` is genuine leakage in a
    policy brief but the subject matter of an AI-safety paper.  ``downgrade`` keeps
    a verify signal (fail -> warn) so the model still confirms the term is being
    discussed rather than accidentally exposed; ``ignore`` drops a warning that is
    functional in the declared genre.  Exemptions never touch fact, citation, or
    number protection -- those live in semantic review, not this preflight.
    """

    profile: str
    rule_id: str
    action: str  # "downgrade" (fail -> warn) or "ignore"
    rationale: str


# Topic/context profiles authorized by references/leakage.md "允许出现的情况".
CONTEXT_PROFILES: frozenset[str] = frozenset(
    {
        "ai-safety",
        "prompt-engineering",
        "software-docs",
        "ai-disclosure",
        "dialogue-transcript",
        "editorial-audit",
    }
)

# Genre profiles matching references/genre-packs/<id>.md filenames.
GENRE_PROFILES: frozenset[str] = frozenset(
    {
        "official-document",
        "policy-document",
        "public-article",
        "technical-commentary",
        "research-report",
        "marketing-copy",
    }
)


EXEMPTIONS: tuple[Exemption, ...] = (
    # AI-safety / prompt-injection / model-transparency research discusses these
    # terms as its object of study; keep a warn so the author confirms context.
    Exemption("ai-safety", "RW-F-001", "downgrade", "提示词术语是 AI 安全研究的讨论对象"),
    Exemption("ai-safety", "RW-F-002", "downgrade", "推理/分析通道是模型透明度研究的主题"),
    Exemption("ai-safety", "RW-F-003", "downgrade", "模型身份是 AI 论文的讨论对象"),
    Exemption("ai-safety", "RW-F-005", "downgrade", "工具/运行时术语是智能体研究的主题"),
    # Prompt templates and software docs legitimately name prompts and modules.
    Exemption("prompt-engineering", "RW-F-001", "downgrade", "提示模板本身就是正文内容"),
    Exemption("prompt-engineering", "RW-F-005", "downgrade", "工具与模块名是提示工程内容"),
    Exemption("software-docs", "RW-F-005", "downgrade", "skill/agent/route/模块名是文档主题"),
    # An acknowledgement or methods statement may disclose AI assistance.
    Exemption("ai-disclosure", "RW-F-003", "downgrade", "AI 辅助披露声明可合法提及模型身份"),
    # A transcript's content is exactly chat turns and closings.
    Exemption("dialogue-transcript", "RW-F-001", "downgrade", "对话标签是转写内容"),
    Exemption("dialogue-transcript", "RW-W-103", "ignore", "聊天式收尾是转写记录的内容"),
    # An editorial audit report quotes leakage and edits as evidence.
    Exemption("editorial-audit", "RW-F-001", "downgrade", "审计报告引用泄漏作为证据"),
    Exemption("editorial-audit", "RW-F-002", "downgrade", "审计报告引用推理泄漏作为证据"),
    Exemption("editorial-audit", "RW-F-003", "downgrade", "审计报告引用模型自述作为证据"),
    Exemption("editorial-audit", "RW-F-004", "downgrade", "审计报告引用指令复述作为证据"),
    Exemption("editorial-audit", "RW-F-005", "downgrade", "审计报告引用工具泄漏作为证据"),
    Exemption("editorial-audit", "RW-W-102", "ignore", "审计报告本就记录编辑待办"),
    # Bold-labeled list items are a standard, functional form in these genres.
    Exemption("official-document", "RW-W-205", "ignore", "公文条目式结构是规范形式"),
    Exemption("policy-document", "RW-W-205", "ignore", "政策条文的结构化条目是规范形式"),
    Exemption("public-article", "RW-W-205", "ignore", "公众号常用加粗小标题分节"),
    Exemption("research-report", "RW-W-205", "ignore", "研究报告常用结构化要点"),
    Exemption("marketing-copy", "RW-W-205", "ignore", "营销文案常用加粗卖点列表"),
)


ALL_PROFILES: frozenset[str] = CONTEXT_PROFILES | GENRE_PROFILES


def _resolve_action(rule_id: str, active: frozenset[str]) -> tuple[str | None, str | None]:
    """Return (action, profile) for the strongest matching exemption.

    ``ignore`` outranks ``downgrade`` when several active profiles both apply.
    """
    downgrade_profile: str | None = None
    for exemption in EXEMPTIONS:
        if exemption.rule_id != rule_id or exemption.profile not in active:
            continue
        if exemption.action == "ignore":
            return "ignore", exemption.profile
        if downgrade_profile is None:
            downgrade_profile = exemption.profile
    if downgrade_profile is not None:
        return "downgrade", downgrade_profile
    return None, None


def _line_and_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    last_newline = text.rfind("\n", 0, offset)
    column = offset + 1 if last_newline < 0 else offset - last_newline
    return line, column


def _excerpt_for(text: str, offset: int, limit: int = 180) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end < 0:
        end = len(text)
    excerpt = " ".join(text[start:end].strip().split())
    return excerpt if len(excerpt) <= limit else excerpt[: limit - 1] + "…"


def lint_text(
    text: str,
    ignored_rules: Iterable[str] = (),
    profiles: Iterable[str] = (),
) -> list[Finding]:
    ignored = set(ignored_rules)
    active = frozenset(profiles)
    findings: list[Finding] = []
    seen: set[tuple[str, int]] = set()

    for rule in RULES:
        if rule.rule_id in ignored:
            continue
        action, profile = _resolve_action(rule.rule_id, active) if active else (None, None)
        if action == "ignore":
            continue
        for match in re.finditer(rule.pattern, text, rule.flags):
            key = (rule.rule_id, match.start())
            if key in seen:
                continue
            seen.add(key)
            severity = rule.severity
            applied_profile: str | None = None
            original_severity: str | None = None
            if action == "downgrade" and severity == "fail":
                original_severity = severity
                severity = "warn"
                applied_profile = profile
            line, column = _line_and_column(text, match.start())
            findings.append(
                Finding(
                    rule_id=rule.rule_id,
                    severity=severity,
                    category=rule.category,
                    message=rule.message,
                    line=line,
                    column=column,
                    excerpt=_excerpt_for(text, match.start()),
                    applied_profile=applied_profile,
                    original_severity=original_severity,
                )
            )

    findings.extend(_composite_findings(text, active))
    return sorted(findings, key=lambda item: (item.line, item.column, item.rule_id))


def exit_code_for(findings: Sequence[Finding], strict: bool = False) -> int:
    if any(item.severity == "fail" for item in findings):
        return 1
    if strict and findings:
        return 1
    return 0


def _read_input(path_value: str) -> tuple[str, str]:
    if path_value == "-":
        return sys.stdin.read(), "<stdin>"
    path = Path(path_value)
    try:
        return path.read_text(encoding="utf-8"), str(path)
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"无法读取 {path}: {exc}") from exc


def _render_text(
    source: str,
    findings: Sequence[Finding],
    strict: bool,
    profiles: Sequence[str] = (),
) -> str:
    fail_count = sum(item.severity == "fail" for item in findings)
    warn_count = sum(item.severity == "warn" for item in findings)
    lines = [f"ReviewWrite preflight: {source}"]
    if profiles:
        lines.append(f"profiles: {', '.join(profiles)}")

    for item in findings:
        header = (
            f"{item.severity.upper()} {item.rule_id} "
            f"L{item.line}:C{item.column} [{item.category}] {item.message}"
        )
        if item.applied_profile:
            header += (
                f" (由 {item.original_severity} 降级；profile={item.applied_profile})"
            )
        lines.append(header)
        lines.append(f"  {item.excerpt}")

    status = "FAIL" if fail_count or (strict and warn_count) else "PASS"
    lines.append(f"{status}: {fail_count} fail, {warn_count} warn")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="检测正式稿中的提示、推理、工作流和聊天残留。"
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="UTF-8 文本文件；使用 - 从 stdin 读取（--list-profiles 时可省略）",
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default="text", dest="output_format"
    )
    parser.add_argument(
        "--strict", action="store_true", help="将风格警告也视为失败"
    )
    parser.add_argument(
        "--ignore-rule",
        action="append",
        default=[],
        metavar="RULE_ID",
        help="忽略指定规则；可重复使用",
    )
    parser.add_argument(
        "--surface",
        choices=("full", *SURFACES),
        default="full",
        help="只检查指定输出 surface；命名 surface 必须使用标签包裹",
    )
    parser.add_argument(
        "--genre",
        choices=sorted(GENRE_PROFILES),
        metavar="GENRE",
        help="声明体裁；对该体裁中功能性的格式/风格警告放宽",
    )
    parser.add_argument(
        "--context",
        action="append",
        default=[],
        choices=sorted(CONTEXT_PROFILES),
        metavar="CONTEXT",
        help="声明授权语境（如 ai-safety）；把该语境下合理的硬失败降级为警告；可重复",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="列出可用体裁与语境 profile 及其豁免规则后退出",
    )
    return parser


def _render_profiles() -> str:
    lines = ["ReviewWrite profiles"]
    for label, names in (("genre", sorted(GENRE_PROFILES)), ("context", sorted(CONTEXT_PROFILES))):
        for name in names:
            entries = [ex for ex in EXEMPTIONS if ex.profile == name]
            lines.append(f"[{label}] {name}")
            for exemption in entries:
                lines.append(
                    f"  {exemption.action:9s} {exemption.rule_id}  {exemption.rationale}"
                )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_profiles:
        print(_render_profiles())
        return 0

    if args.path is None:
        parser.error("缺少 path 参数（仅 --list-profiles 时可省略）")

    profiles = ([args.genre] if args.genre else []) + list(args.context)

    try:
        text, source = _read_input(args.path)
        text = extract_surface(text, args.surface)
    except (RuntimeError, ProtocolError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    findings = lint_text(text, args.ignore_rule, profiles)
    code = exit_code_for(findings, args.strict)

    if args.output_format == "json":
        payload = {
            "source": source,
            "surface": args.surface,
            "profiles": profiles,
            "status": "fail" if code else "pass",
            "strict": args.strict,
            "summary": {
                "fail": sum(item.severity == "fail" for item in findings),
                "warn": sum(item.severity == "warn" for item in findings),
            },
            "findings": [asdict(item) for item in findings],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        rendered_source = f"{source} [{args.surface}]" if args.surface != "full" else source
        print(_render_text(rendered_source, findings, args.strict, profiles))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
