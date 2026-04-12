import os
import requests
import calendar
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from zhdate import ZhDate

# ================= 配置区 =================
API_KEY = os.environ.get("ZECTRIX_API_KEY")
MAC_ADDRESS = os.environ.get("ZECTRIX_MAC")
PUSH_URL = f"https://cloud.zectrix.com/open/v1/devices/{MAC_ADDRESS}/display/image"

# 和风天气配置
QWEATHER_KEY = os.environ.get("QWEATHER_API_KEY")  # 必须设置环境变量
CITY_CODE = "101030103"  # 津南区

FONT_PATH = "font.ttf"
try:
    font_huge = ImageFont.truetype(FONT_PATH, 55)
    font_title = ImageFont.truetype(FONT_PATH, 24)
    font_item = ImageFont.truetype(FONT_PATH, 18)
    font_tiny = ImageFont.truetype(FONT_PATH, 11)
    font_small = ImageFont.truetype(FONT_PATH, 14)
except:
    print("错误: 找不到 font.ttf")
    exit(1)

# ================= 精确节气表（2024-2027，避免连续多天显示同一节气）=================
def get_accurate_solar_term(year, month, day):
    """根据精确日期返回节气名称，非节气返回None"""
    term_table = {
        # 2024年
        (2024, 2, 4): "立春", (2024, 2, 19): "雨水", (2024, 3, 5): "惊蛰", (2024, 3, 20): "春分",
        (2024, 4, 4): "清明", (2024, 4, 19): "谷雨", (2024, 5, 5): "立夏", (2024, 5, 20): "小满",
        (2024, 6, 5): "芒种", (2024, 6, 21): "夏至", (2024, 7, 6): "小暑", (2024, 7, 22): "大暑",
        (2024, 8, 7): "立秋", (2024, 8, 22): "处暑", (2024, 9, 7): "白露", (2024, 9, 22): "秋分",
        (2024, 10, 8): "寒露", (2024, 10, 23): "霜降", (2024, 11, 7): "立冬", (2024, 11, 22): "小雪",
        (2024, 12, 6): "大雪", (2024, 12, 21): "冬至",
        # 2025年
        (2025, 1, 5): "小寒", (2025, 1, 20): "大寒", (2025, 2, 3): "立春", (2025, 2, 18): "雨水",
        (2025, 3, 5): "惊蛰", (2025, 3, 20): "春分", (2025, 4, 4): "清明", (2025, 4, 20): "谷雨",
        (2025, 5, 5): "立夏", (2025, 5, 21): "小满", (2025, 6, 5): "芒种", (2025, 6, 21): "夏至",
        (2025, 7, 7): "小暑", (2025, 7, 22): "大暑", (2025, 8, 7): "立秋", (2025, 8, 23): "处暑",
        (2025, 9, 7): "白露", (2025, 9, 22): "秋分", (2025, 10, 8): "寒露", (2025, 10, 23): "霜降",
        (2025, 11, 7): "立冬", (2025, 11, 22): "小雪", (2025, 12, 7): "大雪", (2025, 12, 21): "冬至",
        # 2026年
        (2026, 1, 5): "小寒", (2026, 1, 20): "大寒", (2026, 2, 4): "立春", (2026, 2, 18): "雨水",
        (2026, 3, 5): "惊蛰", (2026, 3, 20): "春分", (2026, 4, 5): "清明", (2026, 4, 20): "谷雨",
        (2026, 5, 5): "立夏", (2026, 5, 21): "小满", (2026, 6, 6): "芒种", (2026, 6, 21): "夏至",
        (2026, 7, 7): "小暑", (2026, 7, 23): "大暑", (2026, 8, 7): "立秋", (2026, 8, 23): "处暑",
        (2026, 9, 7): "白露", (2026, 9, 23): "秋分", (2026, 10, 8): "寒露", (2026, 10, 23): "霜降",
        (2026, 11, 7): "立冬", (2026, 11, 22): "小雪", (2026, 12, 7): "大雪", (2026, 12, 21): "冬至",
        # 2027年
        (2027, 1, 5): "小寒", (2027, 1, 20): "大寒", (2027, 2, 4): "立春", (2027, 2, 19): "雨水",
        (2027, 3, 6): "惊蛰", (2027, 3, 21): "春分", (2027, 4, 5): "清明", (2027, 4, 20): "谷雨",
        (2027, 5, 6): "立夏", (2027, 5, 21): "小满", (2027, 6, 6): "芒种", (2027, 6, 22): "夏至",
        (2027, 7, 7): "小暑", (2027, 7, 23): "大暑", (2027, 8, 8): "立秋", (2027, 8, 24): "处暑",
        (2027, 9, 8): "白露", (2027, 9, 23): "秋分", (2027, 10, 9): "寒露", (2027, 10, 24): "霜降",
        (2027, 11, 7): "立冬", (2027, 11, 22): "小雪", (2027, 12, 7): "大雪", (2027, 12, 22): "冬至",
    }
    return term_table.get((year, month, day), None)

