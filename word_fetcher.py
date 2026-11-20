import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "lingo/0.1 (personal project)"}
DEF_URL = "https://en.wiktionary.org/api/rest_v1/page/definition/{}"
HTML_URL = "https://en.wiktionary.org/api/rest_v1/page/html/{}"


def clean(html):
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def get_definitions(word):
    response = requests.get(
        DEF_URL.format(word),
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()
    return response.json().get("es", [])


# ---------- pronunciation + gender ----------
def _find_spanish_section(soup):
    """
    Return the element(s) representing the Spanish language section.
    Handles both <h2 id="Spanish"> and lowercased <h2 id="spanish">,
    and both the section-wrapped and flat-sibling layouts.
    """
    heading = soup.find(
        lambda tag: tag.name in ("h2", "h3", "h4")
        and tag.get("id", "").lower() == "spanish"
    )
    if heading is None:
        span = soup.find(
            "span",
            class_="mw-headline",
            id=lambda v: v and v.lower() == "spanish"
        )
        if span:
            heading = span.find_parent(["h2", "h3", "h4"])
    if heading is None:
        return None, []

    section = heading.find_parent("section")
    if section is not None:
        return heading, [section]

    collected = []
    for sib in heading.find_next_siblings():
        if sib.name in ("h2", "h3", "h4"):
            break
        collected.append(sib)
    return heading, collected



def get_example(word):
    url = "https://api.tatoeba.org/v1/sentences"

    params = {
        "q": word,
        "lang": "spa",
        "showtrans": "all",
        "sort": "relevance"
    }

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()

    sentences = response.json().get("data", [])

    for sentence in sentences:
        if sentence.get("is_unapproved"):
            continue

        example = sentence.get("text", "")

        for translation in sentence.get("translations", []):
            if (
                translation.get("lang") == "eng"
                and not translation.get("is_unapproved")
            ):
                return example, translation.get("text", "")

    return "", ""

def get_pronunciation_and_gender(word):
    response = requests.get(
        HTML_URL.format(word),
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    heading, parts = _find_spanish_section(soup)
    if not parts:
        return [], ""

    fragment = "".join(str(p) for p in parts)
    scope = BeautifulSoup(fragment, "html.parser")

    # ---- IPA: only real IPA (wrapped in /.../ or [...]) ----
    ipas = []
    for span in scope.select(".IPA"):
        text = span.get_text(" ", strip=True)
        if not text:
            continue
        if text.startswith(("/", "[")) and text not in ipas:
            ipas.append(text)

    # ---- Gender ----
    gender = ""
    gender_span = scope.select_one(".gender")
    if gender_span:
        g = gender_span.get_text(strip=True)
        if g:
            gender = {"m": "masculine", "f": "feminine",
                      "mf": "masculine or feminine",
                      "mfbysense": "masculine or feminine"}.get(g, g)
    if not gender:
        for cell in scope.select("td, th"):
            txt = cell.get_text(" ", strip=True).lower()
            if txt.startswith("gender"):
                sibling = cell.find_next_sibling()
                if sibling:
                    g = sibling.get_text(" ", strip=True)
                    if g:
                        gender = g
                        break

    return ipas, gender


# ---------- example extraction ----------
def _extract_example(definition):
    """
    Return (example, translation) for one definition.
    Checks parsedExamples first, then the raw 'example' field.
    """
    for ex in definition.get("parsedExamples", []) or []:
        text = clean(ex.get("example") or "")
        if text:
            return text, clean(ex.get("translation") or "")

    raw = clean(definition.get("example") or "")
    if raw:
        return raw, ""
    return "", ""


# ---------- main entry ----------
def fetch_word(word):
    word = word.strip().lower()

    if not word:
        raise ValueError("Word cannot be empty.")

    entries = get_definitions(word)
    ipas, gender = get_pronunciation_and_gender(word)

    if not entries:
        raise ValueError(f"No Spanish definitions found for '{word}'.")

    entry = entries[0]
    definitions = entry.get("definitions", [])

    if not definitions:
        raise ValueError(f"No definitions available for '{word}'.")

    first_definition = definitions[0]

    # ---- example: primary definition first, then the rest ----
    example, translation = get_example(word)

    if not example:
        for e in entries:
            for d in e.get("definitions", []):
                example, translation = _extract_example(d)
                if example:
                    break
            if example:
                break

    return {
        "word": word,
        "meaning": clean(first_definition.get("definition", "")),
        "part_of_speech": entry.get("partOfSpeech", ""),
        "gender": gender,
        "pronunciation": ", ".join(ipas),
        "example": example,
        "translation": translation
    }