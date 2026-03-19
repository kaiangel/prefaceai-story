# frontend_Ben — 其他 Agent 需要知道的

> 最后更新: 2026-03-19

## 状态: Contact 页前端联调已完成

## 本次关键事实
- 官网 `/contact` 已改为真实请求后端
- 请求地址是 `/api/contact-us/`
- 前端不再使用 mock 提交成功逻辑
- 失败时会展示错误提示

## 当前联调信息
- 本地前端: `http://127.0.0.1:3000`
- 本地 API: `http://127.0.0.1:8000/api`
- 后端 CORS 已支持 `127.0.0.1:3000`

## 注意
- Founder Frontend 已完成: LP 5.0/5 + Create P0/P1/P2 + 10 子页面
- 本次提交应聚焦 `contact_us` 链路，不混入其他前端改动
