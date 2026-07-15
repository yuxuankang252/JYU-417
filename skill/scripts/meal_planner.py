#!/usr/bin/env python3
"""
AI饮食管家 (Meal Planner) — 核心脚本
=====================================
录入身边的店铺和菜品后，AI根据口味偏好、营养平衡、历史记录和预算，智能推荐每日三餐。
核心AI价值：多维约束下的个性化组合优化，传统程序无法实现。

Usage:
  python meal_planner.py profile set       # 设置用户画像
  python meal_planner.py profile show      # 查看用户画像
  python meal_planner.py shop add          # 添加店铺
  python meal_planner.py shop list         # 列出所有店铺
  python meal_planner.py dish add          # 为店铺添加菜品
  python meal_planner.py dish list         # 列出所有菜品
  python meal_planner.py log               # 记录今天吃了什么
  python meal_planner.py log today         # 查看今天的饮食记录
  python meal_planner.py recommend         # AI推荐明日三餐
  python meal_planner.py recommend --offline  # 离线规则引擎推荐
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Windows下强制 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
# 配置
# ============================================================

# 数据目录 (相对于脚本位置)
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

# LLM配置 (可修改为 DeepSeek / 通义千问 等兼容 OpenAI 接口的服务)
LLM_CONFIG = {
    "api_key": os.environ.get("OPENAI_API_KEY", "your-api-key-here"),
    "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    "model": os.environ.get("LLM_MODEL", "gpt-3.5-turbo"),
    "temperature": 0.7,
    "max_tokens": 1024,
}

# 营养参考数据 (菜名 → 估算卡路里)
# 这个字典是简易参考库，实际推荐由AI完成
CALORIE_REF = {
    # 主食类
    "米饭": 150, "馒头": 220, "花卷": 200, "油条": 230, "豆浆": 60,
    "鸡蛋灌饼": 350, "肉包": 180, "素包": 120, "粥": 80, "皮蛋瘦肉粥": 200,
    "炒饭": 500, "炒面": 450, "炒粉": 420, "汤面": 350, "捞面": 300,
    # 肉类
    "白切鸡": 280, "白切鸡饭": 550, "烧鸭": 350, "烧鸭饭": 600,
    "叉烧": 320, "叉烧饭": 580, "卤肉饭": 650, "鸡腿饭": 500,
    "宫保鸡丁": 380, "红烧肉": 500, "糖醋里脊": 450, "回锅肉": 480,
    "水煮肉片": 350, "鱼香肉丝": 320, "牛肉面": 500, "牛肉拉面": 480,
    "牛腩饭": 580, "排骨饭": 550,
    # 蔬菜类
    "炒时蔬": 80, "炒青菜": 70, "炒豆芽": 60, "拍黄瓜": 40,
    "番茄炒蛋": 180, "麻婆豆腐": 200, "清炒土豆丝": 150, "凉拌木耳": 60,
    # 汤类
    "紫菜蛋花汤": 50, "番茄蛋汤": 60, "冬瓜排骨汤": 120,
    "鸡汤": 100, "老火汤": 80,
    # 小吃/饮品
    "奶茶": 350, "果汁": 150, "可乐": 140, "矿泉水": 0,
    "烧饼": 250, "煎饼果子": 400, "肉夹馍": 350,
    # 广式经典
    "肠粉": 180, "虾饺": 150, "烧卖": 200, "凤爪": 180,
    "干炒牛河": 580, "煲仔饭": 600, "云吞面": 380, "及第粥": 250,
    "猪脚饭": 550, "豉汁排骨饭": 500, "腊味饭": 520,
}

# 预估卡路里 (菜名不在参考库时用这个)
DEFAULT_CALORIES = {
    "早餐": 350, "午餐": 550, "晚餐": 450, "正餐": 500, "小吃": 200
}


# ============================================================
# 数据管理
# ============================================================

def load_json(filename):
    """加载JSON数据文件"""
    path = DATA_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_json(filename, data):
    """保存JSON数据文件"""
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


# ============================================================
# LLM 调用
# ============================================================

def call_llm(system_prompt, user_prompt):
    """调用大模型API，失败时返回None"""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"],
        )
        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=LLM_CONFIG["temperature"],
            max_tokens=LLM_CONFIG["max_tokens"],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [提示] LLM调用失败: {e}")
        print(f"  [提示] 将使用离线规则引擎")
        return None


# ============================================================
# 用户画像
# ============================================================

DEFAULT_PROFILE = {
    "name": "",
    "height_cm": 170,
    "weight_kg": 65,
    "goal": "维持",  # 减脂 / 增肌 / 维持
    "budget_per_meal": 25,  # 每餐预算上限 (元)
    "allergies": [],  # 忌口 ["花生", "海鲜"]
    "preferences": [],  # 口味偏好 ["辣", "清淡", "粤菜"]
    "dislikes": [],  # 不喜欢 ["苦瓜", "芹菜"]
    "target_calories": 2000,  # 每日目标卡路里
    "schedule": {"早餐": "07:30", "午餐": "12:00", "晚餐": "18:30"},
}


def load_profile():
    """加载用户画像"""
    data = load_json("profile.json")
    if data is None:
        return DEFAULT_PROFILE.copy()
    # 补全缺失字段
    for k, v in DEFAULT_PROFILE.items():
        if k not in data:
            data[k] = v
    return data


def save_profile(profile):
    """保存用户画像"""
    save_json("profile.json", profile)
    print(f"  画像已保存 → {DATA_DIR / 'profile.json'}")


def calc_target_calories(height, weight, goal):
    """根据身高体重和目标估算每日目标卡路里"""
    bmr = 10 * weight + 6.25 * height - 5 * 20 + 5  # Mifflin-St Jeor (假设20岁男性)
    if goal == "减脂":
        return int(bmr * 1.2 - 300)
    elif goal == "增肌":
        return int(bmr * 1.2 + 300)
    else:
        return int(bmr * 1.2)


def cmd_profile_set():
    """交互式设置用户画像"""
    print("\n  === 设置你的饮食画像 ===\n")
    profile = load_profile()

    name = input(f"  你的名字 [{profile.get('name', '')}]: ").strip()
    if name:
        profile["name"] = name

    h = input(f"  身高(cm) [{profile.get('height_cm', 170)}]: ").strip()
    if h:
        profile["height_cm"] = int(h)

    w = input(f"  体重(kg) [{profile.get('weight_kg', 65)}]: ").strip()
    if w:
        profile["weight_kg"] = int(w)

    goal = input(f"  目标 减脂/增肌/维持 [{profile.get('goal', '维持')}]: ").strip()
    if goal:
        profile["goal"] = goal

    budget = input(f"  每餐预算上限(元) [{profile.get('budget_per_meal', 25)}]: ").strip()
    if budget:
        profile["budget_per_meal"] = int(budget)

    allergies = input(f"  忌口(逗号分隔) [{','.join(profile.get('allergies', []))}]: ").strip()
    if allergies:
        profile["allergies"] = [a.strip() for a in allergies.split(",") if a.strip()]

    prefs = input(f"  口味偏好(逗号分隔) [{','.join(profile.get('preferences', []))}]: ").strip()
    if prefs:
        profile["preferences"] = [p.strip() for p in prefs.split(",") if p.strip()]

    dislikes = input(f"  不喜欢吃的(逗号分隔) [{','.join(profile.get('dislikes', []))}]: ").strip()
    if dislikes:
        profile["dislikes"] = [d.strip() for d in dislikes.split(",") if d.strip()]

    profile["target_calories"] = calc_target_calories(
        profile["height_cm"], profile["weight_kg"], profile["goal"]
    )

    save_profile(profile)
    print(f"\n  [画像摘要]")
    print(f"  身高{profile['height_cm']}cm / 体重{profile['weight_kg']}kg")
    print(f"  目标: {profile['goal']}")
    print(f"  每日目标热量: {profile['target_calories']} kcal")
    print(f"  每餐预算: {profile['budget_per_meal']}元")
    if profile['allergies']:
        print(f"  忌口: {', '.join(profile['allergies'])}")
    if profile['preferences']:
        print(f"  偏好: {', '.join(profile['preferences'])}")
    if profile['dislikes']:
        print(f"  不吃: {', '.join(profile['dislikes'])}")


def cmd_profile_show():
    """查看用户画像"""
    profile = load_profile()
    print("\n  === 你的饮食画像 ===\n")
    print(f"  姓名: {profile.get('name', '未设置')}")
    print(f"  身高: {profile['height_cm']}cm")
    print(f"  体重: {profile['weight_kg']}kg")
    print(f"  目标: {profile['goal']}")
    print(f"  每日目标热量: {profile['target_calories']} kcal")
    print(f"  每餐预算: {profile['budget_per_meal']}元")
    print(f"  忌口: {', '.join(profile['allergies']) if profile['allergies'] else '无'}")
    print(f"  偏好: {', '.join(profile['preferences']) if profile['preferences'] else '无'}")
    print(f"  不吃: {', '.join(profile['dislikes']) if profile['dislikes'] else '无'}")


# ============================================================
# 店铺管理
# ============================================================

def load_shops():
    """加载店铺列表"""
    data = load_json("shops.json")
    return data if data else []


def save_shops(shops):
    """保存店铺列表"""
    save_json("shops.json", shops)


def cmd_shop_add():
    """添加店铺"""
    print("\n  === 添加店铺 ===\n")
    shops = load_shops()

    name = input("  店铺名称: ").strip()
    if not name:
        print("  [错误] 店铺名称不能为空")
        return

    category = input("  类别 (食堂/快餐/面馆/粤菜/川菜/小吃/其他): ").strip() or "其他"
    location = input("  位置 (如 一食堂二楼): ").strip() or ""
    notes = input("  备注 (如 排队久/外卖快): ").strip() or ""

    shop = {
        "id": len(shops) + 1,
        "name": name,
        "category": category,
        "location": location,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
    }
    shops.append(shop)
    save_shops(shops)
    print(f"  [OK] 已添加店铺: {name}")


def cmd_shop_list():
    """列出所有店铺"""
    shops = load_shops()
    if not shops:
        print("\n  还没有添加任何店铺，先执行 shop add")
        return

    print(f"\n  === 我的店铺 ({len(shops)}家) ===\n")
    for s in shops:
        loc = f" ({s['location']})" if s.get("location") else ""
        cat = f" [{s.get('category', '')}]" if s.get("category") else ""
        print(f"  #{s['id']} {s['name']}{cat}{loc}")
        if s.get("notes"):
            print(f"     备注: {s['notes']}")


# ============================================================
# 菜品管理
# ============================================================

def load_dishes():
    """加载菜品库"""
    data = load_json("dishes.json")
    return data if data else []


def save_dishes(dishes):
    """保存菜品库"""
    save_json("dishes.json", dishes)


def cmd_dish_add():
    """添加菜品"""
    shops = load_shops()
    if not shops:
        print("\n  [提示] 还没有店铺，请先添加店铺 (shop add)")
        return

    print("\n  === 添加菜品 ===\n")
    print("  已有哪些店铺:")
    for s in shops:
        print(f"    #{s['id']} {s['name']}")

    try:
        shop_id = int(input("\n  选择店铺编号: ").strip())
    except ValueError:
        print("  [错误] 请输入数字")
        return

    shop = next((s for s in shops if s["id"] == shop_id), None)
    if not shop:
        print(f"  [错误] 未找到编号为 {shop_id} 的店铺")
        return

    name = input("  菜名: ").strip()
    if not name:
        print("  [错误] 菜名不能为空")
        return

    try:
        price = float(input("  价格(元): ").strip())
    except ValueError:
        print("  [错误] 价格请输入数字")
        return

    try:
        rating = int(input("  好吃程度 (1-5星): ").strip())
        rating = max(1, min(5, rating))
    except ValueError:
        rating = 3

    meal_type = input("  适合哪餐 (早/午/晚, 逗号分隔, 留空=都适合): ").strip()
    if meal_type:
        meal_types = [m.strip() for m in meal_type.split(",")]
    else:
        meal_types = ["早", "午", "晚"]

    category = input("  菜品类别 (主食/肉菜/素菜/汤/小吃/饮品): ").strip() or "主食"
    notes = input("  备注 (如 分量大/偏咸/推荐加辣): ").strip() or ""

    # 尝试匹配卡路里
    cal_est = CALORIE_REF.get(name, DEFAULT_CALORIES.get(category, 450))

    dishes = load_dishes()
    dish = {
        "id": len(dishes) + 1,
        "shop_id": shop_id,
        "shop_name": shop["name"],
        "name": name,
        "price": price,
        "rating": rating,
        "meal_types": meal_types,
        "category": category,
        "notes": notes,
        "calories_est": cal_est,
        "created_at": datetime.now().isoformat(),
    }
    dishes.append(dish)
    save_dishes(dishes)
    print(f"  [OK] 已添加菜品: {shop['name']} - {name} (¥{price}, {rating}星)")


def cmd_dish_list():
    """列出所有菜品，按店铺分组"""
    dishes = load_dishes()
    shops = load_shops()
    if not dishes:
        print("\n  还没有添加任何菜品，先执行 dish add")
        return

    # 按店铺分组
    by_shop = {}
    for d in dishes:
        sid = d.get("shop_name", f"店铺#{d['shop_id']}")
        by_shop.setdefault(sid, []).append(d)

    print(f"\n  === 我的菜品库 ({len(dishes)}道) ===\n")
    for shop_name, items in by_shop.items():
        print(f"  [{shop_name}]")
        for d in items:
            stars = "★" * d["rating"] + "☆" * (5 - d["rating"])
            meals = "+".join(d.get("meal_types", ["早", "午", "晚"]))
            cal = d.get("calories_est", "?")
            print(f"    {d['name']}  ¥{d['price']}  {stars}  {meals}  ~{cal}kcal")
            if d.get("notes"):
                print(f"      → {d['notes']}")
        print()


# ============================================================
# 饮食记录
# ============================================================

def load_history():
    """加载饮食历史"""
    data = load_json("history.json")
    return data if data else {}


def save_history(history):
    """保存饮食历史"""
    save_json("history.json", history)


def cmd_log():
    """记录今天吃了什么"""
    dishes = load_dishes()
    if not dishes:
        print("\n  [提示] 还没有菜品，请先添加菜品 (dish add)")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    history = load_history()

    if today in history:
        print(f"\n  [提示] 今天({today})已有记录，想覆盖吗?")
        confirm = input("  输入 y 继续录入: ").strip().lower()
        if confirm != "y":
            return

    print(f"\n  === 记录今日饮食 ({today}) ===\n")

    meals = {}
    for meal_type in ["早餐", "午餐", "晚餐"]:
        print(f"\n  --- {meal_type} ---")
        print("  可选菜品:")
        for d in dishes:
            print(f"    #{d['id']} {d['shop_name']} - {d['name']}  ¥{d['price']}")

        chosen = []
        while True:
            sel = input(f"  选菜品编号 (多个用逗号分隔, 跳过直接回车): ").strip()
            if not sel:
                break
            try:
                ids = [int(x.strip()) for x in sel.split(",")]
                for did in ids:
                    dish = next((d for d in dishes if d["id"] == did), None)
                    if dish:
                        chosen.append(dish["id"])
                        print(f"    已选: {dish['shop_name']} - {dish['name']} (¥{dish['price']})")
                    else:
                        print(f"    未找到编号 {did}")
            except ValueError:
                print("    请输入数字编号")
            add_more = input(f"  还加菜吗? (y/n): ").strip().lower()
            if add_more != "y":
                break

        meals[meal_type] = chosen

    # 计算统计 + 自评好吃程度
    total_cal = 0
    total_cost = 0
    taste_ratings = {}  # {dish_id: rating 1-5}

    print("\n  === 自评好吃程度 (1=踩雷 5=超好吃) ===")
    all_dish_ids = []
    for meal_type, dish_ids in meals.items():
        for did in dish_ids:
            if did not in taste_ratings:
                all_dish_ids.append(did)
                d = next((di for di in dishes if di["id"] == did), None)
                if d:
                    total_cal += d.get("calories_est", 450)
                    total_cost += d["price"]

    for did in all_dish_ids:
        d = next((di for di in dishes if di["id"] == did), None)
        if d:
            while True:
                rating = input(f"  {d['shop_name']} - {d['name']} 好吃吗? (1-5, 回车=跳过): ").strip()
                if not rating:
                    break
                try:
                    r = int(rating)
                    if 1 <= r <= 5:
                        taste_ratings[str(did)] = r
                        break
                    print("    请输入1-5之间的数字")
                except ValueError:
                    print("    请输入数字")

    profile = load_profile()

    history[today] = {
        "meals": meals,
        "total_calories": total_cal,
        "total_cost": total_cost,
        "taste_ratings": taste_ratings,
        "recorded_at": datetime.now().isoformat(),
    }
    save_history(history)

    print(f"\n  === 今日总结 ===")
    print(f"  总消耗: {total_cal} kcal (目标 {profile['target_calories']})")
    print(f"  总花费: {total_cost} 元")

    diff = total_cal - profile["target_calories"]
    if diff > 200:
        print(f"  [提醒] 今天超标 {diff} kcal，明天可以控制一下")
    elif diff < -200:
        print(f"  [提醒] 今天差了 {-diff} kcal，注意别吃太少")
    else:
        print(f"  热量在合理范围内 ✓")

    # AI评估
    print("\n  [AI营养评估]")
    ai_result = ai_evaluate_today(profile, history, today, dishes)
    print(ai_result)


def cmd_log_today():
    """查看今天的饮食记录"""
    today = datetime.now().strftime("%Y-%m-%d")
    history = load_history()
    dishes = load_dishes()

    if today not in history:
        print(f"\n  今天({today})还没有饮食记录")
        return

    record = history[today]
    print(f"\n  === 今日饮食记录 ({today}) ===\n")

    for meal_type in ["早餐", "午餐", "晚餐"]:
        dish_ids = record["meals"].get(meal_type, [])
        if dish_ids:
            print(f"  [{meal_type}]")
            for did in dish_ids:
                d = next((d for d in dishes if d["id"] == did), None)
                if d:
                    taste = record.get("taste_ratings", {}).get(str(did), "")
                    taste_str = f" ★{taste}" if taste else ""
                    print(f"    {d['shop_name']} - {d['name']}  ¥{d['price']}{taste_str}")
        else:
            print(f"  [{meal_type}] 未记录")

    print(f"\n  总热量: {record.get('total_calories', '?')} kcal")
    print(f"  总花费: {record.get('total_cost', '?')} 元")


# ============================================================
# AI智能推荐 (核心)
# ============================================================

def build_recommendation_context(profile, history, dishes):
    """构建推荐所需的上下文"""
    today = datetime.now()
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    weekday = (today + timedelta(days=1)).strftime("%A")
    weekday_cn = {"Monday": "周一", "Tuesday": "周二", "Wednesday": "周三",
                   "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日"}
    weekday_name = weekday_cn.get(weekday, weekday)

    # 过去7天的饮食记录
    recent_days = []
    for i in range(1, 8):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if day in history:
            recent_days.append((day, history[day]))

    # 最近吃过的菜品ID
    recent_dish_ids = []
    for day_str, record in (recent_days[:3]):  # 最近3天
        for meal_type, dish_ids in record.get("meals", {}).items():
            recent_dish_ids.extend(dish_ids)

    # 统计各菜品出现频率 + 自评口味均值
    dish_freq = {}
    dish_taste = {}  # {dish_id: [ratings]}
    for day_str, record in recent_days:
        taste_ratings = record.get("taste_ratings", {})
        for meal_type, dish_ids in record.get("meals", {}).items():
            for did in dish_ids:
                dish_freq[did] = dish_freq.get(did, 0) + 1
                if str(did) in taste_ratings:
                    dish_taste.setdefault(did, []).append(taste_ratings[str(did)])

    # 计算自评均值
    dish_taste_avg = {}
    for did, ratings in dish_taste.items():
        dish_taste_avg[did] = round(sum(ratings) / len(ratings), 1)

    # 格式化菜品列表
    dish_list = []
    for d in dishes:
        freq = dish_freq.get(d["id"], 0)
        recently_eaten = "最近吃过" if d["id"] in recent_dish_ids else ""
        meal_labels = "+".join(d.get("meal_types", ["午", "晚"]))
        stars = "★" * d["rating"]
        dish_list.append({
            "id": d["id"],
            "shop": d.get("shop_name", ""),
            "name": d["name"],
            "price": d["price"],
            "rating": d["rating"],
            "stars": stars,
            "category": d.get("category", ""),
            "calories": d.get("calories_est", "?"),
            "notes": d.get("notes", ""),
            "meal_types": meal_labels,
            "freq_7d": freq,
            "recently_eaten": bool(recently_eaten),
        })

    # 过去7天平均热量
    recent_cals = [r.get("total_calories", profile["target_calories"])
                   for _, r in recent_days]
    avg_recent_cal = int(sum(recent_cals) / len(recent_cals)) if recent_cals else profile["target_calories"]

    context = {
        "tomorrow": tomorrow,
        "weekday": weekday_name,
        "profile": {
            "goal": profile["goal"],
            "budget_per_meal": profile["budget_per_meal"],
            "target_calories": profile["target_calories"],
            "allergies": profile["allergies"],
            "preferences": profile["preferences"],
            "dislikes": profile["dislikes"],
        },
        "dishes": dish_list,
        "recent_7d_avg_cal": avg_recent_cal,
        "recent_dish_ids": recent_dish_ids,
        "dish_freq_7d": dish_freq,
        "dish_taste_avg": dish_taste_avg,  # 自评口味均值
    }
    return context


def ai_recommend(profile, history, dishes):
    """AI核心推荐：调用大模型生成明日三餐推荐"""
    ctx = build_recommendation_context(profile, history, dishes)

    if not ctx["dishes"]:
        return "  [提示] 菜品库为空，请先用 dish add 添加一些菜品"

    # 构建Prompt
    system_prompt = """你是一位专业的营养师，也是了解用户口味的饮食管家。

