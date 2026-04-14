# TASK-HARNESS-ENGINEERING-V1：序话Story Harness Engineering 升级

> **发起人**: Coordinator/Founder
> **执行协调**: PM
> **优先级**: P0（基础设施级改进，影响所有后续开发质量）
> **日期**: 2026-04-12

---

## 一、背景：什么是 Harness Engineering，为什么我们要做

### 核心公式
```
Agent = Model + Harness
```

Harness 是模型之外的一切——工具配置、权限控制、验证循环、沙箱环境、记忆系统、可观测性。决定 AI agent 成败的，不是模型本身，而是包裹模型的系统。

### 行业实证

**Can Boluk 实验**：不改模型，只改 harness 中的编辑格式（模型输出→代码修改的翻译层），Grok Code Fast 1 从 6.7% 跳到 68.3%。15 个模型全部提升，零训练成本。

**OpenAI Codex 实验**：3 人团队用 agent 写了 100 万行代码，0 行手写。核心靠三件事：
1. 强制分层架构（每层只能依赖下层，违反自动拦截）
2. 每个 PR 自动跑结构测试（测试不过就提交不了）
3. 机器可读文档作为唯一事实来源

### 我们的现状评估

| 维度 | 评分 | 说明 |
|------|------|------|
| Guides（前馈控制） | 8.5/10 | claude.md、agent 定义、协议做得很好 |
| Sensors（反馈控制） | 4/10 | 几乎没有自动化验证，全靠人/agent 手动 |
| 计算性控制 | 3/10 | 约束只存在于文档里，没有代码强制执行 |
| 编排设计 | 7.5/10 | 多 agent 协调机制精细，但有扩展性隐患 |

**核心问题**：我们的 Harness 严重偏科——Guide（前馈）做到了 8.5 分，但 Sensor（反馈）只有 4 分。这是 Bockeler 警告的 "feedforward-only" 模式："编码了规则但永远不知道规则是否生效"。

---

## 二、要修复的 6 个缺陷（CI/CD 除外）

### 缺陷 1：没有自动化验证循环（Sensor 最大缺口）
- **现状**：测试靠 Tester agent 手动跑，其他 agent 写完代码无任何自动检查
- **目标**：Agent 写代码 → Hook 自动类型检查 → Agent 提交 → Hook 自动跑测试 → 失败自动打回

### 缺陷 2：所有 Agent 共享同一套权限（无角色隔离）
- **现状**：settings.json 的 permissions 对所有 agent 都一样。Frontend agent 可以直接修改 app/services/ 里的后端代码，Backend agent 可以修改 frontend/src/ 的前端代码，AI-ML agent 可以跑 npm install 修改前端依赖。角色边界只存在于文档里（Guide），没有计算性强制执行（Sensor）。对比 Claude Code 自身的 harness：它有三级权限管道（Tier 1/2/3），还有一个独立模型在后台做分类——用代码强制执行，而不是靠"请遵守规则"。
- **目标**：通过架构测试（test_architecture.py 中的前后端隔离测试）+ 各 agent 的角色定义文档中明确"可修改文件范围"约束，在计算层面强制角色边界。由于 Claude Code 的 settings.json 不支持 per-agent 权限，我们用架构测试作为 Sensor 来弥补——agent 跨界修改的代码在 commit 时会被测试拦截。
- **具体措施**：
  1. test_architecture.py 已包含 `test_frontend_does_not_import_backend` 和 `test_backend_does_not_import_frontend`
  2. 在各 agent 的角色定义 .md 文件中增加"可修改文件白名单"章节（由 PM 在 Phase 2 执行）
  3. PreCommit hook 自动执行这些检查

### 缺陷 3：TEAM_CHAT.md 已 35,178 行（定时炸弹）
- **现状**：只增不减，无轮转/归档机制，agent 每次读最新内容消耗大量 context
- **目标**：自动归档机制，主文件只保留最近内容

### 缺陷 5：错误修复是临时的，没有系统化沉淀
- **现状**：发现 bug → 修 bug → 记到 DECISIONS.md。这是知识沉淀，不是工程化解决
- **目标**：每次 agent 犯错 → 工程化一个 sensor，让它结构上不可能再犯（Mitchell Hashimoto 原则）

### 缺陷 6：没有上下文预算管理
- **现状**：10 个 agent 每次开工要读的"必读文件"越来越长，无策略控制 context 消耗
- **目标**：明确每个角色的"必读/选读"文件清单，控制上下文预算

