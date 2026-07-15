# AI饮食管家 迭代升级说明

## 迭代总览

按照5步迭代法，以下3个升级方向均来源于真实使用中发现的痛点，不是凭空设想。

---

## 迭代1: 智能推荐理由引擎

### Step1 描述具体痛点
离线规则引擎推荐时只给"评分4星 价格12元"这样的冷冰冰数据，用户看不懂"为什么推荐牛肉面而不是煲仔饭"。缺少决策透明度让人不信任推荐结果，最终还是要自己翻菜单。

### Step2 量化影响
- 每次推荐后我需要额外花30-60秒思考"到底选不选这个"
- 6天测试中，有3天看了推荐后手动改了选择
- 对推荐系统的信任度从"跟着走"变成了"仅供参考"

### Step3 假设原因
- 提示词问题：离线模式下根本没有生成理由的逻辑
- 数据结构问题：没有存储"为什么选这个"的上下文信息
- 交互问题：推荐只是输出结果，没有解释过程

### Step4 指挥AI/自己改代码实现
核心改动：为离线推荐增加理由生成逻辑

```python
def generate_reason(dish, profile, history, meal_type):
    """生成人性化的推荐理由"""
    reasons = []
    
    # 评分维度
    if dish["rating"] >= 5:
        reasons.append("你给过5星")
    elif dish["rating"] >= 4:
        reasons.append("评价不错")
    
    # 时间维度 (通过history判断)
    days_since = get_days_since_last_eaten(dish["id"], history)
    if days_since > 3:
        reasons.append(f"{days_since}天没吃了")
    elif days_since == 0:
        reasons.append("今天还没吃过类似的")
    
    # 营养维度
    if meal_type == "早餐" and dish.get("category") in ["主食"]:
        reasons.append("早上需要碳水撑到中午")
    if dish.get("category") in ["素菜"]:
        reasons.append("补充蔬菜均衡营养")
    if dish.get("category") in ["汤"]:
        reasons.append("吃点带汤的暖胃")
    
    # 预算维度
    budget = profile["budget_per_meal"]
    if dish["price"] <= budget * 0.5:
        reasons.append(f"才¥{dish['price']}，预算充裕")
    elif dish["price"] <= budget:
        reasons.append("在预算内")
    else:
        reasons.append(f"小超预算但值得")
    
    return "，".join(reasons) + "。"
```

### Step5 评估效果
- 推荐结果包含决策理由，用户无需额外思考时间 ✓
- 对推荐信任度从"仅供参考"提升到"看理由能接受" ✓
- 引入新问题: 理由有时过于模板化，缺少个性化 — 将在迭代3中解决

---

## 迭代2: 场景化加餐推荐

### Step1 描述具体痛点
系统只有三餐推荐，但现实中经常需要下午加餐或夜宵。场景举例：
- 上午有体育课 → 中午特别饿，想多吃
- 下午上课到6点 → 晚饭前需要垫一下
- 晚上自习到11点 → 回宿舍想吃夜宵
- 周末睡到10点 → 早餐和午餐合并成brunch

### Step2 量化影响
- 6天测试中，有4天实际吃了加餐（水果/面包/夜宵），但系统完全没有追踪
- 有2天因为体育课中午多吃了一个菜，热量评估不准
- 周末作息变化导致推荐完全失效

### Step3 假设原因
- 数据结构问题: 餐别只有"早午晚"三种，不支持"加餐"和"夜宵"
- 交互问题: 录入时没有询问"今天有没有特殊情况"
- 功能缺失: 没有周末模式和活动日模式

### Step4 指挥AI/自己改代码实现
核心改动：
1. 扩展meal_types支持 "加餐" 和 "夜宵"
2. 在 `cmd_log()` 开头询问"今天有没有特殊情况"
3. 在推荐时支持场景选择: 正常日 / 运动日 / 周末

```python
# 场景提示
scene_prompts = {
    "正常日": "正常作息，7:30起床，12:00午餐，18:30晚餐",
    "运动日": "上午/下午有体育活动，中午多吃，下午需要加餐",
    "周末": "睡到自然醒，早餐晚吃或跳过，午晚正常",
}

def cmd_log():
    # ... 现有代码 ...
    scene = input("今天什么日子? (正常日/运动日/周末): ").strip() or "正常日"
    # 根据场景调整后续录入流程
```

### Step5 评估效果
- 热量统计更准确，运动日和周末的热量偏差从±300降到±100 ✓
- 添加夜宵/加餐选项解决了"吃完晚饭又饿了但没记录"的问题 ✓
- 引入新问题: 场景选择需要用户主动判断，容易忘记 — 未来可接入课表自动判断

---

## 迭代3: 个性化学习 + LLM强化

### Step1 描述具体痛点
系统学习能力不足——虽然记录了6天数据，但推荐没有越来越懂我。具体表现：
- 我给白切鸡饭评了5星且反复点它，但系统不知道主动推荐它
- 我吃过一次红烧肉(3星)后再没点过，系统没学到"我不太喜欢这个"
- 某些店我连续去但某些店一周才去一次，系统没识别"常去/偶尔去"模式
- 离线规则引擎始终是机械的"评分排序+排除近3天"，没有任何学习曲线

### Step2 量化影响
- 系统给白切鸡饭的推荐优先级和番茄炒蛋一样（都是按评分排），但我点白切鸡的频率是番茄炒蛋的3倍
- 6天中3天手动改了推荐，其中2次是把"不常吃的菜"换成"常吃的菜"
- 对推荐结果的满意度约为60%（6天中4天没完全采纳）

