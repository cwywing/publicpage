# 三清 × 望仙谷 × 篁岭 × 景德镇 × 庐山 · 2026 国庆 7 天

公开行程页：https://cwywing.github.io/publicpage/jiangxi-2026/

4 成人，深圳高铁进出，10.01–10.07。住宿：金沙 1 + 望仙谷 1 + 篁岭 1 + 景德镇 2 + 牯岭 1。对齐同伴望仙谷骨架。浮梁史子园茶山不排进主行程。

## 景点解说音频

三清山、望仙谷、篁岭、景德镇、庐山五张景点卡各有多段解说。写的是地质、传说和历史（景德镇写瓷史），不写排队、住宿和拍照。页面上的文字就是录音稿。语音用免费 Microsoft Edge 神经网络音色（Python 包 `edge-tts`），不是付费 Azure Speech。

- 音色：`zh-CN-XiaoxiaoNeural`
- 语速：`-5%`（约 0.95）
- 文件：`audio/sq-01.mp3`、`audio/wxg-02.mp3`、`audio/hl-03.mp3`、`audio/jd-04.mp3`、`audio/ls-05.mp3` 这一类

改 `index.html` 里某段 `p.seg-script` 之后重跑：

```bash
pip install edge-tts
python3 jiangxi-2026/scripts/generate_audio.py
```

只检查字数、段数和文件名、不请求语音：

```bash
python3 jiangxi-2026/scripts/generate_audio.py --check
```
