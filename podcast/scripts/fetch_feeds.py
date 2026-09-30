#!/usr/bin/env python3
"""生成 RSS 订阅数据：feeds.js（台标 + 写死的订阅地址）+ feeds-cache.js（节目单快照）。

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

# 19 档中文播客，全部为官方/权威 feed，已于 2026-09-30 逐个验证：
# https 直达、enclosure 音频可播。group: commute=陪伴通勤，talk=访谈。
# 直连情况分三类：wavpub/喜马拉雅/storyfm 自带 CORS 可页面直连；
# 小宇宙(xyzfm)与 fireside 无 CORS，页面运行时走公共代理，失败则用快照。
FEEDS = [
    # ---- 陪伴通勤 ----
    {"id": "blt", "group": "commute", "title": "半拿铁｜商业沉浮录", "rss": "https://proxy.wavpub.com/caffebreve.xml",
     "note": "把商业史讲成故事"},
    {"id": "hzyy", "group": "commute", "title": "忽左忽右", "rss": "https://feed.xyzfm.space/cv4bkgpuglwp",
     "note": "JustPod 出品的沙龙访谈"},
    {"id": "rtgy", "group": "commute", "title": "日谈公园", "rss": "https://www.ximalaya.com/album/5574153.xml",
     "note": "社会人文闲聊，十年老节目"},
    {"id": "zxh", "group": "commute", "title": "知行小酒馆", "rss": "https://feed.xyzfm.space/j8yp8gxkmgqr",
     "note": "有知有行：人生、职业与财富"},
    {"id": "whyx", "group": "commute", "title": "文化有限", "rss": "https://s1.proxy.wavpub.com/weknownothing.xml",
     "note": "聊书、电影与文化"},
    {"id": "dqxd", "group": "commute", "title": "东腔西调", "rss": "https://www.ximalaya.com/album/41153937.xml",
     "note": "历史、国际与人文漫谈"},
    {"id": "gsfm", "group": "commute", "title": "故事FM", "rss": "https://storyfm.cn/feed/episodes",
     "note": "采访一百个人的一千零一个故事"},
    {"id": "swh", "group": "commute", "title": "三五环", "rss": "https://proxy.wavpub.com/35huan.xml",
     "note": "和互联网从业者的对话"},
    {"id": "btts", "group": "commute", "title": "不把天聊si", "rss": "https://www.ximalaya.com/album/51103902.xml",
     "note": "年轻人的生活、关系与职场"},
    {"id": "zkjj", "group": "commute", "title": "展开讲讲", "rss": "https://www.ximalaya.com/album/24672021.xml",
     "note": "影视文化与人物长谈"},
    # ---- 访谈 ----
    {"id": "sjbd", "group": "talk", "title": "随机波动", "rss": "https://feeds.fireside.fm/stovol/rss",
     "note": "三位媒体人的泛文化对谈"},
    {"id": "bhsy", "group": "talk", "title": "不合时宜", "rss": "https://feed.xyzfm.space/ww7cqnybekty",
     "note": "跨文化视野的谈话类播客"},
    {"id": "yzhs", "group": "talk", "title": "岩中花述", "rss": "https://feed.xyzfm.space/hwen8wf69c6g",
     "note": "鲁豫对话女性的长访谈（官方）"},
    {"id": "ydj", "group": "talk", "title": "游荡集", "rss": "https://feed.xyzfm.space/6m6qmdfmaf6d",
     "note": "许知远的官方音频播客"},
    {"id": "dywx", "group": "talk", "title": "得意忘形", "rss": "https://feed.xyzfm.space/klaak6nmc3ux",
     "note": "科技的认真对谈与漫谈"},
    {"id": "wrxz", "group": "talk", "title": "无人知晓", "rss": "https://feed.xyzfm.space/ypn9dydpbxpc",
     "note": "孟岩：人物经历与人生选择"},
    {"id": "syf", "group": "talk", "title": "沈奕斐的播客", "rss": "https://feed.xyzfm.space/99b3wkblwf9c",
     "note": "关系、婚姻与社会观察"},
    {"id": "sdjx", "group": "talk", "title": "声东击西", "rss": "https://feeds.fireside.fm/shengdongjixi/rss",
     "note": "国际视野的科技与社会访谈"},
    {"id": "dygcj", "group": "talk", "title": "东亚观察局", "rss": "https://feed.xyzfm.space/eye-on-east-asia",
     "note": "中日韩社会、文化与历史"},
    {"id": "bwl", "group": "talk", "title": "贝望录", "rss": "https://www.ximalaya.com/album/42715423.xml",
     "note": "商业、人物与企业观察"},
    {"id": "qjkt", "group": "talk", "title": "钱婧老师的会客厅", "rss": "https://feed.xyzfm.space/9lgcqvwrheuj",
     "note": "人物、职场与女性生活"},
    {"id": "zxjy", "group": "talk", "title": "张小珺商业访谈录", "rss": "https://feed.xyzfm.space/dk4yh3pkpjp3",
     "note": "企业家与商业人物长访谈"},
    # ---- 经典访谈存档（民间上传的电视节目音频，Spotify Anchor 托管）----
    {"id": "qqq", "group": "classic", "title": "锵锵三人行 06–17", "rss": "https://anchor.fm/s/22ab0ed8/podcast/rss",
     "note": "窦文涛全档案 3000+ 期"},
    {"id": "qqq2", "group": "classic", "title": "锵锵三人行 98–10", "rss": "https://anchor.fm/s/8488a278/podcast/rss",
     "note": "早期节目 397 期"},
    {"id": "yztp", "group": "classic", "title": "圆桌派（存档）", "rss": "https://anchor.fm/s/10bfbcf64/podcast/rss",
     "note": "窦文涛圆桌谈话 185 期"},
]

SHOW = {"title": "旅途随声听", "subtitle": "中文播客 · 边走边听"}

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
        "/* 由 scripts/fetch_feeds.py 生成：节目台标 + 写死的 RSS 订阅地址。 */\n"
        "window.PODCAST_SHOW = " + json.dumps(SHOW, ensure_ascii=False, indent=2) + ";\n"
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
