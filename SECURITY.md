# Security policy

## Runtime boundary

Release 中的 `.skill` 运行时包只包含：

- `SKILL.md` 与 `agents/openai.yaml`；
- `references/` 下的 Markdown 规则、体裁包和 few-shot；
- `scripts/reviewwrite_lint.py` 本地 UTF-8 文本预检；
- `scripts/office_qa.py` 本地 DOCX/PPTX 只读结构审计。
- 一个不含真实字体名称的 `examples/office-qa/font-profile.example.json` 配置结构样例。

运行时包不包含安装器、更新器、发布脚本、令牌读取或网络请求逻辑。`reviewwrite_lint.py` 只读取用户指定的本地文件或标准输入，输出诊断结果；它不联网、不读取凭证或环境变量、不修改输入文件，也不会上传正文。`office_qa.py` 默认只读取用户指定的 `.docx`/`.pptx` 和可选的本地 profile/字体清单；它不会修改或上传输入文件。仅当调用者显式使用渲染模式时，它才会尝试调用本机可发现的 `soffice` 和可选 `pdftoppm`，并只向调用者指定的输出目录（或临时目录）写入 PDF/PNG 预览。

宿主智能体、模型提供方和用户自行启用的工具可能具有不同权限。ReviewWrite 不能替代宿主平台的权限确认、数据处理政策或对不可信 Skill 的审查。

## 安装前核验

1. 使用官方仓库 `songhai-dg/review-write` 和对应 Release tag；
2. 检查 Release 中的 SHA-256 文件与 GitHub artifact attestation；
3. 阅读 `SKILL.md`、`scripts/reviewwrite_lint.py` 和引用的文件；
4. 已有安装时先确认版本和路径，不覆盖未知目录；
5. 在受控项目或临时目录先验证发现与预检行为，再扩展到长期工作环境。

## 漏洞与安全问题

请不要在公开 Issue 中提交未公开漏洞、凭证、私人文本或受保密约束的材料。对安全问题，请通过 GitHub 的私密安全通告渠道联系维护者：<https://github.com/songhai-dg/review-write/security/advisories/new>。

报告应说明受影响版本、复现步骤、实际影响和可公开的最小样例。维护者会先确认问题，再协调修复与披露。
