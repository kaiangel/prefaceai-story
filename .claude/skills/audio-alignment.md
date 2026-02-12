# Skill: Audio Alignment

> 音画对齐是视频质量的关键。误差目标 ≤80ms。

## Activation Triggers

当涉及以下内容时，必须阅读此skill：
- 修改 `alignment_service.py`
- 修改 `whisper_service.py`
- 讨论"时间戳"、"对齐"、"繁简转换"

**大白话触发**: 声音和画面对不上、字幕时间不对、说话和图片不同步、时间轴错了

**完整触发词映射**: [XUHUASTORY_SKILL_TRIGGERS.md](./XUHUASTORY_SKILL_TRIGGERS.md)

---

## Core Algorithm

### 多策略文本匹配

```python
# 匹配策略优先级
1. 精确匹配 - 完全相同
2. 去标点匹配 - 移除标点后相同
3. 前缀匹配 - 开头相同
4. 子序列匹配 - 包含关系
```

### 繁简转换（关键！）

```python
# Whisper常输出繁体中文
# TTS使用简体中文
# 必须统一转换后再匹配

from opencc import OpenCC
cc = OpenCC('t2s')  # 繁体转简体
simplified = cc.convert(traditional_text)
```

---

## Whisper Integration

### Word-level时间戳

```python
# Whisper返回结构
{
  "text": "完整文本",
  "words": [
    {"word": "你好", "start": 0.0, "end": 0.5},
    {"word": "世界", "start": 0.5, "end": 1.0}
  ]
}
```

### 注意事项

1. Whisper可能输出繁体 → 必须转换
2. 标点符号可能不一致 → 去标点匹配
3. 某些词可能被拆分 → 子序列匹配

---

## Timeline Generation

### 目标

每个shot映射到精确的时间段：

```json
{
  "shot_id": 1,
  "start_time": 0.0,
  "end_time": 8.5,
  "duration": 8.5,
  "image_path": "images/shot_01.png"
}
```

### 验证标准

- [ ] 覆盖完整音频时长
- [ ] 无时间重叠
- [ ] 每个shot都有时间段
- [ ] 误差 ≤80ms

---

## TTS Service

### 火山引擎豆包

```python
# 配置参数
voice_id = "zh_female_tianmeixiaoyuan"  # 甜美
sample_rate = 24000
volume = 1.0
speed = 1.0
```

### 音色选择

| 音色ID | 描述 | 适用场景 |
|--------|------|---------|
| zh_female_tianmeixiaoyuan | 甜美小媛 | 甜美故事 |
| zh_male_chunhou | 淳厚 | 男性旁白 |
| zh_female_wenrou | 温柔 | 柔和故事 |

---

## Common Pitfalls

| 问题 | 错误做法 | 正确做法 |
|------|----------|----------|
| 繁简不匹配 | 直接比较Whisper和原文 | 先繁简转换 |
| 精确匹配失败 | 放弃匹配 | 尝试去标点/前缀/子序列 |
| 时间重叠 | 忽略 | 检查并修复 |
| 标点不一致 | 硬编码处理 | 统一去标点后匹配 |

---

## Key Files

| 文件 | 职责 |
|------|------|
| `alignment_service.py` | 音画对齐核心逻辑 |
| `whisper_service.py` | Whisper API调用 |
| `tts_service.py` | 火山引擎TTS |

---

## Testing

```bash
# 运行音频对齐测试
pytest tests/test_alignment_service.py -v

# 检查点
# - [ ] 时间戳精度
# - [ ] 繁简转换
# - [ ] 多策略匹配
```
