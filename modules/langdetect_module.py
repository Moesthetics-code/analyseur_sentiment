"""
Automatic language detection using langdetect.
Falls back to 'fr' on failure.
"""

SUPPORTED_LANGS = {'fr', 'en', 'es', 'de', 'it', 'pt', 'nl', 'ru', 'ar', 'zh'}


def detect_language(text: str) -> dict:
    """
    Detects the language of text.
    Returns {'lang': 'fr', 'confidence': 0.99, 'supported': True}
    """
    if not text or len(text.strip()) < 10:
        return {"lang": "fr", "confidence": 0.0, "supported": True}

    try:
        from langdetect import detect_langs
        results = detect_langs(text)
        if results:
            top = results[0]
            lang = top.lang
            confidence = round(top.prob, 3)
            # Map zh-cn/zh-tw → zh
            if lang.startswith("zh"):
                lang = "zh"
            supported = lang in SUPPORTED_LANGS
            return {"lang": lang, "confidence": confidence, "supported": supported}
    except Exception as e:
        print(f"[langdetect] Detection failed: {e}")

    return {"lang": "fr", "confidence": 0.0, "supported": True}