# Writing ontology

本体用于建立最小写作契约，不要求所有任务输出完整知识图谱。

## 核心实体

| 实体 | 含义 | 最低要求 |
| --- | --- | --- |
| Author | 实际作者或责任机构 | 不用模型身份替代作者 |
| Audience | 真实读者或决策者 | 至少识别专业程度和行动权限 |
| Purpose | 文本要促成的理解或行动 | 与体裁一致 |
| Genre | 社会场景中的文本类型 | 选择一个主要体裁 |
| Claim | 可被支持、质疑或限定的主张 | 与证据建立关系 |
| Evidence | 支持主张的事实、数据、文献或材料 | 不得由语言流畅度替代 |
| Source | 证据出处 | 保留引用和待核验状态 |
| Qualifier | 范围、条件、不确定性和例外 | 改写不得静默删除 |
| Unit | 标题、段落、句子、表格、图注等文本单元 | 标记功能而非只看长度 |
| Revision | 从原文到候选文本的变化 | 说明修复哪个问题 |
| Risk | 事实、引用、政策、隐私、泄漏或体裁风险 | 对应严重程度 |
| Example | 用于校准修改边界的授权样例 | 不迁移其中事实 |

## 核心关系

- `Author writes_for Audience`
- `Document serves Purpose`
- `Document instantiates Genre`
- `Claim supported_by Evidence`
- `Evidence derived_from Source`
- `Qualifier limits Claim`
- `Unit realizes Purpose`
- `Revision repairs Risk`
- `Revision preserves ProtectedItem`
- `Example demonstrates Transformation`

## 文档契约最小字段

```yaml
language: zh-CN | en | bilingual
genre: primary genre id
audience: reader and decision context
purpose: intended understanding or action
preserve:
  - facts
  - numbers
  - citations
  - names and defined terms
  - qualifiers and uncertainty
editable_scope: local | section | full-document
output: review | rewrite | review-and-rewrite
```

## 保护项

默认保护：

- 数字、日期、比例、单位和统计显著性；
- 引文、参考文献、链接和脚注指向；
- 人名、机构名、项目名、政策名和法律定义；
- “可能”“在样本内”“截至某日”等限定语；
- 责任主体、适用对象、资格、义务、禁止、期限和例外；
- 用户明确要求保留的句子、术语、结构或语气。

保护不意味着原文一定正确。发现疑点时标为待核验，不静默纠错。
