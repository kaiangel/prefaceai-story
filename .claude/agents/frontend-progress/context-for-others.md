# Frontend 状态速览（供其他Agent参考）

> 更新时间: 2026-03-16

---

## 当前状态: TASK-BRAND-MANIFESTO + TASK-LOGO-REPLACE 完成，待 PM 审查 + DevOps 部署

**可预览地址**: http://localhost:3000 (需要运行 `npm run dev`)

---

## 最新完成 (2026-03-16)

### TASK-BRAND-MANIFESTO（品牌宣言整合）

| 文件 | 改动 |
|------|------|
| `Pipeline.tsx` | slogan → "每个人脑子里都在放电影"，core message → "你说出来。所有人看见。"，技术标签删除，tagline → V2 精神 |
| `AboutContent.tsx` | 使命段 → V2 完整宣言，理念段重写，三卡片 V2 重写，新增"技术基座"段（技术标签迁入），核心团队不动（位置调到卡片下方） |

### TASK-LOGO-REPLACE（全站 Logo 替换）

| 文件 | 改动 |
|------|------|
| `Header.tsx` | `<Sparkles>` → `<Image src="/brand/logo-48.png">` |
| `SubPageHeader.tsx` | `<Sparkles>` → `<Image src="/brand/logo-40.png">` |
| `CreateHeader.tsx` | `<Sparkles>` → `<Image src="/brand/logo-40.png">` |
| `Footer.tsx` | `<Sparkles>` → `<Image src="/brand/logo-48.png">` |

favicon.ico 已由 Coordinator 预先替换。

### 部署状态
- 本地 build 通过（18/18 路由）
- **需要 DevOps push + 部署到 prefaceai.mov**
- **需要 PM 文案审查 → Founder 终审**

---

## 静态资源汇总

- `public/team/` — 团队照片 3 张
- `public/demo.mp4` — 产品 Demo 视频
- `public/styles/` — 15 张风格缩略图
- `public/brand/` — 13 张 logo 图片（琥珀版 + 黑色版多尺寸）

---

## 待做（记录）

### 视频预览器组件（等后端 Phase 4.5 视频合成就绪后再做）

当前 Phase 4.5（视频合成）进度 5%，暂无真实视频可播放。

---

## 技术栈

| 技术 | 版本 |
|------|------|
| Next.js | 14.2.35 |
| TailwindCSS | 3.x |
| TypeScript | 5.x |
| Framer Motion | 最新（含 AnimatePresence） |
| Lucide Icons | 最新 |
