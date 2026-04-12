import os
import requests
import calendar
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from zhdate import ZhDate

# ================= 配置区 =================
API_KEY = os.environ.get("ZECTRIX_API_KEY")
MAC_ADDRESS = os.environ.get("ZECTRIX_MAC")
PUSH_URL = f"https://cloud.zectrix.com/open/v1/devices/{MAC_ADDRESS}/display/image"

FONT_PATH = "font.ttf"
try:
    font_huge = ImageFont.truetype(FONT_PATH, 55)   # 月份大字
    font_title = ImageFont.truetype(FONT_PATH, 24)  # 标题/年份
    font_item = ImageFont.truetype(FONT_PATH, 18)   # 阳历/建议
    font_tiny = ImageFont.truetype(FONT_PATH, 11)   # 农历（必须小，否则重叠）
    font_small = ImageFont.truetype(FONT_PATH, 14)  # 星期/一言标题
except:
    print("错误: 找不到 font.ttf")
    exit(1)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# ================= 辅助函数 =================

def get_wrapped_lines(text, max_chars=18):
    lines = []
    while text:
        lines.append(text[:max_chars])
        text = text[max_chars:]
    return lines

def get_lunar_info(y, m, d):
    """获取农历日期或节日，确保不重复"""
    try:
        date_obj = datetime(y, m, d)
        lunar = ZhDate.from_datetime(date_obj)
        
        # 1. 优先级最高：法定/重大节日
        fests = {
            (1,1): "元旦", (5,1): "劳动节", (10,1): "国庆节",
            (4,4): "清明", (4,5): "清明" # 清明通常在这两天
        }
        if (m, d) in fests: return fests[(m, d)]
        
        # 2. 农历节日
        l_fests = { (1,1):"春节", (5,5):"端午", (8,15):"中秋" }
        if (lunar.lunar_month, lunar.lunar_day) in l_fests:
            return l_fests[(lunar.lunar_month, lunar.lunar_day)]
        
        # 3. 普通农历日期 (如: 初五, 廿十)
        lunar_str = lunar.lunar_date_str() # 类似 "二零二六正月初五"
        return lunar_str[-2:]
    except:
        return ""

def push_image(img, page_id):
    img.save(f"page_{page_id}.png")
    api_headers = {"X-API-Key": API_KEY}
    files = {"images": (f"page_{page_id}.png", open(f"page_{page_id}.png", "rb"), "image/png")}
    data = {"dither": "true", "pageId": str(page_id)}
    requests.post(PUSH_URL, headers=api_headers, files=files, data=data)

# ================= Page 1 & 2: 知乎热榜 (略，保持你之前的动态高度逻辑) =================

def task_zhihu():
    print("获取知乎热榜...")
    try:
        url = "https://api.zhihu.com/topstory/hot-list"
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        titles = [item['target']['title'] for item in res['data']]
    except: titles = ["数据获取失败"] * 5

    def draw_hot_list(draw, title, items, start_idx):
        draw.rounded_rectangle([(10, 10), (390, 45)], radius=8, fill=0)
        draw.text((20, 15), title, font=font_title, fill=255)
        y, last_idx = 55, start_idx
        for i in range(start_idx, len(items)):
            lines = get_wrapped_lines(items[i], 19)
            h = len(lines) * 22
            if y + h > 295: break
            draw.rounded_rectangle([(10, y), (36, y+24)], radius=6, fill=0)
            draw.text((18 if i+1 < 10 else 11, y+2), str(i+1), font=font_small, fill=255)
            for line in lines:
                draw.text((45, y+2), line, font=font_item, fill=0)
                y += 22
            y += 10
            last_idx = i + 1
            if y < 290: draw.line([(45, y-5), (380, y-5)], fill=0, width=1)
        return last_idx

    img1 = Image.new('1', (400, 300), color=255)
    ns = draw_hot_list(ImageDraw.Draw(img1), "🔥 知乎热榜 (一)", titles, 0)
    push_image(img1, 1)

    img2 = Image.new('1', (400, 300), color=255)
    draw_hot_list(ImageDraw.Draw(img2), "🔥 知乎热榜 (二)", titles, ns)
    push_image(img2, 2)

