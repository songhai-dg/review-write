# Office QA 示例

`font-profile.example.json` 只展示配置结构，所有字体名称都是占位符，不能直接用于真实交付。

单元测试会在临时目录生成最小 DOCX/PPTX OOXML 样本，覆盖：中文 `eastAsia/ea` 字体不匹配、英文 `latin` 字体匹配、主题解析、没有字体库存时不伪造可用性结论，以及 `--render required` 在渲染器缺失时产生 blocker。测试不向仓库提交二进制 Office 文件，也不依赖本机安装的字体。

真实项目应使用单位确认的模板与一份可共享的脱敏样本，在目标 Office 环境中渲染并逐页检查。
