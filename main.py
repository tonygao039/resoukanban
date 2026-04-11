import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# ================= 配置区 =================
API_KEY = os.environ.get("ZECTRIX_API_KEY")
MAC_ADDRESS = os.environ.get("ZECTRIX_MAC")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
PUSH_URL = f"https://cloud.zectrix.com/open/v1/devices/{MAC_ADDRESS}/display/image"

FONT_PATH = "font.ttf"
try:
    font_title = ImageFont.truetype(FONT_PATH, 24)
    font_item = ImageFont.truetype(FONT_PATH, 18)
    font_small = ImageFont.truetype(FONT_PATH, 14)
except:
    print("错误: 找不到 font.ttf")
    exit(1)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# ================= 核心工具函数：智能换行与动态绘图 =================

def get_wrapped_lines(text, max_chars=18):
    """根据字数手动换行，确保中英文混合不乱码"""
    lines = []
    while text:
        lines.append(text[:max_chars])
        text = text[max_chars:]
    return lines

def draw_dynamic_hot_list(draw, title, all_items, start_idx=0):
    """
    动态布局函数：自动计算高度，填满即止
    返回：本页显示的最后一个条目的索引
    """
    # 绘制你喜欢的黑底标题栏
    draw.rounded_rectangle([(10, 10), (390, 45)], radius=8, fill=0)
    draw.text((20, 15), title, font=font_title, fill=255)
    
    y = 55
    item_gap = 12
    line_height = 22
    last_idx = start_idx
    
    for i in range(start_idx, len(all_items)):
        text = all_items[i]
        lines = get_wrapped_lines(text, max_chars=19)
        
        # 计算这一条总共需要的高度
        required_h = len(lines) * line_height
        
        # 如果当前高度 + 所需高度 超过屏幕底部（留点边距），则停止
        if y + required_h > 290:
            break
            
        # 绘制序号（根据你的要求，保留前5个有黑框的icon效果，之后的只显示数字）
        current_num = i + 1
        if current_num <= 5:
            draw.rounded_rectangle([(10, y), (34, y+24)], radius=6, fill=0)
            draw.text((16 if current_num < 10 else 12, y+2), str(current_num), font=font_small, fill=255)
        else:
            draw.text((15, y+2), f"{current_num}.", font=font_item, fill=0)
            
        # 绘制多行标题
        curr_y = y + 2
        for line in lines:
            draw.text((45, curr_y), line, font=font_item, fill=0)
            curr_y += line_height
            
        # 动态更新 y 坐标
        y += max(24, required_h) + item_gap
        last_idx = i + 1 # 记录处理到了第几条
        
        # 绘制淡淡的分割线
        if y < 285:
            draw.line([(45, y - item_gap/2), (380, y - item_gap/2)], fill=0, width=1)
            
    return last_idx

def push_image(img, page_id):
    img.save("temp.png")
    api_headers = {"X-API-Key": API_KEY}
    files = {"images": ("temp.png", open("temp.png", "rb"), "image/png")}
    data = {"dither": "true", "pageId": str(page_id)}
    try:
        res = requests.post(PUSH_URL, headers=api_headers, files=files, data=data)
        print(f"推送第 {page_id} 页成功:", res.status_code)
    except Exception as e:
        print(f"推送第 {page_id} 页失败:", e)

# ================= 页面执行任务 =================

def page_zhihu():
    print("获取知乎热榜...")
    try:
        url = "https://api.zhihu.com/topstory/hot-list"
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        titles = [item['target']['title'] for item in res['data']]
    except:
        titles = ["数据获取失败，请检查网络"] * 10

    # 页面 1：从第 1 条开始画
    img1 = Image.new('1', (400, 300), color=255)
    next_start = draw_dynamic_hot_list(ImageDraw.Draw(img1), "🔥 知乎热榜 (1-5)", titles, 0)
    push_image(img1, page_id=1)

    # 页面 2：从页面 1 结束的地方接着画
    img2 = Image.new('1', (400, 300), color=255)
    draw_dynamic_hot_list(ImageDraw.Draw(img2), "🔥 知乎热榜 (续)", titles, next_start)
    push_image(img2, page_id=2)

