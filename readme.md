# Lango

**A personal Spanish vocabulary learning application built with Python.**

Lango is a desktop application designed to make vocabulary learning easier through automatically fetched Spanish words, definitions, pronunciation, example sentences, and a simple learning system.

Instead of manually searching for vocabulary, Lango prepares small learning sessions and lets you decide which words you want to remember.

## Features

- **Automatic Vocabulary Fetching** — Retrieves Spanish words from a frequency-based word list.
- **Word Definitions** — Fetches English meanings and parts of speech.
- **Pronunciation** — Displays Spanish IPA pronunciation when available.
- **Example Sentences** — Retrieves Spanish example sentences and their English translations.
- **Learning Sessions** — Presents 10 words per session.
- **Save Learned Words** — Save words you want to remember in a local SQLite database.
- **Study Later** — Temporarily postpone a word and see it again later in the current session.
- **Practice Mode** — Review previously learned words in random order.

## Technologies Used

- Python
- Tkinter
- SQLite
- Requests
- BeautifulSoup
- Wiktionary API
- Tatoeba API

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/tetumer/lango-sp-.git
cd lango-sp-
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

## How It Works

1. Lango retrieves candidate words from a Spanish frequency list.
2. It filters out words already stored in the local database.
3. It fetches definitions and pronunciation from Wiktionary.
4. It retrieves example sentences and translations from Tatoeba.
5. You go through the words and decide which ones to mark as learned.
6. Learned words are stored locally and become available in Practice Mode.

## Data Storage

Lango uses SQLite to store learned vocabulary.

The database is created locally when the application starts. Your learned words are stored on your own machine rather than being uploaded to the repository.

## Project Status

**Currently in development.**

Lango is a personal learning project. Features and functionality may change as development continues.

## License

No license has been specified yet.
