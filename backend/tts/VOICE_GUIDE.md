# 语音选择指南

## 🎤 如何选择语音

ElevenLabs提供了多种语音，每种语音都有不同的特点。以下是选择和使用语音的完整指南。

---

## 📋 查看可用语音

### 方法1：使用命令行脚本

```bash
python scripts/list_voices.py
```

这将列出您账户中所有可用的语音，包括：
- 语音名称
- Voice ID（用于代码中）
- 口音（american, british, australian等）
- 性别（male, female, neutral）
- 年龄（young, middle_aged, old）
- 描述

### 方法2：在代码中查询

```python
from services.synthesis_service import create_synthesis_service
import os

service = create_synthesis_service(
    provider="elevenlabs",
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# 获取所有可用语音
voices = await service.get_available_voices()

for voice in voices:
    print(f"{voice.name}: {voice.voice_id}")
    print(f"  口音: {voice.accent}, 性别: {voice.gender}")
```

---

## 🌟 推荐语音（当前账户）

基于您的账户，以下是一些推荐的语音：

### 美国英语（American English）

| 名称 | Voice ID | 性别 | 年龄 | 特点 |
|------|----------|------|------|------|
| **Sarah** | `EXAVITQu4vr4xnSDxMaL` | Female | Young | 自信、温暖（默认推荐）|
| Laura | `FGY2WhTYpPnrIDTdsKH5` | Female | Young | 阳光、热情 |
| Roger | `CwhRBWXzGAHq8TQ4Fs17` | Male | Middle | 随意、友好 |
| Clyde | `2EiwWnXFnvU5JabPnv8n` | Male | Middle | 适合角色扮演 |
| Brian | `nPczCjzI2devNBz1zQrb` | Male | Middle | 共鸣、舒适 |

### 英国英语（British English）

| 名称 | Voice ID | 性别 | 年龄 | 特点 |
|------|----------|------|------|------|
| **George** | `JBFqnCBsd6RMkjVDRZzb` | Male | Middle | 温暖、迷人 |
| Alice | `Xb7hH8MSUJpSbSDYk0k2` | Female | Middle | 清晰、友好 |
| Daniel | `onwK4e9ZLuTAKqWW03F9` | Male | Middle | 专业、广播级 |
| Lily | `pFZP5JQG7iQjIQuC4Bku` | Female | Middle | 天鹅绒般、新闻播报 |

### 澳大利亚英语（Australian English）

| 名称 | Voice ID | 性别 | 年龄 | 特点 |
|------|----------|------|------|------|
| **Charlie** | `IKne3meq5aSn9XLyUdCD` | Male | Young | 自信、充满活力 |

### 其他语言

| 名称 | Voice ID | 语言 | 特点 |
|------|----------|------|------|
| Felix | `MbbPUteESkJWr4IAaW35` | 德语 | 温暖清晰的德语男声 |
| Stacy | `hkfHEbBvdQFNX4uWHqRF` | 中文（台湾） | 年轻可爱的女声 |
| Varsha | `kL06KYMvPY56NluIQ72m` | 印地语/英语 | 印度女声，温暖清晰 |

---

## 💡 使用示例

### 基础使用

```python
# 使用Sarah（默认推荐）
response = await service.synthesize_whole(
    text="Hello, this is Sarah speaking.",
    voice_id="EXAVITQu4vr4xnSDxMaL",
)
```

### 自定义语音参数

不同语音可以通过参数调整特性：

```python
from domain.models import VoiceSettings

# 使用George，调整为更稳定的声音
response = await service.synthesize_whole(
    text="Good evening, this is the news.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # George
    voice_settings=VoiceSettings(
        stability=0.75,          # 更稳定（0.0-1.0）
        similarity_boost=0.5,    # 中等相似度
        style=0.0,               # 不使用风格强化
        use_speaker_boost=True,  # 启用说话人增强
    ),
)
```

### 参数说明

| 参数 | 范围 | 说明 | 推荐值 |
|------|------|------|--------|
| **stability** | 0.0-1.0 | 稳定性。越高越一致，但可能单调 | 0.5-0.75 |
| **similarity_boost** | 0.0-1.0 | 与原始语音的相似度 | 0.75 |
| **style** | 0.0-1.0 | 风格强度。增加表现力 | 0.0-0.3 |
| **use_speaker_boost** | bool | 增强清晰度 | True |

