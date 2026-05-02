import csv
import io
from datetime import datetime


def export_history_csv(history: list[dict]) -> str:
    """Convert analysis history list to CSV string."""
    if not history:
        return ''

    output = io.StringIO()
    fieldnames = ['timestamp', 'text_preview', 'sentiment', 'compound', 'pos', 'neu', 'neg', 'language', 'model']
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for entry in history:
        row = {
            'timestamp': entry.get('timestamp', ''),
            'text_preview': entry.get('text', ''),
            'sentiment': entry.get('sentiment', ''),
            'compound': entry.get('compound', ''),
            'pos': entry.get('pos', ''),
            'neu': entry.get('neu', ''),
            'neg': entry.get('neg', ''),
            'language': entry.get('language', ''),
            'model': entry.get('model', ''),
        }
        writer.writerow(row)

    return output.getvalue()
