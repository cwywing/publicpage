#!/usr/bin/env python3
"""生成 RSS 订阅数据：feeds.js（写死的订阅地址）+ feeds-cache.js（节目单快照）。

订阅列表在本文件 FEEDS 里维护（单一来源）。运行时会先尝试直连/代理拉取
最新节目单，失败时退回本快照，保证离线也能看到列表。

  python podcast/scripts/fetch_feeds.py
"""

from __future__ import annotations

import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 访谈类中文播客，全部为官方/权威 feed，已验证 https 直达、enclosure 可播。
# 2026-09-30 验证：storyfm/wavpub 自带 CORS 头可页面直连；xyzfm 无 CORS 头，
# 页面运行时走公共代理，失败则用快照。
FEEDS = [
    {"id": "gsfm", "title": "故事FM", "rss": "https://storyfm.cn/feed/episodes",
     "note": "采访一百个人的一千零一个故事"},
    {"id": "hzyy", "title": "忽左忽右", "rss": "https://feed.xyzfm.space/cv4bkgpuglwp",
     "note": "JustPod 出品的沙龙访谈"},
    {"id": "bhsy", "title": "不合时宜", "rss": "https://feed.xyzfm.space/ww7cqnybekty",
     "note": "跨文化视野的谈话类播客"},
    {"id": "dywx", "title": "得意忘形", "rss": "https://feed.xyzfm.space/klaak6nmc3ux",
     "note": "科技的认真对谈与漫谈"},
    {"id": "swh", "title": "三五环", "rss": "https://proxy.wavpub.com/35huan.xml",
     "note": "和互联网从业者的对话"},
]

MAX_EPISODES = 20
ITUNES_NS = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"


def parse_duration(text: str | None) -> int:
    """itunes:duration 可能是 秒 / MM:SS / HH:MM:SS。"""
    if not text:
        return 0
    parts = text.strip().split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return 0
    sec = 0
    for n in nums:
        sec = sec * 60 + n
    return sec


def fmt_date(text: str | None) -> str:
    if not text:
        return ""
    try:
        dt = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return ""
    if dt is None:
        return ""
    return f"{dt.year}-{dt.month:02d}-{dt.day:02d}"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read()


def parse_feed(xml: bytes) -> list[dict]:
    root = ET.fromstring(xml)
    eps = []
    for item in root.iterfind(".//item"):
        enc = item.find("enclosure")
        title_el = item.find("title")
        if enc is None or enc.get("url") is None or title_el is None or not (title_el.text or "").strip():
            continue
        eps.append({
            "t": title_el.text.strip(),
            "u": enc.get("url"),
            "d": parse_duration(item.findtext(f"{ITUNES_NS}duration")),
            "p": fmt_date(item.findtext("pubDate")),
        })
        if len(eps) >= MAX_EPISODES:
            break
    return eps


def main() -> None:
    cache = {}
    for feed in FEEDS:
        try:
            eps = parse_feed(fetch(feed["rss"]))
            cache[feed["id"]] = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "eps": eps}
            print(f"  {feed['title']}: {len(eps)} 集")
        except Exception as exc:  # noqa: BLE001 — 单个源失败不影响其他
            print(f"  {feed['title']}: 抓取失败 {exc}")

    (ROOT / "feeds.js").write_text(
        "/* 由 scripts/fetch_feeds.py 生成：写死的 RSS 订阅地址。 */\n"
        "window.PODCAST_FEEDS = " + json.dumps(FEEDS, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    (ROOT / "feeds-cache.js").write_text(
        "/* 由 scripts/fetch_feeds.py 生成：节目单快照，运行时拉取失败时兜底。 */\n"
        "window.PODCAST_FEEDS_CACHE = " + json.dumps(cache, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    total = sum(len(v["eps"]) for v in cache.values())
    print(f"{len(cache)}/{len(FEEDS)} 个源，快照共 {total} 集 -> feeds.js + feeds-cache.js")


if __name__ == "__main__":
    main()
