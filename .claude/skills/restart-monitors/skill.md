# restart-monitors — 干净重启前后端 + 全维度日志监控 + 2 min cron

> 一键拉起完整开发环境监控体系。用于 Founder 准备测试前。

---

## 用途

任何需要"干净重启+完整监控"的场景:
- Founder 准备跑 e2e 测试
- 排查难复现 bug 前重置环境
- 部署/代码大改后干净开测
- session 切换 / 浏览器隐身模式开测

---

## 完整流程 (按顺序执行)

### Step 1: 清理 — 先 audit 再 kill

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
ps aux | grep -E "uvicorn.*app.main|npm.*dev|next.*dev" | grep -v grep
```

**clean stop 流程**:
```bash
pkill -f "uvicorn.*app.main:app"
pkill -f "next dev"
pkill -f "npm.*dev"
sleep 3
ps aux | grep -E "uvicorn|next|npm.*dev" | grep -v grep || echo "✅ 全停"
```

memory `feedback_diagnose_before_destructive`: PM 不得先 kill -9, 先 SIGTERM (pkill 默认), 等 3s 没退再升级。

---

### Step 2: rotate 旧日志 (保留历史不删)

```bash
TS=$(date +%Y%m%d-%H%M)
for f in backend.log frontend.log client.log; do
  if [ -f "logs/$f" ] && [ -s "logs/$f" ]; then
    mv "logs/$f" "logs/$f.${TS}-rotate"
  fi
