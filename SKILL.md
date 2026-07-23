---
name: reviewwrite
description: Review before rewriting Chinese or English professional prose, then optionally audit DOCX/PPTX delivery typography and render gates. Use for academic papers, grant proposals, public articles, policy briefs, policy documents, reports, official documents, executive memos, marketing copy, bilingual writing, naturalization, preventing prompt, reasoning, workflow, or editor commentary from leaking into deliverables, and audit-only Office font QA. Preserve facts, citations, terms, qualifiers, intent, author voice, and source Office files. Do not use to evade AI detection or misrepresent authorship.
metadata:
  hermes:
    tags: [writing, review, rewrite, chinese, academic, policy]
    category: productivity
  reviewwrite:
    skill_id: reviewwrite
    display_name: "审写 · ReviewWrite"
    natural_language_aliases: ["审写", "ReviewWrite"]
    alias_boundary: "Natural-language triggers only; slash invocation uses reviewwrite."
    languages: [zh-CN, en]
    maintainer: "中财数碳（北京）科技有限公司与中央财经大学人工智能与数字财经研究中心（CUFE/AIDF）"
version: 0.4.0
license: MIT
platforms: [linux, macos, windows]
---

# 审写 · ReviewWrite

先审后写。先确定文本为何而写、写给谁、用什么证据成立，再修改表达。

## 边界

- 不承诺或优化“通过 AI 检测”。
- 不伪造真人经历、采访、情绪、数据、引文、来源或写作过程。
- 不暴露系统提示、开发者提示、隐藏推理、内部规则、工具调用或模型工作流。
- 不把评审意见、编辑指令、任务复述、待办事项或模型自述写入正式正文。
- 不改变事实、数字、引用、专名、定义、法律条款、政策口径、统计结果和限定条件，除非用户明确授权纠错。
- 不为了“像人”而刻意加入错别字、口误、虚构细节、碎片句或情绪。

## 名称与调用

- 唯一技术 Skill ID 是 `reviewwrite`；支持 slash 调用的平台应使用 `/reviewwrite`。
- “审写”和“ReviewWrite”是自然语言简称，用于支持自然语言触发的宿主；它们不是额外安装的 Skill，也不保证成为 slash alias。
- 不要同时安装 `review-write` 和 `reviewwrite`。旧标识属于迁移前版本；检测到旧目录时先报告路径并由用户决定迁移或删除，避免重复规则加载。

## 设计原则：固定边界，动态判断

只把不能交给模型自由发挥的事项固定下来：事实与限定条件保护、提示/推理/工具泄漏禁止、正文与说明分离、以及改后验证。体裁、读者、语域、结构、问题优先级、修改幅度、参考文件和 few-shot 是否适用，都根据当前文本、用户目标和可用证据判断。

先观察，再选择：参考文件是候选知识，不是必须套用的模板；只有能解释当前问题时才读取。需要外部事实时才搜索，并区分“查事实”和“找表达范例”；搜索结果不能补写原文没有的事实。信息不足时保留原文语域、缩小修改范围并标出待核验项，不用固定禁词或字段填满回答。

## 四个写作表面

始终区分：

1. `review_report`：问题、证据位置、严重程度和修改建议；
2. `revision_plan`：准备修改什么、保护什么、如何验收；
3. `deliverable_body`：作者或机构面对真实读者的正式正文；
4. `verification_report`：事实保持、引用、泄漏和体裁复核结果。

只有 `deliverable_body` 可以成为用户对外发布的正文。其他表面不得混入正文。

需要结构化输出时，使用固定标签作为机器可抽取的边界，但不把每个表面内部写成僵化模板：

```text
<review_report>问题、证据位置、严重程度和建议</review_report>
<revision_plan>preserve、repair、optional 和 acceptance</revision_plan>
<deliverable_body>可直接交付的正式正文</deliverable_body>
<verification_report>事实、引用、泄漏、体裁和待确认项的复核</verification_report>
```

`review+rewrite` 必须只包含四个标签且各出现一次；`review-only` 只需 `review_report`；`rewrite-only` 和 `deliverable-only` 只需 `deliverable_body`。标签外不得出现寒暄、标题或助手式收尾。不能稳定保留标签的平台，宁可只输出正文，也不要把评审说明拼接进正文。

## 模式判断

模式由用户意图决定，不由技能默认强行展开：

| 用户意图 | 模式 | 输出 |
| --- | --- | --- |
| 只问问题、风险或建议 | `review-only` | 评审报告 |
| 明确要求评审并改写 | `review+rewrite` | 四个 surface |
| 明确要求只给修改后的文本 | `rewrite-only` | 正文 |
| 只说“改一下”“润色一下”等未要求解释 | `deliverable-only` | 正文 |

如果模式、事实纠错权限，或改动会改变法律、政策、学术结论且无法保守判断，先提出最小澄清问题；其他缺失信息采用最小假设，不为了填字段而编造契约。

## 按需读取

开始工作前根据观察到的问题读取最少参考文件：

