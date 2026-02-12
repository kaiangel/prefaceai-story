# 序话Story Landing Page 视觉规范

> 版本: v1.0
> 创建日期: 2026-01-29
> 作者: PM
> 关联文档: `docs/LANDING_PAGE_ARCHITECTURE.md`

---

## 设计理念

### 核心定位：故事感 Dark Mode

**与竞品的差异化**：所有竞品（Vidu、OiiOii、MovieFlow）的Dark Mode都偏"科技感"——纯黑背景、冷色调主色、强调"AI能力"。

**序话Story的定位**：不是"科技感Dark Mode"，而是**"故事感Dark Mode"**——像夜晚在温暖的咖啡馆里翻阅一本条漫故事书。

### 视觉隐喻

| 竞品隐喻 | 序话Story隐喻 |
|---------|--------------|
| 实验室 | 咖啡馆 |
| 剪辑室 | 书房 |
| 工作站 | 故事书 |

### 情感关键词

- 温暖（Warm）
- 沉浸（Immersive）
- 叙事（Narrative）
- 灵感（Spark）

---

## 一、配色系统

### 1.1 品牌色 - 暖光琥珀系（Warm Amber）

与 FrameSpark™ 品牌呼应——"Spark"是火花、灵感，视觉上应该有温度、有光芒。

```css
/* 品牌色 */
--brand-primary: #FF9500;     /* 主色：琥珀橙（火花感） */
--brand-secondary: #FFB347;   /* 浅琥珀（渐变终点） */
--brand-gradient: linear-gradient(135deg, #FF9500 0%, #FFD93D 100%);

/* CTA渐变 */
--cta-gradient: linear-gradient(135deg, #FF9500 0%, #FF6B00 100%);
```

### 1.2 背景色 - 故事感深色

```css
/* 背景层 - 深炭灰（比纯黑更温暖） */
--bg-primary: #121212;        /* 主背景 */
--bg-secondary: #1E1E1E;      /* 卡片背景 */
--bg-tertiary: #2A2A2A;       /* 悬浮/输入框背景 */
--bg-elevated: #333333;       /* 浮层背景 */
```

### 1.3 强调色 - 情感表达

用于不同类型故事的视觉区分：

```css
/* 强调色 */
--accent-warm: #FF6B6B;       /* 暖红：激动、冲突、都市情感 */
--accent-cool: #4ECDC4;       /* 青绿：平静、回忆、古风 */
--accent-purple: #9B59B6;     /* 紫色：梦幻、想象、科幻 */
--accent-gold: #FFD700;       /* 金色：高光、成就 */
```

### 1.4 文字色

```css
/* 文字色 */
--text-primary: #FFFFFF;      /* 主标题：纯白 */
--text-secondary: #E0E0E0;    /* 正文：浅灰 */
--text-tertiary: #9E9E9E;     /* 辅助文字：中灰 */
--text-muted: #666666;        /* 禁用状态：深灰 */
--text-link: #FF9500;         /* 链接：品牌色 */
```

### 1.5 功能色

```css
/* 功能色 */
--success: #4ADE80;           /* 成功：绿色 */
--warning: #FBBF24;           /* 警告：黄色 */
--error: #EF4444;             /* 错误：红色 */
--info: #3B82F6;              /* 信息：蓝色 */
```

### 1.6 配色对比表

| 对比项 | 竞品典型 | 序话Story | 差异 |
|--------|---------|----------|------|
| 背景 | #0A0A0A 纯黑 | #121212 深炭灰 | 更温暖 |
| 主色 | #3B82F6 冷蓝 | #FF9500 暖琥珀 | 更有温度 |
| 情感 | 科技、专业 | 温暖、故事感 | 更人文 |

---

## 二、字体系统

### 2.1 字体选择

