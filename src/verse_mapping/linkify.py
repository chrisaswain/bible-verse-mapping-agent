"""Linkification utilities — turn plain-text citations into markdown links."""

from __future__ import annotations

import re
import urllib.parse

# ---------------------------------------------------------------------------
# Bible reference → BibleGateway URL
# ---------------------------------------------------------------------------

# Matches references like "1 Timothy 2:12", "Gen 2:18-23", "1 Cor 11:3-12",
# "Romans 16:1-7", "Judges 4:4-5", "2 Tim 3:14-15", etc.
# Also handles multi-verse like "1 Timothy 2:13-14" and "Acts 2:17-18".
_BOOK_PATTERN = (
    r"(?:[123]\s?)?"  # optional leading number (1, 2, 3)
    r"(?:"
    r"Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|"
    r"Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs|"
    r"Ecclesiastes|Song\s?of\s?Solomon|Isaiah|Jeremiah|Lamentations|Ezekiel|"
    r"Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|"
    r"Haggai|Zechariah|Malachi|"
    r"Matthew|Mark|Luke|John|Acts|Romans|"
    r"Corinthians|Galatians|Ephesians|Philippians|Colossians|"
    r"Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|"
    r"Jude|Revelation|"
    # Abbreviations
    r"Gen|Exod?|Lev|Num|Deut|Josh|Judg|Sam|Kgs|Chr|Neh|Esth|Ps|Prov|"
    r"Eccl|Isa|Jer|Lam|Ezek|Dan|Hos|Mic|Nah|Hab|Zeph|Hag|Zech|Mal|"
    r"Matt?|Mk|Lk|Jn|Rom|Cor|Gal|Eph|Phil|Col|Thess|Tim|Tit|Phlm|"
    r"Heb|Jas|Pet|Rev"
    r")"
)

_VERSE_REF_RE = re.compile(
    rf"(?<!\[)"  # not already inside a markdown link
    rf"(?<!\()"  # not inside a URL
    rf"({_BOOK_PATTERN})\s+"  # book name
    rf"(\d+)"  # chapter
    rf":(\d+)"  # verse start
    rf"(?:[–\-](\d+))?"  # optional verse end
    rf"(?!\])"  # not already a markdown link label
)

_DEFAULT_TRANSLATION = "ESV"


def bible_url(ref: str, translation: str = _DEFAULT_TRANSLATION) -> str:
    """Build a BibleGateway URL for a Scripture reference."""
    encoded = urllib.parse.quote_plus(ref)
    return f"https://www.biblegateway.com/passage/?search={encoded}&version={translation}"


def bible_link(ref: str, translation: str = _DEFAULT_TRANSLATION) -> str:
    """Return a markdown link for a Scripture reference."""
    return f"[{ref}]({bible_url(ref, translation)})"


# ---------------------------------------------------------------------------
# Strong's number → BibleHub URL
# ---------------------------------------------------------------------------

_STRONGS_RE = re.compile(r"(?<!\[)\b([GH])(\d+)\b(?!\])")


def strongs_url(strongs_id: str) -> str:
    """Build a BibleHub URL for a Strong's number (e.g., G831, H2617)."""
    lang_char = strongs_id[0].upper()
    number = strongs_id[1:]
    lang = "greek" if lang_char == "G" else "hebrew"
    return f"https://biblehub.com/{lang}/{number}.htm"


def strongs_link(strongs_id: str) -> str:
    """Return a markdown link for a Strong's number."""
    return f"[{strongs_id}]({strongs_url(strongs_id)})"


# ---------------------------------------------------------------------------
# Lexical source → best available online URL
# ---------------------------------------------------------------------------

_SOURCE_URLS: dict[str, str] = {
    "BDAG": "https://www.billmounce.com/greek-dictionary",
    "Thayer's": "https://www.blueletterbible.org/lexicon/",
    "BDB": "https://www.blueletterbible.org/lexicon/",
    "HALOT": "https://www.sbl-site.org/publications/article.aspx?ArticleId=802",
    "LSJ": "https://lsj.gr/",
    "TDNT": "https://www.logos.com/product/3210/theological-dictionary-of-the-new-testament",
    "NIDNTTE": "https://www.logos.com/product/44592/new-international-dictionary-of-new-testament-theology-and-exegesis",
}


def source_link(source_name: str) -> str:
    """Return a markdown link for a lexical source, or plain text if no URL."""
    url = _SOURCE_URLS.get(source_name)
    if url:
        return f"[{source_name}]({url})"
    return source_name


def source_link_with_strongs(source_name: str, strongs_id: str = "") -> str:
    """Return a markdown link for a lexical source, deep-linking to the
    Strong's entry when possible."""
    if not strongs_id:
        return source_link(source_name)

    number = strongs_id.lstrip("GHgh")
    lang_char = strongs_id[0].upper() if strongs_id else ""

    # Blue Letter Bible has direct Strong's entry pages
    if source_name == "Thayer's" and lang_char == "G":
        return f"[{source_name}](https://www.blueletterbible.org/lexicon/g{number}/kjv/tr/0-1/)"
    if source_name == "BDB" and lang_char == "H":
        return f"[{source_name}](https://www.blueletterbible.org/lexicon/h{number}/kjv/wlc/0-1/)"

    # BibleHub has per-Strong's pages that show BDAG-like glosses
    if source_name == "BDAG" and lang_char == "G":
        return f"[{source_name}](https://biblehub.com/greek/{number}.htm)"

    return source_link(source_name)


# ---------------------------------------------------------------------------
# Bulk linkification of free text
# ---------------------------------------------------------------------------

def linkify_refs(text: str, translation: str = _DEFAULT_TRANSLATION) -> str:
    """Replace plain Scripture references in text with markdown links.

    Skips references that are already inside markdown link syntax.
    """
    # We do a two-pass approach:
    # 1. Find all references
    # 2. Replace from right to left to preserve offsets

    replacements: list[tuple[int, int, str]] = []

    for m in _VERSE_REF_RE.finditer(text):
        full = m.group(0)
        # Skip if already inside a markdown link [...](...)
        before = text[:m.start()]
        if before.endswith("[") or ("](" in text[m.end():m.end() + 5]):
            continue
        link = bible_link(full, translation)
        replacements.append((m.start(), m.end(), link))

    # Apply right-to-left
    for start, end, link in reversed(replacements):
        text = text[:start] + link + text[end:]

    return text


def linkify_strongs(text: str) -> str:
    """Replace plain Strong's numbers in text with markdown links."""
    def _replace(m: re.Match) -> str:
        sid = m.group(0)
        return strongs_link(sid)

    return _STRONGS_RE.sub(_replace, text)


def linkify_all(text: str, translation: str = _DEFAULT_TRANSLATION) -> str:
    """Apply all linkification passes to a block of text."""
    text = linkify_refs(text, translation)
    text = linkify_strongs(text)
    return text
