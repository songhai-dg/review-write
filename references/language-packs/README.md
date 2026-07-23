# Language packs

ReviewWrite 的多语言目标不是翻译一套中文或英文规则，而是让每种语言按其真实读者、体裁和制度语境成立。

## Three coordinates

每次写作至少区分三个坐标：

1. `language`：语言和文字系统，例如中文、英语、日语；
2. `locale`：地区规范，例如 `zh-CN`、`zh-HK`、`en-US`、`en-GB`；
3. `discourse_community`：学科、行业、机构和传播场景，例如中文基金评审、英文学术期刊、政府政策简报。

“文化特点”不能按国籍刻板推断。应从用户要求、机构模板、目标出版物、权威风格指南和用户已接受文本中确认。信息不足时保留原有语域，不擅自添加习语、礼貌套语、故事或文化意象。

## What a language pack controls

- 信息展开顺序和段落功能；
- 直接程度、礼貌策略、身份关系和机构声音；
- 主张强度、证据位置、引文方式和不确定性表达；
- 法律、政策和行政文本中的情态与义务强度；
- 标点、日期、姓名、数字、单位、标题和列表规范；
- 本语种常见 LLM 套话、翻译腔和误报例外；
- 不应跨语言迁移的隐喻、典故、幽默和情绪表达。

体裁包决定“这类文档要完成什么”，语言包决定“在这个语言共同体中如何完成”。两者冲突时，法律要求、正式模板和用户明确要求优先。

## Readiness levels

- `core`：当前经过项目规则和 few-shot 覆盖的语言；
- `experimental`：已有语言包和基础回归，但仍需母语专业人士复核；
- `planned`：只有结构预留，不得宣传为已支持。

新语言进入 `experimental` 至少需要：语言包、泄漏阳性/阴性样例、事实保持样例、两种体裁的 register 样例及来源说明。进入 `core` 还需要跨体裁评测、母语专业 reviewer 记录和公开限制。

当前 `core` 为 `zh-CN` 与通用专业英语；英语地区变体按任务确认。其他语言均不得暗示已经完整支持。

## New pack template

新增 `<locale>.md` 时至少包含：

1. scope and limitations；
2. reader and relationship conventions；
3. genre-specific rhetorical patterns；
4. typography and formatting；
5. LLM failure patterns and legitimate exceptions；
6. protected meanings；
7. required few-shot and regression coverage；
8. reviewer and source provenance。