| 用途 | 字体 | 备选 | 理由 |
|------|------|------|------|
| **Hero大标题** | 阿里妈妈数黑体 | DingTalk JinBuTi | 现代感 + 有力量 + 免费商用 |
| **章节标题** | 思源黑体 Bold | Noto Sans SC Bold | 清晰、稳重 |
| **正文/UI** | 思源黑体 Regular | Noto Sans SC | 可读性最佳 |
| **特殊强调** | 思源宋体 | Noto Serif SC | 文学感、引用语 |
| **英文/数字** | Inter | SF Pro Display | 现代、清晰 |

### 2.2 字体层级

```css
/* 字体层级（移动端优先） */

/* Hero区域 */
--font-hero: 40px;
--font-hero-weight: 800;
--font-hero-line-height: 1.2;
--font-hero-letter-spacing: -0.02em;

/* 大标题 */
--font-title-1: 28px;
--font-title-1-weight: 700;
--font-title-1-line-height: 1.3;

/* 章节标题 */
--font-title-2: 22px;
--font-title-2-weight: 600;
--font-title-2-line-height: 1.4;

/* 小标题 */
--font-title-3: 18px;
--font-title-3-weight: 600;
--font-title-3-line-height: 1.4;

/* 正文 */
--font-body: 16px;
--font-body-weight: 400;
--font-body-line-height: 1.6;

/* 辅助说明 */
--font-caption: 14px;
--font-caption-weight: 400;
--font-caption-line-height: 1.5;

/* 极小文字 */
--font-tiny: 12px;
--font-tiny-weight: 400;
--font-tiny-line-height: 1.4;
```

### 2.3 桌面端字体放大

```css
/* 桌面端（≥1024px） */
--font-hero-desktop: 56px;
--font-title-1-desktop: 40px;
--font-title-2-desktop: 28px;
--font-title-3-desktop: 22px;
--font-body-desktop: 18px;
```

### 2.4 特殊字体应用

| 场景 | 字体 | 示例 |
|------|------|------|
| Slogan | 思源宋体 | "每个人都有自己的故事" |
| 故事标题 | 思源宋体 | 《最后一碗面》 |
| 数据数字 | Inter Bold | "10,000+ 故事" |
| CTA按钮 | 思源黑体 Medium | "开始你的故事" |

---

## 三、间距系统

### 3.1 基础单位

**基础单位**：8px（行业标准）

### 3.2 间距Token

```css
/* 间距Token */
--space-0: 0;
--space-1: 4px;    /* 极小间距：图标与文字 */
--space-2: 8px;    /* 基础间距：组件内部 */
--space-3: 12px;   /* 小间距 */
--space-4: 16px;   /* 标准间距：元素间 */
--space-5: 24px;   /* 中间距：卡片内边距 */
--space-6: 32px;   /* 大间距：模块分隔 */
--space-8: 48px;   /* 超大间距：区块间 */
--space-10: 64px;  /* 区域间距 */
--space-12: 80px;  /* 模块间距（移动端） */
--space-16: 120px; /* 模块间距（桌面端） */
```

### 3.3 圆角系统

```css
/* 圆角 */
--radius-xs: 4px;   /* 极小：标签 */
--radius-sm: 8px;   /* 小：按钮、Badge */
--radius-md: 12px;  /* 中：输入框、小卡片 */
--radius-lg: 16px;  /* 大：卡片、弹窗 */
--radius-xl: 24px;  /* 超大：特殊展示区 */
--radius-full: 9999px; /* 圆形：头像、圆按钮 */
```

### 3.4 容器宽度

```css
/* 容器宽度 */
--container-sm: 640px;   /* 小容器：表单 */
--container-md: 768px;   /* 中容器：内容 */
--container-lg: 1024px;  /* 大容器：主内容 */
--container-xl: 1280px;  /* 超大容器：全宽展示 */
--container-2xl: 1440px; /* 最大容器 */
```

---

## 四、动效系统

### 4.1 设计理念

**核心理念**：序话Story讲的是"故事"，故事需要节奏。稍慢的动效传达"沉浸感"，而不是"工具效率"。

