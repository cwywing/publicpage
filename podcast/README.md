# podcast · 旅途随声听

iPhone 优先的单页播客播放器，纯静态，无构建、无依赖。内置 6 集本地演示
（带逐句字幕）+ 5 个写死的中文访谈播客 RSS 订阅。

## 结构

```
podcast/
├── index.html              # 页面 + 样式 + 播放器逻辑（单文件）
├── data.js                 # 本地演示数据：分类/单集/字幕时间轴（脚本生成）
├── audio/*.mp3             # edge-tts 合成的演示音频（脚本生成）
├── feeds.js                # 写死的 RSS 订阅地址（脚本生成，勿手改）
├── feeds-cache.js          # RSS 节目单离线快照（脚本生成，拉取失败时兜底）
└── scripts/
    ├── generate_audio.py   # 重新生成本地演示音频与 data.js
    └── fetch_feeds.py      # 维护订阅列表 + 更新节目单快照
```

## 功能

- 左侧节目库：分类可展开收起；窄屏（iPhone）为抽屉，宽屏常驻
- RSS 订阅（写死地址）：故事FM / 忽左忽右 / 不合时宜 / 得意忘形 / 三五环，
  展开即拉取最新 50 集；本地演示集有逐句字幕，RSS 单集无字幕稿
- 右侧播放器：拖拽/点按进度条（拖动时有时间气泡预览）、±15 秒、倍速
- 实时字幕：句子随播放高亮并自动滚动，点任意一句跳播；手动滚动后暂停跟随 3 秒
- iOS 适配：安全区（刘海/底部横条）、`100dvh` 动态视口、深色模式、锁屏播放控制（Media Session）
- 记忆播放位置：刷新后恢复上一集与进度（localStorage）

## RSS 说明（静态页的边界）

- 订阅地址写死在 `scripts/fetch_feeds.py` 的 `FEEDS`，跑一次脚本同时产出
  `feeds.js` 和节目单快照 `feeds-cache.js`（每源最近 20 集）
- 运行时拉取链路：直连 → allorigins → corsproxy.io → rss2json，
  成功后缓存 6 小时；全部失败时显示离线快照并可手动重试
- 故事FM、三五环的 feed 自带 CORS 头，任何环境直连可用；
  小宇宙系（忽左忽右/不合时宜/得意忘形）依赖代理是否可达
- 音频跨域可直接播（`<audio>` 不受 CORS 限制），feed 里均为 https，
  GitHub Pages 上不会触发混合内容拦截

## 重新生成本地演示内容

```bash
pip install edge-tts
python podcast/scripts/generate_audio.py --check   # 只校验文案
python podcast/scripts/generate_audio.py           # 生成 audio/ + data.js
```

改节目内容直接编辑 `scripts/generate_audio.py` 里的 `CATEGORIES`（每集一句
连续的稿子，按 `。！？；…` 切句成字幕），再跑上面的命令。

## 更新 RSS 快照 / 改订阅

```bash
python podcast/scripts/fetch_feeds.py   # 抓取并重写 feeds.js + feeds-cache.js
```

## 本地预览

```bash
python -m http.server 8000
# iPhone 上访问 http://<电脑IP>:8000/podcast/
```
