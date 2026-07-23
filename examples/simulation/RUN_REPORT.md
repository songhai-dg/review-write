# ReviewWrite 端到端模拟报告

执行日期：2026-07-22

Skill 版本：0.2.0

执行方式：按已安装的 ReviewWrite Skill 完成 `Review → Plan → Rewrite → Verify`，并使用 `reviewwrite_lint.py --strict` 做确定性泄漏预检。

这些文本都是项目原创的合成测试样本，只用于验证过程泄漏、体裁校准和事实保持，不用于判断作者身份，也不代表真实研究、项目、政策或经营数据。

## 总体结果

| 样本 | 体裁 | 修改前 | 修改后 | 保护项 |
| --- | --- | ---: | ---: | --- |
| 中文学术摘要 | academic-paper | 5 fail / 4 warn | 0 fail / 0 warn | 10 项全部保留 |
| 中文基金申请 | grant-proposal | 3 fail / 6 warn | 0 fail / 0 warn | 8 项全部保留 |
| 中文政策简报 | policy-brief | 2 fail / 8 warn | 0 fail / 0 warn | 10 项全部保留 |
| 英文管理备忘录 | executive-memo | 4 fail / 5 warn | 0 fail / 0 warn | 10 项全部保留 |
| **合计** | 4 类 | **14 fail / 23 warn** | **0 fail / 0 warn** | **38 项逐字保留** |

检测器只负责定位提示、推理、工具、编辑和聊天残留等确定性信号。修改稿能否成立，还必须经过主张—证据、体裁和限定条件复核。

## 1. 中文学术摘要

### 文档契约

- 读者：学术期刊审稿人；
- 目的：报告数字化培训参与与劳动生产率之间的样本内关系；
- 保护：年份、地区数、样本量、分组、方法、效应值、置信区间、p 值和两项局限；
- few-shot：`zh-process-leakage-001` 与 `zh-academic-001`，只借用变换原则。

### 评审结论

1. `blocker`：正文包含对话标签、模型身份、用户任务和完整推理过程；
2. `major`：“充分证明”“所有中小企业”超出非随机、3 个省样本能够支持的范围；
3. `minor`：章节预告、编辑待办和聊天式结尾不属于摘要正文。

### 修改计划

- `preserve`：186 家企业、74/112 分组、倾向得分匹配、4.8%、95% CI 和 p 值；
- `repair`：删除内部过程，将结论缩小为样本内相关关系，把外推和因果限制保留在结果之后；
- `acceptance`：保护项逐字存在，修改稿严格预检为零发现。

[查看问题样本](inputs/academic-abstract.zh.md) · [查看修改稿](outputs/academic-abstract.zh.md)

## 2. 中文基金申请

### 文档契约

- 读者：基金项目同行评审人；
- 目的：说明研究设计、拟创新点和可检验目标；
- 保护：3 年、2018—2025 年、12 个地区、月度面板、两类模型、10% 性能目标和 80% 审计要求；
- few-shot：`zh-process-leakage-001` 与 `zh-grant-001`。

### 评审结论

1. `blocker`：系统提示、用户要求和内部 skill 混入申请正文；
2. `major`：“国际领先”“首次全面突破”和“重大社会影响”没有比较对象或证据；
3. `major`：团队成果与合作条件尚未提供，不能由模型补写；
4. `minor`：时代背景、排比宣传词和版本待办削弱可评审性。

### 修改计划

- `preserve`：研究周期、数据范围、面板粒度、比较对象、成功指标和数据审计要求；
- `repair`：将领先性口号改为两项拟验证设计，并明确文献对照、团队成果和合作条件仍待真实材料；
- `acceptance`：不新增团队经历、合作单位、预实验结果或影响承诺。

[查看问题样本](inputs/grant-rationale.zh.md) · [查看修改稿](outputs/grant-rationale.zh.md)

## 3. 中文政策简报

### 文档契约

- 读者：市级政策决策者；
- 目的：在三套方案中选择处理材料重复提交问题的路径；
- 保护：时间、8 个区、12 项事项、38%/27%、三个方案、责任主体、试点时间和监测指标；
- few-shot：`zh-process-leakage-001` 与 `zh-policy-brief-001`。

### 评审结论

1. `blocker`：用户任务、搜索工具和本地文件路径出现在政策正文；
2. `major`：重要性和治理口号没有帮助决策者比较方案；
3. `major`：三套方案缺少成本数据，应显式保留这一证据缺口；
4. `minor`：写作预告、版本说明和聊天交接语破坏交付边界。

### 修改计划

- `preserve`：全部观察数据、三个选项、方案二的主体、时间、范围和指标；
- `repair`：按“决策问题—方案比较—建议与监测”重组，并把成本缺口写入判断；
- `acceptance`：不虚构成本、法律依据、部门意见或实施效果。

[查看问题样本](inputs/policy-brief.zh.md) · [查看修改稿](outputs/policy-brief.zh.md)

## 4. 英文管理备忘录

### Document contract

- Reader: an executive approving a temporary staffing response;
- Purpose: decide whether to reassign 4 employees for 14 days;
- Preserve: dates, queue size, ageing rate, staffing gap, three options, owner, checkpoint, and the reported 18% trade-off;
- Few-shots: `en-process-leakage-001`; no author-voice example was available.

### Review conclusion

1. `blocker`: the draft exposes the user prompt, model identity, chain of thought, tool output, and a local path;
2. `major`: the opening labels the backlog strategically without evidence and delays the requested decision;
3. `major`: the source material does not provide comparable cost or throughput estimates;
4. `minor`: formulaic contrast, presentation-style labels, and a chat handoff remain in the memo.

### Revision plan

- `preserve`: all operational figures, options, owner, date, and stated risk;
- `repair`: place the decision first, separate supplied evidence from recommendation, and retain the missing comparison data as a limitation;
- `acceptance`: no invented approval, cost, throughput, or causal explanation; strict preflight returns zero findings.

[View the problematic sample](inputs/executive-memo.en.md) · [View the revision](outputs/executive-memo.en.md)

## 复现命令

```bash
python3 scripts/reviewwrite_lint.py examples/simulation/inputs/academic-abstract.zh.md --strict
python3 scripts/reviewwrite_lint.py examples/simulation/outputs/academic-abstract.zh.md --strict
python3 -m unittest discover -s tests -v
```

`tests/test_lint.py` 会遍历 `manifest.json`，确认每份问题样本达到预期的 fail/warn 下限、每份修改稿严格预检为零发现，并逐项检查保护字面量在修改前后均存在。
