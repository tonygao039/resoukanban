# 极趣墨水屏 NewsNow 风格看板

这是一个开源的 Python 脚本，利用 GitHub Actions 自动为极趣墨水屏推送每日看板信息。

### 功能特点：

- 📱 Page 1&2: 知乎实时热搜榜（NewsNow 圆角风格）
- 💻 Page 3: GitHub 热门开源榜
- 🌤️ Page 3: 综合面板（当地天气、穿衣建议、周末倒计时、每日一言）

### 如何使用：

1. 点击右上角的 **Fork**，把这个项目复制到你的账号下。
2. 准备一个你喜欢的字体，命名为 font.ttf 覆盖掉本仓库里的字体文件。
3. 到你的仓库 Settings -> Secrets and variables -> Actions 里添加两个变量：
   - ZECTRIX_API_KEY: 填入你的极趣云 API Key。
   - ZECTRIX_MAC: 填入你的墨水屏 MAC 地址。
4. 在 Actions 页面手动运行一次即可生效！每天每隔 1 小时自动更新。
