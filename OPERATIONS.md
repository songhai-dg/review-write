# ReviewWrite Operations

运营节奏的目标是持续获得真实改进，而不是制造版本号。

## Release train

### Daily edge candidate

每天的自动任务检查四类输入：新 issue、误报/漏报样例、上游项目变更、现有评测失败。只有满足以下条件才创建一个 edge 候选 PR：

1. 能描述一个具体问题和受影响体裁；
2. 改动范围单一，可在一次 PR 中审阅；
3. 新增或更新回归样例；
4. 结构验证、单元测试和泄漏预检通过；
5. 不降低事实、数字、引用和政策口径保护。

没有合格改进时记录“no release”，不空发版本。合格的日更通常增加 patch，并标记为 prerelease；安全修复可以立即发布。

### Weekly stable promotion

每周将已验证的 edge 改动合并为稳定候选，运行全量体裁评测和改前/改后保护项检查。通过人工 review 后增加 minor 版本并发布稳定版。SemVer 的 major 只用于破坏兼容性的变化，不应每周增加。

## Automation boundary

自动任务可以：读取 issue 和上游 diff、选择一个小问题、修改规则或示例、添加测试、更新 changelog、执行 patch/minor 版本同步、创建 PR。

自动任务不可以：直接推送受保护的 `main`、自动发布 stable、删除用户样例、降低现有门禁、改变许可、覆盖本地安装或把未经授权文本加入 few-shot。

建议仓库规则：

- `main` 开启 branch protection；
- edge PR 至少通过 CI；
- stable 发布至少一名维护者批准；
- GitHub Release 包含 `.skill`、`.skill.sha256` 和 artifact attestation；
- bot 分支使用 `bot/daily-*` 和 `bot/weekly-*`；
- PR 必须报告“新增能力、测试证据、可能回归、来源与许可”。

## Agent task files

- `automation/daily-evolution.md`：每日自动任务的固定契约；
- `automation/weekly-promotion.md`：每周稳定版候选契约；
- `scripts/bump_version.py`：跨文件同步版本，默认只预览；
- `.github/workflows/ci.yml`：每次 PR 的硬门；
- `.github/workflows/release.yml`：tag 后构建、校验、签名和发布。
- `.github/workflows/mirror-gitee.yml`：将 GitHub 的 `main` 和正式版本标签推送到 Gitee；Gitee 不作为第二个开发源，也不使用强制覆盖。

首次启用 Gitee 镜像时，目标仓库为 `cufe01/songhai-dg`（页面显示名为 `haisong2/review-write`），再在 GitHub Actions secrets 中添加 `GITEE_USERNAME` 和 `GITEE_TOKEN`。先手动运行一次 `Mirror to Gitee` 验证仓库权限，再依赖后续 push/tag 自动同步。Release 附件仍以 GitHub 为官方校验源，需要在 SkillHub 上架时上传同一份 `.skill` 与 `.sha256`。

自动任务应调用这些固定入口，而不是每次自行发明发布流程。

## Operating metrics

不要用 commit 数量或版本数量作为主要指标。每周跟踪：

- 泄漏测试召回率及误报数；
- 受保护事实、数字、引用和限定条件的保持率；
- 各体裁的人工接受率；
- 用户应用修改后再次返工的比例；
- 安装成功率、更新成功率和回滚次数；
- issue 首次响应和有效修复时间；
- GitHub star 到实际安装、安装到重复使用的转化。