### 缺陷 7：Hooks 严重不足
- **现状**：只有 1 个 hook（清 Next.js 缓存）
- **目标**：加 Python 类型检查、TypeScript 编译检查、提交前自动测试

---

## 三、额外借鉴项（来自 Harness Engineering 研究）

### 借鉴 A：Pipeline 翻译层优化（Can Boluk 式）

**关键认知：我们已经在做 harness engineering，但没意识到。** 回顾项目历史，以下改动全是 Can Boluk 式的——零训练、零微调，只改 harness，质量直接跳档：

| 我们做过的 Harness 改动 | 改之前 | 改之后 | 本质 |
|------------------------|--------|--------|------|
| `_build_identity_line()` 加入完整物理描述 | 角色经常"变脸" | 3人场景 100% 一致性 | 改了 prompt 拼装格式 |
| 只传 fullbody 给 shot generation（去掉 portrait） | 信息过载，模型混淆 | 模型清晰理解角色 | 改了输入筛选规则 |
| StyleEnforcer 前置（最高注意力权重） | 风格漂移 | 风格稳定 | 改了 prompt 元素排序 |
| No-text prompt + 后处理 TextOverlay | Gemini 画不了中文字 | 42/42 shots PASS, 4.9/5 | 绕过模型缺陷的 harness 设计 |
| Flash 做 reference + Pro 做 shot | Flash 70-80% 一致性 | Pro 100% 一致性 | 改了模型分配策略 |

**这些改动本质上和 Can Boluk 做的完全一样——不改模型，只改包裹模型的系统，性能就跳了一个档。** 现在我们要做的是**系统性、有意识地**审视 Pipeline 每个阶段的翻译层，而不是靠踩坑后的被动优化。

我们的 Pipeline 有 6 个翻译层（Outline → Character → Screenplay → Storyboard → Shot Prompt → Image），每个翻译层的数据格式和 prompt 组装方式都是 "harness 组件"。优化这些翻译层可能带来 Can Boluk 式的性能跳涨。

**Stage 1（Outline）→ Stage 2（Character Design）的翻译层**：
- 故事大纲里的角色描述怎么转换成 Character Design 的 prompt？
- 描述的顺序、详细程度、措辞方式，可能直接影响角色设计的质量
- 我们刚完成的 AM-1（Stage 1 prompt 新增 `description_zh` 字段）就是这种翻译层优化——不改模型，只改了阶段间数据传递的格式，就增加了场景的中文氛围表达能力

**Stage 4（Storyboard）→ Stage 5（Shot Image）的翻译层**（重点关注）：
- 分镜指令怎么转成 image prompt？
- camera_angle、shot_type、characters_in_scene 的拼装顺序和格式
- 相同信息，不同格式，可能导致截然不同的生成结果。例如：
  - 格式A："A medium shot of Zhang Wei (tall, athletic build, sharp jawline...) standing in a dimly lit alley"
  - 格式B："Dimly lit alley. Medium shot. Zhang Wei stands in center. He is tall, athletic build, sharp jawline..."
  - 同样的信息，但格式A把角色嵌入句子，格式B用断句分隔——哪个让 Gemini 生成更好的图？需要实验验证
- 当前的 `unified_prompt_builder.py` + `shot_prompt_generator.py` + `character_prompt_builder.py` 的组装顺序、格式、措辞，可能不是最优的

### 借鉴 B：结构性测试（OpenAI Codex 式）
用代码强制执行架构规则：
- Shot 生成必须用 Pro 模型
- Image prompt 不能包含中文
- 前端代码不能引用后端模块
- Pipeline 阶段顺序不可跳过

### 借鉴 C：Bockeler 的三大调节领域
| 领域 | 关注点 | 我们的成熟度 | 需要做的 |
|------|--------|------------|---------|
| 可维护性 Harness | 代码质量 | 中 | 加 pyright/tsc 自动检查 |
| 架构适应度 Harness | 结构约束 | 低 | 加架构测试 |
| 行为 Harness | 功能正确性 | 中 | 加质量门测试（一致性阈值） |

### 借鉴 D：Anthropic 的洞察
"Harness 的每个组件都编码了一个关于'模型靠自己做不到什么'的假设。随着模型变强，有些组件可以简化。"——这意味着 harness 是活的，需要持续审视。

---

## 四、任务分解与派发

### Phase 1：自动化 Sensor 基础设施（P0，立即执行）

---

#### TASK-HE-DEVOPS-1：Hook 基础设施升级
**派发给**: @devops
**优先级**: P0
**预计工作量**: 30 分钟

