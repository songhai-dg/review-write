#!/usr/bin/env python3
"""Generate a deterministic, platform-neutral promotion kit for a release."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path
from typing import Sequence

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
    short = "审写 · ReviewWrite：面向论文、基金、政策、报告、公文、公众号和中英文专业写作，先审后写，保护事实、数字、引用、术语与限定条件，交付可直接使用的正文。"
    long = (
        "中央财经大学人工智能与数字财经研究中心（CUFE/AIDF）与中财数碳联合开发的审写 · ReviewWrite，"
        "把专业写作中的评审、改写和复核放进同一条工作流。它根据体裁、读者和证据动态判断修改幅度，"
        "区分评审说明与正式正文，重点防止提示词、推理、工具调用、编辑残留和空泛套话混入交付文本。"
        "它不承诺规避检测，也不通过制造错误来模仿所谓人味。"
    )
    posts = {
        "github-release.md": f"# 审写 · ReviewWrite v{version}\n\n{long}\n\n- 官方仓库：{link['github']}\n- 国内镜像：{link['gitee']}\n- 案例：{link['examples']}\n- SkillHub：{link['skillhub']}\n",
        "skillhub-update.md": f"## 版本更新 v{version}\n\n{short}\n\n更新说明：补充快速开始、输入处理、常见问题和平台安装回退说明；核心原则仍是先审后写、保护事实、正文与说明分离。\n\n项目地址：{link['github']}\n国内镜像：{link['gitee']}\n",
        "agent-directory.md": f"## 审写 · ReviewWrite\n\n{short}\n\n安装来源：{link['github']}\nGitHub 不可访问时：{link['gitee']}\n示例：{link['examples']}\n",
        "wechat-and-video.md": f"# 对外宣传文案\n\n{long}\n\n适合需要处理论文、基金、政策材料、研究报告和公众号文章的人：先把问题看清，再动文字；该保留的数字、引用和限定条件不被改写带走。\n\n了解与安装：{link['github']}\n国内镜像：{link['gitee']}\nSkillHub：{link['skillhub']}\n",
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
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    paths.append(manifest_path)
    for name, content in posts.items():
        path = output / name
        path.write_text(content)
        paths.append(path)
    return paths


def main(argv: Sequence[str] | None = None) -> int:
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
