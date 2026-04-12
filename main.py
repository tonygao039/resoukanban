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

# 字体加载
FONT_PATH = "font.ttf"
try:
    font_huge = ImageFont.truetype(FONT_PATH, 65)   # 实时气温/月份大字
    font_title = ImageFont.truetype(FONT_PATH, 24)  # 标题栏
    font_item = ImageFont.truetype(FONT_PATH, 18)   # 正文/阳历/建议
    font_small = ImageFont.truetype(FONT_PATH, 14)  # 序号/星期
    font_tiny = ImageFont.truetype(FONT_PATH, 11)   # 农历/预报细节
except:
    print("错误: 找不到 font.ttf，请确保字体文件在同一目录下")
    exit(1)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# ================= 工具函数 =================

def get_wrapped_lines(text, max_chars=18):
    """通用手动换行函数"""
    lines = []
    while text:
        lines.append(text[:max_chars])
        text = text[max_chars:]
    return lines

def get_clothing_advice(temp):
    """根据实时气温给出具体的穿衣建议"""
    try:
        t = int(temp)
        if t >= 28: return "建议穿短袖、短裤，注意防晒补水。"
        elif t >= 22: return "体感舒适，建议穿 T 恤配薄长裤。"
        elif t >= 16: return "建议穿长袖衬衫、卫衣或单层薄外套。"
        elif t >= 10: return "气温微凉，建议穿夹克、风衣或毛衣。"
        elif t >= 5: return "建议穿大衣、厚毛衣或薄款羽绒服。"
        else: return "天气寒冷，建议穿厚羽绒服，注意防寒。"
    except:
        return "请根据实际体感气温调整着装。"

def get_lunar_txt(y, m, d):
    """获取农历或节日/节气"""
    try:
        date_obj = datetime(y, m, d)
        lunar = ZhDate.from_datetime(date_obj)
        # 1. 公历节日
        fests = {(1,1):"元旦", (5,1):"劳动节", (10,1):"国庆节"}
        if (m, d) in fests: return fests[(m, d)]
        # 2. 农历节日
        l_fests = {(1,1):"春节", (5,5):"端午", (8,15):"中秋"}
        if (lunar.lunar_month, lunar.lunar_day) in l_fests: return l_fests[(lunar.lunar_month, lunar.lunar_day)]
        # 3. 节气 (清明手动判断)
        if m == 4 and (d == 4 or d == 5): return "清明"
        # 4. 普通农历日
        return lunar.lunar_date_str()[-2:]
    except:
        return ""

def push_image(img, page_id):
    """推送图像到极趣云"""
    img.save(f"page_{page_id}.png")
    api_headers = {"X-API-Key": API_KEY}
    files = {"images": (f"page_{page_id}.png", open(f"page_{page_id}.png", "rb"), "image/png")}
    data = {"dither": "true", "pageId": str(page_id)}
    try:
        res = requests.post(PUSH_URL, headers=api_headers, files=files, data=data)
        print(f"Page {page_id} 推送成功: {res.status_code}")
    except Exception as e:
        print(f"Page {page_id} 推送失败: {e}")

# ================= 页面 1 & 2: 知乎热榜 (动态高度) =================

def task_zhihu():
    print("获取知乎热榜...")
    try:
        url = "https://api.zhihu.com/topstory/hot-list"
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        titles = [item['target']['title'] for item in res['data']]
    except Exception as e:
        print(f"知乎获取异常: {e}")
        titles = ["数据获取失败，请检查网络"] * 10

    def draw_list(draw, page_title, items, start_idx):
        # 绘制黑底标题栏
        draw.rounded_rectangle([(10, 10), (390, 45)], radius=8, fill=0)
        draw.text((20, 15), page_title, font=font_title, fill=255)
        
        y, last_idx = 55, start_idx
        item_gap = 12
        line_height = 22
        
        for i in range(start_idx, len(items)):
            lines = get_wrapped_lines(items[i], 19)
            required_h = len(lines) * line_height
            
            if y + required_h > 295:
                break
            
            # 统一黑底方块序号
            current_num = i + 1
            draw.rounded_rectangle([(10, y), (36, y+24)], radius=6, fill=0)
            num_x = 18 if current_num < 10 else 11
            draw.text((num_x, y+2), str(current_num), font=font_small, fill=255)
            
            # 绘制多行标题
            curr_y = y + 2
            for line in lines:
                draw.text((45, curr_y), line, font=font_item, fill=0)
                curr_y += line_height
            
            y += max(24, required_h) + item_gap
            last_idx = i + 1
            # 画线
            if y < 290:
                draw.line([(45, y - item_gap/2), (380, y - item_gap/2)], fill=0, width=1)
        return last_idx

    # 推送两页知乎
    img1 = Image.new('1', (400, 300), color=255)
    next_s = draw_list(ImageDraw.Draw(img1), "🔥 知乎热榜 (一)", titles, 0)
    push_image(img1, 1)

    img2 = Image.new('1', (400, 300), color=255)
    draw_list(ImageDraw.Draw(img2), "🔥 知乎热榜 (二)", titles, next_s)
    push_image(img2, 2)

