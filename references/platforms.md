# Platform compatibility

审写 · ReviewWrite 的能力源是 `SKILL.md`、按需读取的 `references/` 和可选脚本。平台适配不改变写作规则，也不把某个平台的目录约定写成通用真相。

## 给智能体的安装说明

请从官方仓库 https://github.com/songhai-dg/review-write 安装 ReviewWrite Skill；如当前网络无法访问 GitHub，使用同步镜像 https://gitee.com/cufe01/songhai-dg。如果当前智能体已经安装，不要重复安装，也不要搜索或替换成名称相近的其他技能。请使用所在平台自己的 Skill 安装或导入机制；如果仓库已在当前目录，直接以当前目录为安装来源。平台不支持、没有权限或无法访问来源时，说明限制并停止。

唯一技术 Skill ID 是 `reviewwrite`。支持 slash 调用的平台使用 `/reviewwrite`；“审写”和“ReviewWrite”只是在支持自然语言触发的平台中的简称，不是第二份可安装 Skill。支持 tap 或技能仓库目录的宿主应安装仓库中的 `skills/reviewwrite/`；根目录的 README、测试和维护脚本不属于运行时技能。
