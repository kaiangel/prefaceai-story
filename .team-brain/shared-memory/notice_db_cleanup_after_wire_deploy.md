# 通知: WIRE 部署后 DB 脏数据清理

> **日期**: 2026-04-04
> **来自**: @pm (Founder 团队)
> **给**: @backend_Ben
> **状态**: ✅ 已完成 (Ben 微信确认 2026-04-07 16:00 "现在数据是对的")

---

## 背景

Ben 在阿里云 MySQL 中发现：同一个 idea 产生 2 条 projects 记录 + generation_jobs 大量 failed/stuck processing。

**根因**: 旧代码的 `POST /projects/` 每次调用都创建 Project + Chapter + GenerationJob 并启动后台 pipeline。StageA 和 StageB 各调一次 = 2 个项目 + 2 条 job。

**已修复**: TASK-CONFIRM-OUTLINE-WIRE（本地 7 文件改动，待 DevOps 部署）。修复后 `POST /projects/` 仅创建项目，pipeline 只在 StageB 确认后通过 `POST /projects/{id}/start-generation` 启动。

## 部署后建议清理

部署完成后，建议 Ben 清理历史脏数据：

1. **重复项目**: 同一 user_id + original_idea 有 2 条记录，其中 title="未命名项目" 的是 StageB 重复创建的
2. **stale generation_jobs**: status=failed（progress=0）或 status=processing（卡住的）
3. **orphan chapters**: 关联到被删除项目的 chapters 记录

清理策略由 Ben 决定（数据库是 Ben 的领域）。

## 参考 SQL

```sql
-- 查看重复项目
SELECT user_id, LEFT(original_idea, 50) as idea, COUNT(*) as cnt
FROM projects
GROUP BY user_id, LEFT(original_idea, 100)
HAVING cnt > 1;

-- 查看 stale jobs
SELECT id, status, progress, stage_message, created_at
FROM generation_jobs
WHERE status IN ('failed', 'processing', 'queued');
```