---

## 🎯 场景推荐

### 1. 新闻播报/专业叙述
- **推荐**：Daniel（英国男声）、Brian（美国男声）
- **参数**：高stability（0.7-0.8），低style（0.0）

```python
voice_settings=VoiceSettings(
    stability=0.75,
    similarity_boost=0.5,
    style=0.0,
    use_speaker_boost=True,
)
```

### 2. 友好对话/客服
- **推荐**：Sarah（美国女声）、Roger（美国男声）
- **参数**：中stability（0.5），中style（0.2）

```python
voice_settings=VoiceSettings(
    stability=0.5,
    similarity_boost=0.75,
    style=0.2,
    use_speaker_boost=True,
)
```

### 3. 有声书/故事叙述
- **推荐**：George（英国男声）、Alice（英国女声）
- **参数**：中低stability（0.4-0.6），高style（0.3-0.5）

```python
voice_settings=VoiceSettings(
    stability=0.5,
    similarity_boost=0.75,
    style=0.4,
    use_speaker_boost=True,
)
```

### 4. 营销视频/社交媒体
- **推荐**：Laura（美国女声）、Charlie（澳洲男声）
- **参数**：低stability（0.3-0.5），高style（0.4-0.6）

```python
voice_settings=VoiceSettings(
    stability=0.4,
    similarity_boost=0.75,
    style=0.5,
    use_speaker_boost=True,
)
```

---

## 🌍 多语言支持

ElevenLabs的`eleven_multilingual_v2`模型支持29种语言，包括：

- 🇬🇧 英语（美国、英国、澳洲等）
- 🇨🇳 中文（简体、繁体）
- 🇯🇵 日语
- 🇰🇷 韩语
- 🇩🇪 德语
- 🇫🇷 法语
- 🇪🇸 西班牙语
- 🇮🇹 意大利语
- 🇵🇹 葡萄牙语
- 🇮🇳 印地语
- ... 等等

### 使用中文示例

```python
# 使用Stacy（台湾中文女声）
response = await service.synthesize_whole(
    text="你好，这是一个中文测试。",
    voice_id="hkfHEbBvdQFNX4uWHqRF",  # Stacy
)
```

**注意**：即使使用英文语音（如Sarah），也可以合成其他语言，但口音可能不够地道。推荐使用对应语言的专用语音。

---

## ⚙️ 配置默认语音

在`.env`文件中设置默认语音：

```bash
# 设置默认语音ID
ELEVENLABS_VOICE_DEFAULT=EXAVITQu4vr4xnSDxMaL  # Sarah

# 或选择其他语音
# ELEVENLABS_VOICE_DEFAULT=JBFqnCBsd6RMkjVDRZzb  # George
# ELEVENLABS_VOICE_DEFAULT=IKne3meq5aSn9XLyUdCD  # Charlie
```

---

## ❓ 常见问题

### Q: 为什么找不到"Rachel"这个语音？

**A**: ElevenLabs已经移除了"Rachel"语音。请使用当前可用的语音，如"Sarah"（`EXAVITQu4vr4xnSDxMaL`）。

### Q: 如何知道哪个语音最适合我的项目？

**A**: 
1. 运行`python scripts/list_voices.py`查看所有语音
2. 参考本文档的"场景推荐"部分
3. 访问ElevenLabs官网试听每个语音
4. 在项目中测试几个候选语音

### Q: 可以使用语音名称（name）而非ID吗？

**A**: 不可以。API要求使用`voice_id`（如`EXAVITQu4vr4xnSDxMaL`），而非名称（如`Sarah`）。名称仅用于显示。

### Q: 语音列表会变化吗？

**A**: 是的。ElevenLabs会定期添加新语音或移除旧语音。建议定期运行`list_voices.py`查看最新列表。

### Q: 如何创建自定义语音？

**A**: ElevenLabs支持语音克隆功能，但需要通过他们的Web界面操作。创建后，自定义语音会出现在您的可用语音列表中。

---

## 📚 延伸阅读

- [ElevenLabs官方文档](https://elevenlabs.io/docs)
- [Voice Lab](https://elevenlabs.io/voice-lab) - 创建自定义语音
- [API参考](https://elevenlabs.io/docs/api-reference)

---

**提示**：始终使用`voice_id`而非`name`，并定期检查可用语音列表！

