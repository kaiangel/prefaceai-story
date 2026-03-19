# backend_Ben 当前状态

> 最后更新: 2026-03-19

## 状态: contact_us 后端链路已跑通，等待整理提交范围

### 已完成
- 新增 `contact_us` 的 model / schema / API
- 后端配置已支持 MySQL 连接串和 `MYSQL_*` 自动拼装
- 本地 CORS 已补充 `http://127.0.0.1:3000`
- `prefacestory.contact_us` 已完成真实建表
- `contact_us.id` 已改为自增主键
- 历史 UUID 已保存在 `legacy_id`
- 已完成真实 MySQL 写入验证

### 当前任务
- 收敛本次改动范围，只保留 `contact_us` 相关必要差异
- 支持前端手工测试 `/contact`
- 继续观察本地运行链路是否还有环境问题

### 已知现状
- 本地前端: `http://127.0.0.1:3000`
- 本地后端: `http://127.0.0.1:8000`
- 新提交的 `contact_us` 记录会获得自增 `id`
