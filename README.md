# AI饮食管家 (Meal Planner)

> 你录入附近的店和好吃的菜，AI明天帮你选 —— 不是随机抽，而是看过你吃过什么、爱吃什么、该补什么之后，给你一个有理由的推荐。

## 一句话说清楚这个项目

大学生每天面临"吃什么"的选择困难：食堂几十个窗口、校外一堆店，挑花眼、选重复、算热量太麻烦。这个项目解决的就是这个问题 —— 让你的AI记住你去过的每家店、每道菜，然后像个懂你的美食搭子一样，帮你决定明天去哪吃、点什么。

## 核心AI价值

**没有AI，这个功能根本做不出来。**

| 维度 | 没有AI的做法 | 有AI的做法 |
|------|------------|----------|
| 偏好学习 | 固定规则（if 粤菜 then 粤味轩） | 从实际点餐历史中学习你的真实偏好 |
| 营养评估 | 人工查每道菜的卡路里 → 放弃 | AI估算营养结构并评估均衡性 |
| 避免重复 | 硬规则"7天内不吃同样的" → 有时想吃也不行 | AI考虑"多久没吃"、"吃了会不会腻" |
| 推荐理由 | 无 | 每条推荐附带可理解的决策理由 |
| 约束冲突 | 无选项时直接报错 | AI在冲突约束间做权衡 |

## 快速开始

### 环境要求
- Python 3.9+
- 可选: LLM API Key（DeepSeek/豆包/通义千问，学生免费）

### 安装

```bash
# 1. 安装依赖 (仅LLM推荐需要)
pip install openai

# 2. 进入项目目录
cd meal-planner

# 3. 设置API（可选，不设置也能用离线引擎）
# 在系统环境变量中配置 (具体见 skill/references/api_examples.md)
```

### 使用流程

```bash
# 第一步: 告诉我你的情况
python skill/scripts/meal_planner.py profile set
# → 输入身高、体重、目标、预算、忌口、口味偏好

# 第二步: 录入你常去的店
python skill/scripts/meal_planner.py shop add
# → 输入店名、类别、位置、备注

# 第三步: 录入每家店好吃的菜
python skill/scripts/meal_planner.py dish add
# → 选店铺 → 输入菜名、价格、好吃程度(1-5星)

# 第四步: 每天记录吃了什么
python skill/scripts/meal_planner.py log
# → 选早/午/晚餐分别吃了什么

# 第五步: 让AI推荐明天吃什么
python skill/scripts/meal_planner.py recommend
# → AI综合画像+历史+偏好给出推荐

# 如果还没配置API，用离线引擎:
python skill/scripts/meal_planner.py recommend --offline
```

## 项目结构

```
meal-planner/
├── README.md                           # 本文件
├── skill/
│   ├── SKILL.md                        # Skill定义文件
│   ├── scripts/
│   │   └── meal_planner.py             # 核心脚本 (~500行)
│   └── references/
│       └── api_examples.md             # LLM API配置参考
├── data/                               # 数据存储 (JSON, 初始为空)
│   ├── profile.json                    # 用户画像
│   ├── shops.json                      # 店铺列表
│   ├── dishes.json                     # 菜品库
│   └── history.json                    # 饮食历史
├── tests/
│   ├── test_record.md                   # 测试记录 (含截图证据)
│   ├── ai_recommend_log.json            # AI推荐日志
│   ├── screenshot_recommend_table.png   # 截图1: 8元预算推荐
│   └── screenshot_data_cleanup.png      # 截图2: 数据清理决策
└── iteration/
    └── iteration_log.md                 # 迭代升级说明 (5个方向)
```

## 使用数据

所有数据由用户自己录入，初始为空。系统不预填任何虚拟数据——店铺、菜品、饮食记录均来自真实使用。详见 `tests/test_record.md`。

## 迭代升级

按5步迭代法完成了3个方向的迭代（含代码实现），另有2个方向已规划：

1. **智能推荐理由引擎** — 推荐不再是冷冰冰的"评分X星"，而是"3天没吃+你给过5星+预算内"
2. **自评好吃程度 (核心AI价值)** — 吃饭后自评1-5星，让系统动态学习你的真实口味变化
3. **单店搭配约束** — 修复跨店混搭bug，识别"压3饭馆没有青菜"等真实问题

详见 `iteration/iteration_log.md`

## 3分钟结课展示要点

1. **演示系统** — 运行 `recommend` 展示推荐结果
2. **真实使用时长** — 所有店铺和菜品为真实录入，饮食记录为实际使用产生
3. **解决的真实痛点** — "每天选饭像开盲盒，看菜单看半天最后还是那几家"
4. **AI独特价值** — 动态偏好学习：系统从"你给5星"逐渐变成"你经常点"；这个能力没有AI做不到
5. **具体改变** — 选饭时间从2-3分钟降到10秒，不再连续吃同一家

## 许可

本项目为课程作业项目。
