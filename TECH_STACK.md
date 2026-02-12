# 技术栈速查

> 所有 Agent 的技术参考，保持统一

---

## 后端技术栈

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | FastAPI | 0.115.5 | 异步 Web 框架 |
| ORM | SQLAlchemy | 2.0.36 | 异步 ORM |
| 数据库 | SQLite/PostgreSQL | - | 开发用 SQLite，生产用 PG |
| 验证 | Pydantic | 2.10.2 | 数据模式验证 |
| HTTP | httpx | 0.28.1 | 异步 HTTP 客户端 |
| 测试 | pytest | 8.3.4 | 测试框架 |

## 前端技术栈 (规划)

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Next.js | 14.x | React 全栈框架 |
| 样式 | TailwindCSS | 3.x | 原子化 CSS |
| 状态 | Zustand | 4.x | 轻量状态管理 |
| 请求 | TanStack Query | 5.x | 数据请求管理 |
| UI | shadcn/ui | - | 组件库 |

## AI/ML 服务

| 能力 | 服务商 | 模型 | 用途 |
|------|--------|------|------|
| 故事生成 | Anthropic | Claude Haiku 4.5 | 剧本生成 |
| 故事生成备用 | Google | Gemini 2.5 Flash | 备用 |
| 图像生成 | Google | Gemini 3 Pro Image | Shot 生成 (一致性) |
| 图像生成 | Google | Gemini 2.5 Flash Image | 参考图生成 (低成本) |
| TTS | 火山引擎 | Doubao seed-tts-2.0 | 语音合成 |
| ASR | OpenAI | Whisper | 时间戳提取 |

## DevOps (规划)

| 组件 | 技术 | 说明 |
|------|------|------|
| 容器 | Docker | 容器化部署 |
| CI/CD | GitHub Actions | 自动化流水线 |
| 队列 | Celery + Redis | 异步任务 |
| 存储 | S3/OSS | 媒体文件存储 |
| CDN | CloudFront/阿里CDN | 静态资源加速 |

---

## 代码规范

### Python (后端)
```python
# 类型注解必须
def process_story(story_id: str) -> StoryResult:
    pass

# 异步优先
async def generate_image(prompt: str) -> Image:
    pass

# Pydantic 模型验证
class StoryRequest(BaseModel):
    title: str
    prompt: str
```

### TypeScript (前端)
```typescript
// 严格类型
interface Story {
  id: string;
  title: string;
  status: 'draft' | 'processing' | 'done';
}

// React 组件
const StoryCard: FC<{ story: Story }> = ({ story }) => {
  return <div>{story.title}</div>;
};
```

---

## API 规范

### RESTful 设计
```
GET    /api/projects          # 列表
POST   /api/projects          # 创建
GET    /api/projects/{id}     # 详情
PATCH  /api/projects/{id}     # 更新
DELETE /api/projects/{id}     # 删除
```

### 响应格式
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### 错误格式
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input"
  }
}
```
