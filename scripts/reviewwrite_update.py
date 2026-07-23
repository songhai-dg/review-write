#!/usr/bin/env python3
"""Check and download ReviewWrite releases without changing an installed skill.

The updater is deliberately conservative: checks are cached, downloads are
verified, and installation remains a separate platform-native or explicit step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "release-policy.json"
USER_AGENT = "ReviewWrite-Updater/0.4.0"
MAX_ASSET_BYTES = 20 * 1024 * 1024
VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "Version":
        match = VERSION_RE.fullmatch(value.strip())
        if not match:
            raise ValueError(f"无效版本号: {value}")
        return cls(*(int(part) for part in match.groups()))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def load_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def repository_from(args_repo: str | None, policy: dict[str, Any]) -> str | None:
    value = args_repo or os.environ.get("REVIEWWRITE_REPOSITORY") or policy.get("repository")
    if value is None:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise ValueError("repository 必须使用 owner/repo 格式")
    return value


def cache_root() -> Path:
    configured = os.environ.get("REVIEWWRITE_CACHE_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.home() / ".cache" / "reviewwrite"


def _request_json(url: str) -> dict[str, Any] | list[dict[str, Any]]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def _select_release(repository: str, channel: str) -> dict[str, Any]:
    if channel == "stable":
        payload = _request_json(f"https://api.github.com/repos/{repository}/releases/latest")
        if not isinstance(payload, dict):
            raise ValueError("GitHub latest release 响应无效")
        return payload

    payload = _request_json(
        f"https://api.github.com/repos/{repository}/releases?per_page=20"
    )
    if not isinstance(payload, list):
        raise ValueError("GitHub releases 响应无效")
    for release in payload:
        if not release.get("draft"):
            return release
    raise ValueError("没有可用的 edge release")


def _cache_file(repository: str, channel: str) -> Path:
    safe_repo = repository.replace("/", "--")
    return cache_root() / f"release-{safe_repo}-{channel}.json"


def release_info(
    repository: str,
    channel: str,
    max_age_hours: int,
    force: bool = False,
) -> tuple[dict[str, Any], bool]:
    path = _cache_file(repository, channel)
    if not force and path.is_file():
        age_seconds = time.time() - path.stat().st_mtime
        if age_seconds <= max_age_hours * 3600:
            return json.loads(path.read_text(encoding="utf-8")), True

    release = _select_release(repository, channel)
    compact = {
        "tag_name": release.get("tag_name"),
        "html_url": release.get("html_url"),
        "prerelease": bool(release.get("prerelease")),
        "published_at": release.get("published_at"),
        "assets": [
            {
                "name": item.get("name"),
                "browser_download_url": item.get("browser_download_url"),
                "size": item.get("size"),
            }
            for item in release.get("assets", [])
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return compact, False


def policy_allows(current: Version, latest: Version, update_policy: str) -> bool:
    if latest <= current or update_policy in {"off", "notify"}:
        return False
    if update_policy == "auto-patch":
        return latest.major == current.major and latest.minor == current.minor
    if update_policy == "auto-minor":
        return latest.major == current.major
    raise ValueError(f"未知更新策略: {update_policy}")


def _asset(release: dict[str, Any], suffix: str) -> dict[str, Any]:
    matches = [item for item in release.get("assets", []) if str(item.get("name", "")).endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"release 中需要且只能有一个 {suffix} 资产，当前 {len(matches)} 个")
    return matches[0]


def _download(url: str, destination: Path, expected_size: int | None = None) -> None:
    if expected_size is not None and expected_size > MAX_ASSET_BYTES:
        raise ValueError("下载资产超过 20 MiB 安全上限")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_ASSET_BYTES:
            raise ValueError("下载资产超过 20 MiB 安全上限")
        data = response.read(MAX_ASSET_BYTES + 1)
    if len(data) > MAX_ASSET_BYTES:
        raise ValueError("下载资产超过 20 MiB 安全上限")
    destination.write_bytes(data)


def download_verified(
    repository: str,
    release: dict[str, Any],
    require_attestation: bool,
) -> Path:
    package = _asset(release, ".skill")
    checksum = _asset(release, ".skill.sha256")
    destination_dir = cache_root() / "downloads" / str(release["tag_name"])
    destination_dir.mkdir(parents=True, exist_ok=True)
    package_path = destination_dir / str(package["name"])
    checksum_path = destination_dir / str(checksum["name"])
    package_part = package_path.with_suffix(package_path.suffix + ".part")
    checksum_part = checksum_path.with_suffix(checksum_path.suffix + ".part")
    try:
        _download(str(package["browser_download_url"]), package_part, package.get("size"))
        _download(str(checksum["browser_download_url"]), checksum_part, checksum.get("size"))
        expected = checksum_part.read_text(encoding="utf-8").split()[0].lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("SHA-256 文件格式无效")
        actual = hashlib.sha256(package_part.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("SHA-256 校验失败")

        if require_attestation:
            gh = shutil.which("gh")
            if not gh:
                raise ValueError("要求验证 GitHub attestation，但当前未安装 gh")
            subprocess.run(
                [gh, "attestation", "verify", str(package_part), "--repo", repository],
                check=True,
                capture_output=True,
                text=True,
            )
        package_part.replace(package_path)
        checksum_part.replace(checksum_path)
    except Exception:
        package_part.unlink(missing_ok=True)
        checksum_part.unlink(missing_ok=True)
        raise
    return package_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="安全检查或下载 ReviewWrite 更新")
    parser.add_argument("command", choices=("check", "download"))
    parser.add_argument("--repo", help="GitHub 仓库，格式 owner/repo")
    parser.add_argument("--channel", choices=("stable", "edge"), default="stable")
    parser.add_argument("--policy", choices=("off", "notify", "auto-patch", "auto-minor"))
    parser.add_argument("--force", action="store_true", help="忽略 24 小时缓存")
    parser.add_argument("--require-attestation", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_policy()
        repository = repository_from(args.repo, config)
        if not repository:
            payload = {
                "status": "disabled",
                "reason": "release-policy.json 尚未配置 repository",
            }
        else:
            update_config = config["update"]
            update_policy = args.policy or update_config["default_policy"]
            if update_policy == "off":
                payload = {"status": "disabled", "reason": "update policy is off"}
            else:
                release, cached = release_info(
                    repository,
                    args.channel,
                    int(update_config["check_interval_hours"]),
                    args.force,
                )
                current = Version.parse(str(config["current_version"]))
                latest = Version.parse(str(release["tag_name"]))
                payload = {
                    "status": "update-available" if latest > current else "current",
                    "current": str(current),
                    "latest": str(latest),
                    "channel": args.channel,
                    "cached": cached,
                    "release_url": release.get("html_url"),
                    "automatic_download_allowed": policy_allows(current, latest, update_policy),
                }
                if args.command == "download" and latest > current:
                    automatic_policy = update_policy.startswith("auto-")
                    if automatic_policy and not payload["automatic_download_allowed"]:
                        payload["status"] = "policy-blocked"
                        payload["reason"] = f"{update_policy} 不允许下载该版本"
                    else:
                        path = download_verified(repository, release, args.require_attestation)
                        payload["downloaded_to"] = str(path)
                        payload["status"] = "downloaded"
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(payload.get("reason") or json.dumps(payload, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, urllib.error.URLError, subprocess.CalledProcessError) as exc:
        print(f"更新检查失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
