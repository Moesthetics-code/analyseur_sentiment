import re
import base64
import io
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


STOPWORDS_FR = {
    "le", "la", "les", "un", "une", "des", "et", "est", "il", "elle", "ils",
    "elles", "nous", "vous", "je", "tu", "on", "ce", "cette", "ces", "que",
    "qui", "qu", "quoi", "dont", "où", "à", "au", "aux", "de", "du", "des",
    "en", "par", "pour", "avec", "sans", "sous", "sur", "dans", "entre",
    "vers", "chez", "après", "avant", "depuis", "pendant", "selon", "pas",
    "ne", "plus", "moins", "très", "non", "oui", "si", "alors", "mais", "ou",
    "car", "donc", "c", "d", "j", "l", "m", "n", "s", "t", "y", "a", "être",
    "avoir", "faire", "aller", "voir", "savoir", "pouvoir", "vouloir",
    "comme", "tout", "tous", "toute", "toutes", "aucun", "aucune", "chaque",
    "the", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "shall", "can", "need", "dare", "ought", "used",
}


def extract_word_frequencies(text: str, top_n: int = 50) -> dict:
    """Extract top_n most frequent non-stopword words from text."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    words = [w for w in words if w not in STOPWORDS_FR and len(w) > 2]

    freq: dict = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_words[:top_n])


def generate_wordcloud_base64(word_freq: dict) -> str:
    """Generate a word cloud image and return it as a base64 PNG string."""
    if not word_freq:
        return ''

    wc = WordCloud(
        width=900,
        height=400,
        background_color='#0f172a',
        colormap='cool',
        max_words=60,
        prefer_horizontal=0.7,
    ).generate_from_frequencies(word_freq)

    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor('#0f172a')
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    plt.tight_layout(pad=0)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#0f172a')
    plt.close(fig)
    buf.seek(0)

    return base64.b64encode(buf.read()).decode('utf-8')
