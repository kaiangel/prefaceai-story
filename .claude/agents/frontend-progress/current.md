# Frontend 当前任务进度

> 更新时间: 2026-03-24
> 状态: TASK-STAGE1-FRONTEND 完成，等 PM Review

---

## 最新完成: TASK-STAGE1-FRONTEND — StageA → 真实 API (2026-03-24)

### 状态: 完成，`npm run build` 20 路由通过

**修改文件**: `CreateContent.tsx`

**核心改动**:
1. StageA handleSubmit: mock → 真实 API 两步链路 (create project → generate outline)
2. 篇幅→参数映射: flash/short/medium/epic → duration + character_count
3. Loading: "AI 正在构思故事大纲..." + "约需 10-30 秒"
4. 错误处理: 红色错误卡 + "重试"按钮
5. 未登录降级: 无 token 时用 mock 数据

---

## 环境提醒

- 真实 API 需后端 + MySQL 运行
- 未登录/无后端时自动降级为 mock（/create 页面始终可用）
