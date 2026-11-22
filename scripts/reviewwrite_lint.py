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

from runtime_io import configure_utf8_stdio


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
        r"<\s*/?\s*(?:think|thought|reasoning|scratchpad|reflection|inner_monologue)\s*>|"
        r"◁\s*/?\s*think\s*▷|"
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
        r"working\s+tree|内部(?:skill|agent|route|模块|路由)|"
        r"(?:🤖\s*)?generated\s+with\s+(?:claude\s+code|chatgpt|gemini|grok|cursor|codex)|"
        r"co-authored-by:\s*(?:claude|chatgpt|gemini|grok|github\s+copilot))",
    ),
    Rule(
        "RW-F-006",
        "fail",
        "internal-contract-leakage",
        "正文疑似暴露只供宿主或编辑流程使用的内部契约术语；交付稿应直接给出读者可用的事实、结论或建议。",
        r"(?:证据边界|保留(?:约束|项)|验收标准|交付(?:正文|表面)|审写协议|评审协议|"
        r"内部(?:状态|规则|契约|协议|检查清单)|回改(?:一|两|三)?轮|最终门禁|严格终检|"
        r"写前预检|正文抽取|deliverable[_ -]?body|review[_ -]?report|revision[_ -]?plan|"
        r"verification[_ -]?report|preflight(?:\s+check)?|final\s+gate|repair\s+loop|"
        r"evidence\s+boundary|preserve\s+constraints?|acceptance\s+criteria)",
    ),
    Rule(
        "RW-F-007",
        "fail",
        "latent-instruction-process-leakage",
        "正文疑似把任务服从、写作要求或生成步骤写给读者；请直接交付内容，不要叙述如何满足指令。",
        r"(?:(?:为了|为)(?:满足|响应|遵循)(?:用户|客户|任务|上述|相关)?(?:的)?(?:要求|需求|指令)|"
        r"(?:根据|按照|依照)(?:本次|当前|上述|相关|任务)(?:的)?(?:要求|指令)[，,]?[^。！？\n]{0,24}"
        r"(?:本文|本稿|下文|接下来|先|将)|"
        r"(?:本段|本节|本文)(?:需要|应当|必须)(?:先|重点)?[^。！？\n]{0,24}"
        r"(?:保持|采用|使用)(?:正式|专业|简洁|自然|学术)(?:语气|文风|表达)|"
        r"to\s+(?:satisfy|follow|comply\s+with)(?:\s+the)?(?:\s+user)?(?:'s)?\s+"
        r"(?:request|requirements?|instructions?))",
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
    Rule(
        "RW-W-214",
        "warn",
        "extreme-importance-label",
        "极端重要性标签可能用简短口号替代判断标准；请补充比较范围、对象和依据。",
        r"(?:最硬的一点|最关键的是|最核心的是|真正重要的是|最值得注意的是|"
        r"绝对不能|毋庸置疑|关键就在于)(?:[^。！？\n]{0,28})",
    ),
    Rule(
        "RW-W-215",
        "warn",
        "meta-narrative-packaging",
        "叙事、故事或底层逻辑可能只是抽象包装；请展开主体、行动、事实链和结果。",
        r"(?:这(?:是|是一种|背后是|背后有|本质是|核心是|归根结底是)[^。！？\n]{0,24}"
        r"(?:叙事|故事|底层逻辑|背后逻辑)|"
        r"(?:叙事|故事|底层逻辑|背后逻辑)[^。！？\n]{0,14}"
        r"(?:决定|解释|推动|重塑|改变))",
    ),
    Rule(
        "RW-W-216",
        "warn",
        "discourse-filler",
        "连接语可能只是在提示读者“注意”，却没有增加信息；请直接写事实或判断。",
        r"(?:值得注意的是|需要指出的是|可以看出|it\s+is\s+worth\s+noting(?:\s+that)?|"
        r"it\s+should\s+be\s+noted(?:\s+that)?)(?:[，,:：])?",
    ),
    Rule(
        "RW-W-217",
        "warn",
        "redundant-summary",
        "总结标记可能重复前文或越过证据拔高；只保留新增结论及其适用范围。",
        r"(?:总的来说|归根结底|由此可见|all\s+in\s+all|in\s+conclusion)(?:[，,:：])?",
    ),
    Rule(
        "RW-W-219",
        "warn",
        "translationese",
        "句子疑似保留了生硬的跨语言结构；请按目标语言的主谓宾和信息顺序重写。",
        r"(?:对于[^，。！？\n]{1,24}而言[，,][^。！？\n]{0,28}进行(?:了)?一个|"
        r"进行(?:了)?一个[^。！？\n]{1,32}(?:分析|评估|讨论|研究|判断|说明))",
    ),
    Rule(
        "RW-W-222",
        "warn",
        "title-terminal-punctuation",
        "标题疑似带有句末句号；标题通常不使用句号，除非该标点是标题本身的一部分或明确的问句/感叹句结构。",
        r"^[ \t]{0,3}#{1,6}[ \t]+[^\n#]+[。．｡\.]"
        r"(?:[”’\"'）》」』】])?[ \t]*(?:#+[ \t]*)?$",
    ),
    Rule(
        "RW-W-224",
        "warn",
        "self-certifying-claim",
        "句子可能用确定性宣告替代事实或依据；请直接写事实、适用范围和可支持的结论。",
        r"(?:(?:事实|结果|实践|经验)(?:已经|已|再次)?(?:充分|清楚|明确|有力)?"
        r"(?:证明|说明|表明|印证)|"
        r"这(?:一事实|一结果|些事实|些结果)?(?:已经|已|再次)?(?:充分|清楚|明确|有力|无疑)?"
        r"(?:证明|说明|表明|印证)|"
        r"(?:毫无疑问|无可置疑|显而易见|不难看出|显然可见|足以证明|再次印证)(?:[，,:：])?|"
        r"this\s+(?:clearly|plainly|undoubtedly|conclusively)\s+"
        r"(?:shows|demonstrates|proves|confirms)|there\s+is\s+no\s+doubt(?:\s+that)?)",
    ),
    Rule(
        "RW-W-225",
        "warn",
        "certainty-intensifier",
        "强化词与笼统结论相邻；请核对可验证标准、对象、范围和依据。",
        r"(?:(?:真正|完全|彻底|绝对|显然|无疑)(?:地)?"
        r"(?:改变|解决|证明|说明|表明|实现|消除|成功|正确|有效|可靠|可行|成熟|领先)|"
        r"(?:完全|绝对|无疑)(?:正确|成功|有效|可靠|可行|成熟|领先)|"
        r"(?:truly|completely|absolutely|clearly|undoubtedly)\s+"
        r"(?:changes?|solves?|proves?|demonstrates?|succeeds?|works?|correct|effective|reliable))",
    ),
    Rule(
        "RW-W-226",
        "warn",
        "inference-process-narration",
        "正文疑似叙述得出结论的过程；请直接写推论、依据和成立条件。",
        r"(?:(?:因此|据此|由此)(?:我们)?(?:可以|能够|足以)?(?:得出|作出)(?:一个)?(?:结论|判断)|"
        r"(?:我们)?(?:可以|有理由)(?:据此)?(?:认为|相信|判断)|"
        r"it\s+(?:can\s+therefore|follows\s+that\s+we\s+can)\s+be\s+concluded|"
        r"we\s+(?:can|have\s+reason\s+to)\s+(?:conclude|believe|infer))",
    ),
    Rule(
        "RW-W-228",
        "warn",
        "ornamental-separator",
        "正式正文疑似使用模型生成的装饰横线分隔内容；请改为真实标题层级、段落过渡或直接连续行文。",
        r"^[ \t]*(?:-{3,}|_{3,}|(?:\*[ \t]*){3,}|—{3,}|－{3,})[ \t]*\r?$",
    ),
    Rule(
        "RW-W-230",
        "warn",
        "reasoning-monologue-residue",
        "正文疑似残留推理模型的自言自语、自我纠正或拆解独白；请只保留面向读者的最终分析与结论。",
        r"(?:让我(?:们)?先(?:理清|捋一捋|拆解一下|重新审视)|"
        r"(?:等等|慢着|不对)[，,——\- ]{1,3}(?:这里|我们|让我)(?:需要|应该|得|再|重新)|"
        r"思考到这里[，,]|"
        r"(?:wait|hold\s+on)[, —\-]{1,3}(?:let(?:'s|\s+me)|that(?:'s|\s+is)\s+not\s+quite)|"
        r"let\s+me\s+(?:step\s+back|rethink|double[- ]check|think\s+through))",
    ),
    Rule(
        "RW-W-231",
        "warn",
        "buzzword-collocation",
        "句子疑似使用互联网黑话或空洞商业行话替代具体动作；请改写为主体、行动、对象、指标和机制。",
        r"(?:对齐颗粒度|拉通对齐|打出[^，。！？\n]{0,8}组合拳|组合拳打法|"
        r"(?:占领|打透|击穿|引爆|撬动)[^，。！？\n]{0,10}(?:用户)?(?:心智|痛点|痒点|爽点|圈层|私域|势能)|"
        r"沉淀[^，。！？\n]{0,10}(?:方法论|打法|心智|势能)|"
        r"以[^，。！？\n]{1,16}为抓手[，,]?(?:打通|拉通|撬动|赋能|沉淀|构建|形成)|"
        r"(?:打通|跑通|构建|形成)[^，。！？\n]{0,12}(?:生态|商业|流量|增长|心智|私域|打法|赋能)闭环|"
        r"实现品效合一|降维打击|"
        r"(?:move\s+the\s+needle|low[- ]hanging\s+fruit|synergistic\s+ecosystem|"
        r"double[- ]click\s+on\s+(?:this|that)|"
        r"(?:truly|quietly|genuinely|peculiarly)\s+load[- ]bearing|"
        r"load[- ]bearing\s+(?:insight|assumption|claim|detail|metaphor|concept|phrase)))",
    ),
    Rule(
        "RW-W-233",
        "warn",
        "engagement-hook-cliche",
        "正文疑似混入网感钩子、口语标榜或伪坦诚垫词；正式交付稿请直接陈述事实、分歧或结论。",
        r"(?:(?:说白了|不整虚的|打开天窗说亮话)[，,：:]|"
        r"(?:更)?扎心的是[，,：:]?|(?:接下来)?重点来了[，,：:！!]|敲黑板[，,：:！!]|"
        r"真相(?:其实)?很残酷|"
        r"here(?:'s|\s+is)\s+the\s+(?:kicker|plot\s+twist)|"
        r"\bbuckle\s+up\b|\bno\s+fluff\b|"
        r"let(?:'s|\s+us)\s+(?:dive\s+(?:right\s+)?in|be\s+real|cut\s+to\s+the\s+chase)|"
        r"what\s+if\s+I\s+told\s+you|"
        r"^[ \t]*honestly,\s+)",
    ),
)


