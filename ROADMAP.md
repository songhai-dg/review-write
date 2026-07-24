# Roadmap

## 0.1.1 Cross-platform foundation

- 已建立 Codex、Claude Code、Hermes Agent、Gemini CLI、GitHub Copilot、OpenClaw 和 WorkBuddy 单核心适配；
- 已建立安全更新检查、确定性打包、CI 和签名发行基础；
- 已建立 daily edge 与 weekly stable 的自动任务契约。

## 0.2 Capability registry

- 将上游能力统一成可机器读取的 registry；
- 为规则增加体裁、语言、例外和验证字段；
- 将 AI 写作痕迹和 humanizer 类能力拆成“写前约束、写后复核、体裁例外、事实保持回归”四类，不把竞品词表直接升级为核心门禁；
- 增加上游版本差异检查，不直接覆盖本地适配。
- 选择一种新语言试行 language pack、locale-aware few-shot 与母语专业 review 门禁；
- 不把未通过跨体裁回归的语言提升为 core。

## 0.3 Office QA

- 提供 DOCX/PPTX 的只读字体、主题、脚本字体与目标环境库存审计；
- 默认 `audit-only`，以模板或确认的 font profile 为准，不静默替换字体、不覆盖原件；
- 增加渲染门禁：结构通过不等于视觉通过，必须逐页检查缺字、字体回退、截断、溢出和异常换行；
- 使用最小 OOXML 测试样本覆盖中英文、主题解析、profile 不匹配、字体库存和渲染不可用边界；
- 后续修复功能必须另存新文件、明确授权、记录映射并重新审计与渲染。

## 0.4 Author voice

- 提供作者授权语料的本地导入和匿名化流程；
- 从句长、术语、段落功能和立场表达中提取稳定偏好；
- 不提取敏感人格特征，不跨用户共享样例；
- 用留出文本验证“保持声音”而不是制造随机瑕疵。

## 0.5 Evaluation

- 建立论文、基金、公众号、政策和公文的中英文测试集；
- 评估泄漏召回率、误报率、事实保持、引用保持、体裁适配和作者偏好；
- 加入改写前后语义差异和受保护片段检查；
- 与 Stop Slop、Humanizer-zh、单轮通用提示等基线比较。

## 0.6 Integrations

- 扩展更多 Agent Skills 市场和原生更新渠道；
- 提供可选的模型适配器，但保持本地 lint 和数据格式独立；
- 支持 Markdown、DOCX、LaTeX 和 HTML 的正文边界检查；
- 增加 CI 发布和可复现 `.skill` 构建。

所有路线都以真实回归样例为准。没有测出改进的规则不进入默认工作流。
