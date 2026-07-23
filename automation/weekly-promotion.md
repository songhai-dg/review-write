# Weekly stable promotion task

你正在准备 ReviewWrite 的每周稳定候选，不是按日历强制发布。

1. 汇总本周已合并且经过真实样例验证的 edge 改动。
2. 对学术论文、基金申请、公众号、政策文案、公文和英文写作运行全量回归。
3. 比较上一稳定版，确认泄漏、事实保持、引用保持和体裁接受率没有退化。
4. 未达到门禁时创建评测报告并停止，不增加版本。
5. 达到门禁时更新 `CHANGELOG.md`，运行 `python3 scripts/bump_version.py minor --apply`。
6. 创建 `bot/weekly-YYYYMMDD` 稳定候选 PR，等待维护者批准。
7. 批准合并后创建 `vX.Y.Z` tag；GitHub Actions 负责可复现打包、SHA-256、attestation 和 Release。

不得自动升级 major，不得自动修改许可，不得用 star 数代替质量门禁。