**具体任务**：修改 `.claude/settings.local.json`，将现有的 hooks 部分替换为以下完整配置：

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "FILE=\"$CLAUDE_FILE\"; if [[ \"$FILE\" == *.py ]]; then cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story && python -m pyright \"$FILE\" 2>&1 | tail -8; elif [[ \"$FILE\" == *.tsx || \"$FILE\" == *.ts ]]; then cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story/frontend && npx tsc --noEmit 2>&1 | tail -10; rm -rf .next/cache 2>/dev/null; fi"
          }
        ]
      }
    ],
    "PreCommit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story && python -m pytest tests/test_architecture.py tests/test_quality_gates.py -x -q --timeout=120 2>&1 | tail -20"
          }
        ]
      }
    ],
    "PrePush": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story && python -m pytest tests/ -x -q --timeout=300 2>&1 | tail -30"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "Bash(find:*)",
      "Bash(source:*)",
      "Bash(python:*)",
      "Bash(cat:*)",
      "Bash(ls:*)",
      "WebSearch",
      "WebFetch(domain:github.com)",
      "WebFetch(domain:raw.githubusercontent.com)",
      "WebFetch(domain:api.github.com)",
      "Bash(git clone:*)",
      "Bash(python3:*)",
      "Bash(pip3 install:*)",
      "Bash(xargs:*)",
      "Bash(timeout 30 python3:*)",
      "Bash(grep:*)",
      "WebFetch(domain:tongyi.aliyun.com)",
      "WebFetch(domain:www.vidu.com)"
    ]
  }
}
```

**关键变化**：
1. PostToolUse hook 合并为一条：Python 文件用 pyright 检查，TypeScript 文件用 tsc 检查 + 清缓存
2. 新增 PreCommit hook：提交前自动跑架构测试和质量门测试（这两个测试文件由 @tester 创建）
3. 新增 PrePush hook：推送前跑完整测试套件（timeout 300秒，覆盖所有 tests/ 下的测试）——这是最后一道防线，确保坏代码不会推到远程

**验收标准**：
- 编辑任意 `.py` 文件后，终端自动出现 pyright 检查结果
- 编辑任意 `.tsx` 文件后，终端自动出现 tsc 编译结果
- git commit 前自动跑架构测试 + 质量门测试，测试失败则提交被阻止
- git push 前自动跑完整测试套件，测试失败则推送被阻止
- 现有功能（Next.js 缓存清理）不受影响

**注意**：PreCommit hook 依赖 @tester 创建的 `tests/test_architecture.py` 和 `tests/test_quality_gates.py`，在这两个文件就绪前，先用 `python -m pytest tests/test_architecture.py -x -q --timeout=120 2>&1 | tail -20 || true` 避免阻塞。待 @tester 完成后去掉 `|| true`。

---

#### TASK-HE-TESTER-1：架构测试 + 质量门测试
**派发给**: @tester
**优先级**: P0
**预计工作量**: 2-3 小时

**具体任务 A**：创建 `tests/test_architecture.py`——结构性约束的计算性 Sensor

```python
"""
架构适应度测试 - Harness Engineering Sensor
用代码强制执行架构规则，而不是靠文档+自觉
灵感来源：OpenAI Codex 实验的"强制分层架构"
"""
import ast
import os
import re
import glob

# === 1. 前后端边界隔离 ===

def test_frontend_does_not_import_backend():
    """前端 TypeScript 不应直接引用后端 Python 模块路径"""
    frontend_dir = "frontend/src"
    violations = []
    for root, dirs, files in os.walk(frontend_dir):
        for f in files:
            if f.endswith(('.ts', '.tsx')):
                filepath = os.path.join(root, f)
                content = open(filepath).read()
                if 'from app/' in content or 'import app.' in content:
                    violations.append(filepath)
    assert not violations, f"前端文件直接引用了后端模块: {violations}"

def test_backend_does_not_import_frontend():
    """后端 Python 不应引用前端模块"""
    backend_dir = "app"
    violations = []
    for root, dirs, files in os.walk(backend_dir):
        for f in files:
            if f.endswith('.py'):
                filepath = os.path.join(root, f)
                content = open(filepath).read()
                if 'from frontend' in content or 'import frontend' in content:
                    violations.append(filepath)
    assert not violations, f"后端文件引用了前端模块: {violations}"

# === 2. 核心架构规则：Shot 生成必须用 Pro 模型 ===

