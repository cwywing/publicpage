# podcast · 旅途随声听

iPhone 优先的单页播客播放器，纯静态，无构建、无依赖。内置 25 个写死的
中文播客 RSS 订阅：陪伴通勤 10 档、访谈对谈 12 档、经典访谈存档 3 档
（锵锵三人行两套全档案 + 圆桌派，民间上传的电视节目音频）。

## 结构

```
podcast/
├── index.html              # 页面 + 样式 + 播放器逻辑（单文件）
├── icon.png / icon-512.png / favicon.png  # 应用图标（脚本生成）
├── feeds.js                # 台标 + 写死的 RSS 订阅地址（脚本生成，勿手改）
├── feeds-cache.js          # RSS 节目单离线快照（脚本生成，拉取失败时兜底）
└── scripts/
    ├── fetch_feeds.py      # 维护订阅列表 + 更新节目单快照
    └── make_icon.py        # 重新生成应用图标
```

## 功能

- 左侧订阅库：23 档按「陪伴通勤 / 访谈对谈 / 经典访谈存档」三组展示，
  展开即拉取最新 100 集；窄屏（iPhone）为抽屉，宽屏常驻
- 右侧播放器：拖拽/点按进度条（拖动时有时间气泡预览）、±15 秒、倍速、
  播完自动切同一下一集（待按播放，iOS 不允许无手势续播）
- iOS 适配：安全区（刘海/底部横条）、`100dvh` 动态视口、深色模式、锁屏播放控制（Media Session）
- 贴近原生 App：应用图标（Safari「分享 → 添加到主屏幕」后获得独立图标与
  全屏体验，首次访问有引导条）、订阅列表带图标、抽屉左滑关闭手势、
  拉取/加载转圈动画、按压缩放反馈、首次进入自动展开订阅库
- 记忆播放位置：刷新后从本地缓存/快照恢复上次的单集与进度（localStorage）
- RSS 单集暂无字幕稿（feed 不提供转录文本），字幕区显示占位说明

## RSS 说明（静态页的边界）

- 订阅地址写死在 `scripts/fetch_feeds.py` 的 `FEEDS`，跑一次脚本同时产出
  `feeds.js` 和节目单快照 `feeds-cache.js`（每源最近 20 集）
- 运行时拉取链路：直连 → allorigins → corsproxy.io → rss2json，
  成功后缓存 6 小时；全部失败时显示离线快照并可手动重试
- 故事FM、三五环、半拿铁、文化有限与全部喜马拉雅系 feed 自带 CORS 头，
  任何环境直连可用；小宇宙系（xyzfm.space）、fireside 系（随机波动、
  声东击西）与 Anchor 系（锵锵/圆桌派存档）依赖代理是否可达
- 音频跨域可直接播（`<audio>` 不受 CORS 限制），feed 里均为 https，
  GitHub Pages 上不会触发混合内容拦截

## 更新快照 / 改订阅

```bash
python podcast/scripts/fetch_feeds.py   # 抓取并重写 feeds.js + feeds-cache.js
```

订阅列表改 `FEEDS`（id/title/rss/note/group），group 取 `commute`（陪伴
通勤）、`talk`（访谈对谈）或 `classic`（经典访谈存档）；台标在 `SHOW`。

## 本地预览

```bash
python -m http.server 8000
# iPhone 上访问 http://<电脑IP>:8000/podcast/
```