你的任务是：根据用户的画像、饮食历史和菜品库，推荐明日三餐。

规则：
1. 必须只从菜品库中选择，不允许推荐没有的菜
2. 考虑过去7天的饮食，避免连续吃同样的菜
3. 结合用户目标(减脂/增肌/维持)调节热量
4. 每餐控制在用户预算之内
5. 避开用户忌口和不喜欢的食材
6. 尽量保证营养均衡(碳水、蛋白质、蔬菜搭配)
7. 优先推荐用户评分高的菜，尤其注意"自评"口味分——这是用户亲自吃过后给出的评价，比初始星级更可靠
8. 早餐推荐适合早餐的菜(meal_types含"早")

输出格式要求(严格遵循)：
```
[明日推荐]
  早餐: [店名] - [菜名] (¥价格)
  理由: [一句话理由，说明为什么选这个]
  午餐: [店名] - [菜名] + [菜名] (¥总价)
  理由: [一句话理由]
  晚餐: [店名] - [菜名] (¥价格)
  理由: [一句话理由]
  全天消费: ¥总价 (预算内✓/超预算⚠)
  营养评估: [一句话营养搭配评价]
```"""

    user_prompt = f"""明日日期: {ctx['tomorrow']} ({ctx['weekday']})

=== 用户画像 ===
目标: {ctx['profile']['goal']}
每日目标热量: {ctx['profile']['target_calories']} kcal
每餐预算: {ctx['profile']['budget_per_meal']}元
忌口: {', '.join(ctx['profile']['allergies']) if ctx['profile']['allergies'] else '无'}
口味偏好: {', '.join(ctx['profile']['preferences']) if ctx['profile']['preferences'] else '无'}
不喜欢: {', '.join(ctx['profile']['dislikes']) if ctx['profile']['dislikes'] else '无'}
最近7天平均摄入: {ctx['recent_7d_avg_cal']} kcal