def test_shot_generation_uses_pro_model():
    """Shot 图像生成的默认配置必须使用 Pro 模型（一致性生命线）"""
    target_file = "app/services/image_generator.py"
    if not os.path.exists(target_file):
        return  # 文件不存在时跳过
    content = open(target_file).read()
    # 检查 generate_shot_image 或类似函数中是否有 pro model 相关配置
    # 具体断言逻辑需要根据实际代码结构调整
    assert 'pro' in content.lower() or 'PRO_MODEL' in content, \
        "image_generator.py 中未找到 Pro 模型配置，Shot 生成必须使用 Pro 模型"

# === 3. Image Prompt 语言规则：不能包含中文 ===

def test_prompt_templates_are_english():
    """所有 image prompt 模板和构建函数的输出应为英文"""
    prompt_files = glob.glob("app/services/*prompt*.py") + \
                   glob.glob("app/services/*style*.py")
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    violations = []
    for filepath in prompt_files:
        content = open(filepath).read()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            # 检查函数返回的字符串常量中是否有中文
            # 排除注释和 docstring，只检查实际的 prompt 字符串
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if chinese_pattern.search(node.value):
                    # 排除 docstring、注释、描述性字符串
                    val = node.value.strip()
                    # 如果是以 prompt/image/shot 相关关键词开头的，标记为违规
                    if len(val) > 20 and 'prompt' not in val.lower():
                        continue  # 可能是文档字符串，跳过
                    # 需要根据实际代码进一步细化判断逻辑
    # 注意：这个测试需要 @tester 根据实际 prompt builder 代码结构调整
    # 核心意图是确保 image prompt 输出不会混入中文

# === 4. Pipeline 阶段文件完整性 ===

def test_pipeline_services_exist():
    """5 阶段 Pipeline 的核心服务文件必须存在"""
    required_services = [
        "app/services/story_outline_generator.py",      # Stage 1
        "app/services/character_designer.py",            # Stage 2
        "app/services/screenplay_writer.py",             # Stage 3
        "app/services/storyboard_director.py",           # Stage 4
        "app/services/image_generator.py",               # Stage 5
    ]
    missing = [f for f in required_services if not os.path.exists(f)]
    assert not missing, f"Pipeline 核心服务文件缺失: {missing}"

# === 5. 参考图生成策略：必须串行（portrait → fullbody） ===

def test_reference_generation_is_serial():
    """参考图生成必须是串行的（先 portrait 再 fullbody），不能并行"""
    target_file = "app/services/image_generator.py"
    if not os.path.exists(target_file):
        return
    content = open(target_file).read()
    # 检查是否存在 asyncio.gather 同时生成 portrait 和 fullbody 的模式
    # 这是曾经导致"不像同一个人"的 bug
    if 'portrait' in content and 'fullbody' in content:
        # 确认没有将两者放入同一个 gather/parallel 执行
        assert 'gather' not in content or \
               content.index('portrait') < content.index('fullbody'), \
            "参考图必须串行生成：先 portrait，再用 portrait 作为参考生成 fullbody"

# === 6. 数据格式不向后兼容 ===

def test_no_backward_compat_code():
    """不应存在旧格式兼容代码（Founder 核心原则：No backward compatibility）"""
    # 检查是否有 field1 or field2 这种兼容模式
    # 这个测试作为提醒性检查，具体阈值需根据项目调整
    pass  # @tester 根据实际代码模式实现
```

**具体任务 B**：创建 `tests/test_quality_gates.py`——质量阈值的计算性 Sensor

```python
"""
质量门测试 - Harness Engineering Sensor
将口头的质量标准转化为可执行的自动检查
"""
import json
import os

# === 1. Story JSON Schema 验证 ===

def test_story_json_schema():
    """story.json 输出必须包含必需字段"""
    required_character_fields = [
        'name', 'name_en', 'gender', 'age_appearance',
        'character_type', 'physical', 'clothing'
    ]
    required_physical_fields = [
        'height', 'build', 'skin_tone', 'face_shape',
        'hair_color', 'hair_style', 'eye_color'
    ]
    # 检查 test_output 目录下最新的 story.json（如果存在）
    test_outputs = sorted(
        [d for d in os.listdir('test_output') if os.path.isdir(f'test_output/{d}')],
        reverse=True
    ) if os.path.exists('test_output') else []
    
    for output_dir in test_outputs[:3]:  # 只检查最近 3 个
        story_path = f'test_output/{output_dir}/story.json'
        if os.path.exists(story_path):
            data = json.load(open(story_path))
            if 'characters' in data:
                for char in data['characters']:
                    for field in required_character_fields:
                        assert field in char, \
                            f"{story_path}: 角色 {char.get('name', '?')} 缺少必需字段 '{field}'"

