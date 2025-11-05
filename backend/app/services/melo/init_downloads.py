import nltk


def download_nltk_data():
    """下载 NLTK 所需的数据资源"""
    try:
        nltk.download('averaged_perceptron_tagger_eng', quiet=True)
        print("NLTK data downloaded successfully.")
    except Exception as e:
        print(f"Error downloading NLTK data: {e}")


if __name__ == '__main__':
    # 首先下载 NLTK 数据
    download_nltk_data()
    
    from melo.api import TTS
    device = 'auto'
    models = {
        'EN': TTS(language='EN', device=device),
        'ES': TTS(language='ES', device=device),
        'FR': TTS(language='FR', device=device),
        'ZH': TTS(language='ZH', device=device),
        'JP': TTS(language='JP', device=device),
        'KR': TTS(language='KR', device=device),
    }