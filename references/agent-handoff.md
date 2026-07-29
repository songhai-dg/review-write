# 智能体交接协议

ReviewWrite 不是只能被用户手动点名的末端工具，但也不应拦截所有对话。宿主先用风险路由选择接入级别，再把 ReviewWrite 作为生成前后的质量控制层。

## 可执行风险路由

宿主可在本地、只读地运行：

```bash
python3 scripts/reviewwrite_route.py --task-type rewrite --genre research-report --format json
```

路由返回三档结果：高风险 `required`（正式体裁、证据/保留约束或十万字及以上长文）、中风险 `suggested`（普通正文生成、改写、翻译或总结）和低风险 `not-needed`（事实问答、概念解释、命令、格式操作）。用户明确跳过时返回 `skipped_by_user`，宿主不得声称已经审写。只要实际接入，终检就是必需项，失败最多定向回改两轮。

## 触发边界

### 高风险：必须接入

- 输入包含论文、基金、政策、报告、公文、公众号、营销、备忘录或双语专业文本；
- 输入达到长文阈值，或需要章节、数字和术语一致性检查；
- 任务要求保留数字、引用、术语、限定条件、作者声音或责任边界；

### 中风险：建议接入

- 用户要求写作、改写、润色、总结成稿、翻译、扩写、压缩或发布文案；
- 用户要求“去 AI 味”“自然一点”但仍然需要正式交付。
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
4. `Extract`：从结构化响应中抽取唯一的 `deliverable_body`；只要正文，不向用户展示内部交接信息。
5. `Final gate`：对抽取后的正文运行严格预检，并复核数字、引用、专名、限定条件、义务和主张强度。
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

## 版本与会话刷新

宿主安装或发现 Skill 后，应读取其 front matter 的 `version`，在会话开始时确认当前版本与目标安装源一致。升级后刷新 Skill 发现缓存或新建会话；不要在活跃写作任务中途替换规则。