=== 菜品库 ===
"""
    for d in ctx["dishes"]:
        eaten = " [最近吃过]" if d["recently_eaten"] else ""
        freq_info = f" (7天吃了{d['freq_7d']}次)" if d["freq_7d"] > 0 else ""
        taste_info = ""
        if d["id"] in ctx.get("dish_taste_avg", {}):
            taste_info = f" [自评★{ctx['dish_taste_avg'][d['id']]}]"
        user_prompt += f"#{d['id']} [{d['shop']}] {d['name']} ¥{d['price']} {d['stars']} {d['meal_types']} ~{d['calories']}kcal [{d['category']}]{eaten}{freq_info}{taste_info}\n"
        if d["notes"]:
            user_prompt += f"  备注: {d['notes']}\n"

    user_prompt += f"""
=== 过去3天饮食 ===
"""
    for i in range(1, 4):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        if day in history:
            record = history[day]
            user_prompt += f"{day}: "
            items = []
            for meal_type in ["早餐", "午餐", "晚餐"]:
                for did in record["meals"].get(meal_type, []):
                    d = next((x for x in dishes if x["id"] == did), None)
                    if d:
                        items.append(f"[{meal_type}]{d['name']}")
            user_prompt += ", ".join(items) + f" (共{record.get('total_calories','?')}kcal ¥{record.get('total_cost','?')})\n"

    user_prompt += """