done
touch logs/backend.log logs/frontend.log logs/client.log
```

memory `feedback_no_delete_without_confirm`: 永远不主动删, 只 rotate。

---

### Step 3: 启动后端 (uvicorn 不带 --reload)

```bash
nohup venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
echo "✅ backend PID=$!"
```

memory `feedback_local_backend_no_reload`: --reload + 阿里云远程 MySQL = metadata lock 死锁, 必须不带 --reload。

---

### Step 4: 启动前端

```bash
cd frontend && nohup npm run dev > ../logs/frontend.log 2>&1 &
echo "✅ frontend PID=$!"
cd ..
```

---

### Step 5: 等启动 + verify 健康

```bash
sleep 25
curl -s -o /dev/null -w "backend  /health  HTTP %{http_code}\n" http://localhost:8000/health
curl -s -o /dev/null -w "frontend          HTTP %{http_code}\n" http://localhost:3000
ps aux | grep -E "uvicorn.*app.main|next.*dev" | grep -v grep | awk '{printf "  PID %s: %s\n", $2, $11}'
```

预期: 两个 200 + 2 进程 alive。如 frontend 慢启动 200 OK 也可。

---

### Step 6: 拉起 4 个 Monitor (persistent, session-length)

调用 Monitor tool 4 次, 每个 `persistent: true`, `timeout_ms: 3600000`:

| Monitor | filter (grep -E 模式) |
|---|---|
| **backend.log errors** | `ERROR\|Traceback\|CRITICAL\|Exception\|MySQL.*OperationalError\|500 Internal\|FAIL\|asyncmy.*error` |
| **frontend.log errors** | `error\|warn\|failed\|fatal\|cannot find\|module not found\|webpack.*error\|TypeError\|ReferenceError` (用 `-iE`) |
| **client.log browser console** | `error\|warn\|uncaught\|promise.*reject\|network.*fail\|fetch.*fail\|TypeError\|ReferenceError\|hydration` (用 `-iE`) |
| **Pipeline Stage + Layer 1** | `Stage [0-9]\|Layer 1 (injected\|SKIPPED)\|LLMFallbackChain\|AdjustCharacter\|ScreenplayWriter\|StoryboardDirector\|CharacterDesigner\|Pipeline.*complete\|Pipeline.*error\|R4-[1-3]\|ShotValidator.*FAIL\|Schema 验证通过` |

**Monitor command 模板** (改 filter pattern):
```
tail -F /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story/logs/<LOG>.log 2>/dev/null | grep --line-buffered -E "<FILTER>"
```

⚠️ `--line-buffered` 必须 (不然 grep pipe 缓冲会延迟事件)
⚠️ `tail -F` 用大写 F (file rotate 后跟踪新 file)

---

### Step 7: CronCreate 2 min 全维度扫 (recurring)

调用 CronCreate tool, `cron: "*/2 * * * *"`, `recurring: true`:

```
2 min 全维度日志监控扫: 1) curl localhost:8000/health 看 backend 状态码 + curl localhost:3000 看 frontend; 2) tail -50 logs/backend.log 找 ERROR/Traceback/Exception/CRITICAL/MySQL OperationalError/500 Internal 任何 hit 立即报告; 3) tail -50 logs/frontend.log 找 error/warn/Failed/fatal/TypeError/ReferenceError 任何 hit 报告; 4) tail -50 logs/client.log 找浏览器 console error/warn/uncaught/promise-reject/network-fail 任何 hit 报告; 5) ps aux 找 uvicorn + next dev 进程是否存活 (PID 不在则报告); 6) Pipeline 状态 grep "Stage [1-9]" logs/backend.log 最新看是否有 Pipeline 跑中; 任何异常立即用 PushNotification 通知 Founder, 一切正常则一句话简报。
```

⚠️ 不需要 `/loop` 包装, 直接 prompt — cron 每次 fire 时整段当 prompt 跑。

---

## 完成后报告 Founder

```
✅ Backend PID X + Frontend PID Y (健康 200)
✅ 4 Monitor persistent: <task IDs>
✅ Cron <id> every 2 min 全维度扫
```

等 Founder 开测。

---

## 停止流程 (后续 Founder 说"停掉"时)

```
1. CronList → CronDelete 所有 cron
2. TaskList → TaskStop 所有 Monitor (含 zombie 之前 session 残留)
3. (可选) 不 kill backend/frontend 进程 — 等 Founder 决定下一步
```

---

## 注意事项

### 必须遵守的 memory
- `feedback_local_backend_no_reload`: uvicorn 不带 --reload
- `feedback_restart_services_pm_do`: 常规重启 PM 直接 Bash (不派 DevOps)
- `feedback_diagnose_before_destructive`: pkill 先 SIGTERM, 不直接 kill -9
- `feedback_no_delete_without_confirm`: 旧日志 rotate 不删

### 浏览器 console 监控 (client.log)
- `client.log` 由 TASK-CLIENT-LOG-PIPE (5/12 落地) 写入
- 浏览器 fetch `/api/_client_log` POST 上报 console error/warn
- frontend 端 `layout.tsx:26` window.console hook 自动 capture
- 监控 `client.log` = 监控浏览器 console (Founder 浏览器跑测时所有 error/warn 自动入 log)

### 4 Monitor 设计原则
- backend/frontend/client 三大日志各 1 Monitor (error filter)
- Pipeline Stage + Layer 1 是**事件 marker monitor** (不只 error, 含 Stage 切换 / wire 触发 / Validator FAIL 等)
- 不监控 sqlalchemy noise (排除 `INFO sqlalchemy`)
- 不监控 routine warn (排除 `routine|non-fatal` for client)

### Cron 2 min 频率
- 每 2 min 全维度扫一次, 比 Monitor 持续监控**周期性补充** (Monitor 是事件触发, Cron 是定时巡检)
- Cron prompt 含 6 检查项 (health + 3 log + 进程 + Pipeline)
- 0 阻塞 = 一句话简报, 有阻塞 = PushNotification

### Zombie Monitor 处理
- TaskStop 后 events 队列残留 flush 几条是正常的
- 如 TaskList 显示 No tasks 但 events 仍 fire = zombie (上一 session 残留)
- 收到 zombie event 立即再 TaskStop 该 task_id

---

## 历史 (这个流程的来源)

- 5/22 19:50 首次完整执行 (Founder 准备 e2e test27 跑前)
- 5/22 20:01 fresh 监控启动后 Founder 浏览器开测
- 5/23 17:30 再次执行 (Founder 准备测试)

memory 关联:
- KEY_LEARNINGS #47: 不凭 agent 自报, PM 自跑 verify
- KEY_LEARNINGS #58: destructive git 前 commit/stash
- DEC-050 SECRET_HANDLING_PROTOCOL