COMPOSITE_RULE_IDS: frozenset[str] = frozenset(
    {
        "RW-W-209",
        "RW-W-210",
        "RW-W-211",
        "RW-W-212",
        "RW-W-213",
        "RW-W-218",
        "RW-W-220",
        "RW-W-221",
        "RW-W-223",
        "RW-W-227",
        "RW-W-229",
        "RW-W-232",
        "RW-W-234",
    }
)
ALL_RULE_IDS: frozenset[str] = frozenset({rule.rule_id for rule in RULES}) | COMPOSITE_RULE_IDS


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
ENUMERATION_MARKERS = re.compile(
    r"(?:第一|第二|第三|第四|第五|首先|其次|再次|最后|"
    r"first|second|third|fourth|fifth|firstly|secondly|thirdly|finally)"
    r"(?=[、，,.:：．.\s])",
    re.IGNORECASE,
)
INFERENCE_MARKERS = re.compile(
    r"(?:我们可以看到|我们能够看到|这说明|这表明|we\s+can\s+see(?:\s+that)?|"
    r"this\s+(?:shows|indicates)(?:\s+that)?)(?:[，,:：])?",
    re.IGNORECASE,
)
VAGUE_AUTHORITY = re.compile(
    r"(?:(?:研究|调查|数据|统计)(?:结果)?(?:表明|显示|发现)|"
    r"(?:专家|业内人士|业界|学界)(?:普遍)?(?:认为|指出|表示)|"
    r"(?:studies|research|surveys?|data|statistics)\s+(?:show|shows|suggest|suggests|indicate|indicates)|"
    r"experts?\s+(?:believe|argue|say))",
    re.IGNORECASE,
)
CITATION_SIGNAL = re.compile(
    r"(?:\[[0-9,，;；\-–— ]+\]|（[^）\n]{0,50}\d{4}[^）\n]*）|"
    r"\([^\)\n]{0,50}\d{4}[^\)\n]*\)|来源\s*[:：]|doi\s*[:：]?|https?://)",
    re.IGNORECASE,
)
SYMMETRIC_STRUCTURES = re.compile(
    r"(?:既要[^。！？；;\n]{1,60}也要|从[^。！？；;\n]{1,24}到[^。！？；;\n]{1,24}(?=[，。！？；;])|"
    r"both\s+[^.?!;\n]{1,60}\s+and\s+[^.?!;\n]{1,60}(?=[.?!;]))",
    re.IGNORECASE,
)
HEADING_RHETORIC = re.compile(
    r"(?:这才是|真正(?:的)?(?:问题|关键|核心|答案|价值|意义)|"
    r"完全(?:改变|解决|不同)|彻底(?:改变|解决)|"
    r"不是[^。！？\n]{1,50}而是|为什么[^。！？\n]{0,30}才|"
    r"the\s+real\s+(?:problem|key|answer)|not\s+[^.?!\n]{1,60}\s+but)",
    re.IGNORECASE,
)
RHETORICAL_STACK = re.compile(
    r"(?:真正|完全|彻底|绝对|显然|无疑|毫无疑问|事实(?:已经|已)?(?:充分)?证明|"
    r"这(?:充分|清楚|明确)?(?:说明|表明|证明)|这才是|不是[^。！？\n]{1,60}而是|"
    r"由此可见|因此(?:我们)?可以得出|"
    r"truly|completely|absolutely|clearly|undoubtedly|this\s+proves|not\s+[^.?!\n]{1,60}\s+but)",
    re.IGNORECASE,
)
BUZZWORD_TOKENS = re.compile(
    r"(?:抓手|颗粒度|组合拳|拉通|心智|势能|打法|卡位|生态位|痛点|痒点|爽点|"
    r"私域|品效合一|赋能|裂变|复盘|矩阵式)",
    re.IGNORECASE,
)
ADDITIVE_TRANSITIONS = re.compile(
    r"(?:^|(?<=[。！？；.!?\n]))[ \t]*(?:此外|与此同时|不仅如此|更为重要的是|在此基础上|进一步来看|"
    r"furthermore|moreover|additionally|consequently|importantly)[，,:]",
    re.IGNORECASE | re.MULTILINE,
)
SHALLOW_PARTICIPLE_TAILS = re.compile(
    r"(?:[，,][ \t]*(?:从而|进而)?(?:充分)?(?:彰显|凸显|印证|折射)了[^。！？\n]{1,28}"
    r"(?:重要性|必要性|关键作用|深远意义|核心价值)|"
    r",\s*(?:thereby\s+)?(?:highlighting|underscoring|showcasing|exemplifying|paving\s+the\s+way\s+for)\s+"
    r"(?:the\s+)?(?:importance|significance|value|role|need|potential)\b)",
    re.IGNORECASE,
)
SETEXT_HEADING_RE = re.compile(
    r"(?m)^(?P<title>[ \t]*[^ \t\r\n#>*+\-][^\n\r]{0,79})\r?\n(?P<underline>[=-]{3,}[ \t]*)\r?$"
)
YAML_FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n(?:[A-Za-z0-9_.-]+[ \t]*:[^\n]*\r?\n)+---[ \t]*(?:\r?\n|\Z)"
)
FENCED_CODE_BLOCK_RE = re.compile(
    r"(?ms)^([ \t]{0,3})(`{3,}|~{3,})[^\n]*\n.*?(?:^\1\2[ \t]*\r?$|(?=\Z))"
)


