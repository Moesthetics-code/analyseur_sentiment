from flask import Blueprint, request, jsonify, session, Response
from datetime import datetime
from modules.sentiment import analyze_with_vader
from modules.wordcloud_gen import extract_word_frequencies, generate_wordcloud_base64
from modules.export import export_history_csv
from modules.translator import LANGUAGE_NAMES
from modules.langdetect_module import detect_language
from modules.batch import analyze_batch, batch_stats
from modules.highlight import build_highlight_html

api_bp = Blueprint('api', __name__)


def get_history() -> list:
    if 'history' not in session:
        session['history'] = []
    return session['history']


def _run_analysis(text, source_lang, model, generate_wc=True):
    if model == 'transformers':
        return jsonify({"error": "transformers_disabled_on_free_plan"}), 400
        #result = analyze_with_transformers(text, source_lang)
    else:
        result = analyze_with_vader(text, source_lang)
    result['highlight_html'] = build_highlight_html(result.get('sentence_analysis', []))
    result['wordcloud'] = ''
    if generate_wc:
        try:
            wf = extract_word_frequencies(text)
            result['wordcloud'] = generate_wordcloud_base64(wf)
        except Exception:
            pass
    return result


def _save_to_history(text_preview, result, source_lang):
    history = get_history()
    history.append({
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'text': text_preview,
        'sentiment': result['sentiment'],
        'compound': result['scores']['compound'],
        'pos': result['scores']['pos'],
        'neu': result['scores']['neu'],
        'neg': result['scores']['neg'],
        'language': LANGUAGE_NAMES.get(source_lang, source_lang),
        'model': result.get('model', ''),
    })
    session['history'] = history[-50:]
    session.modified = True


@api_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    source_lang = data.get('lang', 'fr')
    model = data.get('model', 'vader')
    generate_wc = data.get('wordcloud', True)
    if not text:
        return jsonify({'error': 'no_text'}), 400
    try:
        result = _run_analysis(text, source_lang, model, generate_wc)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    _save_to_history(text[:60] + ('...' if len(text) > 60 else ''), result, source_lang)
    return jsonify(result)


@api_bp.route('/analyze-file', methods=['POST'])
def analyze_file():
    if 'file' not in request.files:
        return jsonify({'error': 'no_file'}), 400
    f = request.files['file']
    if not f.filename.endswith('.txt'):
        return jsonify({'error': 'invalid_type'}), 400
    try:
        text = f.read().decode('utf-8').strip()
    except Exception:
        return jsonify({'error': 'read_error'}), 400
    source_lang = request.form.get('lang', 'fr')
    model = request.form.get('model', 'vader')
    try:
        result = _run_analysis(text, source_lang, model)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    _save_to_history(f'[Fichier] {f.filename}', result, source_lang)
    return jsonify(result)


@api_bp.route('/detect-lang', methods=['POST'])
def detect_lang():
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'lang': 'fr', 'confidence': 0, 'supported': True})
    result = detect_language(text)
    return jsonify(result)


@api_bp.route('/batch', methods=['POST'])
def batch():
    data = request.get_json(silent=True) or {}
    raw = (data.get('texts') or '').strip()
    source_lang = data.get('lang', 'fr')
    model = data.get('model', 'vader')
    texts = [t.strip() for t in raw.splitlines() if t.strip()]
    if not texts:
        return jsonify({'error': 'no_texts'}), 400
    if len(texts) > 50:
        return jsonify({'error': 'too_many', 'max': 50}), 400
    try:
        results = analyze_batch(texts, source_lang, model)
        stats = batch_stats(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    history = get_history()
    avg = stats.get('avg_compound', 0)
    sentiment = 'positif' if avg >= 0.05 else ('negatif' if avg <= -0.05 else 'neutre')
    history.append({
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'text': f'[Lot] {len(texts)} textes',
        'sentiment': sentiment,
        'compound': avg,
        'pos': 0, 'neu': 0, 'neg': 0,
        'language': LANGUAGE_NAMES.get(source_lang, source_lang),
        'model': model,
    })
    session['history'] = history[-50:]
    session.modified = True
    return jsonify({'results': results, 'stats': stats})


@api_bp.route('/compare', methods=['POST'])
def compare():
    data = request.get_json(silent=True) or {}
    text_a = (data.get('text_a') or '').strip()
    text_b = (data.get('text_b') or '').strip()
    source_lang = data.get('lang', 'fr')
    model = data.get('model', 'vader')
    if not text_a or not text_b:
        return jsonify({'error': 'both_texts_required'}), 400
    try:
        res_a = _run_analysis(text_a, source_lang, model, generate_wc=False)
        res_b = _run_analysis(text_b, source_lang, model, generate_wc=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    ca, cb = res_a['scores']['compound'], res_b['scores']['compound']
    winner = 'A' if ca > cb else ('B' if cb > ca else 'tie')
    return jsonify({
        'a': {'scores': res_a['scores'], 'sentiment': res_a['sentiment'], 'highlight_html': res_a['highlight_html']},
        'b': {'scores': res_b['scores'], 'sentiment': res_b['sentiment'], 'highlight_html': res_b['highlight_html']},
        'winner': winner,
        'diff': round(ca - cb, 4),
    })


@api_bp.route('/history', methods=['GET'])
def get_history_route():
    return jsonify(get_history())


@api_bp.route('/history', methods=['DELETE'])
def clear_history_route():
    session['history'] = []
    session.modified = True
    return jsonify({'ok': True})


@api_bp.route('/export-csv', methods=['GET'])
def export_csv():
    history = get_history()
    csv_data = export_history_csv(history)
    return Response(csv_data, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=sentiment_results.csv'})