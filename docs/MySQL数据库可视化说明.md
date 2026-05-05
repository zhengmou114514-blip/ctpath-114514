# MySQL 数据库可视化说明

## 1. 系统内置查看方式

本项目新增管理员只读数据库预览入口，用于在前端系统中心查看后端 MySQL 业务表。

使用步骤：

1. 启动后端前配置环境变量：

   ```powershell
   $env:CTPATH_DB_URL="mysql+pymysql://用户名:密码@127.0.0.1:3306/数据库名?charset=utf8mb4"
   ```

2. 启动后端：

   ```powershell
   cd backend
   uvicorn app.main:app --reload
   ```

3. 启动前端并登录管理员账号：

   ```powershell
   cd frontend
   npm run dev
   ```

4. 使用 `demo_admin / demo123456` 登录，进入“后台管理系统 -> 系统中心”，查看“MySQL 数据库预览”区域。

该入口只允许管理员访问，只展示白名单业务表的表名、行数、字段和前 50 行数据，不开放任意 SQL，避免误删或误改数据。

## 2. 外部数据库工具建议

如果想像数据库软件一样查看全部表和数据，推荐使用以下方式之一：

| 工具 | 适合场景 | 连接方式 |
|---|---|---|
| DBeaver Community | 免费、跨平台、适合截图表结构和数据 | 新建 MySQL 连接，填写 host、port、database、username、password |
| Navicat | 已安装商业工具时使用，界面直观 | 新建 MySQL 连接后打开表数据 |
| DataGrip | JetBrains 用户适合使用 | Database 面板添加 MySQL Data Source |
| VS Code Database Client/JDBC 插件 | 不想切换 IDE 时使用 | 在 VS Code 里添加 MySQL 连接 |

连接参数一般为：

| 参数 | 示例 |
|---|---|
| Host | `127.0.0.1` |
| Port | `3306` |
| Database | `ctpath` 或你实际创建的数据库名 |
| User | MySQL 用户名 |
| Password | MySQL 密码 |
| Charset | `utf8mb4` |

## 3. 论文截图建议

截图时可以准备两类图：

1. 系统内截图：后台管理系统的“MySQL 数据库预览”区域，体现系统内置只读查看能力。
2. 数据库工具截图：DBeaver 或 Navicat 中的表结构与表数据，体现数据库表真实存在。

建议优先截图以下表：

- `patients`：患者主索引与基础档案字段。
- `patient_events`：病程事件和模型输入。
- `outpatient_tasks`：随访任务。
- `patient_medications`：当前用药。
- `drug_catalog`：药品目录。
- `prediction_results`：模型预测结果。
- `system_audit_logs`：系统审计记录。
