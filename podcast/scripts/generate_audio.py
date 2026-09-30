#!/usr/bin/env python3
"""生成播客 MVP 的演示音频与字幕数据（edge-tts，音色 zh-CN-XiaoxiaoNeural）。

每集一句话稿，按句读切分成字幕 cue；时间轴来自 edge-tts 的 WordBoundary
词边界事件，所以字幕和语音天然对齐，不需要再做语音识别。

  pip install edge-tts
  python podcast/scripts/generate_audio.py --check   # 只检查文案
  python podcast/scripts/generate_audio.py           # 生成 audio/ + data.js
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-5%"

SHOW = {
    "title": "旅途随声听",
    "subtitle": "边走边听的私人电台 · 演示数据",
}

CATEGORIES = [
    {
        "id": "tech",
        "title": "科技前哨",
        "episodes": [
            {
                "id": "tech-01",
                "title": "智能手机的这十年",
                "desc": "从按键机到全面屏，回顾一代人掌上的变迁。",
                "text": (
                    "智能手机的这十年，变化比很多人想象的更彻底。十年前，我们还在为"
                    "一块更大的屏幕而兴奋，为多出的两百毫安时电池而沾沾自喜。如今，"
                    "手机早已不只是通讯工具，它是钱包、是钥匙、是相机，也是我们看世"
                    "界的窗口。屏幕从十六比九变成二十比九，边框一年比一年窄，指纹解"
                    "锁从背后挪到了屏下，摄像头从一颗变成了三颗。但真正的变化不在硬"
                    "件，而在习惯。我们不再提前下载离线地图，不再记路，也不再背电话"
                    "号码。手机替我们记住了一切，也让我们忘记了一切。下一个十年，也"
                    "许屏幕会消失，眼镜会成为新的入口。但可以肯定的是，人与信息的距"
                    "离，只会越来越近。"
                ),
            },
            {
                "id": "tech-02",
                "title": "AI 就在你身边",
                "desc": "聊聊天气预报、相册搜索和输入法里悄悄变聪明的算法。",
                "text": (
                    "很多人以为人工智能还很遥远，其实它早就藏进了日常。你早上看到的"
                    "天气预报，是模型算出来的；相册里搜一句海边，就能翻出三年前的照"
                    "片；输入法猜到你下一句想说什么，导航悄悄帮你避开了拥堵。这些都"
                    "是人工智能，只是它们安静得不像是技术。真正值得关心的，不是它什"
                    "么时候取代谁，而是我们怎么和它相处。把它当成工具，它放大你的效"
                    "率；把它当成答案，它会慢慢替你做决定。技术从来都是中性的，关键"
                    "在于握着它的那只手，还听不听自己的。"
                ),
            },
        ],
    },
    {
        "id": "travel",
        "title": "旅行漫谈",
        "episodes": [
            {
                "id": "travel-01",
                "title": "赣北七日慢游记",
                "desc": "庐山的雾、景德镇的窑火、望仙谷的夜，一次国庆出错的复盘。",
                "text": (
                    "国庆七天，我们从南昌出发，把赣北绕了一个圈。第一站庐山，山上起"
                    "雾，能见度不到十米，如琴湖只剩一个轮廓，反倒有种水墨画的留白。"
                    "第三天到景德镇，陶阳里的老窑还留着松柴的味道，老师傅说，一窑瓷"
                    "器，成与不成，七分靠人，三分靠天。最后两天在望仙谷，白天的峡谷"
                    "人声鼎沸，到了夜里，灯笼一盏一盏亮起来，整条山谷安静得只剩下水"
                    "声。回头看，这次旅程最大的收获不是打卡了几个景点，而是学会了在"
                    "人潮里放慢速度。旅行和过日子一样，急着赶路的人，反而什么都看不"
                    "见。"
                ),
            },
            {
                "id": "travel-02",
                "title": "带耳朵去旅行",
                "desc": "为什么声音比照片更容易把人带回现场。",
                "text": (
                    "照片负责记录样子，声音负责记录气氛。多年以后，你可能记不清某次"
                    "旅行的画面，但一定记得海浪的节奏、夜市里锅铲敲铁板的声音，还有"
                    "山间缆车咯吱咯吱的响动。声音有个奇怪的属性，它不需要你刻意去"
                    "听，却会在多年后的某个瞬间突然把你拽回现场。所以现在出门，我除"
                    "了拍照，还会录几段环境音。一段十秒的雨声，比一百张照片更能唤醒"
                    "一段记忆。下次旅行，不妨也试试，闭上眼睛听一分钟，你会在声音里"
                    "看见另一座城。"
                ),
            },
        ],
    },
    {
        "id": "reading",
        "title": "深夜读书",
        "episodes": [
            {
                "id": "reading-01",
                "title": "慢阅读的乐趣",
                "desc": "在信息流时代，重新找回一页一页读完一本书的耐心。",
                "text": (
                    "我们现在的阅读，大多是滑出来的，而不是读进去的。信息流把每一篇"
                    "文章都切成了一百五十字的碎片，我们以为自己在阅读，其实只是在扫"
                    "视。慢阅读不是慢，而是完整。一本真正的好书，值得你关掉通知，泡"
                    "一杯茶，从第一页读到最后一页，让作者的思维在你脑子里完整地走一"
                    "遍。你会发现，读完一本书的满足感，和刷一百条短消息完全不同。前"
                    "者像吃了一顿饭，后者只是不停地嚼口香糖。今晚试试看，给自己三十"
                    "分钟，不滑手机，只翻书。"
                ),
            },
            {
                "id": "reading-02",
                "title": "重读瓦尔登湖",
                "desc": "一百多年前湖边的小木屋，如何回答今天的焦虑。",
                "text": (
                    "梭罗在瓦尔登湖边住了两年零两个月，他自己说，是想活得从容一点，"
                    "只面对生命里最基本的事实。一百多年过去，这句话忽然变得很应景。"
                    "我们焦虑，往往不是因为拥有得太少，而是因为想要得太多。梭罗记录"
                    "了他盖木屋的全部开销，二十八美元一角二分五厘，然后得出结论，一"
                    "年的生计，只需要工作六个星期。这不是鼓励大家逃离城市，而是提醒"
                    "我们，生活的成本里，有一部分是我们自己加上去的。减少一件不必"
                    "要的欲望，比多赚一笔钱，更能让人自由。"
                ),
            },
        ],
    },
]

SENTENCE_END = "。！？；…"
STRIP_RE = re.compile(r"[^\w\u4e00-\u9fff]+")


def sentences(text: str) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    for ch in text:
        buf.append(ch)
        if ch in SENTENCE_END:
            out.append("".join(buf).strip())
            buf = []
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return out


async def synth_with_cues(text: str, dest: Path) -> list[dict]:
    """合成一集 mp3，同时用词边界事件切出句子级字幕 cue。"""
    import edge_tts

    parts = sentences(text)
    targets = [len(STRIP_RE.sub("", s)) for s in parts]

    last: Exception | None = None
    for attempt in range(4):
        audio = bytearray()
        words: list[tuple[float, float, str]] = []
        try:
            comm = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    audio.extend(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    words.append(
                        (
                            chunk["offset"] / 1e7,
                            chunk["duration"] / 1e7,
                            chunk["text"],
                        )
                    )
            if len(audio) < 2000:
                raise RuntimeError(f"音频过小 ({len(audio)} bytes)")
            if not words:
                raise RuntimeError("没有收到词边界事件")
            dest.write_bytes(bytes(audio))

            cues: list[dict] = []
            wi = 0
            for i, seg in enumerate(parts):
                first_word = wi
                counted = 0
                while wi < len(words) and counted < targets[i]:
                    counted += len(STRIP_RE.sub("", words[wi][2])) or 1
                    wi += 1
                start = words[first_word][0]
                end = words[wi - 1][0] + words[wi - 1][1]
                if cues and start < cues[-1]["e"]:
                    start = cues[-1]["e"]
                cues.append({"s": round(start, 2), "e": round(max(end, start + 0.3), 2), "t": seg})
            if wi != len(words):
                raise RuntimeError(f"词边界没有对齐稿子: 用了 {wi}/{len(words)}")
            return cues
        except Exception as exc:  # noqa: BLE001 — 重试瞬时 TTS 错误
            last = exc
            await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{dest.name}: {last}")


async def generate() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(3)
    data = {"show": SHOW, "categories": []}

    async def one(ep: dict) -> None:
        dest = AUDIO / f"{ep['id']}.mp3"
        cues = await synth_with_cues(ep["text"], dest)
        ep2 = {k: v for k, v in ep.items() if k != "text"}
        ep2["src"] = f"audio/{ep['id']}.mp3"
        ep2["duration"] = cues[-1]["e"]
        ep2["cues"] = cues
        return ep2

    for cat in CATEGORIES:
        tasks = [one(ep) for ep in cat["episodes"]]
        eps = await asyncio.gather(*tasks)
        data["categories"].append({"id": cat["id"], "title": cat["title"], "episodes": eps})

    (ROOT / "data.js").write_text(
        "/* 由 scripts/generate_audio.py 生成：演示节目 + 字幕时间轴。 */\n"
        "window.PODCAST_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    total = sum(p.stat().st_size for p in AUDIO.glob("*.mp3"))
    for cat in data["categories"]:
        for ep in cat["episodes"]:
            n = sum(len(c["t"]) for c in ep["cues"])
            print(f"  {ep['id']}  {len(ep['cues'])} 句 {n} 字  {ep['duration']:.1f}s")
    print(f"共 {sum(len(c['episodes']) for c in data['categories'])} 集，"
          f"{total / 1024 / 1024:.2f} MB -> {AUDIO.relative_to(ROOT)} + data.js")


def validate() -> None:
    for cat in CATEGORIES:
        for ep in cat["episodes"]:
            text = ep["text"]
            if re.search(r"\s", text):
                raise SystemExit(f"{ep['id']} 稿子含空白字符")
            if not 150 <= len(text) <= 400:
                raise SystemExit(f"{ep['id']} 字数 {len(text)}，需要 150–400")
            ss = sentences(text)
            if not all(6 <= len(s) <= 60 for s in ss):
                raise SystemExit(f"{ep['id']} 有过长/过短的句子弹幕: {ss}")


def main() -> None:
    argp = argparse.ArgumentParser(description="生成播客演示音频 + 字幕数据（edge-tts）")
    argp.add_argument("--check", action="store_true", help="只检查文案，不请求语音")
    args = argp.parse_args()
    validate()
    n_eps = sum(len(c["episodes"]) for c in CATEGORIES)
    print(f"{len(CATEGORIES)} 个分类 {n_eps} 集，音色 {VOICE}，语速 {RATE}")
    if args.check:
        return
    asyncio.run(generate())


if __name__ == "__main__":
    main()
