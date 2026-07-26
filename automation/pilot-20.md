# Codex Scheduled：ReviewWrite 20 轮滚动候选任务

在 `review-skills` 项目中运行。先读取：

- `AGENTS.md`（如存在）；
- `automation/pilot-20.json`；
- `automation/pilot-state.json`；
- `automation/pilot-log.md`；
- `OPERATIONS.md`；
- `release-policy.json`；
- `references/competitor-evaluation.md`；
- `sources.lock.json`。

一次 Scheduled 运行最多完成一轮，不连续执行多轮。

## 运行资格

1. 当前分支必须是 `bot/pilot-20`；否则只报告并停止，不创建新分支。
2. `completed_rounds >= 20`、状态为 `stopped`，或存在未解决的 blocker 时停止。
3. 使用 `America/Los_Angeles` 日期，将一天划分为六个四小时槽。用
   `SHA-256("reviewwrite-pilot-20|YYYY-MM-DD")` 的前两个互不相同字节对 6 取模，得到当天两个有效槽。
4. 当前槽不在有效槽内，或该槽今天已完成时，输出 `not due`，不修改文件、不增加轮次、不增加版本。
5. 任何开始执行的轮次先把状态写为 `running`；完成或停止时必须恢复为 `ready`、`review-required`、`completed` 或 `stopped`。

## 普通轮：1–3、5–7、9–11、13–15、17–19

1. 从四条证据通道各取有限候选：仓库 bug/回归、用户或 issue 样例、竞品第一手资料、研究第一手资料。
2. 每轮最多评估三个外部候选，只选择一个有本地失败证据的问题。
3. 先增加最小失败测试，再做最小实现。不得复制未知许可代码、私人文本、竞品专有规则表或营销文案。
4. “超越竞品”必须遵守 `references/competitor-evaluation.md`，同时报告改善和仍落后的维度。
5. 运行：
   - `python3 scripts/validate_skill.py`
   - `python3 -m unittest discover -s tests -v`
   - `git diff --check`
   - `python3 scripts/package_skill.py`
6. 验证全部通过且存在用户可见改进时，更新 `CHANGELOG.md` 并执行一次 patch 版本提升。没有足够证据时记录 `no release`，不改版本。
7. 每轮修改不超过配置的文件数量，不新增运行时依赖，不降低安全、事实、引用或体裁门禁。

## Review 轮：4、8、12、16、20

Review 轮默认不改功能、不升版本。独立检查最近四轮：

- 问题证据是否真实；
- 竞品或研究来源是否为第一手资料，许可证是否清楚；
- 测试是否只迎合新增规则；
- 相邻体裁是否出现误伤；
- 事实、数字、引用和限定条件是否退化；
- 安装、更新、打包、Office QA 和回滚是否可靠；
- 累积指令是否变得过长、冲突或写死；
- 是否应回退某轮、暂停试验或请求人工判断。

Review 失败时将状态设为 `review-required`，记录 blocker，后续 Scheduled 运行不得继续实现。第 20 轮只给出是否进入 stable 候选的建议，不合并 `main`、不创建 stable tag。

## 分支、版本与发布

- 全部 20 轮只使用 `bot/pilot-20`。
- 只维护一个 Draft PR；不要创建每轮分支或每轮 PR。
- 试验阶段不得推送候选分支、合并 `main`、创建公开 Release 或安装本地候选版本，除非用户另行明确授权。
- 有实质实现且全部门禁通过才增加 patch；Review、no-op、来源调查不增加版本。
- major 永不自动增加；stable minor 必须人工 Review。

## 每轮记录

向 `automation/pilot-log.md` 追加：

- 轮次、时间和槽位；
- 轮次类型；
- 问题和本地失败证据；
- 竞品/研究来源、许可证和限制；
- 修改文件；
- 新增测试和结果；
- 比较指标；
- 版本变化或 `no release`；
- 风险、回滚方法和下一轮建议。

最后原子更新 `automation/pilot-state.json`。不得记录凭证、隐藏推理或不可公开材料。
