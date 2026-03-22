# Frontend 当前任务进度

> 更新时间: 2026-03-22
> 状态: Batch 2 完成，等 PM Review

---

## 最新完成: Batch 2 — Dashboard 补全 (2026-03-22)

### 状态: 完成，`npm run build` 20 路由通过，0 错误

---

#### 16 项全部完成

| PM# | 工作项 | 文件 | 状态 |
|-----|--------|------|------|
| 32 | StoryCard 生成中进度条 | StoryCard.tsx | ✅ |
| 33 | Dashboard 顶部生成 banner | DashboardContent.tsx | ✅ |
| 34 | Credits 余额统计卡 | DashboardContent.tsx | ✅ |
| 35 | 排序功能 | StoryGrid.tsx（已有） | ✅ 已在 Batch 1 中实现 |
| 38 | 做同款按钮 | StoryDetailContent.tsx | ✅ URL query 预填 |
| 39 | 页面内播放 | StoryDetailContent.tsx | ✅ 2s/3s/5s 可调速 |
| 40 | 分享功能 | ShareModal.tsx（新建）| ✅ 链接+QR+社交 |
| 41 | 收藏功能 | StoryDetailContent.tsx | ✅ Heart toggle |
| 42 | Shot 排序 | StoryDetailContent.tsx | ✅ 默认故事顺序 |
| 43 | 导出素材细化 | ExportModal.tsx（新建）| ✅ 三选项 |
| 44 | 合成视频入口 | VideoSynthesisModal.tsx（新建）| ✅ 进度条+完成 |
| 45 | 删除确认弹窗 | ConfirmModal.tsx（新建）| ✅ 危险操作确认 |
| 48 | 浏览器推送通知 | notifications.ts（新建）| ✅ 权限+推送 |
| 49 | Toast 通知组件 | Toast.tsx（新建）+ layout.tsx | ✅ 成功/失败/信息 |
| — | mock generating 故事 | mock-data.ts | ✅ |
| — | ToastProvider 全局接入 | layout.tsx | ✅ |

---

#### 新建文件（7 个）

| 文件 | 说明 |
|------|------|
| `components/ui/Toast.tsx` | 通用 Toast 通知（ToastProvider + useToast） |
| `components/ui/ConfirmModal.tsx` | 通用确认弹窗（支持 danger 模式） |
| `components/ui/ShareModal.tsx` | 分享弹窗（链接+QR+社交平台） |
| `components/ui/ExportModal.tsx` | 导出弹窗（仅图片/图片+音频/全部素材） |
| `components/ui/VideoSynthesisModal.tsx` | 视频合成弹窗（进度条→完成→下载） |
| `lib/notifications.ts` | 浏览器推送通知工具 |
| mock-data.ts 新增 | generating 状态故事 |

#### 修改文件（4 个）

| 文件 | 改动 |
|------|------|
| `StoryCard.tsx` | 生成中进度条覆盖层 |
| `DashboardContent.tsx` | 生成 banner + Credits 卡片 + 4 列统计 |
| `StoryDetailContent.tsx` | 完全重写：做同款/播放/分享/收藏/导出/合成视频/删除确认 |
| `layout.tsx` | 接入 ToastProvider |

---

## 待做

### Batch 3-5（未派发，等 PM）

- Batch 3: 输入方式升级（OCR/语音/模板）
- Batch 4: 商业化 UI + 比例
- Batch 5: API 对接
