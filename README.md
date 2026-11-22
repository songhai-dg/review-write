# 审写 · ReviewWrite

**把不该交付的 AI 过程残留，变成可核验的专业正文。**

**不拿幻觉换“人味”：不编造经历、数据、来源、案例或细节。**

**1.0 双层门禁：规则未命中，不再等于正文可以交付。**

*Review before rewrite. Keep the facts. Lose the slop.*

不是 AI 检测规避器；是专业写作的交付质量控制。

可复现证据：4 份合成案例在 1.0.0 规则下从 **14 fail / 24 warn** 降至 **0 / 0**；38 项受保护字面量通过逐字回归检查。另有一项 **324,015 字符、55 个分块**的长文回归，能将问题定位回全文第 9,001 行。[查看完整报告](examples/simulation/RUN_REPORT.md)

[中文](#中文) · [English](#english)

审写 · ReviewWrite is an evidence-preserving review-and-rewrite Skill for professional writing. It provides compatibility and installation guidance for Codex, Claude Code, Hermes Agent, Gemini CLI, GitHub Copilot, OpenClaw, WorkBuddy, and other Agent Skills-compatible systems.

---

## 中文

ReviewWrite 1.1.0 在 1.0“确定性规则 + 正文哈希绑定语义复核”双层门禁基础上，新增**跨模型写作特征校准（GPT、Gemini、Claude、Grok、DeepSeek、通义 Qwen）**、**互联网与职场黑话解构**、**推理标签与自言自语独白拦截**，以及**证据保持型去同质化（降低机器模板复现度）**。五项语义复核仍与最终正文的 SHA-256 绑定，正文改一个字符都必须重新复核；规则没有命中，也不能直接冒充审核通过。

这不是扩充一份禁词表，更不是用同义词乱替或塞入虚构细节去迎合检测器。“闭环控制、模型对齐、时间颗粒度、真正、显著、不是……而是……”有明确工程、统计、定义或规范功能时完整保留；只有在“对齐颗粒度、以……为抓手、跑通商业闭环、说白了、Here's the kicker、No fluff”或连续递进套话空转时，才提示还原为主体、动作、指标和依据。

### 先审后写，保护事实，交付正文

审写 · ReviewWrite 面向中英文专业写作：无论初稿由 GPT、Gemini、Claude、Grok、DeepSeek 还是 Qwen 生成或润色，都先判断文本和目标，再评审、改写、复核。它保护事实、引用、限定条件和作者声音，通过打破等长矩形段落、清理机械连接词链与空泛拔高尾巴来消除高重复模板感，不把“像人”或“降模板率”理解为制造错字、打乱语序或规避检测。

运行环境要求 Python 3.10 或更高版本；正文审写默认只读取本地输入，不联网。更新检查是可选能力，只有用户或平台明确启用时才访问 Release。

### 超长文档也能审，但不夸大完成度

面对十万字、几十万字的报告、论文、政策材料或长篇研究文本，ReviewWrite 不把全文粗暴塞进一次上下文，也不把几段抽样结果包装成“全文已审核”。它按章节和段落分块，保留全文行号与块号，建立数字、标题和术语一致性索引，并明确报告尚未完成的跨章主张—证据复核。

```bash
python3 scripts/long_document_review.py path/to/long-draft.md --format json
```

分块预检解决上下文长度、定位和一致性线索问题；事实、引用、法律责任和跨章论证仍需全局模型或人工复核。

### 核心边界：不拿幻觉换人味

ReviewWrite 不会为了让文字更像人，而主动编造经历、数据、来源、案例、情绪或细节，也不会凭模型记忆向通用草稿塞入原文未提供的外部事实。无法确认的内容，会保留限定条件，指出需要核实的部分，或降低主张强度。文字可以更自然，但事实不能靠虚构来补齐。

它背后的方法论来自教授团队与专业研发团队长期从事高质量写作、审稿和交付的经验积累，不是把几个“去 AI 痕迹”词表拼在一起。ReviewWrite 关注的是主张是否有证据、限定条件是否完整、体裁是否合适，以及修改后能否真正交付。

### 来源透明度：只审计，不清除

ReviewWrite 可以检查文件中可观察的 Content Credentials、C2PA/JUMBF 或 SynthID 相关线索（支持区分 DOCX/PPTX 内嵌媒体标记与正文文字引用），并定位可能影响交付完整性的 Unicode 格式控制字符。审计结果严格区分“已发现”“文字引用”和“无法判断”，不把来源线索缺失解释成来源不存在；输入文件保持不变，不提供水印移除、来源伪装或检测器规避功能。

### 名称与调用：短，但不混乱

- 技术 Skill ID：`reviewwrite`。支持 slash 调用的平台使用 `/reviewwrite`。
- 产品名：审写 · ReviewWrite。
- 自然语言简称：审写、ReviewWrite。它们只用于支持自然语言触发的宿主，不是第二份可安装 Skill，也不保证成为 slash alias。
- 不要并行安装旧 `review-write` 和新 `reviewwrite`；安装器发现旧目录时会拒绝并行安装，先报告路径，再由用户决定迁移或删除。

想了解 GPT、Gemini、Claude、Grok、DeepSeek、Qwen 各自常见 AI 味、如何合规降低模板同质化率，以及普通 humanizer 的风险，见 [AI 写作痕迹与跨模型审写策略](references/ai-writing-signals.md)。

### 一句话交给智能体安装

复制下面代码块中的内容：

```text
请从官方仓库 https://github.com/songhai-dg/review-write 安装 ReviewWrite Skill；如当前网络无法访问 GitHub，使用同步镜像 https://gitee.com/cufe01/songhai-dg。如果当前智能体已经安装，不要重复安装，也不要搜索或替换成名称相近的其他技能。请使用所在平台自己的 Skill 安装或导入机制；如果仓库已在当前目录，直接以当前目录为安装来源。平台不支持、没有权限或无法访问来源时，说明限制并停止。
```

国内 SkillHub 入口：[审写 · ReviewWrite](https://skillhub.cn/team-skills/zcst-review-write)。

正式版本会自动生成一份分发包，统一提供 GitHub、Gitee、SkillHub 和其他 Agent Skills 目录所需的安装指令、版本信息与宣传文案，避免各平台出现不同版本。分发包说明见 [distribution/README.md](distribution/README.md)。

它主要解决：

- 提示词、`<think>` 推理标签、自言自语独白、工具尾注和编辑指令混入正式正文；
- 互联网大厂黑话、跨模型网感口头禅、机械递进连接词链和等长矩形段落造成的高同质化模板感；
- 表面“去 AI 腔 / 暴力降重”导致事实、数字、术语、引用、限定条件和作者声音漂移；
- 用一套通用规则误改论文、基金、公众号、政策、公文等不同体裁，或忽略跨语种与机构规范。

### 核心闭环

```text
Understand → Review → Plan → Rewrite → Verify → Evolve
理解文本      独立评审    约束修改     生成正文      双重复核      保留经验
```

ReviewWrite 严格分离四个写作表面：评审报告、修改计划、正式正文和复核报告。只有正式正文可以成为对外交付文本。

### 核心能力

- 适配论文、基金、政策、报告、公文、备忘录、营销和双语写作；
- 1.1.0 新增跨模型写作校准：针对 GPT、Gemini、Claude、Grok、DeepSeek 与通义 Qwen 初稿的不同模板倾向，提供写前契约与改后定向收敛方案；
- 1.1.0 新增互联网黑话解构、推理标签/独白阻断、网感钩子清理与机械连接词/拔高尾句去同质化规则（`RW-W-230—RW-W-234`），在零事实漂移前提下消除模板复现；
- 1.1.0 完善非散文结构保护与豁免一致性：自动屏蔽 Markdown 围栏代码块与 YAML frontmatter 中的版式误报，区分 Setext 二级标题与装饰横线，统一单条与组合规则的体裁豁免及 `--ignore-rule` 控制；
- 支持跨语言专业审写：中英互译时保护数字、引用、术语、主张、限定条件和责任边界，并按目标地区、体裁和话语共同体独立审校；
- 支持超长文档审写：对十万字及更长文本进行章节优先分块，使用一次性全文行索引定位发现项、中文数字和标题，并限制结果体积，避免重复扫描和把片段检查误报成全文完成；
- 可作为宿主智能体的写作质量控制层：风险路由负责决定是否接入，可执行门禁负责抽取、严格终检和“失败时不输出正文”，问题最多回改两轮后再交付；
- 交付语义控制：标题与结构读者化、内部过程分离、自证删除、主张—证据边界和事实限定保持五项复核，与最终正文哈希绑定；
- 增加技术解读/产业评论路由：检查模型、推理、设备、内存和性能主张中的叠加式模板信号与技术口径；
- 泄漏预检支持体裁与语境感知：AI 安全论文讨论 `system prompt`、公文使用结构化条目等被授权情形，用 `--context`/`--genre` 声明后降级或放宽，避免正当写作被误判；
- 对 DOCX/PPTX 提供可选的只读字体、渲染与来源完整性审计：不静默改文件。

```bash
# 先生成与正文绑定的语义复核记录，逐项完成复核，再执行最终门禁
python3 scripts/reviewwrite_semantic.py init path/to/response.txt --output semantic-review.json
python3 scripts/reviewwrite_gate.py path/to/response.txt --semantic-review semantic-review.json
```

### AI 风格与过程残留审查清单

下表列的是可观察的文本信号和交付风险，不是“AI 生成概率”，也不据此判断作者身份。单个词语通常不会触发处理；技能结合体裁、重复频率、证据和段落功能判断。

| 类型 / 规则 | 识别范围 | 常见表现 | 处置与不误伤边界 |
| --- | --- | --- | --- |
| 提示词泄漏 `RW-F-001` | system/developer prompt、角色标签、忽略指令等 | “系统提示词”“忽略以上要求”“[INST]” | 正文 `blocker`；AI 安全论文等授权语境降为人工复核警告 |
| 隐藏推理泄漏 `RW-F-002` | `<think>`/`<thought>` 等推理标签、思考链、分析通道 | `<think>`、“以下是我的完整思考过程” | 正文 `blocker`；不得把内部推理通道写进交付正文 |
| 模型自述 `RW-F-003` | AI/语言模型身份和能力免责声明 | “作为一个 AI……” | 正文 `blocker`；合法的 AI 辅助披露可声明语境后复核 |
| 任务与编辑残留 `RW-F-004/RW-W-102` | 用户要求、改稿待办、版本过程 | “根据用户要求”“待补充”“下一轮修改” | 任务复述和编辑指令不得进入正文；评审报告可以引用 |
| 工具/运行时残留 `RW-F-005` | 工具调用、Skill、内部路径及智能体自动尾注 | “我调用了工具”“SKILL.md”“Generated with Claude Code” | 正文 `blocker`；软件文档或审计报告需声明讨论语境 |
| 内部契约术语 `RW-F-006` | 只供宿主/编辑流程使用的证据边界、验收标准、终检和 surface 名称 | “证据边界”“最终门禁”“deliverable_body” | 普通正文 `blocker`；法律分析、研究方法、软件文档等确实讨论该概念时声明授权语境 |
| 隐性任务服从 `RW-F-007` | 未直说提示词，但叙述如何满足要求、采用文风或安排生成步骤 | “为了满足任务要求，本文将……” | 正文 `blocker`；直接写读者需要的内容 |
| 工作流与聊天收尾 `RW-W-101/RW-W-103` | 过程预告、助手交接语 | “下面我将介绍”“希望这对你有帮助” | `warn`；只清理正文中的过程话术，不改真实对话转写 |
| 推理独白残留 `RW-W-230` | 推理模型自言自语、自我纠正或拆解独白 | “让我先拆解一下”“等等，这里需要重新审视”“Let me step back” | `warn`；删去思考独白，只留面向读者的论据与结论；对话转写豁免 |
| 互联网黑话与行话堆叠 `RW-W-231/RW-W-232` | 空洞商业行话搭配或同段密集堆叠黑话词 | “对齐颗粒度”“以……为抓手跑通商业闭环”“move the needle”、泛化 `load-bearing` | `warn`；还原为主体、动作、对象和指标；闭环控制、模型对齐、时间颗粒度等专业术语保留 |
| 网感钩子与伪坦诚垫词 `RW-W-233` | 社交媒体戏剧钩子、反套话标榜与姿态性坦诚 | “说白了”“不整虚的”“扎心的是”“Here's the kicker”“No fluff”“Honestly,” | `warn`；正式文体直接陈述分歧与结论；对话转写豁免 |
| 同质化递进与拔高尾巴 `RW-W-234` | 近距离连续机械递进词或句末空泛拔高伴随语 | 连续“此外、与此同时、不仅如此”、反复“充分彰显了……的重要性 / highlighting the importance of” | `warn`；改为具体主语承接与因果推进，按证据权重调整句段长短 |
| 空泛开场与重要性 `RW-W-201/RW-W-202/RW-W-207` | 时代背景、无标准的“重要/关键/全面提升” | “在当今时代”“这件事意义重大” | 改成主体、动作、对象、范围和依据；正式规范词保留 |
| 公式化转折与悬念 `RW-W-203/RW-W-208` | 二元反转、悬念桥接和重复总结 | “不是……而是……”“换句话说”“最危险的地方” | 单次有逻辑可保留；连续堆叠或不增加信息时 `warn` |
| 极端重要性标签 `RW-W-214` | “最硬、最关键、绝对不能”等简短排序宣告 | “最硬的一点是效率” | 要求比较范围、判断标准、对象和依据；不能证明排序时改成具体约束 |
| 元叙事包装 `RW-W-215` | “叙事、故事、底层逻辑”替代事实链或机制 | “这背后是一套新的叙事” | 展开主体、行动、对象、过程和结果；确实讨论传播框架时保留并补定义 |
| 话语填充与重复总结 `RW-W-216/RW-W-217` | 提醒读者注意或重复收束，却没有新增信息 | “值得注意的是”“总的来说” | 直接写新增事实、判断、适用范围或行动；单纯重复时删除 |
| 模糊权威与推论旁白 `RW-W-218/RW-W-220` | 无可定位来源的背书，或连续用观察话术推进结论 | “研究表明”“我们可以看到……这说明……” | 补真实来源和推论条件；无法核验时改为有限判断 |
| 翻译腔与对称句式堆叠 `RW-W-219/RW-W-221` | 直译句法或多组平衡结构替代信息取舍 | “对于企业而言，进行一个……”“既要……也要……”连续出现 | 按目标语言重组主谓宾；按事实、判断和行动重排，单个功能性句式可保留 |
| 标题末尾句号 `RW-W-222` | Markdown 标题误带句末句号 | `# 项目实施方案。` | 删除标题末尾句号；代码块注释、问号、感叹号和版本号不误伤 |
| 标题与自证语义 `RW-W-223—RW-W-227` | 标题中的编辑判断、自证式结论、确定性强化、单次推理旁白和段落堆叠 | “这才是真正的问题”“事实充分证明”“因此我们可以得出结论” | 改为对象、事实、条件和有限结论；有定义、比较、统计或规范功能的强词保留 |
| 装饰横线与短横杠碎片 `RW-W-228/RW-W-229` | 独立横线和三个以上短标签式项目切碎正文 | `---`、连续“- 高效协同” | 改为连续正文或真实标题层级；Setext 二级标题、YAML 头及公文/政策规范清单自动区分或豁免 |
| 宣传腔与格式模板 `RW-W-204/RW-W-205` | 空泛赋能、固定卖点、标签式列表 | “全面赋能”“打造新生态” | 结合政策、营销和公文体裁判断，不使用跨体裁禁词 |
| 技术评论叠加信号 `RW-W-209—RW-W-212` | 模型/推理/设备文本中的反转、重要性、用户泛化、预测和数字 | “这个细节很关键”+“大多数用户”+“更可能” | 只在 `public-article`/`technical-commentary` 语境告警；要求补机制、指标、来源和条件 |
| 机械枚举 `RW-W-213` | 三个以上句首“第一、第二、第三/首先、其次、最后” | 全文每段都用同一排序节奏 | `warn`；先区分事实、证据、判断、行动；政策条文、方法步骤和正式清单可保留 |

覆盖范围：中文 `zh-CN` 与通用专业英语；论文、基金、公众号、技术解读、政策、公文、报告、备忘录、营销和双语文本。规则输出评审信号，不生成“人味分数”，也不承诺规避任何检测器。

### 四个内容案例与一项长文回归

四份合成案例直接展示问题稿、修改稿和验证结果：严格预检由 **14 个硬失败 / 23 个警告** 降至 **0 / 0**；38 项受保护字面量（数字、日期、角色与限定词）通过逐字回归检查。[查看完整复现报告](examples/simulation/RUN_REPORT.md)。另有长文回归测试：对 324,015 个字符切分为 55 个块，故意放入一处模型自述，预检将其定位到全文第 9,001 行；同时验证数字索引和重复段落索引。[查看测试代码](tests/test_lint.py)。

| 案例 | 问题稿 | 修改稿 | 主要改进 | 预检 |
| --- | --- | --- | --- | --- |
| 学术摘要 | [查看](examples/simulation/inputs/academic-abstract.zh.md) | [查看](examples/simulation/outputs/academic-abstract.zh.md) | 去除模型身份、推理泄漏和自证式结论，保留样本边界 | 5 fail / 5 warn → 0 / 0 |
| 基金申请 | [查看](examples/simulation/inputs/grant-rationale.zh.md) | [查看](examples/simulation/outputs/grant-rationale.zh.md) | 删除宣传腔和待办，补清研究设计 | 3 fail / 6 warn → 0 / 0 |
| 政策简报 | [查看](examples/simulation/inputs/policy-brief.zh.md) | [查看](examples/simulation/outputs/policy-brief.zh.md) | 清理工具残留，明确选项和证据缺口 | 2 fail / 8 warn → 0 / 0 |
| 英文管理备忘录 | [查看](examples/simulation/inputs/executive-memo.en.md) | [查看](examples/simulation/outputs/executive-memo.en.md) | 直接呈现决策、约束和风险 | 4 fail / 5 warn → 0 / 0 |
| 超长文档预检 | [查看测试](tests/test_lint.py) | — | 324,015 字符分为 55 块，保留全局位置并建立数字、重复段落索引 | 1 fail / 0 warn，定位到 L9,001 |

### 安全与来源

发布包包含 Skill、参考资料、一个配置结构样例、本地文本/Office QA 脚本和可选更新器。默认审写路径不联网、不读取凭证、不修改或上传输入正文与 Office 原件；只有明确启用更新检查/下载时，更新器才访问 Release、读取可选令牌或调用 `gh`。Office QA 只有在显式要求渲染时才向预览目录写入 PDF/PNG。安装前请核对官方 Release、SHA-256 与 artifact attestation，并在已有安装时拒绝覆盖未知目录。完整边界见 [SECURITY.md](SECURITY.md)。

### Office 交付前质检：先审计，再决定是否修复

当用户交付 Word 或 PPT 时，ReviewWrite 可以在正文审写之后增加一个可选的 Office QA 环节。它不是“自动统一字体”：单位模板优先，默认只读审计，原件不会被覆盖。

```bash
# 默认只读结构审计；不生成渲染预览
python3 scripts/office_qa.py path/to/submission.docx --format json

# 模板已确认时再对照字体 profile，并要求完成渲染
python3 scripts/office_qa.py path/to/deck.pptx \
  --font-profile examples/office-qa/font-profile.example.json \
  --render required --output-dir /tmp/reviewwrite-preview --format json
```

报告会区分“字体缺失/回退风险”和“字符本身损坏”，不会把后者伪装成字体问题。结构审计或生成 PDF/PNG 预览都不等于视觉通过：必须逐页查看缺字、字体回退、截断、溢出和异常换行。没有确认模板、目标字体库存或视觉检查时，Skill 不会声称文件在所有设备上均可正常显示。详见 [Office QA 说明](references/office-qa.md) 与 [字体 profile 规范](references/font-profiles.md)。

### 使用示例

```text
使用 ReviewWrite 评审并修改这份政策简报。先给问题清单，再给修改稿，不能改变数字和政策口径。
```

```text
使用 ReviewWrite 修改这篇英文论文摘要。保留术语、样本量、统计结果和引用，不要把编辑过程写进摘要。
```

### 多语言，不只是翻译

当前核心支持 `zh-CN` 和通用专业英语。语言能力使用三个坐标：语言、地区规范和话语共同体。英文不能默认等于美式商业写作，中文也不能默认增加政策口号、谦辞或成语。

0.6.0 开始支持跨语言专业审写：翻译前确认源语言、目标语言、地区规范、体裁、读者和术语；翻译后独立检查数字、引用、主张强度、限定条件、情态和责任边界。重点是把专业判断完整带入目标语言，不能用逐句替换、回译或流畅度代替准确性证明。详见[跨语言专业审写](references/translation-qa.md)。

新增语言必须经过独立语言包、locale-aware few-shot、事实保持回归和本语种专业 review，才能从 `planned` 进入 `experimental`，再进入 `core`。详见[语言包规范](references/language-packs/README.md)。

### few-shot 如何设计

few-shot 不是越大越好的模板库。每次最多选择三个：一个修复最高风险问题，一个校准体裁和 locale，必要时一个保持作者声音。授权、语言、体裁或文化语境匹配不足时宁可不用。示例只传递修改原则，不迁移事实、观点、专名或标志性句式。详见 [few-shot policy](references/few-shot-policy.md)。

### 检查与测试

```bash
python3 scripts/reviewwrite_lint.py path/to/draft.md
python3 scripts/reviewwrite_lint.py path/to/draft.md --strict
python3 scripts/reviewwrite_semantic.py init path/to/structured-response.txt --output semantic-review.json
python3 scripts/reviewwrite_gate.py path/to/structured-response.txt --semantic-review semantic-review.json
python3 scripts/validate_skill.py
python3 -m unittest discover -s tests -v
python3 scripts/package_skill.py
```

### 更新与发布

ReviewWrite 不随机检查，也不在每次调用时联网。新会话第一次调用只读取本地版本和缓存；缓存超过 24 小时时，当前写作完成后再联网刷新。默认只提示新版；可信环境可以自动下载 patch，但安装和会话刷新仍独立执行。minor/major 需要明确升级，宿主平台已有原生版本管理时优先使用平台渠道。

```bash
python3 scripts/reviewwrite_update.py status --format json  # 始终只读本地
python3 scripts/reviewwrite_update.py check --format json   # 仅在任务结束且缓存过期时
```

版本采用双轨制：有证据的小改进进入 edge patch；通过完整回归和人工 review 后提升为 stable minor；没有有效变化就不发布。详见[运营策略](OPERATIONS.md)和[更新策略](references/update-policy.md)。

### 站在已有项目之上

ReviewWrite 吸收并重新组织 Stop Slop、Humanizer-zh、skill-deslop 和 humanizer 的可复用思路，同时严格坚持“不凭模型记忆补写外部事实”的证据边界，增加文档本体、跨模型路由、泄漏硬门、few-shot 选择和双层门禁验证。精确来源、版本和许可见 [NOTICE.md](NOTICE.md) 与 [sources.lock.json](sources.lock.json)。

### 贡献与许可

欢迎提交体裁包、语言包、授权 few-shot、误报样例和事实保持回归。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。项目采用 MIT License。

---

## English

ReviewWrite 1.1 builds on the 1.0 two-layer delivery gate (deterministic signals plus a SHA-256 body-bound semantic review) by adding **cross-model writing calibration across GPT, Gemini, Claude, Grok, DeepSeek, and Qwen**, **corporate/internet buzzword de-slopping**, **reasoning-tag and deliberation-monologue blocking**, and **evidence-preserving de-homogenization**. A clean regex scan is still never sufficient to release a document, and any single-character edit invalidates the semantic review record.

This is neither a larger blacklist nor a detector-bypass spinner. Legitimate domain terms (`load-bearing wall`, `model alignment`, `closed-loop control`, `significant at p < 0.01`, or functional contrasts) remain intact, while empty corporate collocations (`move the needle`, figurative `truly load-bearing`, `synergistic ecosystem`), social engagement hooks (`Here's the kicker`, `No fluff`, `Honestly,`), and stacked transitions/participial tails are flagged for concrete revision.

### Review first, then rewrite

审写 · ReviewWrite is built for professional Chinese and English writing across drafts generated or edited with GPT, Gemini, Claude, Grok, DeepSeek, or Qwen: it identifies the goal and context, then reviews, rewrites, and verifies the text while preserving facts, citations, qualifications, and authorial voice. It reduces template homogeneity through structural specificity rather than adding mistakes or promising detector evasion.

Its central boundary is explicit: ReviewWrite does not invent experiences, data, sources, examples, emotions, or unverified parametric details to make text appear more human. When something cannot be confirmed, it preserves the qualification, marks it for review, or narrows the claim.

Its method is informed by a professor-led and professional product team with long-term experience in high-quality writing, review, and delivery. ReviewWrite is not a bundle of “AI trace removal” word lists; it evaluates claims, evidence, qualifications, genre fit, and whether the revised text is ready for real use.

### Naming and invocation: short without ambiguity

- Technical Skill ID: `reviewwrite`. Use `/reviewwrite` on hosts that support slash invocation.
- Product name: 审写 · ReviewWrite.
- Natural-language names: 审写 and ReviewWrite. They are only natural-language triggers on hosts that support them, not separately installable Skills or guaranteed slash aliases.
- Do not install both legacy `review-write` and `reviewwrite`. The installer refuses a parallel install when it detects the old directory, then reports its path for a user-directed migration or removal.

For cross-model AI writing signals (GPT, Gemini, Claude, Grok, DeepSeek, Qwen), de-homogenization strategy, and common humanizer risks, see [AI writing signals and humanizer strategy](references/ai-writing-signals.md).

### One-sentence agent installation

Copy the text in the code block:

```text
Install ReviewWrite from the canonical repository https://github.com/songhai-dg/review-write. If GitHub is unavailable on the current network, use the synchronized Gitee mirror https://gitee.com/cufe01/songhai-dg. If the current agent already has it, do not install it again or search for a similarly named replacement. Use the current platform's native Skill installation or import flow; if the repository is already in the current directory, use that directory as the installation source. If the platform is unsupported, permissions are unavailable, or the source cannot be reached, state the limitation and stop.
```

It is not an AI-detector bypass tool; it is delivery-quality control for professional writing.

It never trades hallucinations for a more “human” tone: no invented experience, data, sources, cases, or details.

It addresses four recurring failures:

- prompts, `<think>` reasoning tags, deliberation monologues, tool footers, or editorial instructions leaking into the deliverable;
- corporate buzzwords, social-first hooks, stacked transition chains, and uniform paragraph shells inflating template homogeneity;
- surface-level “humanization” or aggressive spinning changing facts, numbers, terminology, citations, qualifications, or authorial voice;
- one generic style rule being applied across papers, grants, public articles, policies, and official documents without locale or genre awareness.

### Core loop

```text
Understand → Review → Plan → Rewrite → Verify → Evolve
```

ReviewWrite separates four writing surfaces: the review report, revision plan, deliverable body, and verification report. Only the deliverable body belongs in the publication-ready text.

### Core capabilities

- genre-aware Chinese and English writing support with cross-model calibration for GPT, Gemini, Claude, Grok, DeepSeek, and Qwen drafts;
- deterministic + composite checks for reasoning-tag/monologue residue, corporate/internet buzzwords, conversational engagement hooks, and homogenized transition/participial-tail chains (`RW-W-230—RW-W-234`);
- non-prose masking for Markdown fenced code blocks and YAML frontmatter, Setext H2 disambiguation, and unified profile exemptions and `--ignore-rule` handling across single and composite rules;
- cross-language professional review between Chinese and English, preserving terminology, claims, qualifications, and responsibility boundaries across translation;
- long-document review for 100k+ characters: heading-aware chunking, one reusable line-offset index, bounded output, global locations, Chinese-context number/heading indexes, term variants, and duplicate-paragraph signals;
- technical commentary review for model, inference, device, memory, and performance claims, including composite template signals and scope checks;
- an executable delivery gate that extracts the unique body, runs strict checks, validates the SHA-256-bound five-part semantic review, emits body-only output on success, and emits no body (with full lint + semantic diagnostics on stderr) on failure;
- optional audit-only DOCX/PPTX delivery typography QA and read-only provenance/Unicode format-control auditing across text, DOCX, and PPTX containers.

```bash
python3 scripts/reviewwrite_semantic.py init path/to/response.txt --output semantic-review.json
python3 scripts/reviewwrite_gate.py path/to/response.txt --semantic-review semantic-review.json
```

### AI-style and process-residue coverage

These are observable writing and delivery signals, not an authorship classifier. A single word is rarely enough; ReviewWrite combines genre, recurrence, evidence, and paragraph function.

| Type / rules | Scope | Typical signal | Handling and boundary |
| --- | --- | --- | --- |
| Prompt leakage `RW-F-001` | System/developer prompts, role tags, instruction overrides | `system prompt`, `[INST]`, “ignore previous instructions” | `blocker` in deliverables; authorized AI-safety discussion is downgraded for review |
| Hidden reasoning `RW-F-002` | `<think>`/`<thought>` tags, chain-of-thought, analysis channels | `<think>`, “my complete reasoning process” | `blocker`; never place hidden reasoning in the deliverable |
| Model self-description `RW-F-003` | AI identity and capability disclaimers | “As an AI…” | `blocker`; authorized disclosure is reviewed in context |
| Task/editor residue `RW-F-004/RW-W-102` | User-task recap, TODOs, revision workflow | “based on the user request”, “TODO” | Remove from deliverables; review reports may quote the span |
| Tool/runtime residue `RW-F-005` | Tool calls, Skill/Agent names, internal paths, generation footers | `tool call`, `SKILL.md`, `Generated with Claude Code` | `blocker` in deliverables; software docs/audits declare their context |
| Internal contract residue `RW-F-006` | Host/editor-only terms such as evidence boundary, acceptance criteria, final gate, and surface names | `evidence boundary`, `final gate`, `deliverable_body` | `blocker` in ordinary deliverables; declare an authorized subject context when the concept itself is being discussed |
| Latent instruction residue `RW-F-007` | Task compliance, style instructions, or generation order without explicit prompt terminology | “To satisfy the user request, this article will…” | `blocker`; deliver reader-facing content directly |
| Workflow/chat handoff `RW-W-101/RW-W-103` | Process previews and assistant closings | “This section will…”, “Hope this helps” | `warn`; does not rewrite genuine dialogue transcripts |
| Reasoning monologue `RW-W-230` | Self-talk, self-correction, or deliberation leaked from reasoning models | “Let me step back”, “Wait—let me double-check” | `warn`; keep only reader-facing evidence and conclusions; exempted in transcripts |
| Buzzword collocations/stacks `RW-W-231/RW-W-232` | Corporate/internet jargon collocations or dense paragraph buzzword stacks | “move the needle”, figurative “truly load-bearing”, Chinese corporate buzzwords | `warn`; replace with actor, action, metric, and mechanism; preserve technical terms |
| Engagement hooks/candor filler `RW-W-233` | Social-media bait, anti-fluff posture, or performative candor | “Here's the kicker”, “No fluff”, “Buckle up”, “Honestly,” | `warn`; state claims and trade-offs directly; exempted in transcripts |
| Homogenized transitions/tails `RW-W-234` | Clustered additive connectors or shallow participial significance tails | “Furthermore… Moreover… Additionally…”, “, highlighting the importance of…” | `warn`; vary clause progression by evidence weight and remove redundant tails |
| Empty opening/significance `RW-W-201/RW-W-202/RW-W-207` | Generic era framing and unsupported emphasis | “in today’s world”, “highly significant” | Replace with actor, action, scope, standard, and evidence; preserve formal normative terms |
| Formulaic contrast/bridge `RW-W-203/RW-W-208` | Binary reversals, suspense bridges, repeated summaries | “not X but Y”, “in other words”, “the most dangerous part” | One functional contrast may stay; stacked or empty uses warn |
| Promotional/format template `RW-W-204/RW-W-205` | Empty enablement language, fixed selling points, label lists | “unlock the ecosystem”, bold label blocks | Apply genre-aware review; no cross-genre blacklist |
| Technical stacked signals `RW-W-209—RW-W-212` | Model/inference/device prose combining contrasts, importance, audience generalization, forecasts, and numbers | “the key detail” + “most users” + “more likely” | Warn only in `public-article`/`technical-commentary`; request mechanism, metrics, sources, and conditions |
| Mechanical enumeration `RW-W-213` | Three or more sentence-initial ordinal markers | Every paragraph starts “First, Second, Third” | `warn`; distinguish facts, evidence, judgment, and action; retain policy clauses and method steps |
| Extreme-importance labels `RW-W-214` | Short ranking claims such as “the hardest point” or “absolutely cannot” | “The hardest point is efficiency” | Add comparison scope, standard, object, and evidence; replace unsupported ranking with a concrete constraint |
| Meta-narrative packaging `RW-W-215` | “Narrative”, “story”, or “underlying logic” replacing a fact chain or mechanism | “Behind this is a new narrative” | Expand actor, action, object, process, and result; define the term when discussing a genuine communication framework |
| Discourse filler/redundant summary `RW-W-216/RW-W-217` | Attention markers or closure without new information | “It is worth noting”, “Overall” | State the new fact, judgment, scope, or action directly |
| Vague authority/inference narration `RW-W-218/RW-W-220` | Unlocatable attribution or stacked “we can see/this shows” narration | “Research shows”, “We can see…this shows…” | Add a real source and inference conditions, or narrow the claim |
| Translationese/symmetric stacking `RW-W-219/RW-W-221` | Source-language syntax or repeated balanced clauses replacing information choices | literal “conduct an analysis” structures; repeated “both…and…” | Rebuild target-language syntax and organize by fact, judgment, and action |
| Heading-final period `RW-W-222` | A Markdown heading is emitted as a full sentence with a terminal period | `# Implementation plan.` | Remove the terminal period; code comments, question/exclamation marks, and version numbers stay untouched |
| Heading/self-certification semantics `RW-W-223—RW-W-227` | Editorial judgments in titles, self-certifying claims, certainty intensifiers, inference narration, and paragraph-level stacks | “The real problem”, “this clearly proves”, “we can conclude” | State the object, evidence, conditions, and bounded conclusion; preserve necessary definitional, statistical, comparative, or normative uses |
| Ornamental rules/fragment bullets `RW-W-228/RW-W-229` | Separator rules and three or more short label-like dash items fragment formal prose | `---`, repeated `- Deep impact` | Use continuous prose or real heading hierarchy; Setext H2 underlines, YAML headers, and official/policy lists are respected |

Coverage includes `zh-CN` and general professional English across papers, grants, public articles, technical commentary, policy, official documents, reports, memos, marketing, and bilingual writing. Findings are review signals, not a “human score” or detector-evasion promise.

### Four reproducible cases

Four synthetic cases show the draft, revision, and verification result. Under the 1.0+ rules, strict preflight moved from **14 hard failures / 24 warnings** to **0 / 0**; a literal regression check retained 38 protected items (numbers, dates, roles, and qualifiers). A long-document regression also processes 324,015 characters in 55 chunks, maps an intentional model self-description to line 9,001, and checks number and duplicate-paragraph indexes. [Read the test code](tests/test_lint.py).

| Case | Draft | Revision | Main improvement | Preflight |
| --- | --- | --- | --- | --- |
| Academic abstract | [View](examples/simulation/inputs/academic-abstract.zh.md) | [View](examples/simulation/outputs/academic-abstract.zh.md) | removes model identity, reasoning leakage, and self-certifying claims | 5 fail / 5 warn → 0 / 0 |
| Grant rationale | [View](examples/simulation/inputs/grant-rationale.zh.md) | [View](examples/simulation/outputs/grant-rationale.zh.md) | removes promotional language and TODOs | 3 fail / 6 warn → 0 / 0 |
| Policy brief | [View](examples/simulation/inputs/policy-brief.zh.md) | [View](examples/simulation/outputs/policy-brief.zh.md) | clarifies options and evidence gaps | 2 fail / 8 warn → 0 / 0 |
| Executive memo | [View](examples/simulation/inputs/executive-memo.en.md) | [View](examples/simulation/outputs/executive-memo.en.md) | puts decision, constraints, and risks first | 4 fail / 5 warn → 0 / 0 |
| Long-document preflight | [View test](tests/test_lint.py) | — | 324,015 characters in 55 chunks, with global location and number/duplicate indexes | 1 fail / 0 warn, mapped to L9,001 |

### Security and provenance

The release bundle contains the Skill, references, one configuration-structure example, local text/Office QA/provenance-audit scripts, and an optional updater. The default writing path stays local: it does not read credentials, modify or upload input prose or source Office files. The provenance audit is read-only: it reports observable Content Credentials/C2PA/JUMBF or SynthID references and Unicode format controls across plain text, DOCX, and PPTX containers, distinguishes embedded binary markers, text references, and indeterminate states, and never removes or disguises source signals. Only an explicitly enabled update check contacts a Release source; only an explicitly requested Office render writes PDF/PNG previews to an output directory. Verify the official Release, SHA-256, and artifact attestation before installation, and never overwrite an unknown existing directory. See [Security](SECURITY.md) and [provenance-integrity](references/provenance-integrity.md) for the full boundary.

### Office delivery QA: audit before any repair

When a Word document or PowerPoint deck is part of the deliverable, ReviewWrite can add an optional Office QA pass after text review. It is not an “apply one font everywhere” button: the confirmed institutional template wins, the default is read-only, and the source file is never overwritten.

```bash
# Default read-only structural audit; it does not generate a render preview.
python3 scripts/office_qa.py path/to/submission.docx --format json

# Use a confirmed profile and require that a render can be produced.
python3 scripts/office_qa.py path/to/deck.pptx \
  --font-profile examples/office-qa/font-profile.example.json \
  --render required --output-dir /tmp/reviewwrite-preview --format json
```

The report separates font-availability/fallback risk from damaged characters. A structural pass or generated PDF/PNG is not visual approval: inspect every page or slide for missing glyphs, fallback, clipping, overflow, and unexpected wrapping. Without a confirmed template, target font inventory, and visual inspection, ReviewWrite does not claim that a file will display correctly on every recipient device. See [Office QA](references/office-qa.md) and the [font-profile specification](references/font-profiles.md).

### Usage examples

```text
Use ReviewWrite to review and revise this policy brief. List the issues first, then provide the revision. Preserve every number and policy qualification.
```

```text
Use ReviewWrite to revise this academic abstract. Preserve terminology, sample size, statistical results, citations, and the author's English variant. Do not leak editorial process into the abstract.
```

### Multilingual by design

The current core supports `zh-CN` and general professional English. Language behavior is modeled through three coordinates: language, locale, and discourse community. English is not assumed to mean US business prose, and Chinese is not assumed to require slogans, honorific padding, or idioms.

Version 0.6.0 adds cross-language professional review between Chinese and English: confirm source and target locale, genre, audience, and terminology before translation, then independently check numbers, citations, claim strength, qualifications, modality, and responsibility boundaries. It is not word substitution, and fluency or back-translation is not proof of professional accuracy. See [cross-language professional review](references/translation-qa.md).

A new language must pass a dedicated language pack, locale-aware few-shots, fact-preservation regressions, and professional native-language review before moving from `planned` to `experimental` and then `core`. See the [language-pack specification](references/language-packs/README.md).

### Few-shot design

Few-shots are not a growing template dump. A task may select up to three examples: one for its highest-risk failure, one for genre and locale, and, when authorized, one for author voice. If authorization, language, genre, or cultural context does not match, ReviewWrite uses no example. Examples teach transformations; they do not transfer facts, opinions, names, or signature phrasing. See the [few-shot policy](references/few-shot-policy.md).

### Validation and tests

```bash
python3 scripts/reviewwrite_lint.py path/to/draft.md
python3 scripts/reviewwrite_lint.py path/to/draft.md --strict
python3 scripts/reviewwrite_semantic.py init path/to/structured-response.txt --output semantic-review.json
python3 scripts/reviewwrite_gate.py path/to/structured-response.txt --semantic-review semantic-review.json
python3 scripts/validate_skill.py
python3 -m unittest discover -s tests -v
python3 scripts/package_skill.py
```

### Updates and release cadence

ReviewWrite uses a deterministic update policy: the first invocation in a new session reads only local version/cache state; a due network refresh runs after the active writing task and at most once per 24 hours. It does not use random checks or replace a Skill during an active task. The default is notify; trusted environments may auto-download patch releases, while installation and session refresh remain explicit. A host platform's native update channel takes precedence when available.

Qualified small improvements enter the edge channel as patches. A stable minor is promoted only after full regressions and human review. No meaningful improvement means no release. See [operations](OPERATIONS.md) and the [update policy](references/update-policy.md).

### Built on existing work

ReviewWrite learns from and reorganizes reusable ideas from Stop Slop, Humanizer-zh, skill-deslop, and humanizer while strictly maintaining its no-invented-facts boundary. It adds a writing ontology, cross-model and genre routing, a delivery-leakage gate, few-shot selection, and body-bound semantic verification. Exact sources, revisions, and licenses are recorded in [NOTICE.md](NOTICE.md) and [sources.lock.json](sources.lock.json).

### Contributing and license

Contributions of genre packs, language packs, authorized few-shots, false-positive examples, and fact-preservation regressions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first. ReviewWrite is released under the MIT License.
