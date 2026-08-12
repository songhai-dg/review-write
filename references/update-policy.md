# Update policy

ReviewWrite 将“检查”“下载”“安装”分开，避免一次普通写作调用突然改变正在使用的规则。

## 默认行为

- 默认策略是 `notify`，不是静默安装。
- 每次调用只读取本地版本和更新缓存，不随机抽查，也不因此联网。可运行 `status` 获取 `cache-fresh` 或 `check-due`。
- 缓存过期时，将一次联网检查安排在当前写作任务结束后；联网查询至多每 24 小时一次。
- 没有新版本时不向用户插入更新提示，更不得把更新日志写入正式正文。
- 有新版本时在任务完成后提示，不打断当前评审或改写。
- 宿主平台已有原生版本管理时，优先使用平台更新渠道。
- Git 仓库工作副本不由更新器覆盖。

## 四种策略

| Policy | Behavior |
| --- | --- |
| `off` | 不检查更新 |
| `notify` | 检查并提示，由用户决定是否下载或安装 |
| `auto-patch` | 允许计划任务下载同一 major/minor 下的补丁版本 |
| `auto-minor` | 允许计划任务下载同一 major 下的补丁或 minor 版本 |

`auto-*` 仅允许下载通过门禁的发行包；安装仍在任务结束后通过平台原生管理器或显式安装操作完成。major 版本从不自动安装。

## 配置和使用

官方仓库由 `release-policy.json` 的 `repository` 固定为 `songhai-dg/review-write`。如果维护 fork，应显式使用 `--repo` 或 `REVIEWWRITE_REPOSITORY`，不要冒充官方更新源。

```bash
python3 scripts/reviewwrite_update.py check
python3 scripts/reviewwrite_update.py status --format json
python3 scripts/reviewwrite_update.py check --channel edge --format json
python3 scripts/reviewwrite_update.py download --require-attestation
```

也可以临时提供仓库：

```bash
REVIEWWRITE_REPOSITORY=owner/fork python3 scripts/reviewwrite_update.py check
```

下载必须验证发行包旁的 SHA-256。自动应用还应验证 GitHub artifact attestation。校验后的文件进入用户缓存目录，不直接覆盖已安装版本。

## 调用时检查

平台或用户明确启用更新检查时，Agent 在每个新会话首次调用 ReviewWrite 时只运行本地状态检查：

```bash
python3 scripts/reviewwrite_update.py status --format json
```

`cache-fresh` 表示本会话不再检查；`check-due` 表示当前任务完成后再运行联网检查：

```bash
python3 scripts/reviewwrite_update.py check --format json
```

结果为 `update-available` 时只报告版本与发行页；不要在同一次写作任务中下载安装。平台提供原生更新提示时，不重复联网检查。

不采用随机检查。随机机制会让同一版本在不同会话表现不可预测，也不能解决活跃任务中途换规则的问题。若大规模集中部署担心同时访问更新源，应由宿主调度器做确定性错峰，而不是由 Skill 随机决定。

## 版本与安装

只要运行时规则、脚本或宿主契约发生变化，发布包就必须升级语义版本。文案错字等不影响运行时的纯文档修订，也应随下一次正式发布同步，但不必为每次小修改立即发版。

- patch：规则修复、误报修复、平台兼容和小功能；可信环境可以选择自动下载，但仍在任务结束后显式安装；
- minor：新增较大能力或改变宿主协同方式；只提示，不默认自动安装；
- major：不兼容变化；必须人工确认。

下载不等于安装。安装完成后必须刷新 Skill 发现缓存或新建会话，下一次调用再使用新版本。
