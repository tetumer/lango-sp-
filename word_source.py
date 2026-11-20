
import csv
import io
import requests

SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "doozan/spanish_data/master/frequency.csv"
)

ALLOWED_POS = {"n", "v", "adj", "adv", "interj"}


def get_word_candidates(saved_words):
    response = requests.get(SOURCE_URL, timeout=30)
    response.raise_for_status()

    saved_words = {word.lower() for word in saved_words}
    candidates = []

    reader = csv.DictReader(io.StringIO(response.text))

    for row in reader:
        word = row.get("spanish", "").strip().lower()
        pos = row.get("pos", "").strip().lower()
        flags = row.get("flags", "").strip()

        if not word or not word.isalpha():
            continue

        if pos not in ALLOWED_POS:
            continue

        if "DUPLICATE" in flags or "NOUSAGE" in flags:
            continue

        if word in saved_words:
            continue

        candidates.append(word)

    return candidates
