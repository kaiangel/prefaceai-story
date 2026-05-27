# full-retrospective — 全维度地毯式深度回溯

> e2e 测试 / 阶段性工作后, 对全程所有 bug 和问题逐条根因深挖 + 最佳方案, 毫无遗漏。
> 核心信条: **不凭记忆 · 不信自报 · 追完整调用栈 · 实测纠正纸面 · 区分本地vs生产 · 像素级看图**

---

## 用途

- Founder 跑完一轮 e2e 测试 (如 test28) 后, 系统回溯全程问题
- 阶段性工作 (一个 Wave) 收尾后的全维度复盘
- Founder 明确要求 "全维度地毯式深度回溯, 不要有任何遗漏"

产出: `analysis/{TESTNAME}_FULL_RETROSPECTIVE_{date}.md` 文档 + 更新 PENDING + 关键教训进 KEY_LEARNINGS。

---

## 完整流程 (6 步, 按顺序)

### Step 1: 全量挖日志 — 不凭记忆, 逐条 grep

⚠️ **不能凭监控中的记忆写问题清单** — 必须 grep 三日志全量, 可能有监控中漏掉的。

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
# A. backend.log 全量 ERROR/CRITICAL (排除 sqlalchemy INFO 噪声)
grep -E "ERROR|CRITICAL" logs/backend.log | grep -v "INFO sqlalchemy" | grep -vE "raise |^\s+File|Traceback" | sort | uniq -c | sort -rn
# B. backend.log 全量 WARNING (归一化数字后 uniq, 看模式)
grep "WARNING" logs/backend.log | grep -v "INFO sqlalchemy" | sed -E 's/[0-9]{3,}/N/g; s/Shot [0-9]+/Shot N/g' | sort | uniq -c | sort -rn
# C. 关键机制计数 (重试/fallback/FAIL/CONTENT_SAFETY/MySQL/BGM)
echo "IncompleteRead #1/#2/#3+: $(grep -c '重试 #1' logs/backend.log)/$(grep -c '重试 #2' logs/backend.log)/$(grep -cE '重试 #[3-9]' logs/backend.log)"
echo "ShotValidator PASS/FAIL: $(grep -c 'valid=True' logs/backend.log)/$(grep -c 'valid=False' logs/backend.log)"
echo "CONTENT_SAFETY/MySQL2003/500/BGM_FAIL/Gemini_fallback: ..."
# D. client.log 全量分类 (前端 UX/性能问题在这) — 区分 routine 良性 vs 真异常
grep -iE '"level": ?"(error|network|promise-reject)"' logs/client.log | grep -vE "routine|non-fatal" | ...
# E. frontend.log 全量 error/warn (next dev server)
grep -iE "error|warn|failed|fatal" logs/frontend.log | grep -viE "Compiled|compiling|✓|ready in"
```

记录: 全量异常列表 + 健康兜底计数 (哪些 fallback/retry 正常工作)。

### Step 2: 根因深挖 — 追完整调用栈, 不拿字符串反推

对每个问题, **追完整调用栈** (不能停在"看到的字符串"):
```
现象 → grep 定位组件/端点 → 读【实际代码】(非注释/非自报) → 追调用链(定义→调用点→数据流→消费点) → 定位真根因
```
⚠️ **铁律**: 
- 不拿"看到的字符串"反推数据源 (test28 教训: 看到 hydrate timeout 就推"拉全列表"是**错的**, 实际单项目+公网延迟)
- 注释说的 ≠ 代码做的 (查实际代码逻辑)
- "已修复"汇报 ≠ 真修复 (对照任务清单逐条 + 实测)

### Step 3: 实测验证 — 纠正纸面判断 (本步最容易出真相)

⚠️ **不信代码审查通过 / 不信 agent 自报 / 不信验证器 PASS** — 亲自实测:
```bash
# pytest 必用 venv (system python 无 fastapi)
venv/bin/python3 -m pytest tests/xxx.py -q
# curl 测端点状态码 + 耗时
curl -s -o /dev/null -w "HTTP %{http_code} %{time_total}s" <url>
# sips 测图片实际尺寸 (验证画幅 aspect_ratio)
sips -g pixelWidth -g pixelHeight <shot.png>   # 3:4 = 0.75
# TCP 测网络延迟 (本地连阿里云 MySQL 公网往返)
python3 -c "import time,socket; t=time.time(); socket.create_connection(('101.132.69.232',3306),5).close(); print(f'{(time.time()-t)*1000:.0f}ms')"
# 像素级看图 (Read 图片) — 不信 ShotValidator PASS, 人眼复核手部/解剖
```
**实证教训 (test28)**:
- TCP 实测阿里云 MySQL 公网往返 333-684ms → 纠正"全列表 N+1"误判, 找到真根因(公网延迟)
- 像素级看 Shot 19 → 纠正 ShotValidator "PASS"(实际手仍畸形)
- 404 分级: layout.tsx 正则匹配存在(代码审查过), 但实测 0 routine-404 → 代码审查≠实测生效
- sips 测 shot 1664×2218=0.75 → 验证 3:4 画幅用户选择真生效

### Step 4: 区分本地开发 vs 生产环境

⚠️ 很多"问题"是本地开发特有, 生产不复现 / 或相反:
- **阿里云 MySQL**: 本地连【公网】(333ms/往返), 生产 VPS 在【内网】(<1ms) — 性能慢主要本地特有
- **数据累积**: 本地累积 N 个测试项目放大查询慢, 生产单用户不同
- **HMR vs 重启**: frontend next dev HMR 自动 reload, backend nohup 无 --reload 需手动重启 (改了代码不重启=测旧代码!)
- **uvicorn --reload**: 本地禁用 (+ 阿里云 MySQL = metadata lock 死锁)
判断每个问题: 本地特有? 生产复现? 生产更糟? — 给分层方案 (生产无法本地复现的, 标注"VPS 实测确认")

### Step 5: 每个问题输出结构

```
### [优先级] 问题标题
- 现象: (用户视角 + 日志证据)
- 根因深挖: (完整调用栈 + 实测证据, 标注纠正的误判)
- 环境判断: (本地特有 / 生产复现 / 生产改善)
- 最佳方案: (分层, 治本+兜底)
- 派: (Agent + 时机)
```
优先级: 🔴P1(内测前必修/阻塞) 🟡P2(体验, 内测前) 🟢P3(轻微/产品考量/决定不修)

### Step 6: 输出物 (3 份, 缺一不可)

1. **回溯文档** `analysis/{TEST}_FULL_RETROSPECTIVE_{date}.md`: 概况+时间线 / 验证通过成果 / 问题清单(逐条根因+方案) / 健康兜底 / 与上轮对比 / 待办汇总表
2. **更新 PENDING**: 每个 P1/P2/P3 进 handoffs/PENDING.md (含派工 + 时机); 纠正的误判要标注作废
3. **关键教训进 KEY_LEARNINGS** (若有方法论级教训, 如"实测纠正纸面")

---

## 质量铁律 (地毯式审查铁律 + Ben 提醒)

1. **不凭记忆** — 逐条 grep 全量, 监控中的印象不算
2. **不信自报** — agent 报 PASS/pytest 通过/审查通过, 都自己实测验证
3. **追完整调用栈** — 函数定义→调用点→数据流→消费点, 不拿字符串反推 (feedback_trace_full_callstack_not_pattern)
4. **实测纠正纸面** — curl/sips/TCP/pytest/像素看图, 纸面判断必被实测检验
5. **区分本地vs生产** — 公网/内网、数据累积、HMR/重启, 别拿本地现象当生产结论
6. **像素级看图** — 不信 ShotValidator PASS, 人眼复核手部/解剖/画幅/一致性
7. **Ben 维度** (涉前后端/DB/架构): DEC-030 前后端契约一致性 + 共享 DB 边界 + 性能问题区分公网/内网
8. **根因修正要透明** — 挖出之前误判 (如"全列表"), 明确标注纠正, 不藏

---

## 实证教训 (这套流程的来源)

- **test26 回溯 (5/24)**: 8 问题 + 健康兜底 + 误报澄清(MySQL 2013 是 "cached since 2013s ago" 字符串误匹配)
- **test28 回溯 (5/25)**: 
  - 实测 TCP 333ms 公网延迟 → **纠正"全列表 N+1"误判** (真根因: 单项目+公网+并发+大字段)
  - 像素看 Shot 19 → 纠正 ShotValidator PASS (手仍畸形)
  - 404 分级 Wave B 代码审查过但实测 0 routine-404 → 代码审查≠实测生效
  - sips 验证 3:4 画幅用户选择真生效

memory 关联:
- feedback_carpet_review_deep_dive: 地毯式追完整调用链路
- feedback_trace_full_callstack_not_pattern: 追调用栈不拿字符串反推
- KEY_LEARNINGS #47: 不凭 agent 自报, PM 自跑 verify
- feedback_aspect_ratio_user_perception: 用户选择参数必须实测生效
- feedback_pipeline_single_model_only: 视觉一致性人眼复核