### Step3 假设原因
- 算法问题: 推荐权重仅依赖静态的rating字段，没有动态的"偏好权重"
- 数据利用不足: history.json记录了饮食数据，但推荐算法没有用这些数据来调整偏好
- LLM未接入: 理论上LLM可以分析"为什么你喜欢白切鸡饭""你的饮食模式是什么"，但离线引擎做不到

### Step4 指挥AI/自己改代码实现

核心改动：
1. 从history中计算动态偏好权重
2. 推荐时综合考虑 原始评分 + 频率权重 + 时间衰减 + 多样性
3. 接入LLM后，把完整的7天history送给模型做深度分析

```python
def calc_preference_weights(history, dishes):
    """从历史记录中学习用户实际偏好"""
    dish_scores = {}
    for day, record in history.items():
        for meal_type, dish_ids in record["meals"].items():
            for did in dish_ids:
                if did not in dish_scores:
                    dish_scores[did] = {"count": 0, "days": set()}
                dish_scores[did]["count"] += 1
                dish_scores[did]["days"].add(day)
    
    weights = {}
    for did, info in dish_scores.items():
        dish = next((d for d in dishes if d["id"] == did), None)
        if not dish:
            continue
        static_rating = dish["rating"]
        frequency = info["count"]  # 吃的次数
        days_span = len(info["days"])  # 在几天内吃过
        # 综合分数 = 静态评分 + 频率加成 + 多样性惩罚
        final_score = static_rating + min(frequency * 0.3, 1.0)
        if days_span > 3:
            final_score += 0.2  # 分散在多天的说明是真爱
        weights[did] = round(final_score, 1)
    
    return weights

def smart_recommend(profile, history, dishes):
    """基于学习权重的智能推荐"""
    weights = calc_preference_weights(history, dishes)
    
    scored_dishes = []
    for d in dishes:
        base = d["rating"]
        learn_bonus = weights.get(d["id"], 0) - base
        penalty = 0
        # 最近3天吃过？惩罚
        if d["id"] in get_recent_ids(history, days=3):
            penalty -= 1.5
        # 忌口？惩罚
        if any(allergy.lower() in d["name"].lower() for allergy in profile["allergies"]):
            penalty -= 5
        
        final_score = base + learn_bonus * 0.5 + penalty
        scored_dishes.append({**d, "score": final_score})
    
    return sorted(scored_dishes, key=lambda x: -x["score"])
```

LLM深度分析 Prompt：

```
你是用户的个人饮食分析师。以下是用户过去7天的完整饮食记录：
[history_detail]

请分析：
1. 用户的饮食偏好模式（常去的店、常点的菜、口味倾向）
2. 营养缺口（缺什么类型的营养）
3. 可优化的习惯（比如某天热量过高或过低的原因）
4. 基于以上分析，推荐明日三餐及其理由
```

### Step5 评估效果
- 推荐结果中高频率菜品排名提升，白切鸡饭明显排在前面 ✓
- 用户对推荐采纳率从60%提升到约80% ✓
- 引入新问题: 算法可能陷入"越推荐越吃、越吃越推荐"的正反馈循环 — 需要加入强制性多样性机制

---

## 后续规划

| 迭代 | 方向 | 状态 | 核心AI价值 |
|------|------|------|-----------|
| 1: 智能推荐理由 | 增强决策透明度 | 已完成 | 无 |
| 2: 场景化加餐 | 支持运动日/周末/加餐 | 已完成 | 无 |
| 3: 个性化学习 | 从历史中学习偏好 | 已完成 | **核心** — 没有AI无法动态学习 |
| 4: 地址搜店初始化 | 输入地址自动搜索周边餐饮，减少手动录入 | 规划中 | AI辅助数据采集 |
| 5: 多人共享菜库 | 宿舍/班级一起用，互相推荐 | 规划中 | AI发现群组饮食模式 |
| 6: 语音录入 | "吃过了"一句话完成记录 | 规划中 | 语音转文字→AI提取菜品信息 |
| 7: 自动对接课表 | 根据课表预判明天在哪里吃 | 规划中 | 结合时间地点优化推荐 |

---

## 迭代4: 地址搜店初始化 (真实使用中发现)

### Step1 描述具体痛点
录入3家店9道菜已经觉得麻烦——每家店要打字输入店名、位置、类别。到了新环境（实习/搬校区），周边几十家店全部手动录入完全不现实。首次建立菜品库的阻力是整个系统最大的使用门槛。

### Step2 量化影响
- 3家店手动录入约2分钟，预期扩展到10家店需要5-8分钟
- 换环境后从零录入30+家店，用户大概率放弃
- 这是"第一次打开"的体验瓶颈

### Step3 假设原因
- 数据来源问题：用户要知道店名才能录，但新环境不知道有什么店
- 交互问题：逐条录入是线性流程，应该有批量化方式
- 信息获取：地图/外卖平台已经有现成的店铺数据，没必要重新打字

### Step4 实现方案

```
初始化流程:
1. 询问用户地址（学校/小区/路口）
2. 调用高德地图"地理编码"API → 经纬度
3. 调用"周边搜索"API，关键词"餐饮"，半径1000m
4. 返回店铺列表（店名、地址、类别、评分）
5. 展示列表让用户勾选要导入的店铺
6. 批量写入 shops.json
7. 提示用户：菜品信息仍需自己补充
```

技术栈：高德地图 Web API（个人开发者免费额度5000次/天，完全够用）

局限：地图API有店铺信息但没有菜单，菜品仍需人工录入。如果结合美团/饿了么公开数据可部分解决，但有合规风险。

### Step5 预期效果
- 首次建立店铺库从"逐条打字"变成"勾选导入"，时间从分钟级降到秒级 ✓
- 引入新问题：地图数据可能过时（店铺已关门），需要用户验证环节
- 菜品录入仍然是手工的——这是下一步要解决的问题（OCR菜单识别）
