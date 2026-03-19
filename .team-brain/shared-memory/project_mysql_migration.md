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
