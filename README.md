# CTpath 慢病辅助诊疗业务系统

最后更新：2026-04-21

本仓库是一个“慢病辅助诊疗业务系统”，不是完整 HIS、完整 EMR、收费系统、住院系统、医保结算系统或药房库存系统。

项目目标是在慢病管理场景中，把业务工作台、患者档案、病程时间线、模型辅助建议、随访闭环、药品权限与治理能力组合成一个可运行、可演示、可继续扩展的医疗信息化原型。

## 给 AI 和开发者的快速结论

请优先阅读：

1. `AGENTS.md`
2. `README.md`
3. `docs/PROJECT_LOGIC_MANIFEST.md`
4. `frontend/src/router/index.ts`
5. `frontend/src/pages/AppWorkspacePage.vue`
6. `app/main.py`

当前系统已经明确分为：

- 前端业务工作台：`frontend/`
- FastAPI 后端：`app/`
- 项目说明文档：`docs/`
- 本地 AI 协作规则：`AGENTS.md`

当前 canonical 前端入口是 Vue Router 中注册的页面。不要把历史 simple、legacy、backup、unused 页面当作主入口。

## 当前系统定位

系统聚焦慢病辅助诊疗，核心业务对象是慢病患者和其连续病程数据。

系统当前覆盖：

- 医生工作台
- 护士随访工作台
- 患者详情 / 电子档案
- 患者附件
- 药品管理
- 药品权限管理
- 模型洞察
- 模型看板
- 治理中心
- 登录认证、审计、限流、trace_id、异常处理等后端治理能力

系统当前不覆盖：

- 收费、结算、医保全流程
- 住院、床位、医嘱全流程
- 药房库存、采购、出入库
- 完整 HIS 或完整 EMR
- 正式训练中心和 CSV 数据导入工作流
- 完整处方流

## 当前前端技术栈

- Vue 3
- TypeScript
- Vue Router
- Pinia
- Element Plus
- ECharts
- Vite

前端启动：

```powershell
cd E:\CTpath-master\frontend
npm install
npm run dev
```

前端构建：

```powershell
cd E:\CTpath-master\frontend
npm run build
```

## 当前后端技术栈

- FastAPI
- Pydantic
- demo store / MySQL 双模式
- CTpath / CHRONIC 数据加载能力
- 慢病预测与建议服务
- SlowAPI 限流
- JWT 认证
- RBAC 权限能力
- TraceId 中间件
- 全局异常处理中间件
- 审计日志
- CORS

后端启动：

```powershell
cd E:\CTpath-master
conda activate ctpath
uvicorn app.main:app --reload
```

默认访问：

- API: `http://127.0.0.1:8000`
- OpenAPI: `http://127.0.0.1:8000/docs`
- 前端开发服务: `http://127.0.0.1:5173`

## demo / mysql 模式

系统根据 `CTPATH_DB_URL` 判断数据源模式。

- 未配置 `CTPATH_DB_URL` 时，后端使用 demo 数据，`/api/health` 返回 `mode=demo`
- 配置 MySQL 连接后，后端使用 MySQL，`/api/health` 返回 `mode=mysql`

MySQL 示例：

```powershell
$env:CTPATH_DB_URL="mysql+pymysql://root:your_password@127.0.0.1:3306/ctpath?charset=utf8mb4"
uvicorn app.main:app --reload
```

初始化示例：

```powershell
Get-Content .\app\mysql_schema.sql | mysql -u root -p ctpath
Get-Content .\app\mysql_seed_demo.sql | mysql -u root -p ctpath
```

## 当前前端路由

`/login` 是独立登录页，`/` 是业务工作台壳层。两者已经分离。

当前主要路由：

- `/login`
- `/`
- `/patient-detail/:patientId?`
- `/nurse-followups`
- `/model-insight`
- `/model-dashboard`
- `/governance`
- `/drug-management`
- `/drug-permission-management`

主路由定义在：

- `frontend/src/router/index.ts`

业务壳层定义在：

- `frontend/src/pages/AppWorkspacePage.vue`
- `frontend/src/layouts/AppShell.vue`
- `frontend/src/components/AppSidebar.vue`
- `frontend/src/components/WorkspaceTopbar.vue`

## 当前前端界面状态

前端已按医疗工作台风格重构：

- 左侧稳定导航
- 顶部状态栏
- 单一主内容区
- 页面头部统一
- 蓝灰工作台色彩体系
- 字号、间距、卡片内边距统一
- loading、empty、error、degraded、no permission 状态有统一样式基础
- `/login` 与 `/` 业务壳层分离

核心页面当前职责：

