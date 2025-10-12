import requests
import json

url = "http://127.0.0.1:8000/internal/asr"
file_path = "story.wav"

with open(file_path, "rb") as f:
    # 显式声明文件类型
    files = {"file": ("story.wav", f, "audio/wav")}
    response = requests.post(url, files=files)

if response.status_code == 200:
    result = response.json()
    print("✅ 转写成功！")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    with open("transcription_result.json", "w", encoding="utf-8") as out:
        json.dump(result, out, indent=2, ensure_ascii=False)
    print("📁 已保存到: transcription_result.json")
else:
    print(f"❌ 请求失败: {response.status_code}")
    print(response.text)
