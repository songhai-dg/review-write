# Platform compatibility

ReviewWrite 的能力源是 `SKILL.md`、按需读取的 `references/` 和可选脚本。平台适配不改变写作规则，也不把某个平台的目录约定写成通用真相。

## 给智能体的安装说明

请从官方仓库 https://github.com/songhai-dg/review-write 安装 ReviewWrite Skill。先确认来源可信并检查是否已有 ReviewWrite；已有版本时报告版本和路径，不得覆盖。再按当前平台的原生 Skill 安装或导入机制执行，并验证 `review-write` 可被发现；平台不支持或权限不足时说明原因后停止。

支持 tap 或技能仓库目录的宿主应安装仓库中的 `skills/review-write/`；根目录的 README、测试和维护脚本不属于运行时技能。