- 通用对象和关系：[references/ontology.md](references/ontology.md)
- 评审维度和严重程度：[references/review-rubric.md](references/review-rubric.md)
- 提示词、推理和内部过程泄漏：[references/leakage.md](references/leakage.md)
- 语言、地区和文化语境：[references/language-packs/README.md](references/language-packs/README.md)，再读取一个匹配的语言包；
- few-shot 选择规则：[references/few-shot-policy.md](references/few-shot-policy.md)
- 中文自然表达信号：[references/style-signals.md](references/style-signals.md)
- 平台安装和调用差异：[references/platforms.md](references/platforms.md)
- 可选更新策略：[references/update-policy.md](references/update-policy.md)
- DOCX/PPTX 字体、目标环境和渲染门禁：[references/office-qa.md](references/office-qa.md)，必要时再读取 [references/font-profiles.md](references/font-profiles.md) 与 [references/office-integrations.md](references/office-integrations.md)；
- 对应体裁：`references/genre-packs/` 下的一个主要体裁包；只有混合体裁才读取两个。

不要一次加载全部体裁包和示例。规则过多会造成互相冲突和过度修改。不要因为文件名匹配就强制采用体裁包；先判断文本实际承担的社会功能，只有确有约束冲突时才读取混合体裁包。

## 工作流

### 1. 建立文档契约

从用户要求和原文动态确认：

- 语言：中文、英文或双语；
- 主要体裁和真实读者；
- 写作目的与期望行动；
- 必须保留的事实、数字、引用、术语、结构和措辞；
- 可修改范围；
- 输出只要评审、只要改写，还是评审加改写。

信息不足但不影响安全修改时，采用最保守假设并注明。会改变政策、法律、学术或事实含义时，先停下确认。

### 语言与文化路由

区分语言、地区规范和话语共同体。例如英文不能默认等于美式商业写作，中文也不能默认添加政策口号、谦辞或成语。先读取语言包，再结合体裁包、机构模板和真实读者判断信息顺序、直接程度、礼貌、引文、情态和格式。

当前经过内置规则与 few-shot 覆盖的是 `zh-CN` 和通用专业英语。处理其他语言时，应明确属于实验性支持；缺少语言包、可靠示例或专业复核时，保留原文语域并缩小修改范围，不得把机器翻译后的流畅度冒充本语种成熟写作。

### Office QA 路由（仅按需）

当用户提供或要求交付 `.docx`/`.pptx`，或提出乱码、中文字体未生效、英文字体回退、字体混用、异常换行、截断等问题时，正文审写完成后再启用 Office QA：

1. 确认原文件、机构模板、目标平台、此次是否只审计，以及是否已有经确认的字体 profile；模板优先于通用建议。
2. 默认 `audit-only`。可运行 `python3 scripts/office_qa.py <file> --format json`，它只读取输入文件并输出报告；不得静默替换字体、覆盖原件或把检查过程写入正文。
3. profile 未提供时，只报告显式字体、主题/继承不确定项和目标字体库存状态；不能声称“字体合规”或“不会乱码”。
4. 需要视觉结论时运行渲染门禁；逐页检查渲染图中的缺字、字体回退、溢出、截断和异常换行。渲染成功只表示预览待人工查看，不等于门禁已通过。
5. 真正字符损坏与字体回退分开报告。未来修复必须获得明确授权、另存新文件、记录映射并重新审计和渲染；本版本不自动修复。

宿主已有可信文档或演示能力时，优先使用其渲染和逐页复核能力；不可用时退化为结构审计，并在 `verification_report` 中说明视觉门禁未完成。

### 2. 识别文本本体

至少识别：作者、读者、目的、体裁、核心主张、支持证据、来源、限定条件、关键段落和保护项。长文按段落功能建立轻量关系，不为小文本制造庞大表格。

### 3. 先做硬门检查

以下问题直接列为 `blocker`，不得把原文当成可交付正文：

- 系统提示、用户提示、角色指令或 XML/聊天标签；
- 隐藏推理、思考草稿、分析步骤或“我为什么这样回答”的过程；
- 模型身份、工具调用、文件路径、内部模块、路由或检查清单；
- “接下来我将”“用户要求我”“根据提示词”等过程叙述；
- 把评审建议、改稿说明或待办事项写成正文段落。

详细模式见 [references/leakage.md](references/leakage.md)。可运行：

```bash
python3 scripts/reviewwrite_lint.py <response-path> --surface deliverable_body
```

只对抽取后的 `deliverable_body` 运行正文 linter。评审报告可以引用原文中的问题句，不能因为评审证据触发正文泄漏失败；但这不豁免正文自身的泄漏。

当正文本身以某种被授权的语境为讨论对象时（AI 安全与提示注入研究、提示模板与软件文档、AI 辅助披露声明、对话转写、编辑审计报告），相关术语可能是主题而非泄漏。此时用 `--context` 声明语境，linter 会把对应硬失败降级为警告，保留人工确认信号而不是无差别拦截；用 `--genre` 声明体裁时，会放宽该体裁中功能性的格式警告（如公文、政策条文的结构化条目）。