# === 2. Prompt 语言纯净性 ===

def test_image_prompts_no_chinese():
    """生成的 image prompt 不应包含中文字符"""
    import re
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    
    if not os.path.exists('test_output'):
        return
    
    test_outputs = sorted(
        [d for d in os.listdir('test_output') if os.path.isdir(f'test_output/{d}')],
        reverse=True
    )
    
    for output_dir in test_outputs[:3]:
        shots_path = f'test_output/{output_dir}/shots.json'
        if os.path.exists(shots_path):
            data = json.load(open(shots_path))
            if isinstance(data, list):
                for shot in data:
                    prompt = shot.get('image_prompt', '')
                    if chinese_pattern.search(prompt):
                        # narration 可以是中文，但 image_prompt 必须是英文
                        assert False, \
                            f"{shots_path}: shot {shot.get('shot_id', '?')} 的 image_prompt 包含中文"

# === 3. 配置完整性 ===

def test_env_example_exists():
    """.env.example 必须存在且包含所有必需变量"""
    assert os.path.exists('.env.example'), ".env.example 文件缺失"

def test_required_directories():
    """项目必需目录必须存在"""
    required = ['app/services', 'frontend/src', 'tests']
    missing = [d for d in required if not os.path.isdir(d)]
    assert not missing, f"必需目录缺失: {missing}"
```

**注意事项**：
- 这些测试是**结构性测试**（Architecture Fitness Tests），不是功能测试
- 它们检查的是"代码结构是否符合架构约束"，不是"功能是否正确"
- 运行时间必须 < 10 秒（因为会在每次 commit 前自动执行）
- @tester 需要根据实际代码结构调整断言逻辑，上面的代码是框架/方向，具体实现需要阅读对应源文件后细化
- 特别是 `test_shot_generation_uses_pro_model` 和 `test_reference_generation_is_serial`，需要读 `image_generator.py` 的实际函数结构来写准确的断言

**验收标准**：
- `python -m pytest tests/test_architecture.py tests/test_quality_gates.py -v` 全部 PASS
- 执行时间 < 10 秒
- 每个测试函数都有清晰的 docstring 说明它在保护什么架构规则

---

### Phase 2：信息治理 + 错误系统化（P1，Phase 1 完成后执行）

---

#### TASK-HE-DEVOPS-2：TEAM_CHAT 归档机制
**派发给**: @devops
**优先级**: P1
**预计工作量**: 1 小时

**具体任务**：创建 `scripts/archive_team_chat.sh` 脚本

功能要求：
1. 将 `.team-brain/TEAM_CHAT.md` 中 7 天前的消息移到 `.team-brain/chat-archive/YYYY-MM.md`
2. 主文件只保留最近 7 天的消息 + 文件头部说明
3. 归档文件按月分割
4. 归档时保留完整消息格式（时间戳、@agent、内容）
5. 脚本需要幂等（跑多次结果一样）

**额外任务**：在 `.team-brain/TEAM_CHAT.md` 头部加入说明：
```markdown
> 历史消息已归档到 `.team-brain/chat-archive/YYYY-MM.md`
> 归档脚本: `scripts/archive_team_chat.sh`
```

**验收标准**：
- 跑完脚本后，TEAM_CHAT.md 行数 < 3000
- 归档文件内容完整，无丢失
- 再跑一次脚本，结果不变（幂等）

---

#### TASK-HE-PM-1：错误模式追踪系统
**PM 自己执行**
**优先级**: P1
**预计工作量**: 1 小时

**具体任务**：创建 `.team-brain/knowledge/ERROR_PATTERNS.md`

格式：
```markdown
# 错误模式追踪

> Mitchell Hashimoto 原则：每次 agent 犯错 → 工程化一个解决方案，让它结构上不可能再犯。
> "不要去改 prompt，去改 harness。"

## 错误模式记录模板

### EP-XXX: [错误标题]
- **发现日期**: YYYY-MM-DD
- **发现者**: @agent
- **错误描述**: [什么出了问题]
- **根因分析**: [为什么出问题]
- **修复方式**: [怎么修的]
- **工程化防护**: [加了什么 sensor/test/hook 来防止再犯]
- **防护状态**: ✅ 已加 / ❌ 仅文档记录（需补 sensor）

## 已记录的错误模式

### EP-001: Flash 模型 shot 生成一致性不足
- **发现日期**: 2025 Phase 2 开发期
- **根因**: Flash 模型多人场景角色特征混淆
- **修复**: 切换 shot 生成到 Pro 模型
- **工程化防护**: ✅ test_architecture.py::test_shot_generation_uses_pro_model