def get_lunar_or_term(y, m, d):
    """返回日期下方应显示的文字：节气 > 节日 > 农历"""
    term = get_accurate_solar_term(y, m, d)
    if term:
        return term
    # 法定节日
    fests = {(1,1):"元旦", (5,1):"劳动节", (10,1):"国庆节"}
    if (m, d) in fests:
        return fests[(m, d)]
    try:
        date_obj = datetime(y, m, d)
        lunar = ZhDate.from_datetime(date_obj)
        l_fests = {(1,1):"春节", (5,5):"端午", (8,15):"中秋"}
        if (lunar.lunar_month, lunar.lunar_day) in l_fests:
            return l_fests[(lunar.lunar_month, lunar.lunar_day)]
        return lunar.lunar_date_str()[-2:]  # 如“初八”
    except:
        return ""  # 无法获取就不显示

# ================= 和风天气获取（带详细错误输出）=================
def get_qweather():
    if not QWEATHER_KEY:
        print("错误: 未设置 QWEATHER_API_KEY 环境变量")
        return None
    try:
        # 3天预报
        url_3d = f"https://devapi.qweather.com/v7/weather/3d?location={CITY_CODE}&key={QWEATHER_KEY}"
        resp_3d = requests.get(url_3d, timeout=10).json()
        if resp_3d.get('code') != '200':
            print(f"和风天气3d接口错误: code={resp_3d.get('code')}, msg={resp_3d}")
            return None
        today = resp_3d['daily'][0]
        weather_text = today['textDay']
        temp_min = today['tempMin']
        temp_max = today['tempMax']

        # 24小时预报
        url_24h = f"https://devapi.qweather.com/v7/weather/24h?location={CITY_CODE}&key={QWEATHER_KEY}"
        resp_24h = requests.get(url_24h, timeout=10).json()
        if resp_24h.get('code') != '200':
            print(f"和风天气24h接口错误: code={resp_24h.get('code')}, msg={resp_24h}")
            return "津南区", weather_text, temp_min, temp_max, None  # 无曲线数据

        hourly = resp_24h['hourly']
        hours = []
        temps = []
        now_hour = datetime.now().hour
        # 取未来12小时（最多12个点）
        for item in hourly[:12]:
            fx_time = datetime.fromisoformat(item['fxTime'])
            hour = fx_time.hour
            temp = int(item['temp'])
            hours.append(hour)
            temps.append(temp)
        return "津南区", weather_text, temp_min, temp_max, (hours, temps)
    except Exception as e:
        print(f"和风天气请求异常: {e}")
        return None

def draw_temp_curve(draw, hours, temps, x0, y0, width, height):
    """绘制温度折线图"""
    if not hours or len(temps) < 2:
        draw.text((x0, y0), "温度数据不足，请检查API", font=font_item, fill=0)
        return
    x_step = width / (len(hours)-1)
    y_min, y_max = min(temps), max(temps)
    y_range = y_max - y_min if y_max != y_min else 1
    points = []
    for i, (h, t) in enumerate(zip(hours, temps)):
        x = x0 + i * x_step
        y = y0 + height - (t - y_min) / y_range * height
        points.append((x, y))
    draw.line(points, fill=0, width=2)
    draw.text((x0, y0-12), f"{temps[0]}℃", font=font_tiny, fill=0)
    draw.text((x0+width-20, y0-12), f"{temps[-1]}℃", font=font_tiny, fill=0)
    # 每隔2个点标时间
    for i in range(0, len(hours), 2):
        x = x0 + i * x_step
        draw.text((x-8, y0+height+2), f"{hours[i]}时", font=font_tiny, fill=0)

