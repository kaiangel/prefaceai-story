# pm_Ben — 其他 Agent 需要知道的

> 最后更新: 2026-03-19

## 状态: contact_us 需求已落地，正在整理提交范围

pm_Ben 负责 Ben 团队内部协调和与 Founder 团队对齐。

## 本次关键结论
- 官网 `/contact` 不能继续使用 mock
- 联系表单必须走真实后端接口并写入 MySQL
- 表名固定为 `contact_us`
- 本次仅 `contact_us.id` 使用自增主键
- 其他表不做主键类型扩散改造

## 当前已知状态
- 前端已改为提交 `/api/contact-us/`
- 后端已提供 `contact_us` API / model / schema
- 本地 CORS 已补充 `http://127.0.0.1:3000`
- MySQL 中 `contact_us.id` 已是自增主键

## Ben 团队当前优先级
1. 继续手工验证 `/contact` 链路
2. 整理本次最小可提交差异
3. 避免把无关改动混入 `contact_us` 提交