### EP-002: Portrait + Fullbody 同时传给 shot 生成导致信息过载
- **发现日期**: 2025 Phase 2 开发期
- **根因**: 模型处理过多参考图时产生混淆
- **修复**: 只传 fullbody
- **工程化防护**: ✅ test_architecture.py::test_reference_generation_is_serial

### EP-003: Image prompt 混入中文导致图像质量下降
- **发现日期**: Phase 2
- **根因**: Narration 中文内容泄漏到 image prompt
- **修复**: Prompt 构建函数强制英文
- **工程化防护**: ✅ test_quality_gates.py::test_image_prompts_no_chinese
```

**目标**：回顾项目历史中所有已知的 bug/错误决策，将它们记录到 ERROR_PATTERNS.md 中，并标注每个错误是否已有工程化防护（test/hook）。没有防护的，记为 ❌，后续由 @tester 补充 sensor。

**验收标准**：
- 至少记录 10 个历史错误模式（从 DECISIONS.md、KEY_LEARNINGS.md、TEAM_CHAT 历史中提取）
- 每个错误都有"工程化防护状态"标注

---

#### TASK-HE-PM-2：上下文预算管理
**PM 自己执行**
**优先级**: P1
**预计工作量**: 30 分钟

**具体任务**：在 `TEAM_PROTOCOL.md` 中新增"上下文预算管理"章节

内容：为每个角色定义分级阅读清单：

```markdown
## 上下文预算管理

### 原则
- 每个 Agent 的"必读"文件总量控制在 context window 的 30% 以内
- 超过 30% 的信息通过"按需阅读"获取
- 优先读 context-for-others.md（精炼信息），而非完整源文件

### 各角色阅读清单

#### Backend Agent
**必读（每次开工）**:
1. `.claude/agents/backend-progress/current.md` — 自己的进度
2. `.team-brain/status/TODAY_FOCUS.md` — 今日重点
3. `.claude/agents/pm-progress/context-for-others.md` — PM 的最新指令
4. `.claude/agents/ai-ml-progress/context-for-others.md` — prompt 约束更新

**按需阅读**:
- `.claude/agents/frontend-progress/context-for-others.md` — 有 API 对接时
- `.claude/agents/tester-progress/context-for-others.md` — 有测试反馈时
- `claude.md` 的对应技术章节 — 需要确认架构约束时

**不需要读**:
- TEAM_CHAT.md 全文（太长，PM 会在 context-for-others 里摘要关键信息）
- 其他 agent 的 completed.md（除非需要了解历史）
- resonance 的所有进度文件

#### Frontend Agent
**必读**: 同 Backend，将 ai-ml 替换为 backend（关注 API 状态）
**按需**: 同上
**不需要读**: ai-ml 的进度（前端不需要了解 prompt 约束细节）

#### AI-ML Agent
**必读**: 自己进度 + TODAY_FOCUS + PM context + Backend context
**按需**: Tester context（一致性测试结果）
**不需要读**: Frontend/DevOps 进度

#### Tester Agent
**必读**: 自己进度 + TODAY_FOCUS + PM context
**必读（额外）**: Backend + Frontend 的 context-for-others（了解最新代码改动）
**不需要读**: AI-ML 的 prompt 优化细节

#### DevOps Agent
**必读**: 自己进度 + TODAY_FOCUS + PM context
**按需**: Backend context（部署相关变更）
**不需要读**: AI-ML/Frontend 的进度