| 页面 | 当前职责 | 主要文件 |
| --- | --- | --- |
| 登录页 | 账号登录、注册入口、健康状态展示 | `frontend/src/pages/LoginPage.vue`, `frontend/src/components/LoginScreen.vue` |
| 业务壳层 | 左导航、顶部状态栏、当前患者上下文、单一内容区 | `frontend/src/pages/AppWorkspacePage.vue`, `frontend/src/layouts/AppShell.vue` |
| 医生工作台 | 待处理患者、当前患者摘要、主动作入口 | `frontend/src/pages/DoctorDashboardPage.vue` |
| 患者详情 | 三栏布局：左档案/附件，中时间线/证据，右用药/建议/动作 | `frontend/src/pages/PatientDetailPage.vue` |
| 护士随访工作台 | 今日随访、未接通联系、医生复核、联系记录 | `frontend/src/pages/NurseFollowupsPage.vue` |
| 药品管理 | 药品目录、剂型规格、处方药、管制药、状态维护 | `frontend/src/pages/medication/DrugCatalogPage.vue` |
| 药品权限管理 | 角色级药品权限矩阵 | `frontend/src/pages/medication/permissions/DrugPermissionManagementPage.vue` |
| 模型洞察 | 当前患者预测、Top-K 风险、证据摘要、建议来源 | `frontend/src/pages/ModelInsightPage.vue` |
| 模型看板 | 模型版本、训练时间、MRR、Hits、调用量、回退比例、健康状态 | `frontend/src/pages/ModelDashboardPage.vue` |
| 治理中心 | 数据质量、异常时间线、冲突、待补全档案、治理动作 | `frontend/src/pages/GovernancePage.vue` |

## 当前后端模块

后端入口：

- `app/main.py`

当前挂载的 API router：

- `app/api/analytics.py`
- `app/api/attachments.py`
- `app/api/audit.py`
- `app/api/auth.py`
- `app/api/authz.py`
- `app/api/drug_permissions.py`
- `app/api/drugs.py`
- `app/api/governance.py`
- `app/api/patient_medications.py`
- `app/api/patients.py`
- `app/api/predictions.py`
- `app/api/worklists.py`

当前主要服务：

- `app/services/drug_catalog_service.py`
- `app/services/drug_permission_service.py`
- `app/services/governance_service.py`
- `app/services/patient_attachment_service.py`
- `app/services/patient_medication_service.py`
- `app/services/medication_assessment_service.py`
- `app/services/suggestion_service.py`
- `app/services/llm_advice_service.py`
- `app/model_service.py`

当前中间件：

- `TraceIdMiddleware`
- `GlobalExceptionMiddleware`
- `JWTAuthMiddleware`
- `CORSMiddleware`
- SlowAPI rate limit handler

认证与权限相关：

- `app/api/auth.py`
- `app/api/authz.py`
- `app/auth/*`
- `app/middleware/jwt_auth.py`
- `app/auth/rbac_middleware.py`
- `app/auth/permission_registry.py`

## 当前完成状态

已完成或基本可用：

- 登录认证与 session 恢复
- 医生工作台
- 患者详情三栏布局
- 患者档案与附件能力
- 护士随访工作台基础视图
- 药品目录管理
- 药品权限矩阵
- 患者当前用药与用药充分性评估
- 模型洞察
- 模型看板
- 治理中心基础视图
- demo/mysql 模式
- JWT、trace_id、全局异常、限流、审计基础能力

部分完成 / 正在收口：

- 护士随访闭环的状态操作和细粒度权限体验
- 治理动作的闭环处理
- 药品权限与业务操作的前端提示细化
- LLM 建议服务的健康检查、降级和审计体验
- 模型看板与真实训练任务的后续衔接
- RBAC 权限覆盖的完整一致性

规划中 / 待完善：

- 模型调试台
- 导入暂存区
- CSV 校验、映射和问题查看
- 正式模型训练中心
- 更完整的数据脱敏策略
- 文件上传安全校验增强
- 更细粒度审计查询

## 开发约束

后续修改必须遵守：

- 不要把本项目扩展成完整 HIS
- 不要新增收费、住院、库存、医保结算模块
- 不要把 CSV 导入放进医生主流程
- 不要把模型训练功能塞进医生首页
- 不要把治理看板、模型看板、患者详情混在一个长页面里
- 不要修改后端接口字段名，除非同步更新前后端和文档
- 不要删除仍被 router、AppWorkspacePage、service、测试或文档显式引用的文件
- 不确定是否废弃的文件先保留

## 推荐 AI 接手顺序

新的 AI 接手本仓库时建议按这个顺序理解：

1. 读 `AGENTS.md`，确认项目边界和禁止事项
2. 读本 README，确认真实当前状态
3. 读 `docs/PROJECT_LOGIC_MANIFEST.md`，确认模块职责和 canonical 文件
4. 看 `frontend/src/router/index.ts`，确认前端入口
5. 看 `frontend/src/pages/AppWorkspacePage.vue` 和 `frontend/src/layouts/AppShell.vue`，确认壳层
6. 看 `app/main.py`，确认后端路由和中间件
7. 再按具体任务进入对应页面或 API