# ================= 页面 3: 实体台历风格 (阳历+农历) =================

def task_calendar():
    print("生成 Page 3: 实体台历...")
    img = Image.new('1', (400, 300), color=255)
    draw = ImageDraw.Draw(img)
    
    now = datetime.now()
    y, m, today = now.year, now.month, now.day
    
    # 顶部年月信息
    draw.text((20, 10), str(m), font=font_huge, fill=0)
    draw.text((90, 20), now.strftime("%B"), font=font_title, fill=0)
    draw.text((90, 48), str(y), font=font_item, fill=0)
    draw.line([(20, 78), (380, 78)], fill=0, width=2)

    # 星期头 (日-六)
    headers = ["日", "一", "二", "三", "四", "五", "六"]
    col_w = 53
    for i, h in enumerate(headers):
        draw.text((25 + i*col_w, 88), h, font=font_small, fill=0)

    # 日历网格
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(y, m)
    curr_y, row_h = 115, 38
    
    for week in cal:
        for c, day in enumerate(week):
            if day != 0:
                dx = 25 + c*col_w
                # 今天的标记框
                if day == today:
                    draw.rounded_rectangle([(dx-3, curr_y-2), (dx+35, curr_y+32)], radius=5, outline=0)
                
                # 绘制数字与农历
                draw.text((dx+2, curr_y), str(day), font=font_item, fill=0)
                lunar = get_lunar_txt(y, m, day)
                draw.text((dx+2, curr_y + 18), lunar, font=font_tiny, fill=0)
        curr_y += row_h
        
    push_image(img, 3)

# ================= 页面 4: 气象仪表盘 (wttr.in 津南区定位) =================

def task_weather_dashboard():
    print("生成 Page 4: 气象仪表盘 (定位: 津南)...")
    img = Image.new('1', (400, 300), color=255)
    draw = ImageDraw.Draw(img)

    try:
        # 使用 wttr.in 锁定 Jinnan,Tianjin
        url = "https://wttr.in/Jinnan,Tianjin?format=j1&lang=zh"
        resp = requests.get(url, timeout=15).json()
        
        curr = resp['current_condition'][0]
        curr_temp = int(curr['temp_C']) 
        weather_text = curr['lang_zh'][0]['value']
        
        forecasts = resp['weather']
        today_f = forecasts[0]
        t_low = today_f['mintempC']
        t_high = today_f['maxtempC']

        # 1. 左侧：大字气温区
        draw.text((20, 15), "天津 | 津南区 (天大北洋园)", font=font_title, fill=0)
        draw.text((25, 60), f"{curr_temp}°C", font=font_huge, fill=0)
        draw.text((25, 128), f"☁️ {weather_text}", font=font_item, fill=0)
        draw.text((25, 153), f"🌡️ {t_low}° ~ {t_high}°", font=font_item, fill=0)

        # 2. 右侧：三日趋势预报
        draw.line([(220, 65), (220, 170)], fill=0, width=1)
        for i in range(1, 4):
            f = forecasts[i]
            dx = 235 + (i-1)*55
            # 日期与描述
            draw.text((dx, 65), f"D+{i}", font=font_small, fill=0)
            draw.text((dx, 82), f['date'][5:], font=font_tiny, fill=0)
            
            f_desc = f['hourly'][4]['lang_zh'][0]['value'][:2] 
            draw.text((dx, 110), f_desc, font=font_tiny, fill=0)
            
            # 高低温显示
            draw.text((dx, 135), f"{f['maxtempC']}°", font=font_tiny, fill=0)
            draw.text((dx, 150), f"{f['mintempC']}°", font=font_tiny, fill=0)

        # 3. 中部：具体穿衣建议
        advice = get_clothing_advice(curr_temp)
        draw.line([(20, 190), (380, 190)], fill=0, width=1)
        draw.text((20, 200), f"👕 {advice}", font=font_item, fill=0)

    except Exception as e:
        print(f"天气获取异常: {e}")
        draw.text((20, 50), "天气数据获取中，请稍后...", font=font_item, fill=0)

    # 4. 底部：每日一言
    try:
        hito_res = requests.get("https://v1.hitokoto.cn/?c=i", timeout=5).json()
        hito = hito_res['hitokoto']
    except:
        hito = "实事求是。"
    
    draw.line([(20, 240), (380, 240)], fill=0, width=2)
    draw.text((20, 248), "「每日一言」", font=font_small, fill=0)
    lines = [hito[i:i+20] for i in range(0, len(hito), 20)]
    for i, line in enumerate(lines[:2]):
        draw.text((20, 268 + i*20), line, font=font_item, fill=0)

    push_image(img, 4)

# ================= 主程序 =================

if __name__ == "__main__":
    if not API_KEY or not MAC_ADDRESS:
        print("错误: 请在 GitHub Secrets 中配置 ZECTRIX_API_KEY 和 ZECTRIX_MAC")
        exit(1)
        
    task_zhihu()              # 生成 Page 1, 2
    task_calendar()           # 生成 Page 3
    task_weather_dashboard()  # 生成 Page 4
    print("所有任务执行完毕！")