# ================= 推送图片 =================
def push_image(img, page_id):
    img.save(f"page_{page_id}.png")
    api_headers = {"X-API-Key": API_KEY}
    files = {"images": (f"page_{page_id}.png", open(f"page_{page_id}.png", "rb"), "image/png")}
    data = {"dither": "true", "pageId": str(page_id)}
    requests.post(PUSH_URL, headers=api_headers, files=files, data=data)

# ================= Page 3: 日历 =================
def task_calendar():
    print("生成 Page 3: 实体台历...")
    img = Image.new('1', (400, 300), color=255)
    draw = ImageDraw.Draw(img)

    now = datetime.now()
    y, m, today = now.year, now.month, now.day

    draw.text((20, 10), str(m), font=font_huge, fill=0)
    draw.text((85, 20), now.strftime("%B"), font=font_title, fill=0)
    draw.text((85, 48), str(y), font=font_item, fill=0)
    draw.line([(20, 78), (380, 78)], fill=0, width=2)

    headers = ["日", "一", "二", "三", "四", "五", "六"]
    col_w = 53
    for i, h in enumerate(headers):
        draw.text((25 + i*col_w, 88), h, font=font_small, fill=0)

    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(y, m)
    curr_y = 115
    row_h = 38

    for week in cal:
        for c, day in enumerate(week):
            if day != 0:
                dx = 25 + c * col_w
                if day == today:
                    draw.rounded_rectangle([(dx-3, curr_y-2), (dx+36, curr_y+32)], radius=5, outline=0)

                # 阳历数字
                draw.text((dx+2, curr_y), str(day), font=font_item, fill=0)

                # 下方文字（节气/节日/农历）
                bottom_text = get_lunar_or_term(y, m, day)
                if bottom_text:
                    if len(bottom_text) > 3:
                        try:
                            font_smaller = ImageFont.truetype(FONT_PATH, 10)
                            draw.text((dx+2, curr_y+18), bottom_text, font=font_smaller, fill=0)
                        except:
                            draw.text((dx+2, curr_y+18), bottom_text[:3], font=font_tiny, fill=0)
                    else:
                        draw.text((dx+2, curr_y+18), bottom_text, font=font_tiny, fill=0)
        curr_y += row_h

    push_image(img, 3)

# ================= Page 4: 综合看板 =================
def task_dashboard():
    print("生成 Page 4: 综合看板 (和风天气)...")
    img = Image.new('1', (400, 300), color=255)
    draw = ImageDraw.Draw(img)

    weather = get_qweather()
    if weather:
        city_name, weather_text, temp_min, temp_max, hourly_data = weather
        title_str = f"{city_name} | {weather_text}"
        temp_range = f"{temp_min}℃ ~ {temp_max}℃"
    else:
        title_str = "津南区 | 天气获取失败"
        temp_range = "请检查API Key或网络"
        hourly_data = None

    # 左侧天气模块
    draw.rounded_rectangle([(10, 10), (195, 120)], radius=10, fill=0)
    draw.text((20, 20), title_str, font=font_title, fill=255)
    draw.text((20, 60), temp_range, font=font_title, fill=255)

    # 右侧周末倒计时
    days = 5 - datetime.today().weekday()
    draw.rounded_rectangle([(205, 10), (390, 120)], radius=10, fill=0)
    draw.text((215, 20), "距离周末", font=font_item, fill=255)
    draw.text((215, 60), "已是周末!" if days <= 0 else f"还有 {days} 天", font=font_title, fill=255)

    # 温度曲线区域
    draw.text((10, 135), "📈 逐小时温度曲线", font=font_item, fill=0)
    if hourly_data:
        hours, temps = hourly_data
        draw_temp_curve(draw, hours, temps, 10, 155, 380, 55)
    else:
        draw.text((10, 155), "无法获取逐小时数据，请检查API Key及权限", font=font_item, fill=0)

    # 每日一言
    try:
        hito = requests.get("https://v1.hitokoto.cn/?c=i", timeout=5).json()['hitokoto']
    except:
        hito = "实事求是。"
    draw.line([(10, 225), (390, 225)], fill=0, width=2)
    draw.text((10, 235), "「每日一言」", font=font_small, fill=0)
    hito_lines = [hito[i:i+20] for i in range(0, len(hito), 20)]
    for i, line in enumerate(hito_lines[:2]):
        draw.text((10, 255 + i*25), line, font=font_item, fill=0)

    push_image(img, 4)

if __name__ == "__main__":
    task_calendar()
    task_dashboard()
    print("全部执行完毕！")