### 4.2 时长Token

```css
/* 动效时长 - 故事节奏版 */
--duration-instant: 100ms;    /* 即时反馈：按钮按下 */
--duration-fast: 200ms;       /* 快速过渡：悬浮状态 */
--duration-normal: 350ms;     /* 标准过渡：展开/收起 */
--duration-slow: 500ms;       /* 慢速过渡：内容呈现 */
--duration-story: 700ms;      /* 故事呈现：条漫展示、Hero动画 */
--duration-page: 400ms;       /* 页面切换 */
```

### 4.3 与竞品对比

| 场景 | 竞品典型 | 序话Story | 效果差异 |
|------|---------|----------|---------|
| 悬浮状态 | 150-200ms | 200ms | 相近 |
| 内容展开 | 250-300ms | 350ms | 更从容 |
| Hero动画 | 300-400ms | 700ms | 更沉浸 |
| 页面切换 | 200-300ms | 500ms | 更叙事感 |

### 4.4 缓动函数

```css
/* 缓动函数 */
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);        /* 自然减速 */
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);    /* 平滑过渡 */
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1); /* 弹性（用于强调） */
--ease-story: cubic-bezier(0.4, 0, 0.2, 1);       /* 故事感（慢入慢出） */
```

### 4.5 动效应用场景

| 场景 | 时长 | 缓动 | 说明 |
|------|------|------|------|
| 按钮悬浮 | 200ms | ease-out | 轻微放大 + 发光 |
| 卡片悬浮 | 200ms | ease-out | 轻微上移 + 阴影 |
| 条漫展示 | 700ms | ease-story | 翻页效果 |
| 模块淡入 | 500ms | ease-out | 滚动触发 |
| CTA发光 | 2000ms | ease-in-out | 循环呼吸 |
| 加载动画 | 1500ms | linear | FrameSpark旋转 |

### 4.6 特色动效设计

1. **条漫翻页效果**
   - 条漫图片以"翻页"效果出现
   - 像翻开故事书的感觉
   - 时长：700ms

2. **CTA按钮发光**
   - hover时有微弱的"发光"效果
   - 呼应FrameSpark的"火花"概念
   - 使用box-shadow动画

3. **Loading状态**
   - FrameSpark的火花图标
   - 带呼吸闪烁 + 旋转
   - 传达"灵感正在迸发"

4. **故事生成进度**
   - 进度条设计成"故事线"形式
   - 每个节点是一个场景
   - 节点点亮时有spark效果

---

## 五、阴影系统

```css
/* 阴影层级 */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.6);

/* 发光效果（品牌色） */
--glow-sm: 0 0 10px rgba(255, 149, 0, 0.3);
--glow-md: 0 0 20px rgba(255, 149, 0, 0.4);
--glow-lg: 0 0 30px rgba(255, 149, 0, 0.5);
```

---

## 六、组件规范

### 6.1 按钮

**主按钮（CTA）**
```css
.btn-primary {
  background: var(--cta-gradient);
  color: #FFFFFF;
  padding: 14px 32px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 16px;
  transition: all var(--duration-fast) var(--ease-out);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--glow-md);
}
```

**次按钮**
```css
.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--text-tertiary);
  padding: 14px 32px;
  border-radius: var(--radius-sm);
}

.btn-secondary:hover {
  border-color: var(--brand-primary);
  color: var(--brand-primary);
}
```

### 6.2 卡片

```css
.card {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  transition: all var(--duration-fast) var(--ease-out);
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}
```

### 6.3 输入框

```css
.input {
  background: var(--bg-tertiary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  padding: 12px 16px;
  color: var(--text-primary);
}

.input:focus {
  border-color: var(--brand-primary);
  outline: none;
  box-shadow: 0 0 0 3px rgba(255, 149, 0, 0.2);
}
```

---

## 七、响应式断点

