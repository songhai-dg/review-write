#!/usr/bin/env python3
"""Generate a deterministic, platform-neutral promotion kit for a release."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path
from typing import Sequence

from runtime_io import configure_utf8_stdio

ROOT = Path(__file__).resolve().parents[1]
REPO = "songhai-dg/review-write"
MIRROR = "https://gitee.com/cufe01/songhai-dg"
SKILLHUB = "https://skillhub.cn/team-skills/zcst-review-write"


def current_version() -> str:
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    import bump_version

    return str(bump_version.synchronized_current())


def urls(version: str) -> dict[str, str]:
    return {
        "github": f"https://github.com/{REPO}",
        "release": f"https://github.com/{REPO}/releases/tag/v{version}",
        "gitee": MIRROR,
        "skillhub": SKILLHUB,
        "examples": f"https://github.com/{REPO}/tree/main/examples/simulation",
    }


def files(version: str, output: Path) -> list[Path]:
    link = urls(version)
    install = (
        f"请从官方仓库 {link['github']} 安装 ReviewWrite Skill；"
        f"如当前网络无法访问 GitHub，使用同步镜像 {link['gitee']}。"
        "如果当前智能体已经安装，不要重复安装，也不要搜索或替换成名称相近的其他技能。"
        "请使用所在平台自己的 Skill 安装或导入机制；如果仓库已在当前目录，直接以当前目录为安装来源。"
        "平台不支持、没有权限或无法访问来源时，说明限制并停止。"
    )
    short = "审写 · ReviewWrite 1.1：面向 GPT、Gemini、Claude、Grok、DeepSeek 与 Qwen 初稿的双层交付门禁；新增互联网黑话解构、推理标签与独白阻断、网感钩子清理及去同质化复核，在零事实漂移下消除机器模板感。"
    long = (
        "中央财经大学人工智能与数字财经研究中心（CUFE/AIDF）与中财数碳联合开发的审写 · ReviewWrite，"
        "把专业写作中的评审、改写和复核放进同一条工作流。无论初稿来自 GPT、Gemini、Claude、Grok、DeepSeek 还是通义 Qwen，"
        "它都根据体裁、读者和证据动态判断修改幅度，区分评审说明与正式正文，重点防止提示词、推理标签、思考独白、内部操作和空泛套话混入交付文本。"
        "1.1 版本新增跨模型写作特征校准、互联网黑话解构（对齐颗粒度、以……为抓手、跑通商业闭环、泛化 load-bearing 等）、"
        "网感钩子与伪坦诚垫词清理（说白了、不整虚的、Here's the kicker、No fluff 等），以及相邻递进连接词链和句尾拔高伴随语去同质化检查，"
        "同时自动保护代码块、YAML 头与闭环控制、模型对齐、时间颗粒度等真实专业术语。"
        "核心边界始终明确：不拿幻觉换人味，不凭模型记忆塞入原文未提供的外部事实，也不靠打乱语序或乱换同义词搞‘暴力降重’；无法确认时保留限定、指出待核实项或降低主张强度。"
        "面对十万字及更长文本，它按章节和段落分块，保留全文行号与块号，建立数字、标题和术语一致性索引（长文回归覆盖 324,015 字符、55 个分块并精确定位至第 9,001 行）。"
        "同时提供只读 DOCX/PPTX 字体渲染审计与 C2PA/JUMBF、SynthID 及 Unicode 控制字符来源完整性审计；不删除水印，不伪装来源。"
        "最终交付执行‘确定性规则 + 正文 SHA-256 绑定五项语义复核’双层门禁：规则没命中不等于能交付，正文改一个字符都必须重新复核。"
    )
    posts = {
        "github-release.md": f"# 审写 · ReviewWrite v{version}\n\n{long}\n\n- 官方仓库：{link['github']}\n- 国内镜像：{link['gitee']}\n- 案例：{link['examples']}\n- SkillHub：{link['skillhub']}\n",
        "skillhub-update.md": f"## 版本更新 v{version}\n\n{short}\n\n更新说明：新增 GPT/Gemini/Claude/Grok/DeepSeek/Qwen 跨模型写作校准；新增 `<think>` 等推理标签与思考独白阻断、互联网黑话搭配与段落堆叠识别、网感钩子清理、递进连接词与拔高尾句去同质化规则（`RW-W-230—RW-W-234`）；新增代码块/YAML 头防误报、Setext 二级标题区分与 DOCX/PPTX 来源审计增强。\n\n项目地址：{link['github']}\n国内镜像：{link['gitee']}\n",
        "agent-directory.md": f"## 审写 · ReviewWrite\n\n{short}\n\n安装来源：{link['github']}\nGitHub 不可访问时：{link['gitee']}\n示例：{link['examples']}\n",
        "wechat-and-video.md": f"# 对外宣传文案\n\n{long}\n\n用 GPT、Gemini、Claude、Grok 或 DeepSeek 写初稿很容易，但交稿时最怕混进 `<think>` 独白、满篇‘抓手/颗粒度/闭环’黑话、网感口头禅或每段一个模子的‘此外/与此同时/不仅如此’。ReviewWrite 1.1 不搞改乱术语的暴力降重，也不编造细节换人味，而是用跨模型校准与正文哈希绑定的双层门禁，把机器套话还原成经得起逐字核对的专业正文。\n\n了解与安装：{link['github']}\n国内镜像：{link['gitee']}\nSkillHub：{link['skillhub']}\n",
        "install-prompt.txt": install + "\n",
    }
    manifest = {
        "schema_version": 1,
        "product": "ReviewWrite",
        "skill_id": "reviewwrite",
        "version": version,
        "publisher": "中央财经大学人工智能与数字财经研究中心（CUFE/AIDF）与中财数碳",
        "canonical_source": link["github"],
        "mirror_source": link["gitee"],
        "directory_listing": {"skillhub": link["skillhub"]},
        "release": link["release"],
        "examples": link["examples"],
        "publishing_policy": "third-party listings receive generated copy only; runtime content remains canonical",
    }
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    manifest_path = output / "distribution-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    paths.append(manifest_path)
    for name, content in posts.items():
        path = output / name
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="生成 ReviewWrite 对外分发素材包")
    parser.add_argument("--version", default=current_version())
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "distribution-kit")
    parser.add_argument("--zip", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.output.exists():
        shutil.rmtree(args.output)
    generated = files(args.version, args.output)
    archive = args.zip or args.output.parent / f"distribution-kit-{args.version}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in generated:
            bundle.write(path, path.relative_to(args.output).as_posix())
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
