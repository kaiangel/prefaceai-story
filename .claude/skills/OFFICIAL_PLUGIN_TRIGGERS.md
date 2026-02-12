# Claude Official Plugins 中英文触发词映射

> 本文档定义 claude-plugins-official 官方插件的中英文触发词，包括专业术语和大白话表达。

---

## 快速查找表

| Plugin | Skill | 命令 | 专业中文 | 大白话中文 |
|--------|-------|------|---------|-----------|
| commit-commands | commit | `/commit` | 提交代码、git commit | 保存代码、提交改动 |
| commit-commands | commit-push-pr | `/commit-push-pr` | 提交并创建PR | 提交代码开PR |
| commit-commands | clean_gone | `/clean_gone` | 清理已删除分支 | 清理没用的分支 |
| code-review | code-review | `/code-review` | 代码审查、PR审查 | 帮我看看代码、检查代码 |
| feature-dev | feature-dev | `/feature-dev` | 功能开发、特性开发 | 帮我写新功能、开发需求 |
| frontend-design | frontend-design | `/frontend-design` | 前端设计、UI设计 | 帮我设计界面、画页面 |
| pr-review-toolkit | (多个agent) | 自动触发 | PR审查工具集 | 专业代码审查 |
| hookify | hookify | `/hookify` | 创建Hook规则 | 设置保护规则 |
| pyright-lsp | - | 自动 | Python类型检查 | Python代码提示 |
| security-guidance | - | 自动 | 安全指导 | 安全建议、防止漏洞 |

---

## 1. commit-commands 插件

### commit - 提交代码

**命令**: `/commit`

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 提交代码、git commit、暂存、staged、提交信息、commit message |
| **大白话中文** | 保存代码、提交改动、把代码存一下、记录这次修改 |
| **English** | commit, save changes, git commit, stage changes |

**使用场景**:
- 完成一个功能/修复后需要提交
- 写完代码想保存进度

---

### commit-push-pr - 提交并创建PR

**命令**: `/commit-push-pr`

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 提交并创建PR、push、pull request、合并请求 |
| **大白话中文** | 提交代码开PR、推上去开个PR、提交然后让别人review |
| **English** | commit and PR, push and create PR, open pull request |

**使用场景**:
- 功能开发完成，准备提交审查
- 需要一步完成 commit + push + 创建 PR

---

### clean_gone - 清理已删除分支

**命令**: `/clean_gone`

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 清理gone分支、删除本地过期分支、分支清理 |
| **大白话中文** | 清理没用的分支、删掉已合并的分支、分支太多了清理下 |
| **English** | clean branches, remove gone branches, prune local branches |

**使用场景**:
- 本地分支太多，需要清理已经在远程删除的分支
- 项目整理

---

## 2. code-review 插件

### code-review - 代码审查

**命令**: `/code-review`

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 代码审查、PR审查、code review、代码检查、审查变更 |
| **大白话中文** | 帮我看看代码、检查下代码有没有问题、review一下、帮我审查 |
| **English** | code review, review PR, check my code, review changes |

**使用场景**:
- 提交代码前想让 Claude 先审查
- 收到 PR 需要审查
- 想检查代码质量

**审查内容**:
- 代码逻辑正确性
- 潜在 bug
- 代码风格
- 性能问题
- 安全问题

---

## 3. feature-dev 插件

### feature-dev - 功能开发引导

**命令**: `/feature-dev`

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 功能开发、特性开发、需求实现、feature开发 |
| **大白话中文** | 帮我写新功能、开发这个需求、实现这个特性、加个新功能 |
| **English** | feature development, implement feature, new feature, develop requirement |

**使用场景**:
- 需要开发一个新功能
- 有明确的需求要实现
- 想要引导式的开发流程

**特点**:
- 先理解代码库架构
- 设计实现方案
- 分步骤实现
- 考虑测试和边界情况

---

## 4. frontend-design 插件

### frontend-design - 前端设计

**命令**: `/frontend-design`

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 前端设计、UI设计、界面设计、组件设计、页面布局 |
| **大白话中文** | 帮我设计界面、画个页面、设计一下UI、这个页面怎么做 |
| **English** | frontend design, UI design, page layout, component design |

**使用场景**:
- 需要设计新页面或组件
- 想要 UI/UX 建议
- 需要前端架构规划

---

## 5. pr-review-toolkit 插件

### PR审查工具集 - 多专业Agent

**触发方式**: 关键词自动触发相应 agent

| Agent | 触发短语 | 职责 |
|-------|---------|------|
| **comment-analyzer** | "检查注释是否准确" | 代码注释准确性分析 |
| **pr-test-analyzer** | "测试覆盖是否充分" | 测试覆盖率和质量分析 |
| **silent-failure-hunter** | "检查错误处理" | 静默失败和异常处理检测 |
| **type-design-analyzer** | "审查类型设计" | 类型设计质量评估（1-10分） |
| **code-reviewer** | "审查代码" | 通用代码审查 |
| **code-simplifier** | "简化这段代码" | 代码简化和重构建议 |

