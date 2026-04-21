# Mureka API 完整文档

**Base URL**: `https://api.mureka.cn`
**Docs URL**: `https://platform.mureka.cn/docs/`
**Authentication**: Bearer Token — `Authorization: Bearer $MUREKA_API_KEY`
**Source**: 从打包的 JS 文件中提取的完整 OpenAPI 规范 (`theme.zbVB06cC.js`)

---

## 目录

1. [文件上传 POST /v1/files/upload](#1-文件上传-post-v1filesupload)
2. [生成歌词 POST /v1/lyrics/generate](#2-生成歌词-post-v1lyricsgenerate)
3. [扩展歌词 POST /v1/lyrics/extend](#3-扩展歌词-post-v1lyricsextend)
4. [生成歌曲 POST /v1/song/generate](#4-生成歌曲-post-v1songgenerate)
5. [查询歌曲任务 GET /v1/song/query/{task_id}](#5-查询歌曲任务-get-v1songquerytask_id)
6. [音色克隆 POST /v1/vocal/clone](#6-音色克隆-post-v1vocalclone)
7. [续写歌曲 POST /v1/song/extend](#7-续写歌曲-post-v1songextend)
8. [识别歌曲 POST /v1/song/recognize](#8-识别歌曲-post-v1songrecognize)
9. [理解歌曲 POST /v1/song/describe](#9-理解歌曲-post-v1songdescribe)
10. [分轨歌曲 POST /v1/song/stem](#10-分轨歌曲-post-v1songstem)
11. [单轨生成 POST /v1/track/generate](#11-单轨生成-post-v1trackgenerate)
12. [局部编辑 POST /v1/song/region-edit](#12-局部编辑-post-v1songregion-edit)
13. [歌曲混音 POST /v1/song/remix](#13-歌曲混音-post-v1songremix)
14. [生成纯音乐 POST /v1/instrumental/generate](#14-生成纯音乐-post-v1instrumentalgenerate)
15. [查询纯音乐任务 GET /v1/instrumental/query/{task_id}](#15-查询纯音乐任务-get-v1instrumentalquerytask_id)
16. [创建上传对象 POST /v1/uploads/create](#16-创建上传对象-post-v1uploadscreate)
17. [追加数据 POST /v1/uploads/add](#17-追加数据-post-v1uploadsadd)
18. [完成上传 POST /v1/uploads/complete](#18-完成上传-post-v1uploadscomplete)
19. [创建语音 POST /v1/tts/generate](#19-创建语音-post-v1ttsgenerate)
20. [创建播客 POST /v1/tts/podcast](#20-创建播客-post-v1ttspodcast)
21. [查询账单 GET /v1/account/billing](#21-查询账单-get-v1accountbilling)
22. [附录：微调相关接口](#22-附录微调相关接口)
23. [公共数据结构](#23-公共数据结构)
24. [错误代码](#24-错误代码)
25. [平台说明](#25-平台说明)

---

## 1. 文件上传 POST /v1/files/upload

**描述**: 上传一个可以在多个接口使用的文件。单个文件大小最多为 10 MB。

**Content-Type**: `multipart/form-data`

### 请求参数

| 参数 | 类型 | 必填 | 枚举值 | 描述 |
|------|------|------|--------|------|
| `file` | string (binary) | 是 | — | 要上传的文件内容（不是文件名） |
| `purpose` | string | 是 | 见下表 | 上传文件的预期用途 |

### purpose 枚举值说明

| 值 | 支持格式 | 时长范围 | 说明 |
|----|----------|----------|------|
| `reference` | mp3, m4a | [30, 30] 秒 | 参考音乐，超出最大时长的部分会被裁剪 |
| `vocal` | mp3, m4a | [15, 30] 秒 | 提取人声，超出最大时长的部分会被裁剪 |
| `melody` | mp3, m4a, mid | [5, 60] 秒 | 提取哼唱人声，建议上传 MIDI 文件 |
| `instrumental` | mp3, m4a | [30, 30] 秒 | 纯音乐参考，超出最大时长的部分会被裁剪 |
| `voice` | mp3, m4a | [5, 15] 秒 | 语音参考（TTS 用），超出最大时长的部分会被裁剪 |
| `audio` | mp3, m4a | — | 通用音频文件，用于歌曲续写等功能 |
| `remix` | mp3, m4a | — | 通用音频文件，用于混音重制（Remix） |

### 响应格式 (200 OK) — FileObject

| 字段 | 类型 | 描述 |
|------|------|------|
| `id` | string | 文件 ID，可以在 API 中引用 |
| `filename` | string | 文件名称 |
| `bytes` | integer (int64) | 文件大小，以字节为单位 |
| `created_at` | integer (int64) | 文件创建的时间戳（以秒为单位） |
| `purpose` | string | 文件的预期用途 |

### 响应示例

```json
{
  "id": "542321",
  "filename": "mydata.mp3",
  "bytes": 120000,
  "created_at": 1677610602,
  "purpose": "reference"
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/files/upload \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -F purpose="reference" \
  -F file="@mydata.mp3"
```

---

## 2. 生成歌词 POST /v1/lyrics/generate

**描述**: 根据提示生成歌词。

**Content-Type**: `application/json`

### 请求参数

| 参数 | 类型 | 必填 | 枚举值 | 默认值 | 描述 |
|------|------|------|--------|--------|------|
| `prompt` | string | 是 | — | — | 生成歌词的提示词 |

### 响应格式 (200 OK) — LyricsGenerateResp

| 字段 | 类型 | 描述 |
|------|------|------|
| `title` | string | 根据提示词生成的标题 |
| `lyrics` | string | 根据提示词生成的歌词 |

### 响应示例

```json
{
  "title": "夜的拥抱",
  "lyrics": "[主歌]\n在暴风雨的夜晚，我独自徘徊\n被雨淋湿，感觉像是被抛弃\n你的回忆，在我眼前闪现\n希望这一刻，能找到一丝幸福\n"
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/lyrics/generate \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "夜的拥抱"
  }'
```

---

## 3. 扩展歌词 POST /v1/lyrics/extend

**描述**: 在现有歌词的基础上，续写下一句歌词。

**Content-Type**: `application/json`

### 请求参数

| 参数 | 类型 | 必填 | 枚举值 | 默认值 | 描述 |
|------|------|------|--------|--------|------|
| `lyrics` | string | 是 | — | — | 要续写的歌词 |

### 响应格式 (200 OK) — LyricsExtendResp

| 字段 | 类型 | 描述 |
|------|------|------|
| `lyrics` | string | 根据输入歌词续写的下一行歌词 |

### 响应示例

```json
{
  "lyrics": "[前奏]\n在星空下，我祈祷\n希望能拥抱你，感受你的怀抱\n"
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/lyrics/extend \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "lyrics": "[主歌]\n在暴风雨的夜晚，我独自徘徊\n被雨淋湿，感觉像是被抛弃"
  }'
```

---

## 4. 生成歌曲 POST /v1/song/generate

**描述**: 根据用户输入生成歌曲（异步任务）。

**Content-Type**: `application/json`

### 请求参数

| 参数 | 类型 | 必填 | 枚举值 | 默认值 | 描述 |
|------|------|------|--------|--------|------|
| `lyrics` | string | 是 | — | — | 生成音乐的歌词，最大 3000 个字符 |
| `model` | string | 是 | `auto`, `mureka-7.6`, `mureka-o2`, `mureka-8`, `mureka-9` | — | 要使用的模型。`auto` 选择常规模型最新版（非 mureka-o 系列）。也可使用 fine-tuning 微调出的模型（此时只能用 prompt 或 reference_id 控制） |
| `n` | integer (int32) | 否 | — | 2 | 每次请求生成的歌曲数量，最大值为 3。注意会根据数量计费 |
| `prompt` | string | 否 | — | — | 通过提示词控制音乐生成，最大 1024 个字符。可与 `vocal_id` 组合使用 |
| `reference_id` | string | 否 | — | — | 通过参考音乐控制生成，由 `files/upload`（purpose: reference）生成。可与 `vocal_id` 组合 |
| `vocal_id` | string | 否 | — | — | 通过音色控制生成，由 `files/upload`（purpose: vocal）生成。可与 `reference_id` 或 `prompt` 组合 |
| `melody_id` | string | 否 | — | — | 通过旋律控制生成，由 `files/upload`（purpose: melody）生成。不支持与其他控制选项组合 |
| `stream` | boolean | 否 | — | false | 如果为 true，任务状态会有 streaming 阶段，可通过 `stream_url` 边生成边收听。mureka-o1 不支持此模式 |

**控制选项组合规则**:
- `prompt` 单独或 `prompt + vocal_id`
- `reference_id` 单独或 `reference_id + vocal_id`
- `vocal_id` 单独或 `vocal_id + reference_id` 或 `vocal_id + prompt`
- `melody_id` 单独，不与其他组合

### 响应格式 (200 OK) — SongTask

见 [公共数据结构 — SongTask](#songtask)

### 响应示例

```json
{
  "id": "1436211",
  "created_at": 1677610602,
  "finished_at": 1677610652,
  "model": "mureka-7.6",
  "status": "preparing"
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/song/generate \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "lyrics": "[主歌]\n在暴风雨的夜晚，我独自徘徊\n被雨淋湿，感觉像是被抛弃\n你的回忆，在我眼前闪现\n希望这一刻，能找到一丝幸福",
    "model": "auto",
    "prompt": "r&b, slow, passionate, male vocal"
  }'
```

---

## 5. 查询歌曲任务 GET /v1/song/query/{task_id}

**描述**: 查询歌曲生成任务的信息。

### 路径参数

| 参数 | 类型 | 必填 | 示例 | 描述 |
|------|------|------|------|------|
| `task_id` | string | 是 | `435134` | 歌曲生成任务的 task_id |

### 响应格式 (200 OK) — SongTask

见 [公共数据结构 — SongTask](#songtask)

### 响应示例

```json
{
  "id": "1436211",
  "created_at": 1677610602,
  "finished_at": 1677610652,
  "model": "mureka-7.6",
  "status": "succeeded",
  "choices": [
    {
      "index": 0,
      "id": "song-123",
      "url": "https://cdn.mureka.cn/song.mp3",
      "flac_url": "https://cdn.mureka.cn/song.flac",
      "wav_url": "https://cdn.mureka.cn/song.wav",
      "duration": 180000,
      "lyrics_sections": [...]
    }
  ]
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/song/query/435134 \
  -H "Authorization: Bearer $MUREKA_API_KEY"
```

---

## 6. 音色克隆 POST /v1/vocal/clone

**描述**: 上传人声音频样本以创建可复用的 Vocal ID。

**Content-Type**: `multipart/form-data`

**注意**: 实际 cURL 示例中的 URL 为 `/v1/song/vocal-clone`（文档一致性问题，建议以 `/v1/vocal/clone` 为准）。

### 请求参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `file` | string (binary) | 是 | 要上传的人声音频文件。支持格式：mp3、m4a，文件大小需小于 10 MB。MIME 类型根据文件名后缀决定。filename 需去掉前面的路径，仅保留 basename.ext |

### 响应格式 (200 OK) — VocalCloneResp

| 字段 | 类型 | 描述 |
|------|------|------|
| `id` | string | 资源 ID |
| `filename` | string | 上传后的文件名，仅保留 basename.ext |
| `bytes` | integer (int64) | 文件大小，单位为字节 |
| `created_at` | integer (int64) | 资源创建时间戳（秒） |

### 响应示例

```json
{
  "id": "file-abc123",
  "filename": "mydata.mp3",
  "bytes": 120000,
  "created_at": 1677610602
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/song/vocal-clone \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@/path/to/file/refer.m4a"
```

---

## 7. 续写歌曲 POST /v1/song/extend

**描述**: 根据输入的歌词，续写歌曲（异步任务）。

**Content-Type**: `application/json`

### 请求参数

| 参数 | 类型 | 必填 | 枚举值 | 默认值 | 描述 |
|------|------|------|--------|--------|------|
| `song_id` | string | 二选一 | — | — | 要续写的歌曲 id，由 `song/generate` API 生成，只支持 1 个月内的生成歌曲。与 `upload_audio_id` 二选一 |
| `upload_audio_id` | string | 二选一 | — | — | 要续写的歌曲上传 id，由 `files/upload`（purpose: audio）生成。与 `song_id` 二选一 |
| `lyrics` | string | 是 | — | — | 续写的歌词 |
| `extend_at` | integer (int64) | 是 | — | — | 续写开始时间，单位毫秒。如果大于歌曲时长，则取歌曲时长。取值范围 [8000, 420000] |
| `extend_type` | string | 否 | `tail`, `head` | `tail` | 歌曲续写的方向。`tail` 从歌曲结尾续写，`head` 从歌曲开头续写。仅当 model 为 `mureka-8` 时支持，使用 `mureka-7.6` 时忽略此参数 |
| `model` | string | 否 | `mureka-7.6`, `mureka-8` | — | 用于歌曲续写的模型 |

### 响应格式 (200 OK) — SongTask

见 [公共数据结构 — SongTask](#songtask)

### cURL 示例

```bash
# 使用 mureka-7.6 从歌曲结尾续写（默认，向后兼容）
curl https://api.mureka.cn/v1/song/extend \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_audio_id": "43543541",
    "lyrics": "[主歌]\n在暴风雨的夜晚，我独自徘徊",
    "extend_at": 12234
  }'

# 使用 mureka-8 从歌曲开头续写
curl https://api.mureka.cn/v1/song/extend \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "song_id": "1436211",
    "lyrics": "[Intro]\nA quiet breath before the storm begins",
    "extend_at": 8000,
    "model": "mureka-8",
    "extend_type": "head"
  }'
```

---

## 8. 识别歌曲 POST /v1/song/recognize

**描述**: 将输入的歌曲转换为带时间戳信息的歌词。

**Content-Type**: `application/json`

### 请求参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `upload_audio_id` | string | 是 | 要识别的歌曲上传 id，由 `files/upload`（purpose: audio）生成 |

### 响应格式 (200 OK) — SongRecognizeResp

| 字段 | 类型 | 描述 |
|------|------|------|
| `duration` | integer (int64) | 歌曲的时长，以毫秒为单位 |
| `lyrics_sections` | array[LyricsSection] | 包含时间戳的歌词段落信息（见 [LyricsSection](#lyricssection)） |

### 响应示例

```json
{
  "duration": 30214,
  "lyrics_sections": [...]
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/song/recognize \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_audio_id": "43543541"
  }'
```

---

## 9. 理解歌曲 POST /v1/song/describe

**描述**: 对输入的歌曲作理解描述（分析风格、配器等）。

**Content-Type**: `application/json`

**注意**: 该接口的 requestBody schema 实际引用的是 `SongStemReq`（与分轨接口相同），即通过 `url` 字段传入歌曲。

### 请求参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `url` | string | 是 | 需要处理的歌曲 URL。支持格式：mp3, m4a。也支持 base64 格式的 URL，最大数据大小为 10 MB。例如：`data:audio/mp3;base64,AAAAGGZ...` |
| `model` | string | 否 | 用于处理的模型（见分轨接口说明） |

### 响应格式 (200 OK) — SongUnderstandResp

| 字段 | 类型 | 描述 |
|------|------|------|
| `instrument` | array[string] | 歌曲使用的配器列表 |
| `genres` | array[string] | 歌曲的曲风列表 |
| `tags` | array[string] | 歌曲的标签列表 |
| `description` | string | 歌曲的总体描述 |

### 响应示例

```json
{
  "instrument": ["Piano", "Synth Bass"],
  "genres": ["Pop", "Electropop"],
  "tags": ["Anthemic", "Motivational"],
  "description": "This is a powerfully dynamic pop-rock track that masterfully builds from an intimate piano ballad into a massive, anthemic electronic rock anthem."
}
```

### cURL 示例

```bash
# 使用标准 URL
curl https://api.mureka.cn/v1/song/describe \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://cdn.mureka.cn/1.mp3"
  }'

# 在 macOS 上使用 base64 格式
echo -n '{"url": "data:audio/mp3;base64,'"$(base64 -i test.mp3)"'"}' | \
  curl https://api.mureka.cn/v1/song/describe \
    -H "Authorization: Bearer $MUREKA_API_KEY" \
    -H "Content-Type: application/json" \
    -d @-

# 在 Linux 上使用 base64 格式
echo -n '{"url": "data:audio/mp3;base64,'"$(base64 -w 0 test.mp3)"'"}' | \
  curl https://api.mureka.cn/v1/song/describe \
    -H "Authorization: Bearer $MUREKA_API_KEY" \
    -H "Content-Type: application/json" \
    -d @-
```

---

## 10. 分轨歌曲 POST /v1/song/stem

**描述**: 对输入的歌曲进行分轨（人声、伴奏等分离）。

**Content-Type**: `application/json`

### 请求参数 — SongStemReq

| 参数 | 类型 | 必填 | 枚举值 | 描述 |
|------|------|------|--------|------|
| `url` | string | 是 | — | 需要处理的歌曲 URL。支持格式：mp3, m4a。也支持 base64 格式的 URL，最大数据大小为 10 MB。例如：`data:audio/mp3;base64,AAAAGGZ...` |
| `model` | string | 否 | `audio-separation-1`, `audio-separation-2` | 用于分轨的模型。仅当 model 为 `audio-separation-2` 时支持导出 MIDI 文件；`audio-separation-1` 不支持 MIDI 输出 |

### 响应格式 (200 OK) — SongStemResp

| 字段 | 类型 | 描述 |
|------|------|------|
| `zip_url` | string | 包含所有分轨音乐的 ZIP 压缩文件的 URL |
| `expires_at` | integer (int64) | URL 过期的时间戳（以秒为单位） |
| `midi_zip_url` | string | MIDI 压缩包地址（仅 audio-separation-2 模型支持） |

### 响应示例

```json
{
  "zip_url": "https://cdn.mureka.cn/1.zip",
  "expires_at": 1677610652,
  "midi_zip_url": null
}
```

### cURL 示例

```bash
# 使用标准 URL
curl https://api.mureka.cn/v1/song/stem \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://cdn.mureka.cn/1.mp3"
  }'

# 在 macOS 上使用 base64 格式
echo -n '{"url": "data:audio/mp3;base64,'"$(base64 -i test.mp3)"'"}' | \
  curl https://api.mureka.cn/v1/song/stem \
    -H "Authorization: Bearer $MUREKA_API_KEY" \
    -H "Content-Type: application/json" \
    -d @-

# 在 Linux 上使用 base64 格式
echo -n '{"url": "data:audio/mp3;base64,'"$(base64 -w 0 test.mp3)"'"}' | \
  curl https://api.mureka.cn/v1/song/stem \
    -H "Authorization: Bearer $MUREKA_API_KEY" \
    -H "Content-Type: application/json" \
    -d @-
```

---

## 11. 单轨生成 POST /v1/track/generate

**描述**: 生成单轨（从参考音频生成配套的人声、伴奏或单一乐器轨道）。异步任务。

**Content-Type**: `application/json`

**更新说明**: 2026.4.8 版本新增——从参考音频生成一个配套的单轨。支持的音轨类型：`vocals | accompaniment | instrument`。

### 请求参数 — TrackGenerateReq

| 参数 | 类型 | 必填 | 枚举值 | 描述 |
|------|------|------|--------|------|
| `generate_type` | string | 是 | `Vocals`, `Instrumental`, `Drums`, `Bass`, `Guitar`, `Keyboard`, `Percussion`, `Strings`, `Synth`, `FX`, `Brass`, `Woodwinds` | 要生成的单轨类型 |
| `song_id` | string | 二选一 | — | 歌曲 ID。与 `upload_audio_id` 参数二选一 |
| `upload_audio_id` | string | 二选一 | — | 上传文件返回的 ID，由 `files/upload`（purpose: audio）生成。与 `song_id` 参数二选一 |
| `generate_start` | integer (int64) | 否 | — | 生成单轨输入片段的开始时间，单位为毫秒 |
| `generate_end` | integer (int64) | 否 | — | 生成单轨输入片段的结束时间，单位为毫秒 |
| `lyrics` | string | 条件必填 | — | 生成人声时使用的歌词。当 `generate_type` 为 `Vocals` 时必填 |
| `prompt` | string | 条件必填 | — | 用于控制生成单轨风格的文本描述。当 `generate_type` 为 `Vocals`、`Instrumental` 或任一乐器类型时必填 |
| `vocal_gender` | string | 否 | `male`, `female` | 生成人声的性别。仅当 `generate_type` 为 `Vocals` 时生效 |

### 响应格式 (200 OK) — SongTask

见 [公共数据结构 — SongTask](#songtask)

### cURL 示例

```bash
# 从伴奏生成歌声
curl https://api.mureka.cn/v1/track/generate \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "generate_type": "Vocals",
    "upload_audio_id": "your_upload_audio_id",
    "lyrics": "[主歌]\n在暴风雨的夜晚，我独自徘徊\n被雨淋湿，感觉像是被抛弃",
    "vocal_gender": "female"
  }'

# 从人声生成伴奏
curl https://api.mureka.cn/v1/track/generate \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "generate_type": "Instrumental",
    "upload_audio_id": "your_upload_audio_id",
    "prompt": "r&b, slow, passionate"
  }'

# 生成单一乐器轨道（不需要 song_id 或 upload_audio_id）
curl https://api.mureka.cn/v1/track/generate \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "generate_type": "Guitar",
    "prompt": "fingerpicking, acoustic, melancholic"
  }'
```

---

## 12. 局部编辑 POST /v1/song/region-edit

**描述**: 对歌曲或单轨的指定时间区间进行局部编辑。异步任务。

**Content-Type**: `application/json`

### 请求参数 — SongRegionEditReq

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `song_id` | string | 二选一 | 用于编辑的歌曲 ID，由 `song/generate` API 生成。与 `upload_audio_id` 二选一 |
| `upload_audio_id` | string | 二选一 | 用于编辑歌曲的上传文件 ID，由 `files/upload`（purpose: audio）生成。仅支持最近 1 个月内的歌曲。与 `song_id` 二选一 |
| `lyrics` | string | 否 | 重写到所选区间中的新歌词 |
| `edit_start` | integer (int64) | 否 | 要重写区间的开始时间（毫秒）。重写区间长度必须至少为 3 秒，且开始点之前必须至少保留 12 秒音频 |
| `edit_end` | integer (int64) | 否 | 要重写区间的结束时间（毫秒）。重写区间长度必须至少为 3 秒，且结束点之后必须至少保留 12 秒音频 |

**注意**: `edit_start` 和 `edit_end` 限制：
- 区间长度 >= 3 秒（3000 毫秒）
- `edit_start` 之前必须保留 >= 12 秒音频
- `edit_end` 之后必须保留 >= 12 秒音频

### 响应格式 (200 OK) — SongTask

见 [公共数据结构 — SongTask](#songtask)

### cURL 示例

```bash
curl https://api.mureka.cn/v1/song/region-edit \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "song_id": "1436211",
    "edit_start": 30000,
    "edit_end": 50000,
    "lyrics": "[Bridge]\nEvery scar tells a story worth telling"
  }'
```

---

## 13. 歌曲混音 POST /v1/song/remix

**描述**: 基于输入歌曲或上传音频重新生成 remix 版本。异步任务。

**Content-Type**: `application/json`

### 请求参数 — SongRemixReq

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `song_id` | string | 二选一 | 用于 Remix 的歌曲 ID，由 `song/generate` API 生成。与 `upload_audio_id` 二选一 |
| `upload_audio_id` | string | 二选一 | 用于 Remix 的歌曲上传文件 ID，由 `files/upload`（purpose: remix）生成。仅支持最近 1 个月内的歌曲。与 `song_id` 二选一 |
| `lyrics` | string | 否 | Remix 后歌曲的新歌词 |
| `n` | integer (int32) | 否 | 生成的数量，最大 3 |
| `prompt` | string | 否 | 用于控制 Remix 后歌曲风格的文本描述 |

### 响应格式 (200 OK) — SongTask

见 [公共数据结构 — SongTask](#songtask)

### cURL 示例

```bash
# 使用 song_id 结合新的 prompt 和歌词进行 Remix
curl https://api.mureka.cn/v1/song/remix \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "song_id": "1436211",
    "prompt": "jazz, upbeat, brass-driven",
    "lyrics": "[Verse]\nWalking down the avenue in the morning light\nEvery step I take feels like everything is right"
  }'

# 使用上传的音频文件进行 Remix
curl https://api.mureka.cn/v1/song/remix \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_audio_id": "your_upload_audio_id",
    "prompt": "jazz, upbeat, brass-driven"
  }'
```

---

## 14. 生成纯音乐 POST /v1/instrumental/generate

**描述**: 根据用户输入生成纯音乐（异步任务）。

**Content-Type**: `application/json`

### 请求参数 — InstrumentalGenerateReq

| 参数 | 类型 | 必填 | 枚举值 | 默认值 | 描述 |
|------|------|------|--------|--------|------|
| `model` | string | 是 | `auto`, `mureka-7.6`, `mureka-o2`, `mureka-8` | — | 要使用的模型。`auto` 选择常规模型最新版 |
| `n` | integer (int32) | 否 | — | 2 | 每次请求生成的纯音乐数量，最大值为 3。注意会根据数量计费 |
| `prompt` | string | 否 | — | — | 通过提示词控制纯音乐的生成，最大 1024 个字符。不支持与其他控制选项组合 |
| `instrumental_id` | string | 否 | — | — | 通过参考音乐控制纯音乐的生成，由 `files/upload`（purpose: instrumental）生成。不支持与其他控制选项组合 |
| `stream` | boolean | 否 | — | false | 如果为 true，任务状态会有 streaming 阶段，可通过 `stream_url` 边生成边收听 |

**注意**: `prompt` 和 `instrumental_id` 只能单独使用，不支持互相组合。

### 响应格式 (200 OK) — InstrumentalTask

见 [公共数据结构 — InstrumentalTask](#instrumentaltask)

### cURL 示例

```bash
curl https://api.mureka.cn/v1/instrumental/generate \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "prompt": "r&b, slow, passionate, male vocal"
  }'
```

---

## 15. 查询纯音乐任务 GET /v1/instrumental/query/{task_id}

**描述**: 查询纯音乐生成任务的信息。

### 路径参数

| 参数 | 类型 | 必填 | 示例 | 描述 |
|------|------|------|------|------|
| `task_id` | string | 是 | `435134` | 纯音乐生成任务的 task_id |

### 响应格式 (200 OK) — InstrumentalTask

见 [公共数据结构 — InstrumentalTask](#instrumentaltask)

### cURL 示例

```bash
curl https://api.mureka.cn/v1/instrumental/query/435134 \
  -H "Authorization: Bearer $MUREKA_API_KEY"
```

---

## 16. 创建上传对象 POST /v1/uploads/create

**描述**: 创建一个上传对象，后续可以向其中追加数据（用于大文件分块上传，如微调数据集）。

**Content-Type**: `application/json`

### 请求参数 — UploadsCreateReq

| 参数 | 类型 | 必填 | 枚举值 | 描述 |
|------|------|------|--------|------|
| `upload_name` | string | 是 | — | 为创建的上传命名，或为要上传的大文件命名 |
| `purpose` | string | 是 | `fine-tuning` | 此次上传的预期用途 |
| `bytes` | integer (int64) | 否 | — | 上传的总大小。如果未提供，则在上传结束时不会检查上传的总大小 |

### 响应格式 (200 OK) — UploadsTask

| 字段 | 类型 | 枚举值 | 描述 |
|------|------|--------|------|
| `id` | string | — | 异步任务的任务 ID |
| `upload_name` | string | — | 上传的名称 |
| `purpose` | string | — | 上传的预期用途 |
| `bytes` | integer (int64) | — | 上传的总大小 |
| `created_at` | integer (int64) | — | 上传任务创建的时间戳（以秒为单位） |
| `expires_at` | integer (int64) | — | 上传任务过期的时间戳（以秒为单位） |
| `status` | string | `pending`, `completed`, `cancelled` | 上传任务的当前状态 |
| `parts` | array[string] | — | 上传中包含的分块列表，仅在状态为 completed 时才有值 |

### 响应示例

```json
{
  "id": "1436211",
  "upload_name": "my.mp3",
  "purpose": "fine-tuning",
  "created_at": 1677610602,
  "expires_at": 1677610652,
  "status": "pending"
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/uploads/create \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_name": "my.mp3",
    "purpose": "fine-tuning"
  }'
```

---

## 17. 追加数据 POST /v1/uploads/add

**描述**: 向上传对象追加数据。追加的数据代表上传对象的一部分或一个大文件的块。上传数据最大可到 10 MB。

**Content-Type**: `multipart/form-data`

### 请求参数 — UploadsAddReq

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `file` | string (binary) | 是 | 要上传的文件内容（不是文件名）。对应用途：fine-tuning 支持格式（mp3, m4a），音频时长在 30 秒到 270 秒之间 |
| `upload_id` | string | 是 | 此次追加数据所属的上传对象 ID |

### 响应格式 (200 OK) — UploadsAddResp

| 字段 | 类型 | 描述 |
|------|------|------|
| `id` | string | 此次追加数据的 ID，用于 `uploads/complete` |
| `upload_id` | string | 此次追加数据所属的上传对象 ID |
| `created_at` | integer (int64) | 此次创建的时间戳（以秒为单位） |

### 响应示例

```json
{
  "id": "16211",
  "upload_id": "1436211",
  "created_at": 1677610602
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/uploads/add \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -F upload_id="1436211" \
  -F file="@mydata.mp3"
```

---

## 18. 完成上传 POST /v1/uploads/complete

**描述**: 完成上传。当创建一个带有指定字节数的上传对象时，它会检查所有部分的大小是否与指定的字节数匹配。

**Content-Type**: `application/json`

### 请求参数 — UploadsCompleteReq

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `upload_id` | string | 是 | 上传对象的 ID |
| `part_ids` | array[string] | 否 | 追加数据 ID 的有序列表。如果此参数为空，则表示使用 `uploads/add` 添加的所有分块，顺序按添加顺序排列 |

### 响应格式 (200 OK) — UploadsTask

与 [创建上传对象](#16-创建上传对象-post-v1uploadscreate) 响应格式相同，但 status 为 `completed`。

### 响应示例

```json
{
  "id": "1436211",
  "upload_name": "my.mp3",
  "purpose": "fine-tuning",
  "created_at": 1677610602,
  "expires_at": 1677610652,
  "status": "completed",
  "parts": ["1.mp3", "2.mp3"]
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/uploads/complete \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "1436211"
  }'
```

---

## 19. 创建语音 POST /v1/tts/generate

**描述**: 根据输入文本生成语音。

**Content-Type**: `application/json`

### 请求参数 — TTSGenerateReq

| 参数 | 类型 | 必填 | 枚举值 | 描述 |
|------|------|------|--------|------|
| `text` | string | 是 | — | 要生成音频的文本，最大长度为 500 个字符 |
| `voice` | string | 二选一 | `Ethan`, `Victoria`, `Jake`, `Luna`, `Emma` | 生成音频时的说话人。选择此选项时，`voice_id` 不能选择 |
| `voice_id` | string | 二选一 | — | 通过参考语音控制生成，由 `files/upload`（purpose: voice）生成。选择此选项时，`voice` 不能选择 |

**注意**: `voice` 和 `voice_id` 互斥，只能选其一。

### 响应格式 (200 OK) — TTSGenerateResp

| 字段 | 类型 | 描述 |
|------|------|------|
| `url` | string | 音频文件的 URL |
| `expires_at` | integer (int64) | URL 过期的时间戳（以秒为单位） |

### 响应示例

```json
{
  "url": "https://cdn.mureka.cn/1.mp3",
  "expires_at": 1677610652
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/tts/generate \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "嗨，我叫艾玛。",
    "voice": "Emma"
  }'
```

---

## 20. 创建播客 POST /v1/tts/podcast

**描述**: 将双人对话文本转换为播客风格音频对话。

**Content-Type**: `application/json`

### 请求参数 — TTSPodcastReq

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `conversations` | array[TTSMessage] | 是 | 对话数组，数组的最大长度为 10 |

**TTSMessage 对象**:

| 字段 | 类型 | 枚举值 | 描述 |
|------|------|--------|------|
| `text` | string | — | 对话的文本，最大长度为 400 个字符 |
| `voice` | string | `Ethan`, `Victoria`, `Jake`, `Luna`, `Emma` | 使用的说话人 |

### 响应格式 (200 OK) — TTSGenerateResp

与 TTS Generate 响应格式相同：

| 字段 | 类型 | 描述 |
|------|------|------|
| `url` | string | 音频文件的 URL |
| `expires_at` | integer (int64) | URL 过期的时间戳（以秒为单位） |

### 响应示例

```json
{
  "url": "https://cdn.mureka.cn/1.mp3",
  "expires_at": 1677610652
}
```

### cURL 示例

```bash
curl https://api.mureka.cn/v1/tts/podcast \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversations": [
      {"text": "嗨，我叫露娜。", "voice": "Luna"},
      {"text": "嗨，我叫杰克。", "voice": "Jake"},
      {"text": "先前的研究表明，与乐器变化和音量增大相关的模式存在一些变化。", "voice": "Luna"},
      {"text": "由于MLLM本身的特性，将视觉与语音结合起来并不是一件简单的事情。", "voice": "Jake"}
    ]
  }'
```

---

## 21. 查询账单 GET /v1/account/billing

**描述**: 查询账户的账单信息。

### 请求参数

无请求参数。

### 响应格式 (200 OK) — AccountBillingResp

| 字段 | 类型 | 描述 |
|------|------|------|
| `account_id` | integer (int64) | 账户 ID |
| `balance` | integer (int64) | 账户的余额，单位分 |
| `total_recharge` | integer (int64) | 账户的总充值额，单位分 |
| `total_spending` | integer (int64) | 账户的总消费额，单位分 |
| `concurrent_request_limit` | integer (int64) | 账户的最大并发请求次数 |

### 响应示例

```json
{
  "account_id": 1436211,
  "balance": 1000,
  "total_recharge": 10000,
  "total_spending": 9000,
  "concurrent_request_limit": 5
}
```

**注意**: 余额单位为"分"（人民币分）。

### cURL 示例

```bash
curl https://api.mureka.cn/v1/account/billing \
  -H "Authorization: Bearer $MUREKA_API_KEY"
```

---

## 22. 附录：微调相关接口

以下两个接口在主文档页面导航中未列出，但存在于 OpenAPI 规范中：

### 创建微调任务 POST /v1/finetuning/create

**描述**: 使用给定的数据集创建一个微调模型。

**请求参数 — FinetuningCreateReq**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `upload_id` | string | 是 | 上传对象的 ID（状态必须为 completed）。一次有效的微调需要上传 100-200 首风格一致的歌，每首歌时长 2-4 分钟，200 首 4 分钟的歌曲约需训练 3 小时 |
| `suffix` | string | 是 | 微调模型名称后缀，最多 32 个字符。仅允许小写字母、数字和连字符。例如后缀 "my-model" 将产生模型名 `lora:mureka-6:4354198:my-model` |

**响应格式 (200 OK) — FinetuningTask**:

| 字段 | 类型 | 枚举值 | 描述 |
|------|------|--------|------|
| `id` | string | — | 异步微调任务的任务 ID |
| `upload_id` | string | — | 上传对象 ID |
| `model` | string | — | 微调所使用的基础模型 |
| `created_at` | integer (int64) | — | 任务创建的时间戳（以秒为单位） |
| `finished_at` | integer (int64) | — | 任务完成的时间戳（以秒为单位） |
| `status` | string | `preparing`, `queued`, `running`, `succeeded`, `failed`, `timeouted`, `cancelled` | 任务的当前状态 |
| `failed_reason` | string | — | 当状态为失败时产生的原因 |
| `fine_tuned_model` | string | — | 微调模型的名称 |

**cURL 示例**:

```bash
curl https://api.mureka.cn/v1/finetuning/create \
  -H "Authorization: Bearer $MUREKA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "1436211",
    "suffix": "my-model"
  }'
```

### 查询微调任务 GET /v1/finetuning/query/{task_id}

**路径参数**: `task_id` (string, 必填) — 微调任务的 task_id

**响应格式**: 同上 FinetuningTask 结构

**cURL 示例**:

```bash
curl https://api.mureka.cn/v1/finetuning/query/1436211 \
  -H "Authorization: Bearer $MUREKA_API_KEY"
```

---

## 23. 公共数据结构

### SongTask

歌曲生成异步任务对象（`POST /v1/song/generate`、`/v1/song/extend`、`/v1/track/generate`、`/v1/song/region-edit`、`/v1/song/remix` 等均返回此结构）：

| 字段 | 类型 | 枚举值 | 描述 |
|------|------|--------|------|
| `id` | string | — | 异步音乐生成任务的任务 ID |
| `created_at` | integer (int64) | — | 任务创建的时间戳（以秒为单位） |
| `finished_at` | integer (int64) | — | 任务完成的时间戳（以秒为单位） |
| `model` | string | — | 用于音乐生成的模型 |
| `status` | string | `preparing`, `queued`, `running`, `streaming`, `reviewing`, `succeeded`, `failed`, `timeouted`, `cancelled` | 任务的当前状态 |
| `failed_reason` | string | — | 当任务失败时发生的原因 |
| `watermarked` | boolean | — | 如果为 true，则表示在生成音乐的尾部添加了 5 秒水印音频 |
| `choices` | array[Song] | — | 生成的歌曲列表，只有 status 为 succeeded 时才有该字段 |

**status 状态说明**:
- `preparing` — 任务准备中
- `queued` — 任务排队中
- `running` — 任务运行中
- `streaming` — 流式生成阶段（stream=true 时才有）
- `reviewing` — 审核中
- `succeeded` — 成功
- `failed` — 失败
- `timeouted` — 超时
- `cancelled` — 已取消

### Song

| 字段 | 类型 | 描述 |
|------|------|------|
| `index` | integer (int32) | 歌曲的索引 |
| `id` | string | 歌曲的 ID |
| `url` | string | 歌曲的 URL，有效期 30 天 |
| `flac_url` | string | 歌曲的无损 FLAC 格式 URL，有效期 30 天 |
| `wav_url` | string | 歌曲的无损 WAV 格式 URL，有效期 30 天 |
| `stream_url` | string | 在请求参数 stream 为 true 时，在 streaming 阶段可以播放的 url |
| `duration` | integer (int64) | 歌曲的时长，以毫秒为单位 |
| `lyrics_sections` | array[LyricsSection] | 包含时间戳的歌词段落信息 |

### LyricsSection

| 字段 | 类型 | 枚举值 | 描述 |
|------|------|--------|------|
| `section_type` | string | `intro`, `verse`, `pre-chorus`, `chorus`, `bridge`, `break`, `outro` | 段落的类型 |
| `start` | integer (int64) | — | 段落的开始时间，以毫秒为单位 |
| `end` | integer (int64) | — | 段落的结束时间，以毫秒为单位 |
| `lines` | array[Line] | — | 段落中包含的行 |

**Line 对象**:

| 字段 | 类型 | 描述 |
|------|------|------|
| `start` | integer (int64) | 行的开始时间，以毫秒为单位 |
| `end` | integer (int64) | 行的结束时间，以毫秒为单位 |
| `text` | string | 行中的歌词 |
| `words` | array[Word] | 行中包含的词 |

**Word 对象**:

| 字段 | 类型 | 描述 |
|------|------|------|
| `start` | integer (int64) | 词的开始时间，以毫秒为单位 |
| `end` | integer (int64) | 词的结束时间，以毫秒为单位 |
| `text` | string | 词的文本 |

### InstrumentalTask

纯音乐生成异步任务对象：

| 字段 | 类型 | 枚举值 | 描述 |
|------|------|--------|------|
| `id` | string | — | 异步纯音乐生成任务的任务 ID |
| `created_at` | integer (int64) | — | 任务创建的时间戳（以秒为单位） |
| `finished_at` | integer (int64) | — | 任务完成的时间戳（以秒为单位） |
| `model` | string | — | 用于纯音乐生成的模型 |
| `status` | string | `preparing`, `queued`, `running`, `streaming`, `reviewing`, `succeeded`, `failed`, `timeouted`, `cancelled` | 任务的当前状态 |
| `failed_reason` | string | — | 当任务失败时发生的原因 |
| `watermarked` | boolean | — | 如果为 true，则表示在生成音乐的尾部添加了 5 秒水印音频 |
| `choices` | array[Instrumental] | — | 生成的纯音乐列表，只有 status 为 succeeded 时才有该字段 |

### Instrumental

| 字段 | 类型 | 描述 |
|------|------|------|
| `index` | integer (int32) | 纯音乐的索引 |
| `id` | string | 纯音乐的 ID |
| `url` | string | 纯音乐的 URL，有效期 30 天 |
| `flac_url` | string | 纯音乐的无损 FLAC 格式 URL，有效期 30 天 |
| `wav_url` | string | 纯音乐的无损 WAV 格式 URL，有效期 30 天 |
| `stream_url` | string | 在请求参数 stream 为 true 时，在 streaming 阶段可以播放的 url |
| `duration` | integer (int64) | 纯音乐的时长，以毫秒为单位 |

---

## 24. 错误代码

| HTTP 状态码 | 错误类型 | 原因 | 解决方案 |
|------------|---------|------|---------|
| 400 | Invalid Request | 请求参数不正确 | 核对参数与文档 |
| 401 | Invalid Authentication | 认证无效 | 使用正确的 API Key |
| 403 | Forbidden | 从不支持的地区访问 | 确保请求来自支持的地区 |
| 429 | Rate Limit Exceeded | 发送请求过于频繁 | 根据计划的并发限制降低频率 |
| 429 | Quota Exceeded | 充值已用完 | 充值账户 |
| 451 | Unavailable For Legal Reasons | 请求参数未通过安全审查 | 修改请求参数 |
| 500 | Server Error | 服务处理时发生故障 | 稍后重试；问题持续则联系支持 |
| 503 | Service Overloaded | 服务负载过高 | 稍后重试 |

**错误响应格式**:

```json
{
  "error": {
    "message": "Invalid Authentication"
  },
  "trace_id": "1e94aba5a2de4cc4bff54a2813c8d36c"
}
```

---

## 25. 平台说明

### 模型列表

| 模型 | 适用场景 | 说明 |
|------|---------|------|
| `auto` | 歌曲生成、纯音乐生成 | 自动选择常规模型最新版（非 mureka-o 系列） |
| `mureka-7.6` | 歌曲/纯音乐生成、续写 | 稳定版，支持续写 |
| `mureka-o2` | 歌曲/纯音乐生成 | o 系列，不支持 stream 模式 |
| `mureka-8` | 歌曲生成、续写 | 最新稳定版，支持双向续写（head/tail） |
| `mureka-9` | 歌曲生成 | 最新版 |
| `mureka-8`（仅纯音乐） | 纯音乐生成 | — |
| `audio-separation-1` | 分轨 | 不支持 MIDI 输出 |
| `audio-separation-2` | 分轨 | 支持 MIDI 输出 |

### 支持语言

中文、英语、日语、韩语、葡萄牙语、西班牙语、德语、法语、意大利语、俄语（共 10 种）。

### 计费规则

- 余额单位：分（人民币分）
- 生成数量 `n` 直接影响费用（按数量计费）
- 余额有效期：12 个月（从最后一次充值起）；新充值会延长所有余额的有效期
- 歌曲下载不额外收费；分轨需要单独付费
- 并发请求数上限由充值额度决定（基础 5 并发，高充值可扩展）
- 生成音频尾部附加 5 秒水印（合规要求）
- 付费 API 调用生成的内容包含完整使用权和商业授权

### 异步任务轮询建议

- **歌曲生成**：使用 `GET /v1/song/query/{task_id}` 轮询
- **纯音乐生成**：使用 `GET /v1/instrumental/query/{task_id}` 轮询
- 轮询间隔建议 2-5 秒
- 任务状态流转：`preparing` → `queued` → `running` → [`streaming`] → `reviewing` → `succeeded` / `failed`

### 流式生成（stream: true）

- 适用于歌曲生成和纯音乐生成
- 任务进入 `streaming` 阶段后，可通过 `stream_url` 边生成边播放
- 流 URL 在歌曲生成完成后额外有效 5 分钟
- `mureka-o1`/`mureka-o2` 不支持 stream 模式

### 技术支持

- 邮箱：api-support@mureka.ai
- 响应时间：24 小时内

---

*文档提取时间：2026-04-14*
*数据来源：从 `https://platform.mureka.cn/docs/assets/chunks/theme.zbVB06cC.js` 中提取的完整 OpenAPI 规范*