```css
/* 断点 */
--breakpoint-sm: 640px;   /* 小手机 */
--breakpoint-md: 768px;   /* 大手机/小平板 */
--breakpoint-lg: 1024px;  /* 平板/小桌面 */
--breakpoint-xl: 1280px;  /* 桌面 */
--breakpoint-2xl: 1536px; /* 大桌面 */
```

---

## 八、品牌元素

### 8.1 Logo使用

- 主Logo：白色版本（用于深色背景）
- 品牌色版本：琥珀橙（用于特殊强调）
- 最小尺寸：高度24px

### 8.2 FrameSpark™ 图标

- 火花形状的图标
- 用于Loading、进度指示、成就展示
- 颜色：品牌渐变色

### 8.3 图案元素

- **纸张纹理**：在Hero区背景添加极淡的纸张纹理（opacity 3-5%），增加"故事书"质感
- **漫画格线**：在条漫展示区可以使用轻微的漫画格线效果

---

## 九、无障碍设计

### 9.1 对比度要求

| 元素 | 最小对比度 | 当前对比度 |
|------|-----------|-----------|
| 正文文字 | 4.5:1 | #E0E0E0 on #121212 = 12.6:1 ✅ |
| 大标题 | 3:1 | #FFFFFF on #121212 = 17.4:1 ✅ |
| 辅助文字 | 3:1 | #9E9E9E on #121212 = 6.5:1 ✅ |

### 9.2 焦点状态

所有交互元素必须有清晰的焦点状态：
```css
:focus-visible {
  outline: 2px solid var(--brand-primary);
  outline-offset: 2px;
}
```

---

## 十、实施检查清单

- [ ] 字体文件引入（思源黑体、思源宋体、Inter）
- [ ] CSS变量定义
- [ ] 基础组件样式
- [ ] 响应式适配
- [ ] 动效实现
- [ ] 无障碍测试
- [ ] 跨浏览器测试

---

## 附录：CSS变量汇总

```css
:root {
  /* 品牌色 */
  --brand-primary: #FF9500;
  --brand-secondary: #FFB347;
  --brand-gradient: linear-gradient(135deg, #FF9500 0%, #FFD93D 100%);
  --cta-gradient: linear-gradient(135deg, #FF9500 0%, #FF6B00 100%);

  /* 背景色 */
  --bg-primary: #121212;
  --bg-secondary: #1E1E1E;
  --bg-tertiary: #2A2A2A;
  --bg-elevated: #333333;

  /* 强调色 */
  --accent-warm: #FF6B6B;
  --accent-cool: #4ECDC4;
  --accent-purple: #9B59B6;
  --accent-gold: #FFD700;

  /* 文字色 */
  --text-primary: #FFFFFF;
  --text-secondary: #E0E0E0;
  --text-tertiary: #9E9E9E;
  --text-muted: #666666;
  --text-link: #FF9500;

  /* 功能色 */
  --success: #4ADE80;
  --warning: #FBBF24;
  --error: #EF4444;
  --info: #3B82F6;

  /* 间距 */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-8: 48px;
  --space-10: 64px;
  --space-12: 80px;
  --space-16: 120px;

  /* 圆角 */
  --radius-xs: 4px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;

  /* 动效 */
  --duration-instant: 100ms;
  --duration-fast: 200ms;
  --duration-normal: 350ms;
  --duration-slow: 500ms;
  --duration-story: 700ms;

  /* 缓动 */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-story: cubic-bezier(0.4, 0, 0.2, 1);

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.6);

  /* 发光 */
  --glow-sm: 0 0 10px rgba(255, 149, 0, 0.3);
  --glow-md: 0 0 20px rgba(255, 149, 0, 0.4);
  --glow-lg: 0 0 30px rgba(255, 149, 0, 0.5);
}
```

---

*此文档为序话Story Landing Page的视觉设计规范，与 `LANDING_PAGE_ARCHITECTURE.md` 配合使用。*
