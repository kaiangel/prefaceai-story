# DevOps Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 DevOps 的工作状态和部署要求
> **最后更新**: 2026-02-12

---

## 当前状态速览

状态: ⚪ 待命（已完成状态检查）
刚完成: 2026-02-12 全面运维状态检查，评估风险和待办事项
下一步: 等待 Coordinator 指令决定是否启动 Phase 6 部署准备工作
需要PM汇总: DevOps 已完成状态检查，确认 Phase 6 进度 0%，无紧急运维问题

---

## 环境状态

| 环境 | 状态 | 最近更新 |
|------|------|----------|
| dev | 🟢 运行中（SQLite + 本地文件） | 2026-02-12 |
| staging | ⚪ 未部署 | - |
| prod | ⚪ 未部署 | - |

---

## 运维风险摘要

| 风险 | 等级 | 影响 | 建议 |
|------|------|------|------|
| 无 git 仓库 | 🟡 中 | 无版本控制、无法搭 CI/CD | 建议尽快初始化 |
| 无成本监控 | 🟡 中 | $9.35/故事，上线后可能失控 | 上线前必须建立 |
| .env.example 不完整 | 🟡 中 | 新成员配置困难 | 可立即修复 |
| 无 deploy/ 目录 | 🟢 低 | Phase 6 时创建 | 不紧急 |

---

## 给 @backend 的信息

### 需要你提供（部署前）

1. **完整环境变量清单确认**
```
GEMINI_API_KEY
ANTHROPIC_API_KEY
OPENAI_API_KEY
VOLCENGINE_ACCESS_KEY
VOLCENGINE_SECRET_KEY
VOLCENGINE_TTS_APPID
DATABASE_URL
```

2. **系统依赖**
```
python 3.11+
ffmpeg (Phase 4.5 视频合成)
Pillow (TextOverlayService)
```

3. **启动命令**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 给 @frontend 的信息

### 需要你提供（部署前）

1. **构建命令**: `npm run build`
2. **环境变量**: `NEXT_PUBLIC_API_URL`
3. **输出目录**: `.next/` 或 `out/`
4. **Node.js 版本要求**: 待确认

---

## 给 @tester 的信息

### CI/CD 中的测试（规划中）

```yaml
# 规划中的 GitHub Actions
- name: Run Tests
  run: |
    pytest tests/ -v
    npm run test  # 前端测试
```

---

## 部署架构规划

```
┌─────────────┐     ┌──────────────────┐
│   Vercel    │     │  Railway / ECS   │
│  (Frontend) │────▶│   (Backend API)  │
└─────────────┘     └────────┬─────────┘
                             │
                    ┌────────┴────────┐
                    │   Celery + Redis │
                    │   (Worker 层)    │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │   外部 AI 服务   │
                    │ Gemini/TTS/Whisper│
                    └─────────────────┘
```

---

## 安全要求

### Secrets 管理

- 开发: .env 文件 (git ignored)
- 生产: 平台环境变量 (Railway/Vercel) 或 AWS Secrets Manager

### 安全红线

- API Key 绝不能出现在代码仓库中
- API Key 绝不能出现在日志中
- 不同环境使用不同的 API Key
