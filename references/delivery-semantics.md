# 交付语义控制

ReviewWrite 1.0 将“是否命中一个词”和“这句话是否适合交付”分开处理。确定性预检负责稳定可定位的结构信号；语义复核负责判断标题、句子和段落是否真正向读者提供信息。

## 五项必审

1. `title_structure_reader_facing`：标题是否直接标明对象、事件、问题或结论范围，结构是否使用真实层级，而不是输出编辑判断、装饰横线或连续短横杠标签。
2. `instruction_process_separated`：正文是否已经移除任务服从、提示词、候选比较、写作步骤、评审意见和模型工作流。
3. `self_certification_removed`：事实之后是否又用“充分证明、无疑、显然、完全正确”等话语给文本自身背书，却没有新增依据。
4. `claims_evidence_bounded`：结论是否保留适用范围、推论条件和证据强度，没有从局部事实直接跳到成功、正确或必然判断。
5. `facts_qualifiers_preserved`：数字、引用、专名、术语、义务、否定、概率和限定条件是否与源材料一致。

五项复核记录必须与最终正文的 SHA-256 绑定。正文任何字符变化后，旧记录失效，必须重新复核。确定性预检通过但缺少有效复核记录时，最终门禁仍然阻断。

## 判断原则

- 不禁止“真正、完全、显著、不是……而是……”等词本身；检查它们是否承担了不可替代的定义、比较、统计或规范功能。
- 删除一句话后，如果事实、条件、结论和行动信息都没有损失，这句话很可能只是组织话术、自证或内部推理旁白。
- 标题按其读者功能判断，不只检查句号。Markdown、Setext 和明确位于文首的短标题都进入标题复核。
- 正式正文默认使用连续段落和真实标题层级；装饰横线、连续短横杠碎片和粗体标签堆叠应合并。法规条款、操作步骤、参数清单等有明确功能的列表保留。
- “未命中规则”不等于“语义通过”；“语义复核已通过”也不能替代确定性门禁。

## 可执行流程

```bash
python3 scripts/reviewwrite_semantic.py init response.txt --output semantic-review.json
# 宿主或审阅者逐项复核，将 pending 改为 passed；不适用项必须写明理由。
python3 scripts/reviewwrite_semantic.py check response.txt semantic-review.json
python3 scripts/reviewwrite_gate.py response.txt --semantic-review semantic-review.json
```

复核记录属于内部交付控制信息，不得混入正式正文。