def _blank_preserving_newlines(segment: str) -> str:
    return "".join(ch if ch in ("\n", "\r") else " " for ch in segment)


def _mask_non_prose(text: str) -> str:
    """Mask YAML frontmatter and fenced code blocks while preserving line/column offsets."""
    masked = YAML_FRONTMATTER_RE.sub(lambda m: _blank_preserving_newlines(m.group(0)), text)
    return FENCED_CODE_BLOCK_RE.sub(lambda m: _blank_preserving_newlines(m.group(0)), masked)


def _first_match(matches: list[re.Match[str]]) -> re.Match[str] | None:
    return matches[0] if matches else None


def _has_window_cluster(matches: Sequence[re.Match[str]], count: int, window_chars: int) -> re.Match[str] | None:
    if len(matches) < count:
        return None
    for idx in range(len(matches) - count + 1):
        if matches[idx + count - 1].start() - matches[idx].start() <= window_chars:
            return matches[idx]
    return None


def _composite_findings(
    text: str,
    profiles: frozenset[str],
    *,
    source_text: str | None = None,
) -> list[Finding]:
    """Find source/syntax stacks without treating every individual phrase as an error.

    Authority, inference-narration, buzzword-stacking, homogenized transitions,
    and symmetry checks apply across prose. Technical contrast and scope
    composites remain limited to public articles and technical commentary.
    """
    raw = source_text if source_text is not None else text
    findings: list[Finding] = []

    def add(
        rule_id: str,
        category: str,
        message: str,
        match: re.Match[str],
    ) -> None:
        line, column = _line_and_column(raw, match.start())
        findings.append(
            Finding(
                rule_id=rule_id,
                severity="warn",
                category=category,
                message=message,
                line=line,
                column=column,
                excerpt=_excerpt_for(raw, match.start()),
            )
        )

    heading_candidates: list[tuple[int, str]] = []
    for match in re.finditer(r"(?m)^[ \t]{0,3}#{1,6}[ \t]+(?P<title>[^\n#]+?)[ \t]*(?:#+[ \t]*)?$", text):
        heading_candidates.append((match.start("title"), match.group("title")))
    for match in SETEXT_HEADING_RE.finditer(text):
        heading_candidates.append((match.start("title"), match.group("title")))
    first = re.match(r"\A[ \t]*(?P<title>[^\n\r]{1,48})\r?\n[ \t]*\r?\n", text)
    if first and first.group("title").strip() and not first.group("title").lstrip().startswith("#"):
        heading_candidates.append((first.start("title"), first.group("title")))
    for offset, title in heading_candidates:
        marker = HEADING_RHETORIC.search(title)
        if not marker:
            continue
        absolute = offset + marker.start()
        synthetic = re.match(r".", text[absolute:])
        if synthetic:
            line, column = _line_and_column(raw, absolute)
            findings.append(
                Finding(
                    rule_id="RW-W-223",
                    severity="warn",
                    category="rhetorical-heading",
                    message="标题疑似直接输出重要性判断、二元反转或内部结论；请改为读者可识别的对象、事件或问题。",
                    line=line,
                    column=column,
                    excerpt=_excerpt_for(raw, absolute),
                )
            )

    paragraph_start = 0
    for paragraph in re.split(r"\r?\n[ \t]*\r?\n", text):
        if paragraph.strip():
            markers = list(RHETORICAL_STACK.finditer(paragraph))
            if len(markers) >= 2:
                absolute = paragraph_start + markers[0].start()
                line, column = _line_and_column(raw, absolute)
                findings.append(
                    Finding(
                        rule_id="RW-W-227",
                        severity="warn",
                        category="rhetorical-reasoning-stack",
                        message="同一段落连续使用强化、自证、反转或推论标记，但不一定增加事实；请按事实、条件和结论重组。",
                        line=line,
                        column=column,
                        excerpt=_excerpt_for(raw, absolute),
                    )
                )
            buzzwords = list(BUZZWORD_TOKENS.finditer(paragraph))
            if len(buzzwords) >= 3:
                absolute = paragraph_start + buzzwords[0].start()
                line, column = _line_and_column(raw, absolute)
                findings.append(
                    Finding(
                        rule_id="RW-W-232",
                        severity="warn",
                        category="buzzword-stacking",
                        message="同一段落密集堆叠多个互联网或职场黑话，信息密度偏低；请拆解为主体、动作、对象、指标和因果关系。",
                        line=line,
                        column=column,
                        excerpt=_excerpt_for(raw, absolute),
                    )
                )
        paragraph_start += len(paragraph)
        following = re.match(r"\r?\n[ \t]*\r?\n", text[paragraph_start:])
        if following:
            paragraph_start += len(following.group(0))

    transition_cluster = _has_window_cluster(list(ADDITIVE_TRANSITIONS.finditer(text)), 3, 600)
    tail_cluster = _has_window_cluster(list(SHALLOW_PARTICIPLE_TAILS.finditer(text)), 2, 800)
    homogenized_anchor = _first_match(
        sorted(
            [m for m in (transition_cluster, tail_cluster) if m is not None],
            key=lambda item: item.start(),
        )
    )
    if homogenized_anchor is not None:
        add(
            "RW-W-234",
            "homogenized-transition-tail-stacking",
            "相邻句段连续堆叠机械递进连接词或空泛拔高尾句，容易形成高重复模板感；请改为直接主谓宾推进并按证据权重调整句长。",
            homogenized_anchor,
        )

    bullet_items = list(
        re.finditer(
            r"(?m)^[ \t]*[-*+][ \t]+(?!\[[ xX]\])(?P<body>[^\n]{1,100})$",
            text,
        )
    )
    short_fragments = [
        match
        for match in bullet_items
        if len(match.group("body").strip()) <= 60
        and not re.search(r"[。！？.!?；;：:]$", match.group("body").strip())
    ]
    if len(short_fragments) >= 3:
        match = short_fragments[0]
        line, column = _line_and_column(raw, match.start())
        findings.append(
            Finding(
                rule_id="RW-W-229",
                severity="warn",
                category="fragment-bullet-stacking",
                message="连续短横杠项目可能把正文切成标签碎片；请合并为连续论述或改用有实际层级的结构。正式条款和操作清单可保留。",
                line=line,
                column=column,
                excerpt=_excerpt_for(raw, match.start()),
            )
        )

    inference_markers = list(INFERENCE_MARKERS.finditer(text))
    if len(inference_markers) >= 2:
        add(
            "RW-W-220",
            "inference-narration-stacking",
            "短文本连续使用“我们可以看到/这说明/这表明”推进判断；请直接写可验证事实和推论条件。",
            inference_markers[0],
        )

    for match in VAGUE_AUTHORITY.finditer(text):
        sentence_start = max(
            text.rfind(mark, 0, match.start())
            for mark in ("。", "！", "？", ".", "!", "?", "\n")
        ) + 1
        sentence_end_candidates = []
        for mark in ("。", "！", "？", ".", "!", "?", "\n"):
            position = text.find(mark, match.end())
            if position >= 0:
                sentence_end_candidates.append(position)
        sentence_end = min(sentence_end_candidates) if sentence_end_candidates else len(text)
        context = text[sentence_start:sentence_end]
        if not CITATION_SIGNAL.search(context):
            add(
                "RW-W-218",
                "vague-authority",
                "“研究表明/专家认为”等归因没有可定位来源；补充真实引用，否则改为有限判断。",
                match,
            )

    symmetric_structures = list(SYMMETRIC_STRUCTURES.finditer(text))
    if len(symmetric_structures) >= 2:
        add(
            "RW-W-221",
            "symmetric-structure-stacking",
            "短文本连续使用对称句式，可能以形式完整替代信息取舍；请按事实、判断和行动重组。",
            symmetric_structures[0],
        )

    if not ({"public-article", "technical-commentary"} & profiles):
        return findings

    is_technical = bool(TECHNICAL_TERMS.search(text))
    contrasts = list(COMPOSITE_CONTRASTS.finditer(text))
    importance = list(IMPORTANCE_SIGNALS.finditer(text))
    audience = list(AUDIENCE_SIGNALS.finditer(text))
    forecasts = list(FORECAST_SIGNALS.finditer(text))
    enum_markers = [
        match
        for match in ENUMERATION_MARKERS.finditer(text)
        if not text[: match.start()].rstrip()
        or text[: match.start()].rstrip()[-1] in "。！？\n"
    ]

    if is_technical and len(contrasts) >= 2:
        add(
            "RW-W-209",
            "stacked-formulaic-signal",
            "技术评论中短距离内连续出现多个二元反转；单个反转可以有功能，叠加时容易形成模板节奏。",
            contrasts[0],
        )
    if is_technical and importance and contrasts:
        add(
            "RW-W-210",
            "empty-importance-stacking",
            "重要性提示与二元反转或总结判断叠加，但没有增加可验证信息；建议直接写机制、指标或条件。",
            _first_match(sorted(importance + contrasts, key=lambda item: item.start())) or importance[0],
        )
    if is_technical and audience and forecasts:
        add(
            "RW-W-211",
            "unsupported-audience-generalization",
            "文本把用户群体、设备需求和行业方向连续概括；请补充样本、场景或适用范围。",
            _first_match(sorted(audience + forecasts, key=lambda item: item.start())) or audience[0],
        )
    if is_technical and TECHNICAL_NUMBER.search(text) and (contrasts or forecasts):
        add(
            "RW-W-212",
            "technical-claim-scope",
            "技术数字、瓶颈或预测需要核对统计口径、测量对象、来源和适用条件；不要用流畅的结论替代技术限定。",
            TECHNICAL_NUMBER.search(text) or contrasts[0],
        )
    if len(enum_markers) >= 3:
        add(
            "RW-W-213",
            "mechanical-enumeration",
            f"短文本内出现 {len(enum_markers)} 个句首排序标记；如果每段都用“第一/第二/第三”推进，文章可能只有编号变化而没有论证或语气变化。",
            enum_markers[0],
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


@dataclass(frozen=True)
class MatchExemption:
    """A narrow exemption that applies only to the matched phrase."""

    profile: str
    rule_id: str
    pattern: str
    action: str
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
        "legal-analysis",
        "research-methods",
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
    Exemption("software-docs", "RW-F-006", "downgrade", "软件文档可能说明输出字段和终检协议"),
    Exemption("editorial-audit", "RW-F-006", "downgrade", "编辑审计可能引用内部契约术语作为问题证据"),
    # An acknowledgement or methods statement may disclose AI assistance.
    Exemption("ai-disclosure", "RW-F-003", "downgrade", "AI 辅助披露声明可合法提及模型身份"),
    # A transcript's content is exactly chat turns and closings.
    Exemption("dialogue-transcript", "RW-F-001", "downgrade", "对话标签是转写内容"),
    Exemption("dialogue-transcript", "RW-W-103", "ignore", "聊天式收尾是转写记录的内容"),
    Exemption("dialogue-transcript", "RW-W-230", "ignore", "对话转写可包含口语思考停顿"),
    Exemption("dialogue-transcript", "RW-W-231", "ignore", "对话转写保留受访者或发言人原话"),
    Exemption("dialogue-transcript", "RW-W-232", "ignore", "对话转写保留受访者或发言人原话"),
    Exemption("dialogue-transcript", "RW-W-233", "ignore", "对话转写保留口语钩子与语气词"),
    # An editorial audit report quotes leakage and edits as evidence.
    Exemption("editorial-audit", "RW-F-001", "downgrade", "审计报告引用泄漏作为证据"),
    Exemption("editorial-audit", "RW-F-002", "downgrade", "审计报告引用推理泄漏作为证据"),
    Exemption("editorial-audit", "RW-F-003", "downgrade", "审计报告引用模型自述作为证据"),
    Exemption("editorial-audit", "RW-F-004", "downgrade", "审计报告引用指令复述作为证据"),
    Exemption("editorial-audit", "RW-F-005", "downgrade", "审计报告引用工具泄漏作为证据"),
    Exemption("editorial-audit", "RW-W-102", "ignore", "审计报告本就记录编辑待办"),
    Exemption("editorial-audit", "RW-W-230", "ignore", "审计报告可引用推理独白残留"),
    # Bold-labeled list items and formal item lists are functional in these genres.
    Exemption("official-document", "RW-W-205", "ignore", "公文条目式结构是规范形式"),
    Exemption("official-document", "RW-W-229", "ignore", "公文清单条目可为简短事项"),
    Exemption("policy-document", "RW-W-205", "ignore", "政策条文的结构化条目是规范形式"),
    Exemption("policy-document", "RW-W-229", "ignore", "政策清单条目可为简短事项"),
    Exemption("public-article", "RW-W-205", "ignore", "公众号常用加粗小标题分节"),
    Exemption("research-report", "RW-W-205", "ignore", "研究报告常用结构化要点"),
    Exemption("marketing-copy", "RW-W-205", "ignore", "营销文案常用加粗卖点列表"),
)


