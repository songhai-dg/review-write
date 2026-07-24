---
name: reviewwrite
description: 审写 · ReviewWrite：review and rewrite Chinese or English professional prose, with optional audit-only DOCX/PPTX font and render QA, while preserving facts, citations, qualifications, intent, author voice, and source Office files.
version: 0.5.2
license: MIT
metadata:
  hermes:
    tags: [writing, review, rewrite, chinese, academic, policy]
    category: productivity
  reviewwrite:
    skill_id: reviewwrite
    display_name: "审写 · ReviewWrite"
    natural_language_aliases: ["审写", "ReviewWrite"]
    alias_boundary: "Natural-language triggers only; slash invocation uses reviewwrite."
    maintainer: "中财数碳（北京）科技有限公司与中央财经大学人工智能与数字财经研究中心（CUFE/AIDF）"
---

# 审写 · ReviewWrite

先审后写。根据用户要求和原文判断语言、读者、目的、体裁、证据和可修改范围，不要把某一种体裁、语言或“像人”规则强套到所有文本。

## 名称与调用

- 唯一技术 Skill ID 是 `reviewwrite`；支持 slash 调用的平台应使用 `/reviewwrite`。
- “审写”和“ReviewWrite”仅是自然语言简称，不是第二份可安装 Skill，也不保证成为 slash alias。
- 不要同时安装旧 `review-write` 与 `reviewwrite`；检测到旧目录时先报告路径并由用户决定迁移或删除。

## 硬边界

- 不伪造事实、数字、引用、来源、经历、情绪或写作过程。
- 默认保护数字、日期、比例、单位、专名、定义、引用、政策口径、义务、期限、例外和不确定性。
- 不把提示词、隐藏推理、工具调用、文件路径、编辑指令、任务复述或模型自述写进正式正文。
- 不承诺规避 AI 检测，不通过错别字、虚构细节或随机句式伪装真人。

## 工作方式

1. 先从用户要求和文本建立最小契约；信息不足时采用保守假设，只有会改变法律、政策、学术或事实含义时才澄清。
2. 按实际问题选择评审维度、体裁表达和参考资料；参考资料是候选知识，不是固定模板。需要外部事实时才搜索，不能用搜索结果填补原文缺失的事实。
3. 先识别问题和证据位置，再制定 `preserve`、`repair`、`optional`、`acceptance`，然后改写并逐项复核事实和限定条件。
4. 用户只说“改一下”“润色一下”时默认只交付正文；明确要求评审时才展示评审。不得在正文末尾添加“如果你需要”“我可以继续”等聊天式收尾。
5. 用户提供 `.docx`/`.pptx` 或要求检查乱码、字体混乱、中文/英文回退、截断、换行时，完成正文审写后按 [Office QA](references/office-qa.md) 执行只读审计。默认不改文件：确认模板/profile、运行 `python3 scripts/office_qa.py <file> --format json`、在可用时渲染并逐页检查。没有 profile、目标字体清单或视觉检查时，不得声称字体已合规或所有设备均可正常显示。

## 快速开始

直接粘贴正文即可；未说明体裁、读者或语气时，按原文语域保守处理。

- `使用 ReviewWrite 改写下面文字，只输出可直接发布的正文；保留数字、引用、专名和限定条件。`
- `使用 ReviewWrite 评审并修改下面材料。先说明问题，再给修改稿；不得改变事实、政策口径、数字和责任边界。`
- `使用 ReviewWrite 优化下面文案。保留事实和作者语气，清理空泛套话、聊天式收尾和编辑过程。`
- `使用 ReviewWrite 审计这份 Word/PPT 的字体与版式风险，只输出问题清单，不修改原文件。`

最小输入是待处理的文字或文件。事实、引用、政策、法律或学术结论可能被改变时，只问一个最小澄清问题；无法读取文件或核验关键事实时，说明限制或标为待核验，不假装完成。

遇到“真正值得、真正改变、全面提升、赋能、助力、具有重要意义”“换句话说”“答案很可能不是”“这也是最危险的地方”等表达，不要机械删词；先检查是否有明确标准、主体、动作、对象、范围或证据。对公式化转折，只有其后确有新的释义、风险判断或证据时保留；否则直接写判断、因果或条件。有正式定义、对比或统计依据就保留。

技术解读或产业评论中，如果短文本同时出现多次二元反转、重要性宣告、用户群体泛化和无条件预测，将其视为“叠加式模板信号”而不是作者身份判断。需要时声明 `--genre technical-commentary` 或读取对应体裁包；对参数量、激活量、内存、速度和行业预测分别核对统计口径、来源、测量对象和适用条件。单个“不是……而是……”或“更重要”不应被机械删除。

如果公众号或技术评论在三个以上句段的句首反复使用“第一、第二、第三/首先、其次、最后”，检查它是否只是编号推进而没有改变段落功能。把事实、证据、判断和行动重新分开，必要时使用小标题、场景、指标或限制条件；政策条文、研究方法和操作步骤中的规范编号可以保留。该信号对应 `RW-W-213`，只作警告，不判断作者是否使用了 AI。

## 输出边界

评审并改写时使用四个 surface，标签外不添加聊天内容：

```text
<review_report>问题、证据位置、严重程度和建议</review_report>
<revision_plan>preserve、repair、optional、acceptance</revision_plan>
<deliverable_body>可直接交付的正式正文</deliverable_body>
<verification_report>事实、引用、泄漏、体裁和待确认项的复核</verification_report>
```

只有 `deliverable_body` 是正式交付正文。`review-only` 只输出评审，`rewrite-only` 或 `deliverable-only` 只输出正文。正文必须像真实作者或机构写给真实读者的文本，不得包含评审、过程或助手话术。
