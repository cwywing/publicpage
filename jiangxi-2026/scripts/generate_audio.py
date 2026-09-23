#!/usr/bin/env python3
"""用免费 edge-tts 重生成江西页景点解说 mp3。

不是付费 Azure Speech。音色固定 zh-CN-XiaoxiaoNeural，语速 -5%（约 0.95）。
文案以 index.html 里 p.seg-script 为准，可见文字和录音同一稿。

  pip install edge-tts
  python3 jiangxi-2026/scripts/generate_audio.py
  python3 jiangxi-2026/scripts/generate_audio.py --check
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
AUDIO = ROOT / "audio"
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-5%"
EXPECTED = {"sq": 5, "wxg": 5, "hl": 5, "jd": 6, "ls": 5}


class GuideParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.segs: list[tuple[str, str, str]] = []
        self._in_seg = False
        self._in_script = False
        self._id = ""
        self._src = ""
        self._text = ""
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        classes = a.get("class", "").split()
        if tag == "li" and "seg" in classes:
            self._in_seg = True
            self._id = a.get("id", "")
            self._src = ""
            self._text = ""
        elif tag == "audio" and self._in_seg:
            self._src = a.get("src", "")
        elif tag == "p" and "seg-script" in classes:
            self._in_script = True
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._in_script:
            self._in_script = False
            self._text = "".join(self._buf).strip()
        elif tag == "li" and self._in_seg:
            self.segs.append((self._id, self._src, self._text))
            self._in_seg = False

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._buf.append(data)


def load_segments() -> list[tuple[str, str, str]]:
    parser = GuideParser()
    parser.feed(HTML.read_text(encoding="utf-8"))
    return parser.segs


def validate(segs: list[tuple[str, str, str]]) -> None:
    if not segs:
        raise SystemExit("index.html 里没有 .seg-script")
    counts: dict[str, int] = {}
    seen: set[str] = set()
    for sid, src, text in segs:
        if not sid or sid in seen:
            raise SystemExit(f"段 id 缺失或重复: {sid!r}")
        seen.add(sid)
        prefix = sid.split("-", 1)[0]
        counts[prefix] = counts.get(prefix, 0) + 1
        if src != f"audio/{sid}.mp3":
            raise SystemExit(f"{sid} 的 audio src 应为 audio/{sid}.mp3，实际 {src!r}")
        if re.search(r"\s", text):
            raise SystemExit(f"{sid} 解说稿含空白，页面文字会和录音不一致")
        n = len(text)
        if not 80 <= n <= 180:
            raise SystemExit(f"{sid} 字数 {n}，需要 80–180")
    if counts != EXPECTED:
        raise SystemExit(f"段数不对: {counts}，期望 {EXPECTED}")


async def synth_one(sem: asyncio.Semaphore, text: str, dest: Path) -> None:
    import edge_tts

    last: Exception | None = None
    async with sem:
        for attempt in range(4):
            try:
                comm = edge_tts.Communicate(text, VOICE, rate=RATE)
                await comm.save(str(dest))
                if dest.stat().st_size < 2000:
                    raise RuntimeError(f"文件过小 ({dest.stat().st_size} bytes)")
                return
            except Exception as exc:  # noqa: BLE001 — retry transient TTS errors
                last = exc
                await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{dest.name}: {last}")


async def generate(segs: list[tuple[str, str, str]]) -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(3)
    tasks = []
    for sid, _src, text in segs:
        dest = AUDIO / f"{sid}.mp3"
        tasks.append(synth_one(sem, text, dest))
    await asyncio.gather(*tasks)


def main() -> None:
    argp = argparse.ArgumentParser(description="生成江西景点解说 mp3（edge-tts）")
    argp.add_argument("--check", action="store_true", help="只检查文案，不请求语音")
    args = argp.parse_args()
    segs = load_segments()
    validate(segs)
    print(f"{len(segs)} 段，音色 {VOICE}，语速 {RATE}")
    for sid, _src, text in segs:
        print(f"  {sid}  {len(text)} 字")
    if args.check:
        return
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        raise SystemExit("缺少 edge-tts。先执行: pip install edge-tts")
    asyncio.run(generate(segs))
    total = 0
    for sid, _src, _text in segs:
        path = AUDIO / f"{sid}.mp3"
        total += path.stat().st_size
        print(f"  wrote {path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")
    print(f"合计 {total / 1024 / 1024:.2f} MB -> {AUDIO.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