MATCH_EXEMPTIONS: tuple[MatchExemption, ...] = (
    MatchExemption(
        "legal-analysis",
        "RW-F-006",
        r"^(?:证据边界|验收标准|evidence\s+boundary|acceptance\s+criteria)$",
        "ignore",
        "法律分析可以讨论证据范围和证明标准本身",
    ),
    MatchExemption(
        "research-methods",
        "RW-F-006",
        r"^(?:证据边界|验收标准|evidence\s+boundary|acceptance\s+criteria)$",
        "ignore",
        "研究方法可以讨论证据边界和验收标准本身",
    ),
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


def _resolve_match_action(
    rule_id: str,
    matched_text: str,
    active: frozenset[str],
) -> tuple[str | None, str | None]:
    for exemption in MATCH_EXEMPTIONS:
        if exemption.rule_id != rule_id or exemption.profile not in active:
            continue
        if re.fullmatch(exemption.pattern, matched_text, re.IGNORECASE):
            return exemption.action, exemption.profile
    return _resolve_action(rule_id, active)


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
    prose_text = _mask_non_prose(text)
    setext_underlines = {
        match.start("underline") for match in SETEXT_HEADING_RE.finditer(prose_text)
    }
    findings: list[Finding] = []
    seen: set[tuple[str, int]] = set()

    for rule in RULES:
        if rule.rule_id in ignored:
            continue
        target = text if rule.severity == "fail" else prose_text
        for match in re.finditer(rule.pattern, target, rule.flags):
            if rule.rule_id == "RW-W-228" and match.start() in setext_underlines:
                continue
            action, profile = (
                _resolve_match_action(rule.rule_id, match.group(0), active)
                if active
                else (None, None)
            )
            if action == "ignore":
                continue
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

    for item in _composite_findings(prose_text, active, source_text=text):
        if item.rule_id in ignored:
            continue
        action, _ = _resolve_action(item.rule_id, active) if active else (None, None)
        if action == "ignore":
            continue
        findings.append(item)

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
    configure_utf8_stdio()
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
