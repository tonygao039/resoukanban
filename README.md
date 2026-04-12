# 极趣墨水屏 NewsNow 风格看板

这是一个开源的 Python 脚本，利用 GitHub Actions 自动为极趣墨水屏推送每日看板信息。  
它借鉴了 NewsNow 的简洁风格，为你提供实时热点、农历日历和天气信息，无需任何服务器，完全免费。

<img src="./images/preview.jpg" width="40%">

## 📸 效果预览

| 页面 | 内容 |
|------|------|
| Page 1 & 2 | 知乎实时热搜榜（圆角卡片，序号醒目） |
| Page 3 | 阳历日历 + 农历/节气/节日 |
| Page 4 | 综合看板（天气、日出日落、未来两天预报、穿衣建议、每日一言） |


<img src="./images/zhihu.jpg" width="40%">
<img src="./images/calendar.jpg" width="40%">
<img src="./images/weather.jpg" width="40%">

## ✨ 功能特点

- 📱 **知乎热榜** – 自动抓取知乎实时热度前20条，自动分两页显示
- 📅 **农历日历** – 阳历日期下方显示农历、节气、公历节日、传统节日（如春节、清明、端午等）
- 🌤️ **天气看板** – 使用 `wttr.in` 免费接口，无需 API Key，全球可用  
  - 实时温度、今日高低温度、天气描述  
  - 湿度、风速（级）、紫外线指数  
  - 日出日落时间  
  - 未来两天预报（日期、天气、温度）  
  - 基于实时温度的穿衣建议  
- 🖼️ **纯黑白图像** – 完美适配墨水屏，400×300 分辨率
- 🔁 **自动推送** – 通过 GitHub Actions 每小时运行一次，无需手动操作

## 📋 准备工作

1. **一个 GitHub 账号** – 用于 Fork 仓库和设置 Actions。
2. **极趣墨水屏** – 已接入极趣云，并记下设备的 MAC 地址。
3. **极趣云 API Key** – 登录 [极趣云控制台](https://cloud.zectrix.com) 获取。
4. **中文字体文件** – 推荐使用 `Noto Sans CJK SC` 或任意支持中文的 `.ttf` 字体，并重命名为 `font.ttf`。

## 🚀 快速开始

### 1. Fork 项目

点击本仓库右上角的 **Fork** 按钮，将项目复制到你的 GitHub 账号下。

### 2. 添加字体文件

- 下载或准备一个中文字体（例如 `SourceHanSansCN-Normal.ttf`）。
- 将其重命名为 **`font.ttf`**。
- 在你的 Fork 仓库中，点击 `Add file` → `Upload files`，上传 `font.ttf` 并提交。

> 如果跳过此步，脚本会因找不到字体而报错。

### 3. 配置 Secrets（敏感信息）

在 GitHub 仓库页面进入 **Settings** → **Secrets and variables** → **Actions**，点击 **New repository secret**，添加以下两个变量：

| Secret 名称 | 说明 |
|------------|------|
| `ZECTRIX_API_KEY` | 你的极趣云 API Key（登录极趣云控制台获取） |
| `ZECTRIX_MAC` | 你的墨水屏 MAC 地址（格式如 `AA:BB:CC:DD:EE:FF`） |

### 4. （可选）修改推送频率

默认每小时运行一次（`cron: '0 * * * *'`）。如果你希望修改频率，请编辑 `.github/workflows/push.yml` 中的 `cron` 表达式。  
例如每天上午 8 点运行：`cron: '0 8 * * *'`

### 5. 手动运行一次测试

- 进入你的仓库 **Actions** 页面。
- 选择左侧的 **墨水屏综合看板推送** 工作流。
- 点击 **Run workflow** → **Run workflow**。
- 等待约 1 分钟，查看运行日志。若成功，你的墨水屏上会显示对应页面。

### 6. 自动更新

之后脚本会按照 cron 设定的时间自动运行，无需任何干预。你随时可以在 Actions 页面查看历史运行记录。

## 🛠️ 自定义修改

### 🗺️ 修改天气城市

默认天气地点为 **津南区（天津）**。如果你想切换到其他城市，请按以下步骤操作：

1. 在 GitHub 仓库中找到 `main.py` 文件，点击进入。
2. 点击右上角的 ✏️ 铅笔图标，编辑文件。
3. 找到 `task_weather_dashboard()` 函数中的这一行：

   ```python
   url = "https://wttr.in/Jinnan,Tianjin?format=j1&lang=zh"
4. 将 Jinnan,Tianjin 替换为你所在城市的英文名称（拼音），例如：
   北京：Beijing
   上海：Shanghai


### 调整布局坐标

所有绘图坐标均硬编码在 `task_zhihu()`、`task_calendar()`、`task_weather_dashboard()` 中。你可以根据需要微调数字（例如 `draw.text((x, y), ...)` 中的 `x`、`y`）。


### 更换 API 接口

天气接口使用免费的 `wttr.in`，无需 API Key，非常稳定。如果你希望使用和风天气、OpenWeatherMap 等，请自行修改 `get_free_weather()` 函数。


## 🙏 致谢

- 天气数据： [wttr.in](https://wttr.in)
- 知乎热榜：知乎官方 API
- 农历转换： [zhdate](https://github.com/CutePandaSh/zhdate)
- 极趣云：提供墨水屏推送服务

---
如果觉得这个项目有用，欢迎给个 ⭐ 支持一下！