def page_github():
    print("获取 GitHub 趋势...")
    items = []
    try:
        gh_headers = HEADERS.copy()
        if GITHUB_TOKEN: gh_headers['Authorization'] = f"token {GITHUB_TOKEN}"
        url = f"https://api.github.com/search/repositories?q=created:>{(datetime.now()-timedelta(days=7)).strftime('%Y-%m-%d')}&sort=stars&order=desc"
        res = requests.get(url, headers=gh_headers, timeout=10).json()
        for item in res['items'][:8]:
            items.append(f"{item['name']} ({item['stargazers_count']}★)")
    except:
        items = ["获取失败"] * 5
        
    img = Image.new('1', (400, 300), color=255)
    draw_dynamic_hot_list(ImageDraw.Draw(img), "💻 GitHub 热门开源", items)
    push_image(img, page_id=3)

def page_dashboard():
    print("生成综合看板...")
    img = Image.new('1', (400, 300), color=255)
    draw = ImageDraw.Draw(img)
    
    # --- 保持你最喜欢的并排天气/倒计时样式 ---
    try:
        url = "http://t.weather.itboy.net/api/weather/city/101030100"
        weather_data = requests.get(url, headers=HEADERS, timeout=10).json()
        city = weather_data['cityInfo']['city']
        forecast = weather_data['data']['forecast'][0]
        wea = forecast['type']
        high_str = forecast['high'].replace('高温 ', '')
        low_str = forecast['low'].replace('低温 ', '')
        avg_temp = (int(high_str.replace('℃','')) + int(low_str.replace('℃',''))) / 2
        
        if avg_temp >= 28: tip = "天气炎热，建议穿清凉衣物。"
        elif avg_temp >= 15: tip = "体感舒适，建议穿单层薄外套。"
        else: tip = "天气寒冷，请注意防寒保暖！"
    except:
        city, wea, high_str, low_str, tip = "天津", "未知", "0℃", "0℃", "获取天气失败"

    # 左侧：天气方块
    draw.rounded_rectangle([(10, 10), (195, 120)], radius=10, fill=0)
    draw.text((20, 20), f"{city} | {wea}", font=font_title, fill=255)
    draw.text((20, 60), f"{low_str}~{high_str}", font=font_title, fill=255)
    
    # 右侧：倒计时方块
    today = datetime.today().weekday()
    days_to_weekend = 5 - today
    draw.rounded_rectangle([(205, 10), (390, 120)], radius=10, fill=0)
    draw.text((215, 20), "距离周末", font=font_item, fill=255)
    draw.text((215, 60), "已是周末!" if days_to_weekend <= 0 else f"还有 {days_to_weekend} 天", font=font_title, fill=255)

    # 中间：穿衣建议（带换行）
    draw.text((10, 135), "👕 建议:", font=font_item, fill=0)
    tip_lines = get_wrapped_lines(tip, 18)
    for i, line in enumerate(tip_lines):
        draw.text((10, 160 + i*22), line, font=font_item, fill=0)

    # --- 保持你最喜欢的“每日一言”分割线布局 ---
    try:
        hitokoto = requests.get("https://v1.hitokoto.cn/?c=a", timeout=5).json()['hitokoto']
    except:
        hitokoto = "永远年轻，永远热泪盈眶。"
        
    draw.line([(10, 220), (390, 220)], fill=0, width=2)
    draw.text((10, 230), "「每日一言」", font=font_small, fill=0)
    
    hito_lines = get_wrapped_lines(hitokoto, 20)
    for i, line in enumerate(hito_lines[:2]): # 最多显示两行，防止溢出
        draw.text((10, 250 + i*25), line, font=font_item, fill=0)

    push_image(img, page_id=4)

if __name__ == "__main__":
    if not API_KEY or not MAC_ADDRESS:
        print("错误: 请配置 GitHub Secrets")
        exit(1)
        
    page_zhihu()     # 分两页推送知乎热搜
    page_github()    # 推送 GitHub
    page_dashboard() # 推送你最喜欢的综合看板
    print("任务执行完毕！")