#### PM Agent
**必读**: 所有 agent 的 context-for-others.md（这是 PM 的核心职责）
**必读**: TODAY_FOCUS + PENDING.md + PROJECT_STATUS.md
**按需**: 各 agent 的 current.md（被阻塞时深入了解）
```

**验收标准**：
- 每个角色的"必读"清单不超过 5 个文件
- 清晰标注"不需要读"，减少 agent 的 context 消耗

---

### Phase 3：Pipeline 翻译层优化（P2，Phase 1-2 完成后执行）

---

#### TASK-HE-AIML-1：Prompt Format A/B Testing
**派发给**: @ai-ml
**优先级**: P2
**预计工作量**: 1-2 天

**背景**：Can Boluk 的实验证明，仅改变 harness 中的"翻译格式"就能让 15 个模型全部提升。我们的 Pipeline 中，Stage 4→5 的翻译层（storyboard shot → image prompt）是最关键的翻译层，也是最可能存在优化空间的。

**具体任务**：

1. **选取测试基准**：选择一个包含 3 个角色、至少 10 个 shot 的测试故事（可以用现有的 teststory 6.x 系列）

2. **设计 3 种 prompt 组装格式变体**：

   **变体 A（当前格式）**：保持现有的 unified_prompt_builder + shot_prompt_generator 输出格式不变，作为 baseline

   **变体 B（场景优先格式）**：
   ```
   [SCENE] Dimly lit alley in Shanghai, rain-slicked concrete, neon reflections.
   [SHOT] Medium shot, eye-level angle, 35mm lens.
   [CHARACTER 1: Zhang Wei] Tall athletic man, sharp jawline, black leather jacket...
   [CHARACTER 2: Li Na] Petite woman, round face, red dress...
   [ACTION] Zhang Wei reaches for Li Na's hand.
   [STYLE] Cinematic, photorealistic, film grain, warm color palette.
   ```

   **变体 C（叙事优先格式）**：
   ```
   A cinematic medium shot in a rain-soaked Shanghai alley. Zhang Wei (tall, athletic, sharp jawline, wearing a black leather jacket) reaches toward Li Na (petite, round face, in a red dress). The scene is lit by neon reflections on wet concrete. Photorealistic style with film grain and warm tones.
   ```

3. **执行测试**：对每个变体，用相同的场景和角色数据，生成 10 个 shot 的图片。使用 Pro 模型。

4. **评估维度**：
   - 角色一致性（主观 1-5 分 + 客观特征匹配率）
   - 场景构图质量（是否符合 shot_type 和 camera_angle）
   - 风格一致性（10 个 shot 之间的风格连贯度）
   - Prompt token 消耗（不同格式的 token 效率）

5. **产出文档**：`/.team-brain/analysis/PROMPT_FORMAT_AB_TEST_AIML.md`，记录完整测试过程和结果

**验收标准**：
- 完成至少 3 种格式的对比测试
- 每种格式至少生成 10 张 shot 图
- 产出明确结论：哪种格式在各维度上最优
- 如果发现优于当前格式的变体，提出具体的代码修改方案给 @backend

---

#### TASK-HE-BACKEND-1：Pipeline 数据流 Schema 验证
**派发给**: @backend
**优先级**: P2
**预计工作量**: 2-3 小时

**具体任务**：为 Pipeline 阶段间的数据传递增加 Schema 验证

1. 在 `app/services/` 中创建 `pipeline_schemas.py`，用 Pydantic 定义每个阶段的输入/输出 schema：

```python
"""
Pipeline 阶段间数据 Schema - Harness Engineering 的 Sensor
确保阶段间数据传递的格式正确性
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re

class CharacterPhysical(BaseModel):
    height: str
    build: str
    skin_tone: str
    face_shape: str
    hair_color: str
    hair_style: str
    eye_color: str
    # ... 其他必需物理字段

class CharacterSchema(BaseModel):
    name: str
    name_en: str
    gender: str
    age_appearance: str
    character_type: str
    physical: CharacterPhysical
    clothing: dict  # 根据实际结构细化

class ShotSchema(BaseModel):
    shot_id: str
    scene_id: str
    image_prompt: str
    narration: str
    shot_type: str
    camera_angle: str
    
    @validator('image_prompt')
    def image_prompt_must_be_english(cls, v):
        """Image prompt 不能包含中文——核心约束"""
        if re.search(r'[\u4e00-\u9fff]', v):
            raise ValueError(f'image_prompt 包含中文字符: {v[:50]}...')
        return v
```

2. 在 Pipeline 的关键阶段转换点加入 Schema 验证调用（具体文件和位置需要读 `pipeline_orchestrator.py` 确定）

3. **Schema Validation 作为运行时 Sensor**：在 Pipeline 每个阶段转换时自动调用 Pydantic 验证。这对应之前缺失 hooks 表中的"修改 story.json 后验证 schema"——不是通过 hook 触发，而是直接嵌入 Pipeline 代码中。每次阶段间数据传递时，自动验证数据格式是否符合 schema，不符合立即抛出错误并中止 Pipeline，而不是让错误数据流到下游产生难以追溯的 bug。

**验收标准**：
- Pydantic schema 覆盖 story.json、characters、shots 三个核心数据结构
- `image_prompt` 的中文检测 validator 生效
- Schema 验证失败时抛出清晰的错误信息，指明哪个字段违规
- Pipeline 阶段转换处有 schema 验证调用（至少覆盖 Stage 1→2、Stage 4→5 两个关键转换点）

---

### Phase 4：持续维护（Ongoing）

---

#### TASK-HE-PM-3：Harness 健康度跟踪
**PM 持续维护**

创建 `.team-brain/status/HARNESS_HEALTH.md`：

```markdown
# Harness 健康度看板

> 上次更新: YYYY-MM-DD

## Sensor 覆盖率

| 架构规则 | 文档记录 | 自动化测试 | Hook 强制 |
|---------|---------|-----------|----------|
| Shot 用 Pro 模型 | ✅ claude.md | ✅ test_architecture | ❌ |
| Image prompt 纯英文 | ✅ claude.md | ✅ test_quality_gates | ✅ Schema validator |
| 参考图串行生成 | ✅ claude.md | ✅ test_architecture | ❌ |
| 前后端隔离 | ✅ TEAM_PROTOCOL | ✅ test_architecture | ❌ |
| Python 类型安全 | ❌ | ❌ | ✅ pyright hook |
| TS 编译安全 | ❌ | ❌ | ✅ tsc hook |
| 提交前测试 | ❌ | ✅ PreCommit hook | ✅ |

## 错误模式防护率

- 已记录错误模式: X 个
- 有工程化防护: Y 个
- 仅文档记录: Z 个
- **防护率**: Y/X = ??%

## 上下文预算

| Agent | 必读文件数 | 估计 token | 状态 |
|-------|----------|-----------|------|
| Backend | 4 | ~3000 | 🟢 |
| Frontend | 4 | ~3000 | 🟢 |
| PM | 8+ | ~6000 | 🟡 需关注 |

## TEAM_CHAT 文件状态

- 当前行数: ???
- 上次归档: ???
- 状态: 🟢/🟡/🔴
```

**更新频率**：每周一次，或每个重大 TASK 完成后更新

---

## 五、执行顺序与依赖关系

```
Phase 1（P0，立即）
  ├── TASK-HE-DEVOPS-1（hooks 配置）——无依赖，立即开始
  └── TASK-HE-TESTER-1（架构测试 + 质量门测试）——无依赖，立即开始
      ↓ 两者都完成后
      DevOps 去掉 PreCommit hook 里的 "|| true"，激活完整闭环

Phase 2（P1，Phase 1 完成后）
  ├── TASK-HE-DEVOPS-2（TEAM_CHAT 归档）——无依赖
  ├── TASK-HE-PM-1（错误模式追踪）——需要读 DECISIONS.md 和 KEY_LEARNINGS.md
  └── TASK-HE-PM-2（上下文预算管理）——无依赖

Phase 3（P2，Phase 2 完成后）
  ├── TASK-HE-AIML-1（Prompt Format A/B Test）——无依赖
  └── TASK-HE-BACKEND-1（Schema 验证）——无依赖

Phase 4（Ongoing）
  └── TASK-HE-PM-3（Harness 健康度跟踪）——依赖前述所有 Phase 完成
```

---

## 六、成功标准

完成后，我们的 Harness 评分应从：

| 维度 | 改前 | 改后目标 |
|------|------|---------|
| Guides（前馈） | 8.5/10 | 9/10（加了上下文预算管理） |
| Sensors（反馈） | 4/10 | **7/10**（hooks + 架构测试 + 质量门 + schema 验证） |
| 计算性控制 | 3/10 | **6/10**（pyright/tsc/PreCommit/Pydantic） |
| 编排设计 | 7.5/10 | 8/10（TEAM_CHAT 归档 + 错误追踪） |

**核心改变**：从 "feedforward-only"（只有规则但不知道是否执行）变为 "feedforward + feedback"（有规则，且自动验证规则是否被执行）。

---

## 七、给 PM 的执行指南

1. **立即行动**：将 Phase 1 的两个任务（TASK-HE-DEVOPS-1 和 TASK-HE-TESTER-1）派发给 @devops 和 @tester，两者可以并行
2. **跟踪进度**：让两个 agent 完成后更新各自的 progress 文件
3. **Review**：PM 验收 hooks 是否生效、测试是否通过
4. **激活闭环**：两者都通过后，让 @devops 去掉 PreCommit 里的 `|| true`
5. **Phase 2**：PM 自己执行 PM-1 和 PM-2，同时派发 DEVOPS-2
6. **Phase 3**：派发给 @ai-ml 和 @backend，并行执行
7. **Phase 4**：PM 创建 HARNESS_HEALTH.md 并持续维护
8. **通知团队**：在 TEAM_CHAT.md 中发布 harness engineering 升级公告，让所有 agent 知晓新的 hooks 和测试机制