请为我推荐明天的三餐，严格从菜品库中选择。"""

    return call_llm(system_prompt, user_prompt)


def offline_recommend(profile, history, dishes):
    """离线规则引擎推荐 (不依赖LLM)"""
    ctx = build_recommendation_context(profile, history, dishes)

    if not ctx["dishes"]:
        return "  [提示] 菜品库为空"

    # 按餐别分组
    breakfast = [d for d in ctx["dishes"] if "早" in d["meal_types"]]
    lunch_dinner = [d for d in ctx["dishes"] if "午" in d["meal_types"] or "晚" in d["meal_types"]]

    # 过滤：排除最近吃过的
    recent = set(ctx["recent_dish_ids"])
    fresh_bf = [d for d in breakfast if d["id"] not in recent]
    fresh_ld = [d for d in lunch_dinner if d["id"] not in recent]

    # 如果没有新鲜的，用全部
    if not fresh_bf:
        fresh_bf = breakfast
    if not fresh_ld:
        fresh_ld = lunch_dinner

    # 按评分排序（含自评口味加成）
    taste_avg = ctx.get("dish_taste_avg", {})
    def sort_by_rating(lst):
        # 综合分 = 初始评分 + 自评口味加成（自评5星加0.5, 1星减0.5）
        for d in lst:
            ta = taste_avg.get(d["id"], 0)
            if ta:
                d["composite_score"] = d["rating"] + (ta - 3) * 0.25
            else:
                d["composite_score"] = d["rating"]
        return sorted(lst, key=lambda x: (-x["composite_score"], x["price"]))

    sorted_bf = sort_by_rating(fresh_bf)
    sorted_ld = sort_by_rating(fresh_ld)

    result = "\n  === [明日推荐] (离线规则引擎) ===\n"

    budget = profile["budget_per_meal"]

    # 早餐
    if sorted_bf:
        pick = sorted_bf[0]
        result += f"\n  早餐: {pick['shop']} - {pick['name']} (¥{pick['price']})\n"
        result += f"  理由: 评分{pick['stars']}，适合早餐，预算以内 ✓\n"
        bf_cost = pick["price"]
        bf_cal = pick["calories"]
    else:
        result += "\n  早餐: 暂无适合早餐的菜品\n"
        bf_cost = 0
        bf_cal = 0

    # 午餐
    lunch_pick = sorted_ld[0] if sorted_ld else None
    # 尝试搭配一个蔬菜
    veg_dishes = [d for d in lunch_dinner if d.get("category") == "素菜" and d["id"] != (lunch_pick["id"] if lunch_pick else -1)]
    veg_pick = None
    if veg_dishes and lunch_pick:
        veg_pick = sorted(veg_dishes, key=lambda x: x["price"])[0]
        if veg_pick["id"] == lunch_pick["id"]:
            veg_pick = None

    if lunch_pick:
        if veg_pick:
            result += f"\n  午餐: {lunch_pick['shop']} - {lunch_pick['name']} + {veg_pick['shop']} - {veg_pick['name']} (¥{lunch_pick['price']+veg_pick['price']})\n"
            result += f"  理由: {lunch_pick['name']}{lunch_pick['stars']}搭配蔬菜，营养均衡\n"
            lunch_cost = lunch_pick["price"] + veg_pick["price"]
            lunch_cal = lunch_pick["calories"] + veg_pick["calories"]
        else:
            result += f"\n  午餐: {lunch_pick['shop']} - {lunch_pick['name']} (¥{lunch_pick['price']})\n"
            result += f"  理由: 评分高的菜品，建议搭配蔬菜(未找到合适菜品)\n"
            lunch_cost = lunch_pick["price"]
            lunch_cal = lunch_pick["calories"]
    else:
        result += "\n  午餐: 暂无合适菜品\n"
        lunch_cost = 0
        lunch_cal = 0

    # 晚餐 (选不同的菜)
    dinner_candidates = [d for d in sorted_ld if d["id"] != (lunch_pick["id"] if lunch_pick else -1)]
    if not dinner_candidates:
        dinner_candidates = sorted_ld

    if dinner_candidates:
        dinner_pick = dinner_candidates[0]
        result += f"\n  晚餐: {dinner_pick['shop']} - {dinner_pick['name']} (¥{dinner_pick['price']})\n"
        result += f"  理由: 与午餐不同的选择，评分{dinner_pick['stars']}\n"
        dinner_cost = dinner_pick["price"]
        dinner_cal = dinner_pick["calories"]
    else:
        result += "\n  晚餐: 暂无合适菜品\n"
        dinner_cost = 0
        dinner_cal = 0

    total_cost = bf_cost + lunch_cost + dinner_cost
    total_cal = bf_cal + lunch_cal + dinner_cal

    result += f"\n  全天消费: ¥{total_cost} "
    result += "(预算内 ✓)" if total_cost <= budget * 3 else "(超预算 ⚠)"
    result += f"\n  全天热量估算: {total_cal} kcal (目标 {profile['target_calories']})"

    if total_cal > profile["target_calories"] + 200:
        result += "\n  营养评估: 热量偏高，可考虑减少份量"
    elif total_cal < profile["target_calories"] - 200:
        result += "\n  营养评估: 热量偏低，可考虑加点小吃"
    else:
        result += "\n  营养评估: 热量在合理范围 ✓"

    result += "\n  [提示] 规则引擎推荐较简单，配置LLM可获得更智能的推荐\n"
    return result


def ai_evaluate_today(profile, history, today, dishes):
    """AI评估今日饮食"""
    if today not in history:
        return "  暂无今日记录"

    record = history[today]

    # 构建当日记要
    items = []
    for meal_type in ["早餐", "午餐", "晚餐"]:
        for did in record["meals"].get(meal_type, []):
            d = next((x for x in dishes if x["id"] == did), None)
            if d:
                items.append(f"[{meal_type}] {d['shop_name']} - {d['name']} ¥{d['price']} ~{d.get('calories_est','?')}kcal")

    system_prompt = "你是营养师，简洁评估一日饮食，2-3句话即可。"
    user_prompt = f"""今日饮食:
{chr(10).join(items)}
总热量: {record['total_calories']} kcal
目标热量: {profile['target_calories']} kcal
用户目标: {profile['goal']}

