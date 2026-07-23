# Daily evolution task

你正在维护 ReviewWrite。一次运行最多完成一个可验证的小改进。

1. 读取 `OPERATIONS.md`、`release-policy.json`、当前 issue、最近评测失败和 `sources.lock.json`。
2. 只选择一个具体问题；若没有足够证据，输出 `no release` 并停止。
3. 先增加最小失败样例，再修改规则、体裁包、few-shot 路由或工具。
4. 保持 `SKILL.md` 为唯一核心，不创建平台分叉。
5. 检查来源和许可，不复制未知许可内容，不收录私人文本。
6. 运行 `python3 scripts/validate_skill.py` 和 `python3 -m unittest discover -s tests -v`。
7. 在 `CHANGELOG.md` 写清用户可见变化，再运行 `python3 scripts/bump_version.py patch --apply`。
8. 创建 `bot/daily-YYYYMMDD-topic` 分支和 edge PR；不得直接合并 `main`，不得发布 stable。

PR 必须包含：问题证据、改动范围、新增测试、回归风险、来源/许可和回滚方法。
