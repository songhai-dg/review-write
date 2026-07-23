# Office QA：DOCX / PPTX 交付前字体与渲染门禁

Office QA 是 ReviewWrite 的按需交付质检层，不是正文改写规则，也不是自动换字体工具。只有用户提供 `.docx` 或 `.pptx`、要求交付格式检查，或明确抱怨乱码、字体混乱、英文回退、截断、异常换行时才启用。

## 先确认边界

1. 原文件、机构模板和目标平台分别是什么；优先以用户提供的模板为准。
2. 此次是仅审计，还是已授权另存修复。默认是 `audit-only`；不得覆盖原文件。
3. 是否有经确认的字体 profile 和目标环境字体清单。没有时，不能宣称字体已在收件人设备上可用。
4. 是否能渲染。结构检查不能证明版式、缺字和字体回退；渲染后仍须逐页人工查看。

“乱码”可能是字体缺失或回退，也可能是文本字符本身已损坏。两种问题必须分开报告；后者不能靠替换字体掩盖。

## 命令

```bash
# 默认：只读结构审计；不渲染、不修改输入文件
python3 scripts/office_qa.py path/to/submission.docx --format json

# 目标模板已确认时，按 profile 审计；在指定目录写入 PDF/PNG 预览
python3 scripts/office_qa.py path/to/deck.pptx \
  --font-profile examples/office-qa/font-profile.example.json \
  --available-fonts path/to/target-fonts.txt \
  --render required --output-dir /tmp/reviewwrite-preview --format json
```

`--render required` 在没有可用渲染器或渲染失败时产生 `blocker`。渲染成功只代表已生成预览，状态仍为 `rendered_pending_inspection`；必须逐页检查 PDF/PNG 后，才能把视觉门禁记为通过。

## 审计内容

| 层级 | DOCX | PPTX | 结论边界 |
| --- | --- | --- | --- |
| OOXML 结构 | run、直接格式、主题引用 | 幻灯片 run、主题引用 | 能找出显式混用，不能完整推断继承样式 |
| 中英文脚本 | `eastAsia` 与 `ascii/hAnsi/cs` | `ea`、`latin`、`cs` 与 run 字体 | 中英文可分别约束，不能假设同一字体适用全部语言 |
| profile 对照 | 显式字体是否符合模板 | 显式字体是否符合模板 | 无 profile 时只报告，不判断“合规” |
| 目标字体库存 | 可选清单对照 | 可选清单对照 | 未提供清单时必须标为 `not_checked` |
| 渲染门禁 | 页面 PDF/PNG | 幻灯片 PDF/PNG | 自动化不能代替人工查看缺字、溢出和回退 |

当前脚本只读，并且只分析直接可见的 run 与主题信息。样式继承、PowerPoint 母版和复杂模板可能使结果出现 `unresolved_inheritance`；它是需要复核的信号，不是自动修复许可。

## 判定与交付

- `blocker`：用户要求渲染但渲染未完成，或后续项目规则明确把某项设为阻断。
- `warn`：已知字体不符合确认 profile、目标环境缺少显式字体等，需要人工决定。
- `info`：继承字体、主题或母版未能静态确定，需要模板或渲染复核。
- `pass`：没有发现当前规则可证明的问题；不等于“所有设备、所有 Office 版本均无风险”。

正文审写、事实保持和泄漏预检仍需照常执行。Office QA 只在 `verification_report` 或单独 QA 报告中陈述结果，绝不把检查过程、命令、路径或工具说明混入 `deliverable_body`。

## 修复的后续边界

本版本不提供自动修复。未来若增加修复流程，必须同时满足：用户明确授权、使用已确认的 profile、输出到新文件、保留原件、记录映射、重新运行结构审计并完成逐页渲染复核。缺少字体、未知模板或字符已损坏时，只报告风险和所需输入，不猜测替换方案。
