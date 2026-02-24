# Frontend 当前任务进度

> 更新时间: 2026-02-14 17:30
> 状态: ✅ **TASK-LP-PAGES-FIX 全部完成，等待 PM 复验**

---

## 当前任务: TASK-LP-PAGES-FIX（4项修复）

### 状态: ✅ 全部完成

| 编号 | 优先级 | 内容 | 状态 |
|------|--------|------|------|
| FIX-1 | P0 | 首页链接新开标签页 + 子页面当前标签页 | ✅ |
| FIX-2 | P1 | 11个页面添加 SEO metadata | ✅ |
| FIX-3 | P1 | Footer 内链改用 `<Link>` | ✅ |
| FIX-4 | P2 | 登录页 setTimeout 清理 | ✅ |

### 构建验证: ✅ `npm run build` 成功通过（15个路由）

---

## 修改的文件清单

### FIX-1 + FIX-3: Footer 链接行为
| 文件 | 修改 |
|------|------|
| `components/layout/Footer.tsx` | 新增 `openSubPagesInNewTab` prop，移除 `"use client"`，锚点链接用 `<a>`，子页面间用 `<Link>`，首页用 `<a target="_blank">` |
| `app/page.tsx` | `<Footer openSubPagesInNewTab />` |
| `components/sections/CTASection.tsx` | "直接登录" 链接加 `target="_blank" rel="noopener noreferrer"` |

### FIX-2: SEO metadata（11个页面拆分为 Server + Client）
| 页面 | 新增文件 | title |
|------|----------|-------|
| /about | AboutContent.tsx | 关于我们 - 序话Story |
| /terms | TermsContent.tsx | 使用条款 - 序话Story |
| /privacy | PrivacyContent.tsx | 隐私政策 - 序话Story |
| /careers | CareersContent.tsx | 加入我们 - 序话Story |
| /help | HelpContent.tsx | 帮助中心 - 序话Story |
| /tutorials | TutorialsContent.tsx | 使用教程 - 序话Story |
| /faq | FAQContent.tsx | 常见问题 - 序话Story |
| /contact | ContactContent.tsx | 联系我们 - 序话Story |
| /pricing | PricingContent.tsx | 定价 - 序话Story |
| /login | LoginContent.tsx | 登录 - 序话Story |

### FIX-4: 登录页 setTimeout 清理
| 文件 | 修改 |
|------|------|
| `app/login/LoginContent.tsx` | `shakeTimerRef` + `apiTimerRef` (useRef)，`clearTimers()` callback，unmount cleanup |

---

## 下一步

1. 等待 PM 复验
2. 根据 PM 反馈继续优化
