<p align="center">
  <br>
  <samp>
    you record nearby shops and dishes · AI picks what to eat tomorrow<br>
    not random · not rules · it learns you
  </samp>
</p>

<p align="center">
  <strong>AI 饮 食 管 家</strong>
</p>

<p align="center">
  <kbd>&nbsp;Python 3.9+&nbsp;</kbd>
  <kbd>&nbsp;DeepSeek&nbsp;</kbd>
  <kbd>&nbsp;零成本&nbsp;</kbd>
</p>

<br>

---

<br>

> 每天站在食堂门口纠结 3 分钟，最后吃的还是昨天那家。这个项目就做一件事 —— 帮你决定明天去哪吃、点什么。不是随机抽，不是死规则，而是看过你吃过什么、爱吃什么、该补什么之后，给你一个有理由的推荐。

<br>

## 为 什 么 必 须 有 AI

<table>
<tr>
<th width="22%">维度</th>
<th width="39%">没有 AI 的做法</th>
<th width="39%">有 AI 的做法</th>
</tr>
<tr>
<td><b>偏好学习</b></td>
<td>写死规则：<code>if 辣 then 川味小厨</code><br>口味变化？改代码。</td>
<td>从你每天真实的选择里，<b>自己学</b>出你喜欢什么</td>
</tr>
<tr>
<td><b>营养评估</b></td>
<td>人工查每道菜的卡路里<br>→ 太麻烦 → 放弃</td>
<td>你只需要告诉 AI 菜名，<b>它来算</b></td>
</tr>
<tr>
<td><b>避免吃腻</b></td>
<td>硬规则：7 天内不重复<br>→ 想吃白切鸡也不让</td>
<td>AI 知道"多久没吃"和"<b>吃了几次会不会腻</b>"</td>
</tr>
<tr>
<td><b>推荐理由</b></td>
<td>没有。</td>
<td>每条推荐附带 <b>人看得懂的决策理由</b></td>
</tr>
<tr>
<td><b>约束冲突</b></td>
<td>找不到菜 → 直接报错</td>
<td>AI 在冲突约束间 <b>做权衡</b>，给你最优方案</td>
</tr>
</table>

<br>

---

<br>

## 快 速 上 手

<p>
<b>环境</b> &nbsp; Python 3.9+ &nbsp;·&nbsp; 可选 LLM Key（DeepSeek / 豆包 / 通义千问，学生免费额度够用）
</p>

```bash
# 第一步 告诉 AI 你的情况
python skill/scripts/meal_planner.py profile set

# 第二步 录 入 你 常 去 的 店
python skill/scripts/meal_planner.py shop add

# 第三步 录 入 每 家 店 好 吃 的 菜
python skill/scripts/meal_planner.py dish add

# 第四步 每 天 记 录 吃 了 什 么
python skill/scripts/meal_planner.py log

# 第五步 让 AI 推 荐 明 天 吃 什 么
python skill/scripts/meal_planner.py recommend
```

<br>

---

<br>

## 推 荐 流 程

```
  [一次性]               [一次性]
  设置画像                录入店铺 + 菜品
   ↓                      ↓
   └────────┬─────────────┘
            ↓
      每天记录饮食 ──→ AI 评估今日营养
            ↓                  ↓
      更新饮食历史 ←──────────┘
            ↓
    AI 综合 5 个维度生成推荐
            ↓
    你反馈好吃 / 不好吃 ──→ AI 学习调整
```

<br>

### AI 思考的 5 个维度

| # | 维度 | 说明 |
|---|------|------|
| 1 | **你的画像** | 减脂还是增肌？一天允许多少热量？ |
| 2 | **7 天饮食历史** | 昨晚刚吃过牛肉面，今天换一个 |
| 3 | **你的自评** | 你给口水鸡打了 5 星 → 优先推荐 |
| 4 | **预算控制** | 每餐 ¥25，帮你凑到刚好不超 |
| 5 | **单店约束** | 午餐不跨店 —— 不会让你为了素菜跑两家 |

