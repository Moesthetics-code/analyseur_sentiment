from deep_translator import GoogleTranslator


def translate_text(text: str, source_lang: str, target_lang: str = 'en') -> str:
    """
    Translate text from source_lang to target_lang.
    Falls back to original text on failure.
    """
    if source_lang == target_lang:
        return text
    try:
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    except Exception as e:
        print(f"[translator] Translation failed: {e}")
        return text


LANGUAGE_NAMES = {
    'fr': 'Français',
    'en': 'English',
    'es': 'Español',
    'de': 'Deutsch',
    'it': 'Italiano',
    'pt': 'Português',
    'nl': 'Nederlands',
    'ru': 'Русский',
    'ar': 'العربية',
    'zh': '中文',
}
