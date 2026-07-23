# 字体 Profile 规范

字体不是一个跨单位、跨系统的通用常量。论文、基金本子、公文、企业汇报和国际材料可能有不同模板；Windows、macOS、Linux 的可用字体与替代规则也不同。因此 ReviewWrite 不内置“中文固定某字体、英文固定某字体”的默认修复规则。

## 优先级

1. 用户提供且确认有效的 DOCX/PPTX 模板；
2. 项目中经确认的 `font-profile.json`；
3. 无 profile 时的审计报告和人工确认。

profile 只声明允许字体，并不安装字体、嵌入字体或修改文件。字体授权、嵌入权和目标环境的安装由文件所有者确认。

## 最小 JSON 格式

```json
{
  "name": "example-bilingual-template",
  "fonts": {
    "eastAsia": ["已确认的中文正文字体"],
    "latin": ["Confirmed Latin Body Font"],
    "complex": ["Confirmed Complex Script Font"]
  },
  "docx": {
    "fonts": {
      "eastAsia": ["已确认的中文正文字体"]
    }
  },
  "pptx": {
    "fonts": {
      "eastAsia": ["已确认的演示中文字体"]
    }
  }
}
```

- `fonts` 是共同默认值；`docx.fonts` 与 `pptx.fonts` 可按文件类型覆盖。
- 值可以是一个字符串或多个允许值的数组。
- `eastAsia` 用于中日韩文字，`latin` 用于英文/拉丁文字，`complex` 用于复杂文字脚本。
- 请从实际模板抽取或由单位确认，不要把示例中的占位字体当作推荐字体。

## 目标字体库存

如果需要判断收件人环境是否缺字体，提供受控环境导出的清单：JSON 数组或一行一个字体名称的 UTF-8 文本。它只用于比对显式使用的字体；没有库存清单时报告必须显示 `availability_inventory: not_checked`。

不要把本机字体清单误当成所有收件人设备的证明，也不要为了消除警告而捏造、下载或嵌入字体。
