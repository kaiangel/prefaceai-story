# backend_Ben — 其他 Agent 需要知道的

> 最后更新: 2026-03-19

## 状态: contact_us 后端链路已完成并可联调

## 本次关键事实
- 官网联系表单后端入口是 `/api/contact-us/`
- 数据表固定是 `contact_us`
- 当前表结构里 `id` 是自增主键
- 历史 UUID 数据保存在 `legacy_id`
- 本次没有把其他历史表主键一起改成自增

## 已完成
- `contact_us` model / schema / API 已实现
- MySQL 真实写入已验证
- 本地 CORS 已支持 `127.0.0.1:3000`

## 当前注意事项
- 提交范围要聚焦 `contact_us`，避免混入无关改动
- 如果再改数据库主键策略，需要单独开任务，不在这次范围内

## 不碰的领域
- Pipeline (Stage 1-5)
- Prompt 工程
- Founder 团队的任何文件（只读）
