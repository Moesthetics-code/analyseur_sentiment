import re
import nltk
import os

# Ensure NLTK data path
nltk_data_path = os.path.join(os.path.expanduser('~'), 'nltk_data')
os.makedirs(nltk_data_path, exist_ok=True)
nltk.data.path.append(nltk_data_path)


def download_nltk_resources():
    """Download required NLTK resources if not present."""
    for resource in ['vader_lexicon', 'punkt']:
        try:
            nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else f'sentiment/{resource}')
        except LookupError:
            nltk.download(resource, quiet=True)


def _simple_sentence_tokenize(text: str) -> list[str]:
    """Split text into sentences without relying on punkt tokenizer."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def analyze_with_vader(text: str, source_lang: str = 'fr') -> dict:
    """
    Analyze sentiment using VADER (NLTK).
    Translates text to English first if needed.
    Returns a normalized result dict.
    """
    from modules.translator import translate_text
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    download_nltk_resources()
    sia = SentimentIntensityAnalyzer()

    # Translate to English for analysis
    text_en = translate_text(text, source_lang, 'en') if source_lang != 'en' else text

    # Global scores
    scores = sia.polarity_scores(text_en)

    # Per-sentence analysis
    sentences = _simple_sentence_tokenize(text)
    sentence_analysis = []

    for sentence in sentences:
        if not sentence:
            continue
        if source_lang != 'en':
            try:
                sentence_en = translate_text(sentence, source_lang, 'en')
            except Exception:
                sentence_en = sentence
        else:
            sentence_en = sentence

        sent_score = sia.polarity_scores(sentence_en)
        sentence_analysis.append({
            'sentence': sentence,
            'compound': round(sent_score['compound'], 4),
            'pos': round(sent_score['pos'], 4),
            'neu': round(sent_score['neu'], 4),
            'neg': round(sent_score['neg'], 4),
        })

    sorted_sents = sorted(sentence_analysis, key=lambda x: x['compound'])
    compound = scores['compound']

    return {
        'sentiment': _compound_to_label(compound),
        'scores': {
            'compound': round(compound, 4),
            'pos': round(scores['pos'], 4),
            'neu': round(scores['neu'], 4),
            'neg': round(scores['neg'], 4),
        },
        'sentence_analysis': sentence_analysis,
        'most_negative': sorted_sents[0] if sorted_sents else None,
        'most_positive': sorted_sents[-1] if sorted_sents else None,
        'model': 'VADER',
    }


def _compound_to_label(compound: float) -> str:
    if compound >= 0.05:
        return 'positif'
    elif compound <= -0.05:
        return 'négatif'
    return 'neutre'