| 类型 | 触发词 |
|------|--------|
| **专业中文** | PR审查、测试覆盖、错误处理、类型设计、代码简化、注释检查 |
| **大白话中文** | 帮我检查PR、测试够不够、错误处理对不对、类型设计合理吗、代码太复杂了 |
| **English** | PR review, test coverage, error handling, type design, code simplification |

**使用示例**:
```
# 专项检查
"检查测试覆盖是否充分"
"审查这个 PR 的错误处理"
"检查类型设计是否合理"

# 综合审查
"请完整审查这个 PR：
1. 测试覆盖
2. 错误处理
3. 代码注释
4. 类型设计"
```

---

## 6. hookify 插件

### hookify - 创建保护规则

**命令**: `/hookify [规则描述]`

| 类型 | 触发词 |
|------|--------|
| **专业中文** | Hook规则、保护规则、安全防护、阻止危险命令 |
| **大白话中文** | 设置保护规则、阻止危险操作、加个提醒、别让我误删 |
| **English** | hook rules, protection rules, safety guard, block dangerous commands |

**常用命令**:
```bash
/hookify 警告我使用 rm -rf 命令      # 创建警告规则
/hookify 编辑 .env 文件时需要确认    # 创建确认规则
/hookify 阻止 git push origin main  # 创建阻止规则
/hookify:list                        # 查看所有规则
/hookify:configure                   # 配置规则启用/禁用
```

**推荐规则**:
```
1. 阻止 rm -rf / 等危险命令
2. 编辑 .env、credentials 需确认
3. 阻止 push --force 到 main/master
4. 编辑 Dockerfile 时警告
5. 修改部署配置时需确认
```

**规则文件位置**: `/.claude/hookify.*.local.md`

---

## 7. pyright-lsp 插件

### pyright-lsp - Python 类型检查

**触发方式**: 自动（编辑 Python 文件时）

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 类型检查、类型注解、类型提示、Pyright、LSP |
| **大白话中文** | Python代码提示、类型错了、参数类型不对、返回值类型 |
| **English** | type check, type hint, type annotation, pyright, LSP |

**功能**:
- 实时类型检查
- 代码补全
- 跳转到定义
- 查找引用
- 悬停提示

**使用场景**:
- 编写 Python 代码时自动激活
- 需要检查类型错误
- 需要代码智能提示

---

## 8. security-guidance 插件

### security-guidance - 安全指导

**触发方式**: 自动（检测到潜在安全问题时）

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 安全漏洞、安全审计、OWASP、SQL注入、XSS、CSRF |
| **大白话中文** | 代码安全吗、有没有漏洞、会不会被攻击、安全问题 |
| **English** | security, vulnerability, injection, XSS, CSRF, OWASP |

**覆盖范围**:
- SQL 注入防护
- XSS 跨站脚本
- CSRF 跨站请求伪造
- 命令注入
- 敏感信息泄露
- 认证/授权问题

**使用场景**:
- 编写涉及用户输入的代码
- 处理敏感数据
- 实现认证/授权逻辑
- 代码安全审查

---

## 组合使用场景

### 场景1: 完整开发流程

```
1. /feature-dev     # 开发新功能
2. /code-review     # 自我审查
3. /commit-push-pr  # 提交并开PR
```

### 场景2: 前端开发流程

```
1. /frontend-design  # 设计界面
2. /feature-dev      # 实现功能
3. /code-review      # 审查代码
4. /commit-push-pr   # 提交PR
```

### 场景3: PR专业审查

```
# 使用 pr-review-toolkit
"请审查这个PR的测试覆盖和错误处理"
```

### 场景4: 安全防护设置

```
/hookify 编辑 image_generator.py 时提醒我检查 use_pro_model
/hookify:list  # 查看已设置的规则
```

### 场景5: 日常提交

```
# 小改动
/commit

# 准备合并
/commit-push-pr
```

### 场景6: 项目整理

```
/clean_gone  # 清理无用分支
```

---

## 与其他 Skills 的关系

| 插件类型 | 来源 | 触发方式 |
|---------|------|---------|
| **Official Plugins** | claude-plugins-official | `/命令` 触发 |
| **Context Engineering** | context-engineering-marketplace | 关键词触发 |
| **xuhuastory Skills** | 本地 /.claude/skills/ | 读取文件 |

---

## 触发词映射文件汇总

```
/.claude/skills/
├── OFFICIAL_PLUGIN_TRIGGERS.md        # 本文件 - 官方插件
├── CONTEXT_ENGINEERING_TRIGGERS.md    # Context Engineering (11 skills)
└── XUHUASTORY_SKILL_TRIGGERS.md       # xuhuastory专属 (4 skills)
```