请用2-3句话评估：
1. 热量是否达标
2. 营养是否均衡
3. 明天应该怎么调整"""

    ai = call_llm(system_prompt, user_prompt)
    if ai:
        return f"  {ai}"
    else:
        return offline_evaluate_today(profile, record)


def offline_evaluate_today(profile, record):
    """离线评估今日饮食"""
    diff = record["total_calories"] - profile["target_calories"]
    if diff > 200:
        return f"  今天热量偏高超标{diff}kcal，明天建议减少份量或多选蔬菜类菜品。"
    elif diff < -200:
        return f"  今天热量偏低{-diff}kcal，明天可以适当加餐或选热量更高的主食。"
    else:
        return "  今日热量摄入在合理范围，继续保持！注意荤素搭配。" if record["total_calories"] > 0 else ""


def cmd_recommend(offline=False):
    """执行推荐"""
    profile = load_profile()
    history = load_history()
    dishes = load_dishes()

    if not dishes:
        print("\n  [提示] 菜品库为空，先用 dish add 添加一些店铺和菜品")
        return

    print("\n  正在生成推荐...\n")

    if offline:
        result = offline_recommend(profile, history, dishes)
    else:
        result = ai_recommend(profile, history, dishes)
        if result is None:
            result = offline_recommend(profile, history, dishes)

    print(result)


# ============================================================
# 命令行入口
# ============================================================

def print_usage():
    print("""
