from flask import Blueprint, render_template, request, session
from modules.i18n import TRANSLATIONS, EXAMPLE_TEXTS
from modules.translator import LANGUAGE_NAMES

main_bp = Blueprint('main', __name__)


def get_ui_lang():
    return session.get('ui_lang', 'fr')


@main_bp.route('/')
def index():
    ui_lang = get_ui_lang()
    t = TRANSLATIONS.get(ui_lang, TRANSLATIONS['fr'])
    examples = EXAMPLE_TEXTS.get(ui_lang, EXAMPLE_TEXTS['fr'])
    return render_template(
        'index.html',
        t=t,
        ui_lang=ui_lang,
        examples=examples,
        lang_names=LANGUAGE_NAMES,
        translations=TRANSLATIONS,
    )


@main_bp.route('/set-ui-lang/<lang>')
def set_ui_lang(lang):
    from flask import redirect, url_for
    if lang in TRANSLATIONS:
        session['ui_lang'] = lang
    return redirect(url_for('main.index'))