# ================= Page 3: 全屏实体台历 (修复农历和清明问题) =================

def task_calendar():
    print("生成 Page 3: 实体台历...")
    img = Image.new('1', (400, 300), color=255)
    draw = ImageDraw.Draw(img)
    
    now = datetime.now()
    y, m, today = now.year, now.month, now.day
    
    # 顶部年月
    draw.text((20, 10), str(m), font=font_huge, fill=0)
    draw.text((85, 20), now.strftime("%B"), font=font_title, fill=0)
    draw.text((85, 48), str(y), font=font_item, fill=0)
    draw.line([(20, 78), (380, 78)], fill=0, width=2)

    # 星期表头
    headers = ["日", "一", "二", "三", "四", "五", "六"]
    col_w = 53
    for i, h in enumerate(headers):
        draw.text((25 + i*col_w, 88), h, font=font_small, fill=0)

    # 日历网格
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(y, m)
    curr_y = 115
    row_h = 36 # 稍微压缩一点行高，确保农历能看到
    
    for week in cal:
        for c, day in enumerate(week):
            if day != 0:
                dx = 25 + c*col_w
                if day == today:
                    draw.rounded_rectangle([(dx-4, curr_y-2), (dx+38, curr_y+30)], radius=5, outline=0)
                
                # 绘制公历
                draw.text((dx+2, curr_y), str(day), font=font_item, fill=0)
                # 绘制农历/节日 (垂直偏移 16 像素)
                lunar_txt = get_lunar_info(y, m, day)
                draw.text((dx+2, curr_y + 17), lunar_txt, font=font_tiny, fill=0)
        curr_y += row_h
        
    push_image(img, 3)

# ================= Page 4: 综合看板 (更换稳定天气接口) =================

def task_dashboard():
    print("生成 Page 4: 综合看板 (津南)...")
    img = Image.new('1', (400, 300), color=255)
    draw = ImageDraw.Draw(img)
    
    # 使用 wttr.in 接口获取津南天气，它识别 "Jinnan" 非常准
    try:
        w_url = "https://wttr.in/Jinnan?format=j1" # 请求 JSON 格式
        w_data = requests.get(w_url, timeout=10).json()
        current = w_data['current_condition'][0]
        weather_desc = current['lang_zh'][0]['value'] if 'lang_zh' in current else current['weatherDesc'][0]['value']
        temp_c = current['temp_C']
        # 建议 logic
        tip = f"当前气温{temp_c}℃，{weather_desc}。请注意增减衣物。"
        title_str = f"津南区 | {weather_desc}"
        temp_range = f"实时气温: {temp_c}℃"
    except:
        title_str, temp_range, tip = "天大北洋园 | 晴", "15℃~22℃", "获取天气失败，请保持好心情。"

    # 天气方块
    draw.rounded_rectangle([(10, 10), (195, 120)], radius=10, fill=0)
    draw.text((20, 20), title_str, font=font_title, fill=255)
    draw.text((20, 60), temp_range, font=font_title, fill=255)
    
    # 倒计时
    days = 5 - datetime.today().weekday()
    draw.rounded_rectangle([(205, 10), (390, 120)], radius=10, fill=0)
    draw.text((215, 20), "距离周末", font=font_item, fill=255)
    draw.text((215, 60), "已是周末!" if days <= 0 else f"还有 {days} 天", font=font_title, fill=255)

    # 建议
    draw.text((10, 135), "👕 建议:", font=font_item, fill=0)
    for i, line in enumerate(get_wrapped_lines(tip, 19)[:2]):
        draw.text((10, 160 + i*22), line, font=font_item, fill=0)

    # 每日一言
    try: hito = requests.get("https://v1.hitokoto.cn/?c=i", timeout=5).json()['hitokoto']
    except: hito = "实事求是。"
        
    draw.line([(10, 220), (390, 220)], fill=0, width=2)
    draw.text((10, 230), "「每日一言」", font=font_small, fill=0)
    for i, line in enumerate(get_wrapped_lines(hito, 20)[:2]):
        draw.text((10, 250 + i*25), line, font=font_item, fill=0)

    push_image(img, 4)

if __name__ == "__main__":
    task_zhihu()
    task_calendar()
    task_dashboard()
    print("全部推送完毕！")