AI饮食管家 (Meal Planner) v1.0

Usage:
  python meal_planner.py profile set    设置用户画像
  python meal_planner.py profile show   查看用户画像
  python meal_planner.py shop add       添加店铺
  python meal_planner.py shop list      列出所有店铺
  python meal_planner.py dish add       为店铺添加菜品
  python meal_planner.py dish list      列出所有菜品
  python meal_planner.py log            记录今天吃了什么
  python meal_planner.py log today      查看今天饮食记录
  python meal_planner.py recommend      AI推荐明日三餐
  python meal_planner.py recommend --offline  离线推荐
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    cmd = sys.argv[1]

    if cmd == "profile":
        sub = sys.argv[2] if len(sys.argv) > 2 else "show"
        if sub == "set":
            cmd_profile_set()
        else:
            cmd_profile_show()

    elif cmd == "shop":
        sub = sys.argv[2] if len(sys.argv) > 2 else "list"
        if sub == "add":
            cmd_shop_add()
        else:
            cmd_shop_list()

    elif cmd == "dish":
        sub = sys.argv[2] if len(sys.argv) > 2 else "list"
        if sub == "add":
            cmd_dish_add()
        else:
            cmd_dish_list()

    elif cmd == "log":
        sub = sys.argv[2] if len(sys.argv) > 2 else "add"
        if sub == "today":
            cmd_log_today()
        else:
            cmd_log()

    elif cmd == "recommend":
        offline = "--offline" in sys.argv
        cmd_recommend(offline=offline)

    else:
        print_usage()


if __name__ == "__main__":
    main()
