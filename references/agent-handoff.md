# 智能体交接协议

ReviewWrite 不是只能被用户手动点名的末端工具，但也不应拦截所有对话。宿主先用风险路由选择接入级别，再把 ReviewWrite 作为生成前后的质量控制层。

## 可执行风险路由

宿主可在本地、只读地运行：

```bash
python3 scripts/reviewwrite_route.py --task-type rewrite --genre research-report --format json
python3 scripts/reviewwrite_route.py --task-type translate --language bilingual --format json
python3 scripts/reviewwrite_route.py --task-type office-audit --format json
```

路由返回三档结果：高风险 `required`（正式体裁、双语专业文本、证据/保留约束、Office 审计或十万字及以上长文）、中风险 `suggested`（普通正文生成、改写、翻译或总结）和低风险 `not-needed`（事实问答、概念解释、命令、格式操作）。用户明确跳过时返回 `skipped_by_user`，宿主不得声称已经审写。路由只给出决策，不等于已经运行 ReviewWrite；只要实际接入，终检就是必需项，失败最多定向回改两轮。

## 触发边界

### 高风险：必须接入

- 输入包含论文、基金、政策、报告、公文、公众号、营销、备忘录或双语专业文本；
- 输入达到长文阈值，或需要章节、数字和术语一致性检查；
- 任务要求保留数字、引用、术语、限定条件、作者声音或责任边界；

### 中风险：建议接入

- 用户要求写作、改写、润色、总结成稿、翻译、扩写、压缩或发布文案；
- 用户要求“去 AI 味”“自然一点”但仍然需要正式交付。

### 不必自动接入

- 用户只问一个事实、概念、命令或普通聊天问题，没有要交付的正式正文；
- 用户明确要求只做格式转换、文件搬运或只读技术检查，且不涉及正文表达；
- ReviewWrite 已在同一轮任务中完成最终门禁，宿主不得重复套用并制造第二份正文。

用户明确要求跳过审写时，可以尊重该选择，但宿主不得声称文本已经过 ReviewWrite 审核；模型仍须遵守事实、隐私和安全边界。

## 交接对象

宿主在调用 ReviewWrite 时，应传递以下最小契约；缺失字段采用保守默认，不为了填满字段而编造信息：

```yaml
task_type: write | rewrite | translate | summarize | long_document | office_audit
language: zh-CN | en | bilingual
locale: confirmed locale or unknown
genre: confirmed genre or unknown
audience: reader or unknown
purpose: intended action or unknown
preserve: numbers, citations, terms, qualifiers, obligations, author_voice
evidence_boundary: supplied facts only unless external verification is authorized
output_mode: deliverable_only | review_and_rewrite | review_only
review_stage: preflight | final_gate
```

这份契约是宿主与 Skill 之间的控制信息，不得原样写进 `deliverable_body`。

## 推荐闭环

```text
Detect → Preflight → Draft → Extract → Final gate → Repair (max 2) → Deliver
识别任务   写前约束    生成       抽正文       严格终检       有限回改          交付
```

1. `Detect`：宿主判断是否属于写作交付任务，并选择语言、体裁和读者。
2. `Preflight`：ReviewWrite 输出 preserve、repair、evidence_boundary 和 acceptance；没有足够信息时缩小修改范围。
3. `Draft`：宿主依据契约生成文本，不能把评审报告、计划或工具过程写进正文。
4. `Extract`：从结构化响应中抽取唯一的 `deliverable_body`；只要正文，不向用户展示标签和内部交接信息。
5. `Final gate`：运行 `python3 scripts/reviewwrite_gate.py <response-path>`。它负责严格抽取与预检；通过时只输出正文，失败时不输出正文。纯正文输入必须显式添加 `--input-mode raw`。
6. `Repair`：出现 `fail` 或严格模式下的 `warn` 时，只针对触发句回改，最多两轮；不得用删掉事实或降低信息密度来换取通过。
7. `Deliver`：通过后按用户要求返回正文；用户要求评审时才返回四个 surface。

## 状态交接

宿主可以内部使用以下状态，不要求用户看到：

```json
{
  "reviewwrite": {
    "stage": "preflight|draft|final_gate|repair|passed|blocked",
    "mode": "deliverable_only|review_and_rewrite|review_only",
    "attempt": 0,
    "findings": [],
    "coverage": "full|chunked|unknown",
    "needs_human_review": false
  }
}
```

`blocked` 表示仍有硬失败、事实无法核验、结构化正文无法抽取或两轮回改后仍未通过。此时宿主应报告触发原因和待确认项，不得把未通过正文伪装成完成稿。

## 可执行交付门禁

```bash
# 结构化响应：默认且推荐
python3 scripts/reviewwrite_gate.py response.txt

# 已确认文件只包含正文时
python3 scripts/reviewwrite_gate.py body.txt --input-mode raw
```

宿主只能使用命令成功后的标准输出作为最终正文。退出码非零时，标准输出为空；诊断写入标准错误，供定向回改使用。路由 JSON、模型自评或“已审核”字样都不能替代这一步。

若正文确实讨论 AI 安全、软件接口或其他授权对象，先用 `--context` 声明；由该语境降级的警告仍默认阻断。只有宿主已经逐条确认术语确属讨论对象时，才可加 `--confirm-context-warnings`。该开关不放行普通风格警告或任何硬失败。

## 版本与会话刷新

宿主安装或发现 Skill 后，应读取其 front matter 的 `version`，在会话开始时确认当前版本与目标安装源一致。升级后刷新 Skill 发现缓存或新建会话；不要在活跃写作任务中途替换规则。
