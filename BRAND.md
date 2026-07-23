# 审写 · ReviewWrite Brand

开发机构：中财数碳（北京）科技有限公司与中央财经大学人工智能与数字财经研究中心（CUFE/AIDF）。

## Positioning

审写 · ReviewWrite 不是 humanizer，也不是 AI detector。它是面向 AI Agent 的专业写作质量控制层：先审后写，保护事实，隔离过程，按体裁交付。

名称分层：产品名为“审写 · ReviewWrite”，唯一技术 Skill ID 为 `reviewwrite`，自然语言简称为“审写”和“ReviewWrite”。简称不作为第二份可安装 Skill，不制造跨平台不一致的 slash alias。

核心品牌句：

> 先审后写，不改坏事实，不泄漏过程。

英文短句：

> Review before rewrite. Keep the facts. Lose the slop.

类别名称可统一使用 `evidence-preserving review-and-rewrite skill`，中文为“证据保持型审写一体 Skill”。GitHub 标题、README、演示和发布说明都重复同一类别，不围绕“过检测”传播。

## Why users remember it

1. 一个动作：Review → Write，而不是两个互相割裂的提示词；
2. 一个硬门：提示词、推理、工具和编辑过程不得进入正文；
3. 一个承诺：事实、引用、数字、术语和限定条件可核对；
4. 一套体裁：论文、基金、公众号、政策、公文、报告和多语言写作；
5. 多个平台：Codex、Claude、Hermes、Gemini、Copilot、OpenClaw、WorkBuddy 使用同一能力核心。

## Open-source moat

开源无法阻止复制代码，真正的护城河应放在持续积累上：

- 官方名称、域名、视觉识别和签名发行通道；
- 有来源、有许可、有反例的中英文评测集；
- 可扩展的语言包、locale-aware few-shot 和本语种专业 review 网络；
- 各体裁真实误报、漏报和事实漂移回归库；
- 用户授权的本地作者声音画像，不上传私人原文；
- 上游能力 registry、差异追踪和跨平台兼容测试；
- 可验证的发布节奏、维护者响应和社区信任。

MIT 便于传播，也允许他人复制和商用。现阶段不要悄悄更换许可；可在正式发布前单独决定是否继续 MIT，并为 ReviewWrite 名称和标识建立商标使用规则。代码许可与品牌授权应分开。

## Growth loop

第一阶段用可验证结果吸引用户：发布 20 组中英文 before/after、一次泄漏基准和五个体裁对比。不发布笼统的“更像人”分数。

第二阶段进入分发渠道：GitHub topics、skills.sh/相关 skill 市场、WorkBuddy SkillHub、OpenClaw 生态目录，以及 Codex、Claude、Hermes、Gemini、Copilot 的安装文档。每个平台只维护适配说明，核心内容保持一份。

第三阶段建立共同维护：按体裁招募 reviewer，公开每周回归报告，给高质量样例贡献者署名。公众号内容围绕“真实失败案例—诊断—改法—复核”，自然导向仓库。

## Content cadence

- 每日：只展示一个具体问题或 edge 改进，不刷空版本；
- 每周：发布稳定版、回归数据和一个完整案例；
- 每月：发布跨体裁基准、路线图复盘和贡献者名单；
- 重要安全问题：即时公告和 patch。

Star 是传播结果，不是产品目标。真正驱动 star 的是可复制演示、可信 benchmark、跨平台一键安装和持续回应 issue。
