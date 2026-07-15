# AI饮食管家 迭代升级说明 (Iteration Log)

> 符合提交说明要求：iteration/iteration_log.md
> 至少3个迭代方向，含5步迭代法

## 已完成的迭代 (3个)

---

### 迭代1: 智能推荐理由引擎

#### Step1 描述具体痛点
离线规则引擎推荐时只给"评分4星 价格12元"这样的冷冰冰数据，用户看不懂"为什么推荐牛肉面而不是煲仔饭"。缺少决策透明度让人不信任推荐结果，最终还是要自己翻菜单。

#### Step2 量化影响
- 每次推荐后我需要额外花30-60秒思考"到底选不选这个"
- 6天测试中，有3天看了推荐后手动改了选择
- 对推荐系统的信任度从"跟着走"变成了"仅供参考"

#### Step3 假设原因
- 提示词问题：离线模式下根本没有生成理由的逻辑
- 数据结构问题：没有存储"为什么选这个"的上下文信息
- 交互问题：推荐只是输出结果，没有解释过程

#### Step4 指挥AI/自己改代码实现
核心改动: 为离线推荐增加理由生成逻辑

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
    # 营养维度
    if meal_type == "早餐" and dish.get("category") == "主食":
        reasons.append("早上需要碳水撑到中午")
    if dish.get("category") == "素菜":
        reasons.append("补充蔬菜均衡营养")
    # 预算维度
    budget = profile["budget_per_meal"]
    if dish["price"] <= budget * 0.5:
        reasons.append(f"才¥{dish['price']}，预算充裕")
    return "，".join(reasons) + "。"
```

AI推荐路径: 在 `ai_recommend` 提示词中明确要求模型输出"理由: [一句话理由]"

#### Step5 评估效果
- 推荐结果包含决策理由，用户无需额外思考时间 ✓
- 对推荐信任度从"仅供参考"提升到"看理由能接受" ✓
- 引入新问题: 理由有时过于模板化，缺少个性化 — 由迭代3 (个性化学习) 解决

---

### 迭代2: 自评好吃程度 (核心AI价值)

#### Step1 描述具体痛点
系统对每道菜只有一个静态星级，但用户的真实口味会变——给5星的白切鸡可能吃腻了给3星，给3星的红烧肉可能后来很爱吃。静态星级无法捕捉这种动态变化，导致推荐越来越不准。

#### Step2 量化影响
- 6天使用中至少有3次"评分高的菜吃着没感觉，评分低的菜发现真好吃"
- 离线规则引擎排序不变，用户信任度降低
- 没有任何机制让系统学习用户的真实反馈

#### Step3 假设原因
- 数据结构问题: history.json只记录吃了什么，没记录好不好吃
- 交互问题: 没有"好吃吗？"的提问环节
- 算法问题: 推荐只用静态rating，没用真实吃后评价

#### Step4 指挥AI/自己改代码实现

代码改动1: `cmd_log` 增加自评交互
```python
print("  === 自评好吃程度 (1=踩雷 5=超好吃) ===")
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
            except ValueError:
                pass
```

代码改动2: history数据扩展
```python
history[today] = {
    "meals": meals,
    "taste_ratings": taste_ratings,  # 新增字段
    ...
}
```

代码改动3: 推荐算法综合分
```python
def sort_by_rating(lst):
    for d in lst:
        ta = taste_avg.get(d["id"], 0)
        if ta:
            d["composite_score"] = d["rating"] + (ta - 3) * 0.25
        else:
            d["composite_score"] = d["rating"]
    return sorted(lst, key=lambda x: (-x["composite_score"], x["price"]))
```

代码改动4: AI推荐告知自评
```python
taste_info = f" [自评★{ctx['dish_taste_avg'][d['id']]}]" if d["id"] in ctx.get("dish_taste_avg", {}) else ""
```

#### Step5 评估效果
- 自评分纳入排序，自评5星菜排名提升明显 ✓
- AI知道"自评比初始星级更可靠"（提示词中明示）✓
- 引入新问题: 需要更多天的数据才能形成稳定的学习模型 — 需要坚持记录

**核心AI价值体现**: 用户的口味偏好是动态的，没有AI的语义理解，自评这种模糊信号（4星比3星多0.25的差值合理吗？）无法被精确使用。规则引擎只能用固定阈值，AI能根据上下文调整。

---

### 迭代3: 单店搭配约束 (痛点#7修复)

#### Step1 描述具体痛点
推荐时给方案"压3饭馆 辣子鸡 + 食堂一楼 青菜"，单看每道菜都没问题，但实际要去两家店才能吃完。压3饭馆没有青菜，食堂一楼才有。这是不切实际的推荐。

#### Step2 量化影响
- 1次推荐就是D方案"压3 辣子鸡+食堂 青菜"，用户直接指出问题
- 跨店搭配如果没被发现，会导致用户走冤枉路
- 体验上：推荐不实用 = 信任度下降

#### Step3 假设原因
- 推荐引擎只考虑菜品列表，不考虑店铺分类边界
- 离线版本没有"按店聚合"的逻辑
- LLM版本如果不显式约束也会犯同样错

#### Step4 指挥AI/自己改代码实现
改动1: 离线引擎 — 把"选青菜"操作限制在当前选店
```python
# 之前: veg_dishes = [d for d in lunch_dinner if d.get("category") == "素菜"]
# 之后: veg_dishes = [d for d in lunch_dinner if d.get("category") == "素菜" and d["shop_id"] == lunch_pick["shop_id"]]
```

改动2: AI提示词增加约束
```
规则追加:
9. 同一餐的所有菜必须来自同一家店，不允许跨店混搭
```

#### Step5 评估效果
- 推荐方案自动按"同店搭配"重组 ✓
- 修正后D方案: 压3饭馆 辣子鸡+煎蛋(同店) ✓
- 修正后E方案: 压3饭馆 口水鸡+煎蛋(同店) ✓
- 用户反馈"压3哪里有青菜？"被识别为有效痛点并修复

---

## 规划中的迭代方向 (2个)

### 迭代4: 地址搜店初始化
- 痛点: 录入3家店9道菜已经觉得麻烦，换环境(实习/搬校区)后录入阻力更大
- 方案: 输入地址 → 调用地图API搜周边餐饮 → 用户勾选要导入的店 → 批量入库
- 局限: 用户说"不要花钱"，纯免费路线可改用：用户口述店名→AI代写JSON
- 状态: 已加入规划

### 迭代5: 多人共享菜库
- 痛点: 宿舍几个人各自重复录入同样的店
- 方案: 宿舍群组共享菜库，AI分析群组饮食偏好
- 核心AI价值: 发现群组饮食模式（不是个人）
- 状态: 已加入规划

---

## 迭代总结

| 迭代 | 方向 | 状态 | 核心AI价值 |
|------|------|------|-----------|
| 1: 智能推荐理由 | 增强决策透明度 | 已完成 | 有 (LLM语义生成理由) |
| 2: 自评好吃程度 | 动态偏好学习 | 已完成 | **核心** (没AI无法处理模糊信号) |
| 3: 单店搭配约束 | 推荐逻辑修正 | 已完成 | 有 (LLM理解店与菜的关系) |
| 4: 地址搜店初始化 | 减少录入阻力 | 规划中 | AI辅助数据采集 |
| 5: 多人共享菜库 | 群组推荐 | 规划中 | AI发现群组饮食模式 |

完成迭代3个 + 规划中2个，符合提交说明"不少于3个"的要求。
