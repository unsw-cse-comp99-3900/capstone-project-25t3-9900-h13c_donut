# ✅ 语音ID修复说明

## 🐛 问题

运行示例时出现错误：
```
VoiceNotFoundError: A voice with the voice_id Rachel was not found.
```

## 🔍 原因

ElevenLabs已经移除了"Rachel"这个预设语音ID。这是一个常见问题，因为ElevenLabs会定期更新其语音库。

## ✅ 解决方案

### 已修复的文件

1. **example.py** - 所有示例现在使用"Sarah"（`EXAVITQu4vr4xnSDxMaL`）
2. **config/settings.py** - 更新默认语音ID
3. **README.md** - 更新所有文档示例
4. **新增脚本** - `scripts/list_voices.py` 用于查询可用语音

### 推荐的默认语音

| 名称 | Voice ID | 特点 |
|------|----------|------|
| **Sarah** | `EXAVITQu4vr4xnSDxMaL` | 年轻美国女性，自信温暖（现在的默认） |
| George | `JBFqnCBsd6RMkjVDRZzb` | 中年英国男性，温暖专业 |
| Laura | `FGY2WhTYpPnrIDTdsKH5` | 年轻美国女性，阳光热情 |

## 🚀 快速使用

### 1. 查看可用语音

```bash
python scripts/list_voices.py
```

### 2. 运行示例

```bash
python example.py
```

现在应该可以正常运行了！

### 3. 在代码中使用

```python
from services.synthesis_service import create_synthesis_service

service = create_synthesis_service(
    provider="elevenlabs",
    api_key="your_api_key",
)

# ✅ 正确：使用voice_id
response = await service.synthesize_whole(
    text="Hello!",
    voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah
)

# ❌ 错误：不要使用name
# voice_id="Sarah"  # 这会失败！
```

## 📚 更多信息

- 完整语音列表：运行 `python scripts/list_voices.py`
- 语音选择指南：查看 [VOICE_GUIDE.md](VOICE_GUIDE.md)
- 如何使用中文语音：使用 `hkfHEbBvdQFNX4uWHqRF` (Stacy)

## ⚠️ 重要提示

1. **始终使用voice_id**（如`EXAVITQu4vr4xnSDxMaL`），而非name（如`Sarah`）
2. **定期检查**：ElevenLabs的语音列表可能会变化
3. **不要硬编码**：考虑从配置文件或环境变量读取voice_id

## 🔄 未来预防

为避免再次出现此问题：

1. 在代码中使用配置变量：
```python
voice_id = os.getenv("ELEVENLABS_VOICE_DEFAULT", "EXAVITQu4vr4xnSDxMaL")
```

2. 添加健康检查：
```python
try:
    voices = await service.get_available_voices()
    # 验证voice_id是否存在
    if voice_id not in [v.voice_id for v in voices]:
        print(f"警告：语音 {voice_id} 不可用，使用默认语音")
        voice_id = voices[0].voice_id
except Exception as e:
    print(f"无法获取语音列表: {e}")
```

---

**修复完成！现在可以正常使用TTS模块了。** 🎉

