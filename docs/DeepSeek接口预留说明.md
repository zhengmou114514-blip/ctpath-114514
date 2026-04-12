# DeepSeek 接口说明

## 当前接入方式

系统采用两层结构：

1. `CTpath` 负责四元组时序推理与 `N+1` 预测。
2. `DeepSeek` 负责基于患者档案、四元组、预测结果生成辅助建议。

## 自动读取配置

后端现在会在启动时自动读取项目根目录的 `.env`。

也就是说，后续你只需要：

1. 在 [/.env](/e:/CTpath-master/.env) 中填好 DeepSeek 配置。
2. 启动后端。

不需要每次手动在终端里重复设置环境变量。

## 推荐配置

`.env` 中建议包含：

```env
CTPATH_LLM_ENABLED=true
CTPATH_LLM_PROVIDER=deepseek
CTPATH_LLM_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_CHAT_PATH=/chat/completions
DEEPSEEK_API_KEY=你的DeepSeekKey
CTPATH_LLM_TIMEOUT=40
CTPATH_LLM_CACHE_TTL=300
CTPATH_LLM_MIN_INTERVAL=30
CTPATH_LLM_CACHE_MAX_ITEMS=256
```

模板见 [/.env.example](/e:/CTpath-master/.env.example)。

## 启动方式

后端启动脚本 [start-backend.ps1](/e:/CTpath-master/scripts/start-backend.ps1) 也会自动加载 `.env`。

启动命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
```

或直接：

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 建议接口输入

后端会把以下内容发送给建议层：

- `patient`
- `quadruples`
- `predictions`
- `evidence`
- `pathExplanation`

## 缓存与限流

当前已加入：

- 同输入缓存
- 同患者短时间限流
- 请求失败自动回退到本地占位建议

对应实现见 [llm_advice_service.py](/e:/CTpath-master/app/services/llm_advice_service.py)。

## 启用后的判断方式

如果 DeepSeek 调用成功，前端会看到：

- `adviceMeta.source = "deepseek"`
- `adviceMeta.connected = true`

如果回退到占位建议，则会看到：

- `adviceMeta.source = "placeholder"`
- `adviceMeta.connected = false`
