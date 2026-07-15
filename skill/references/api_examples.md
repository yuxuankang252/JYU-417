# LLM API 配置参考

## 推荐API (学生免费额度)

### 1. DeepSeek
```env
OPENAI_API_KEY=sk-your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

注册地址: https://platform.deepseek.com
新用户赠送额度，足够个人项目使用。

### 2. 豆包 (Doubao)
```env
OPENAI_API_KEY=your-doubao-key
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_MODEL=doubao-lite-128k
```

### 3. 通义千问 (Qwen)
```env
OPENAI_API_KEY=sk-your-qwen-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-turbo
```

注册地址: https://dashscope.aliyun.com
学生认证后可免费领取额度。

## 注意事项

1. 所有API都兼容OpenAI接口格式，代码无需修改
2. 推荐使用 DeepSeek，中文效果好且免费额度充裕
3. 如果API调用失败，系统会自动降级为离线规则引擎
