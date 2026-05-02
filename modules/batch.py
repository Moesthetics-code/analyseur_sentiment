"""
Batch analysis: analyze multiple texts (one per line) at once.
"""
from modules.sentiment import analyze_with_vader

def analyze_batch(texts: list[str], source_lang: str = "fr", model: str = "vader") -> list[dict]:
    """
    Analyze a list of texts.
    Returns list of simplified result dicts.
    """
    results = []
    for i, text in enumerate(texts):
        text = text.strip()
        if not text:
            continue
        try:
            res = analyze_with_vader(text, source_lang)

            results.append({
                "index": i + 1,
                "text_preview": text[:80] + ("…" if len(text) > 80 else ""),
                "sentiment": res["sentiment"],
                "compound": res["scores"]["compound"],
                "pos": res["scores"]["pos"],
                "neu": res["scores"]["neu"],
                "neg": res["scores"]["neg"],
                "model": res.get("model", model),
            })
        except Exception as e:
            results.append({
                "index": i + 1,
                "text_preview": text[:80],
                "sentiment": "erreur",
                "compound": 0,
                "pos": 0,
                "neu": 0,
                "neg": 0,
                "error": str(e),
            })

    return results


def batch_stats(results: list[dict]) -> dict:
    valid = [r for r in results if r["sentiment"] != "erreur"]
    if not valid:
        return {"total": 0, "positive": 0, "neutral": 0, "negative": 0, "avg_compound": 0}

    pos = sum(1 for r in valid if r["sentiment"] == "positif")
    neg = sum(1 for r in valid if r["sentiment"] == "négatif")
    neu = len(valid) - pos - neg
    avg = sum(r["compound"] for r in valid) / len(valid)

    return {
        "total": len(valid),
        "positive": pos,
        "neutral": neu,
        "negative": neg,
        "avg_compound": round(avg, 4),
    }