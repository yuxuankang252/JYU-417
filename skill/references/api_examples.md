# 独立运行参考（仅限脱离 WorkBuddy 使用）

> 如果安装了 Skill 到 WorkBuddy，不需要看这个。WorkBuddy 内置 AI（DeepSeek）会直接完成推荐。

## 当你想要独立运行脚本时

```bash
# 设置环境变量
export OPENAI_API_KEY=sk-xxx
export OPENAI_BASE_URL=https://api.deepseek.com/v1
export LLM_MODEL=deepseek-chat

# 运行
python skill/scripts/meal_planner.py recommend
```

## 推荐 API（学生免费额度）

| 平台 | 注册地址 | 额度 |
|------|----------|------|
| DeepSeek | https://platform.deepseek.com | 新用户赠送 |
| 豆包 | 火山引擎控制台 | 免费额度 |
| 通义千问 | https://dashscope.aliyun.com | 学生认证免费 |

所有平台兼容 OpenAI 接口格式，代码无需修改。
