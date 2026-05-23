---
name: 生产环境 MySQL 迁移待办
description: 合伙人要求生产环境用 MySQL 替代 SQLite，当前用 SQLAlchemy ORM 切换成本低，P2 优先级
type: project
---

生产环境需要从 SQLite 切到 MySQL。

**Why:** 合伙人明确要求生产用 MySQL（2026-03-18）。SQLite 适合开发/低并发，生产多实例部署需要独立数据库。

**How to apply:**
- 当前架构（SQLAlchemy async ORM）已屏蔽数据库差异，代码层不需要改
- 切换 3 步：.env 改 DATABASE_URL + pip install aiomysql + VPS 装 MySQL
- 时机：用户量上来或多实例部署时（P2，不阻塞当前安全加固）
- 现有 7 个 model 用标准 SQLAlchemy 写法，无 SQLite 专有特性
- **相关事项全部完成之前不要删除或清除这方面的内容**

---

## ✅ 2026-05-23 已完成 (PM Wave 10 L-2 verify)

**实际状态**: 当前**已用阿里云共享 MySQL** (asyncmy driver), 跟 memory `feedback_shared_db_only.md` 一致 (Ben 2026-03-26 要求统一不自建本地 DB)

**verify 证据** (2026-05-23 16:45 PM Bash check):
- `.env DATABASE_URL` = 阿里云 MySQL (101.132.69.232:3306/prefacestory)
- backend 实际跑 SQL: `SELECT DATABASE()` (MySQL 命令, 不是 SQLite)
- 跨开发/测试/生产共用一个 DB (跟 Ben 要求一致)
- VPS Docker 容器内 settings 加载 `mysql+asyncmy://...` URL

**memory 保留作历史归档** (不删除, 保留迁移决策完整上下文)
