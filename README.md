# 审写 · ReviewWrite

**把不该交付的 AI 过程残留，变成可核验的专业正文。**

*Review before rewrite. Keep the facts. Lose the slop.*

不是 AI 检测规避器；是专业写作的交付质量控制。

可复现证据：4 份合成案例的严格预检从 **14 fail / 23 warn** 降至 **0 / 0**；38 项受保护字面量通过逐字回归检查。[查看完整报告](examples/simulation/RUN_REPORT.md)

[中文](#中文) · [English](#english)

审写 · ReviewWrite is an evidence-preserving review-and-rewrite Skill for professional writing. It provides compatibility and installation guidance for Codex, Claude Code, Hermes Agent, Gemini CLI, GitHub Copilot, OpenClaw, WorkBuddy, and other Agent Skills-compatible systems.

---

## 中文

### 先审后写，保护事实，交付正文

审写 · ReviewWrite 面向中英文专业写作：先判断文本和目标，再评审、改写、复核。它保护事实、引用、限定条件和作者声音，不把“像人”理解为制造错误或规避检测。

### 名称与调用：短，但不混乱

- 技术 Skill ID：`reviewwrite`。支持 slash 调用的平台使用 `/reviewwrite`。
- 产品名：审写 · ReviewWrite。
- 自然语言简称：审写、ReviewWrite。它们只用于支持自然语言触发的宿主，不是第二份可安装 Skill，也不保证成为 slash alias。
- 不要并行安装旧 `review-write` 和新 `reviewwrite`；安装器发现旧目录时会拒绝并行安装，先报告路径，再由用户决定迁移或删除。

### 一句话交给智能体安装

复制下面代码块中的内容：

```text
请从官方仓库 https://github.com/songhai-dg/review-write 安装审写（ReviewWrite）Skill。默认安装最新正式 Release，不直接跟踪 `main`；如当前网络无法访问 GitHub，可使用已同步的 Gitee 镜像 https://gitee.com/cufe01/songhai-dg；无论使用哪个来源，都先核对目标版本标签和提交，Release 安装包的 SHA-256 以 GitHub 官方 Release 为准。先确认来源可信并检查是否已有审写或 ReviewWrite；已有版本时报告版本和路径，不得覆盖。再按当前平台的原生 Skill 安装或导入机制执行，并验证 `reviewwrite` 可被发现；平台不支持或权限不足时说明原因后停止。
```

它主要解决：

- 提示词、推理过程、工具调用和编辑指令混入正式正文；
- 表面“去 AI 腔”导致事实、数字、引用、限定条件和作者声音漂移；
- 用一套通用规则误改论文、基金、公众号、政策、公文等不同体裁；
- 把中文规则直接翻译到英文，或忽略本语种、地区和机构的表达规范。

### 核心闭环

```text
Understand → Review → Plan → Rewrite → Verify → Evolve
理解文本      独立评审    约束修改     生成正文      双重复核      保留经验
```

ReviewWrite 严格分离四个写作表面：评审报告、修改计划、正式正文和复核报告。只有正式正文可以成为对外交付文本。

### 核心能力

- 适配论文、基金、政策、报告、公文、备忘录、营销和双语写作；
- 根据语言、读者和真实体裁选择表达，不强套模板；
- 增加技术解读/产业评论路由：检查模型、推理、设备、内存和性能主张中的叠加式模板信号与技术口径；
- 默认保护数字、引用、专名、义务和限定条件；
- 将评审、修改稿和复核分开，并对正式正文做泄漏预检；
- 泄漏预检支持体裁与语境感知：AI 安全论文讨论 `system prompt`、公文使用结构化条目等被授权情形，用 `--context`/`--genre` 声明后降级或放宽，避免正当写作被误判；
- 识别空泛强化和公式化转折，但必须按体裁、上下文与证据判断，不使用生硬禁词表。
- 对 DOCX/PPTX 提供可选的只读字体与渲染质检：检查中英文字体声明、主题/继承不确定项、profile 不匹配和目标字体库存；不静默改文件。

### 四个可复现案例

四份合成案例直接展示问题稿、修改稿和验证结果：严格预检由 **14 个硬失败 / 23 个警告** 降至 **0 / 0**；38 项受保护字面量（数字、日期、角色与限定词）通过逐字回归检查。[查看完整复现报告](examples/simulation/RUN_REPORT.md)。

| 案例 | 问题稿 | 修改稿 | 主要改进 | 预检 |
| --- | --- | --- | --- | --- |
| 学术摘要 | [查看](examples/simulation/inputs/academic-abstract.zh.md) | [查看](examples/simulation/outputs/academic-abstract.zh.md) | 去除模型身份和推理泄漏，保留样本边界 | 5 fail / 4 warn → 0 / 0 |
| 基金申请 | [查看](examples/simulation/inputs/grant-rationale.zh.md) | [查看](examples/simulation/outputs/grant-rationale.zh.md) | 删除宣传腔和待办，补清研究设计 | 3 fail / 6 warn → 0 / 0 |
| 政策简报 | [查看](examples/simulation/inputs/policy-brief.zh.md) | [查看](examples/simulation/outputs/policy-brief.zh.md) | 清理工具残留，明确选项和证据缺口 | 2 fail / 8 warn → 0 / 0 |
| 英文管理备忘录 | [查看](examples/simulation/inputs/executive-memo.en.md) | [查看](examples/simulation/outputs/executive-memo.en.md) | 直接呈现决策、约束和风险 | 4 fail / 5 warn → 0 / 0 |

### 安装与验证

直接让当前智能体使用平台自己的 Skill 机制，并在安装后确认 `reviewwrite` 可被发现。不同平台的范围、导入方式和限制见[平台兼容说明](references/platforms.md)。

### 国内镜像与 SkillHub

GitHub 是唯一官方源；Gitee 仅作为国内只读镜像，SkillHub 作为发现和安装入口。当前镜像地址为 `https://gitee.com/cufe01/songhai-dg`（页面显示名为 `haisong2/review-write`）。不要在 Gitee 单独开发，也不要把 SkillHub 下载包当作新的源码源。

仓库维护者只需在 GitHub 仓库的 Actions secrets 中配置 Gitee 令牌（推荐名称 `GITEE_TOKEN`；当前工作流兼容已存在的 `GITEE`）。之后 `.github/workflows/mirror-gitee.yml` 会在 `main` 或 `v*.*.*` 标签更新时，自动推送对应分支或标签；它不会强制覆盖 Gitee，也不会读取用户正文或运行时凭证。Release 中的 `.skill` 和 `.sha256` 仍以 GitHub 为校验源，上架 SkillHub 时应使用同一份附件。

SkillHub 上架信息建议固定为：技术 ID `reviewwrite`、产品名“审写 · ReviewWrite”、当前版本号、GitHub 官方源、Gitee 镜像、支持的宿主平台和 SHA-256。安装时优先使用平台按钮；若平台只提供下载，则按当前宿主的原生 Skill 安装流程导入，已有目录时不得覆盖。

### 安全与来源

发布包只包含 Skill、参考资料、一个配置结构样例和本地文本/Office QA 脚本；它们不联网、不读取凭证、不修改或上传输入正文与 Office 原件。Office QA 只有在显式要求渲染时才向预览目录写入 PDF/PNG。安装前请核对官方 Release、SHA-256 与 artifact attestation，并在已有安装时拒绝覆盖未知目录。完整边界见 [SECURITY.md](SECURITY.md)。

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

新增语言必须经过独立语言包、locale-aware few-shot、事实保持回归和本语种专业 review，才能从 `planned` 进入 `experimental`，再进入 `core`。详见[语言包规范](references/language-packs/README.md)。

### few-shot 如何设计

few-shot 不是越大越好的模板库。每次最多选择三个：一个修复最高风险问题，一个校准体裁和 locale，必要时一个保持作者声音。授权、语言、体裁或文化语境匹配不足时宁可不用。示例只传递修改原则，不迁移事实、观点、专名或标志性句式。详见 [few-shot policy](references/few-shot-policy.md)。

### 检查与测试

```bash
python3 scripts/reviewwrite_lint.py path/to/draft.md
python3 scripts/reviewwrite_lint.py path/to/draft.md --strict
python3 scripts/validate_skill.py
python3 -m unittest discover -s tests -v
python3 scripts/package_skill.py
```

### 更新与发布

ReviewWrite 默认只提示更新，不在活跃写作任务中静默替换 Skill。联网检查最多每 24 小时一次；宿主平台已有原生版本管理时优先使用平台渠道。

版本采用双轨制：有证据的小改进进入 edge patch；通过完整回归和人工 review 后提升为 stable minor；没有有效变化就不发布。详见[运营策略](OPERATIONS.md)和[更新策略](references/update-policy.md)。

### 站在已有项目之上

ReviewWrite 吸收并重新组织 Stop Slop、Humanizer-zh 和 skill-deslop 的可复用能力，同时增加文档本体、体裁与语言路由、泄漏硬门、few-shot 选择和改后验证。精确来源、版本和许可见 [NOTICE.md](NOTICE.md) 与 [sources.lock.json](sources.lock.json)。

### 贡献与许可

欢迎提交体裁包、语言包、授权 few-shot、误报样例和事实保持回归。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。项目采用 MIT License。

---

## English

### Review first, then rewrite

审写 · ReviewWrite is built for professional Chinese and English writing: it identifies the goal and context, then reviews, rewrites, and verifies the text while preserving facts, citations, qualifications, and authorial voice. It does not promise detector evasion or add mistakes to imitate a human author.

### Naming and invocation: short without ambiguity

- Technical Skill ID: `reviewwrite`. Use `/reviewwrite` on hosts that support slash invocation.
- Product name: 审写 · ReviewWrite.
- Natural-language names: 审写 and ReviewWrite. They are only natural-language triggers on hosts that support them, not separately installable Skills or guaranteed slash aliases.
- Do not install both legacy `review-write` and `reviewwrite`. The installer refuses a parallel install when it detects the old directory, then reports its path for a user-directed migration or removal.

### One-sentence agent installation

Copy the text in the code block:

```text
Install 审写 (ReviewWrite) from the canonical repository https://github.com/songhai-dg/review-write. Install the latest stable Release by default; do not track `main` directly. If GitHub is unreachable on the current network, use the synchronized Gitee mirror https://gitee.com/cufe01/songhai-dg. Whichever source you use, verify the target tag and commit; use the GitHub Release as the authority for the package SHA-256. First verify the source and check whether 审写 or ReviewWrite already exists; if it does, report its version and path and do not overwrite it. Then use the current host platform's native Skill installation or import flow and verify that `reviewwrite` is discoverable; if the platform is unsupported or permissions are insufficient, report the reason and stop.
```

It is not an AI-detector bypass tool; it is delivery-quality control for professional writing.

It addresses four recurring failures:

- prompts, reasoning, tool calls, or editorial instructions leaking into the deliverable;
- surface-level “humanization” changing facts, numbers, citations, qualifications, or authorial voice;
- one generic style rule being applied across papers, grants, public articles, policies, and official documents;
- translating rules between languages without respecting locale, discourse community, or institutional convention.

### Core loop

```text
Understand → Review → Plan → Rewrite → Verify → Evolve
```

ReviewWrite separates four writing surfaces: the review report, revision plan, deliverable body, and verification report. Only the deliverable body belongs in the publication-ready text.

### Core capabilities

- genre-aware Chinese and English writing support;
- technical commentary review for model, inference, device, memory, and performance claims, including composite template signals and scope checks;
- context-sensitive routing by language, audience, locale, and discourse community;
- protection for facts, numbers, citations, names, obligations, and qualifications;
- separated review, revision, deliverable, and verification surfaces with leakage checks;
- genre- and context-aware preflight: authorized cases such as an AI-safety paper discussing `system prompt`, or an official document using structured items, are declared with `--context`/`--genre` and downgraded or relaxed instead of hard-failing legitimate writing;
- contextual checks for empty intensifiers and formulaic pivots, rather than a rigid blacklist of “AI words.”
- optional audit-only DOCX/PPTX delivery QA for Chinese/Latin font declarations, theme/inheritance uncertainty, confirmed-profile mismatches, target font inventories, and a render gate; it never silently rewrites a source Office file.

### Four reproducible cases

Four synthetic cases show the draft, revision, and verification result. Strict preflight moved from **14 hard failures / 23 warnings** to **0 / 0**; a literal regression check retained 38 protected items (numbers, dates, roles, and qualifiers). [Read the full reproducibility report](examples/simulation/RUN_REPORT.md).

| Case | Draft | Revision | Main improvement | Preflight |
| --- | --- | --- | --- | --- |
| Academic abstract | [View](examples/simulation/inputs/academic-abstract.zh.md) | [View](examples/simulation/outputs/academic-abstract.zh.md) | removes model identity and reasoning leakage | 5 fail / 4 warn → 0 / 0 |
| Grant rationale | [View](examples/simulation/inputs/grant-rationale.zh.md) | [View](examples/simulation/outputs/grant-rationale.zh.md) | removes promotional language and TODOs | 3 fail / 6 warn → 0 / 0 |
| Policy brief | [View](examples/simulation/inputs/policy-brief.zh.md) | [View](examples/simulation/outputs/policy-brief.zh.md) | clarifies options and evidence gaps | 2 fail / 8 warn → 0 / 0 |
| Executive memo | [View](examples/simulation/inputs/executive-memo.en.md) | [View](examples/simulation/outputs/executive-memo.en.md) | puts decision, constraints, and risks first | 4 fail / 5 warn → 0 / 0 |

### Installation and verification

Ask the current agent to use its own Skill mechanism, then verify discovery of `reviewwrite`. Platform-specific scopes, import paths, and limitations are in the [platform compatibility guide](references/platforms.md).

### Domestic mirror and SkillHub

GitHub is the single canonical source. Gitee is a read-only domestic mirror, and SkillHub is a discovery and installation channel. The current mirror is `https://gitee.com/cufe01/songhai-dg` (displayed as `haisong2/review-write`). Do not develop a second copy on Gitee or treat a SkillHub download as a new source repository.

Repository maintainers only need to configure the Gitee token as a GitHub Actions secret. The documented token name is `GITEE_TOKEN`; the workflow also accepts the existing `GITEE` secret. `.github/workflows/mirror-gitee.yml` then pushes `main` and `v*.*.*` tags to Gitee without force-overwriting the mirror. GitHub remains the verification source for Release `.skill` and `.sha256` assets; SkillHub listings should use those same assets.

For SkillHub metadata, keep the technical ID `reviewwrite`, product name “审写 · ReviewWrite”, version, canonical GitHub URL, Gitee mirror, supported hosts, and SHA-256 together. Prefer the marketplace's native install button; when it only provides a download, use the current host's native Skill import flow and never overwrite an existing directory.

### Security and provenance

The release bundle contains only the Skill, references, one configuration-structure example, and local text/Office QA scripts. They do not make network requests, read credentials, modify or upload input prose or source Office files. Only an explicitly requested Office render writes PDF/PNG previews to an output directory. Verify the official Release, SHA-256, and artifact attestation before installation, and never overwrite an unknown existing directory. See [SECURITY.md](SECURITY.md) for the full boundary.

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

A new language must pass a dedicated language pack, locale-aware few-shots, fact-preservation regressions, and professional native-language review before moving from `planned` to `experimental` and then `core`. See the [language-pack specification](references/language-packs/README.md).

### Few-shot design

Few-shots are not a growing template dump. A task may select up to three examples: one for its highest-risk failure, one for genre and locale, and, when authorized, one for author voice. If authorization, language, genre, or cultural context does not match, ReviewWrite uses no example. Examples teach transformations; they do not transfer facts, opinions, names, or signature phrasing. See the [few-shot policy](references/few-shot-policy.md).

### Validation and tests

```bash
python3 scripts/reviewwrite_lint.py path/to/draft.md
python3 scripts/reviewwrite_lint.py path/to/draft.md --strict
python3 scripts/validate_skill.py
python3 -m unittest discover -s tests -v
python3 scripts/package_skill.py
```

### Updates and release cadence

ReviewWrite notifies by default and never replaces a Skill during an active writing task. Network checks are cached for up to 24 hours. A host platform's native update channel takes precedence when available.

Qualified small improvements enter the edge channel as patches. A stable minor is promoted only after full regressions and human review. No meaningful improvement means no release. See [operations](OPERATIONS.md) and the [update policy](references/update-policy.md).

### Built on existing work

ReviewWrite learns from and reorganizes reusable ideas from Stop Slop, Humanizer-zh, and skill-deslop. It adds a writing ontology, genre and language routing, a delivery-leakage gate, few-shot selection, and post-rewrite verification. Exact sources, revisions, and licenses are recorded in [NOTICE.md](NOTICE.md) and [sources.lock.json](sources.lock.json).

### Contributing and license

Contributions of genre packs, language packs, authorized few-shots, false-positive examples, and fact-preservation regressions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first. ReviewWrite is released under the MIT License.
