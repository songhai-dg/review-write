# Contributing to 审写 · ReviewWrite

感谢参与 ReviewWrite。项目优先接受能够提高真实写作质量、降低语义漂移或减少误报的贡献。

## 可以贡献什么

- 新体裁包或现有体裁包修订；
- 中英文及其他语言的 before/after few-shot；
- 新语言包、locale 规范和本语种专业 review 记录；
- 提示词、推理、工作流泄漏的新模式和反例；
- 事实、引用、数字和政策口径保持测试；
- 对上游开源项目的新版本差异分析；
- lint 规则的误报修复。

## 示例要求

每个 few-shot 必须包含：

- `language`、`genre`、`issue_tags`；
- 修改前文本；
- 修改后文本；
- 简短、可公开的修改理由；
- 明确的来源和授权状态。

不得提交私人邮件、未公开论文、受保密约束的基金材料、含个人信息的政策材料，除非已经取得明确授权并完成必要匿名化。不要用模型生成的虚构文本冒充真实作者样例。

新增语言不得只翻译现有规则。贡献应说明语言、locale、话语共同体、适用体裁、权威风格来源、文化迁移风险和 reviewer 背景；未达到 [language packs](references/language-packs/README.md) 门禁时只能标记为 experimental。

## 规则要求

- 禁词应当是诊断信号，不应默认成为跨体裁绝对禁令；
- 新增硬失败规则必须有泄漏或事实风险依据，并提供至少一个阳性和一个阴性测试；
- 不接受以绕过 AI 检测器为目标的改动；
- 不接受故意加入错误、口语病或虚构经历的“人类化”方法。

## 提交前检查

```bash
python3 scripts/validate_skill.py
python3 -m unittest discover -s tests -v
```

如果引用或改编上游内容，请同步更新 `NOTICE.md` 和 `sources.lock.json`。