<br>

---

<br>

## 真 实 数 据 ( 无虚拟 )

所有数据由用户亲自录入，系统不预填任何虚拟内容。

<table>
<tr><th>数据类型</th><th>录入量</th><th>录入方式</th></tr>
<tr><td>店铺</td><td>3 家</td><td>用户口述 → AI 代写 JSON</td></tr>
<tr><td>菜品</td><td>9 道</td><td>同上</td></tr>
<tr><td>饮食历史</td><td>持续更新中</td><td><code>meal_planner.py log</code></td></tr>
</table>

> 首次使用面对空数据库时，不需要逐条敲命令 —— 直接告诉 AI "聪明面馆、自选汤粉 9 块" 就行。

<br>

---

<br>

## 目 录 结 构

```
.
├── README.md                          项目说明
├── skill/
│   ├── SKILL.md                       技能定义（含 YAML 配置）
│   ├── scripts/
│   │   └── meal_planner.py            核心脚本 · ~600 行
│   └── references/
│       └── api_examples.md            LLM API 配置参考
├── data/                              数据存储 · JSON
│   ├── profile.json                   用户画像
│   ├── shops.json                     店铺列表
│   ├── dishes.json                    菜品库
│   └── history.json                   饮食历史
├── tests/                             测试数据
│   ├── test_record.md                 测试记录 · 含截图证据
│   ├── ai_recommend_log.json          AI 推荐日志
│   ├── screenshot_*.png               测试截图
└── iteration/
    └── iteration_log.md               迭代升级说明 · 5 个方向
```

<br>

---

<br>

## 迭 代 历 程

按 **5 步迭代法** 完成 3 个方向，另有 2 个已规划。

<table>
<tr><th>#</th><th>方向</th><th>状态</th><th>核心 AI 价值</th></tr>
<tr><td>1</td><td><b>智能推荐理由</b><br>不再冷冰冰的"评分 X 星"</td><td align="center"><code>done</code></td><td>LLM 语义生成理由</td></tr>
<tr><td>2</td><td><b>自评好吃程度</b><br>吃完打分 → 系统动态学你的口味</td><td align="center"><code>done</code></td><td><b>核心</b> · 没 AI 无法处理模糊反馈</td></tr>
<tr><td>3</td><td><b>单店搭配约束</b><br>不让推荐跨店跑两家</td><td align="center"><code>done</code></td><td>LLM 理解店与菜的关系</td></tr>
<tr><td>4</td><td>地址搜店初始化</td><td align="center"><code>plan</code></td><td>AI 辅助数据采集</td></tr>
<tr><td>5</td><td>多人共享菜库</td><td align="center"><code>plan</code></td><td>群组饮食模式分析</td></tr>
</table>

<br>

---

<br>

## 3 分 钟 展 示 要 点

<table>
<tr>
  <td width="5%" align="right"><b>01</b></td>
  <td><b>演示系统</b> · 运行 <code>recommend</code>，AI 当场推荐明日三餐</td>
</tr>
<tr>
  <td align="right"><b>02</b></td>
  <td><b>真实数据</b> · 3 家店 9 道菜全是真实录入，不编不造</td>
</tr>
<tr>
  <td align="right"><b>03</b></td>
  <td><b>真实痛点</b> · "每天选饭像开盲盒，看半天还是那几家" → 被 8 个已记录的痛点驱动</td>
</tr>
<tr>
  <td align="right"><b>04</b></td>
  <td><b>AI 独特价值</b> · 自评"好吃 5 星" → AI 综合 5 个维度排序，规则引擎做不到</td>
</tr>
<tr>
  <td align="right"><b>05</b></td>
  <td><b>具体改变</b> · 选饭从 2-3 分钟降到 10 秒，不再连续吃同一家</td>
</tr>
</table>

<br>

<p align="center">
  <br>
  <samp>课程项目 · 大数据专业 田师 417 · 俞玄康</samp>
</p>