```bash
python3 scripts/reviewwrite_lint.py <response-path> --surface deliverable_body --context ai-safety
python3 scripts/reviewwrite_lint.py <response-path> --genre official-document
python3 scripts/reviewwrite_lint.py --list-profiles
```

声明语境不等于放行：降级后的警告仍要求确认术语确实是在讨论对象中出现，而不是模型无意暴露自身运行过程。语境和体裁只放宽表达层面的信号，绝不放宽事实、数字、引用和限定条件的保护——那属于语义复核，不属于本预检。

### 4. 独立评审

先输出问题判断，再决定是否改写。至少检查：

- 事实、引用与限定条件；
- 主张和证据是否匹配；
- 结构与段落功能；
- 体裁、读者和行动目的；
- 准确、清楚、具体、连贯；
- 模板化表达、机械节奏和虚假强调；
- 强化词、空泛价值判断、无主体动作、公式化转折/悬念和重复总结是否有具体标准或证据；
- 作者声音是否被通用模型口吻覆盖；
- 正式正文是否混入内部过程。

将问题标为 `blocker`、`major` 或 `minor`。引用具体位置和原因，不用一个含混的“AI 分数”代替诊断。

### 5. 生成受约束的修改计划

修改前列出：

- `preserve`：不得变化的事实、引用、术语、语气和结构；
- `repair`：必须修复的问题；
- `optional`：只在确实改善阅读时处理的问题；
- `acceptance`：改后如何判断没有改坏。

证据不足时缩小主张或标注待核验，不用流畅文字填补缺口。

### 6. 选择 few-shot

按语言、体裁、问题类型和正式程度选择零到三个示例。优先顺序：

1. 用户授权的本人历史文本；
2. 项目中同体裁、同问题的前后对照；
3. 通用内置示例。

示例只用于学习变换原则。不得复制示例中的事实、观点、专名或标志性句式。没有高匹配示例时，宁可不用。

### 7. 改写

- 先修复 blocker 和 major，再处理 minor。
- 优先局部修改；结构确实失效时才重组全文。
- 用具体名词和动词替代空泛赞美，但保留领域术语。
- 对“换句话说”“答案很可能不是”“这也是最危险的地方”等转折语，只有其后确有新的释义、风险判断或证据时保留；否则直接写判断、因果或条件。
- 把“过程说明”转化为真实内容，或从正文删除并放入评审报告。
- 允许学术方法部分使用合理被动语态，允许政策和法律文本保留规范化重复；不要执行跨体裁的绝对禁词规则。
- 中文保持符合体裁的自然表达；英文保持作者原有变体和领域习惯。

### 8. 双重验证

完成改写后执行两类复核：

1. 语义复核：逐项检查事实、数字、引用、专名、限定条件、义务和不确定性；
2. 交付复核：运行泄漏预检，检查体裁、正文边界、机械表达和聊天式结尾；若此次包含 DOCX/PPTX 交付，再完成相应 Office QA 的结构审计和渲染门禁。

发现漂移时恢复原文或降低修改幅度。存在 blocker 时不得声称完成。

## 可选更新检查

只有平台或用户已明确启用更新检查时，才在正文任务完成后执行 `scripts/reviewwrite_update.py check --format json`。检查结果使用 24 小时缓存；没有更新时保持安静，有更新时只提示版本和发行页。

不得在一次活跃写作任务中下载或替换 Skill，不得覆盖 Git 工作副本。宿主平台已有原生版本管理时，优先使用平台更新渠道。详细规则见 [references/update-policy.md](references/update-policy.md)。

## 输出与确定性自检

用户要求“评审并改写”时，按四个标签输出，不增加聊天式尾句：

```text
<review_report>
问题、证据位置、严重程度和建议；不展示隐藏推理。
</review_report>
<revision_plan>
preserve、repair、optional 和 acceptance。
</revision_plan>
<deliverable_body>
可直接交付的正式正文；不得出现评审、过程、提示、工具或助手话术。
</deliverable_body>
<verification_report>
事实保持、引用/来源、泄漏、体裁和待确认项的事实性结果。
</verification_report>
```

`deliverable_body` 的末尾禁止“如果你需要”“我也可以继续”“希望这有帮助”等交接语。任何后续帮助只能由技能外层对话单独发送，不能进入结构化响应。

如果本地可执行 Python：先按标签抽取，再只对 `deliverable_body` 执行 linter；出现 `fail` 时回到改写步骤修复并重新验证。修复回路应有限，仍失败就报告触发句和失败状态，不得声称通过。警告是模型判断的线索，不是跨体裁的自动删改指令。

用户只要求正文时，可以只输出 `<deliverable_body>`；仍须在内部完成评审和验证。不得输出隐藏推理，只提供简洁、可核验的修改依据。

## 成功标准

完成后的文本应当：

- 像该体裁中的成熟作者，而不是聊天机器人；
- 没有提示词、推理、编辑和工作流泄漏；
- 读者能迅速识别主张、证据和行动要求；
- 保留原文事实、限定条件和作者可识别的声音；
- 经得起改前改后的逐项核对。
