
import json
import re
import unicodedata

from pathlib import Path
from collections import defaultdict
from difflib import get_close_matches

from rank_bm25 import BM25Okapi


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

QURAN_FILE = (
    BASE_DIR / "data" / "processed" / "quran_bilingual.jsonl"
)

RETRIEVAL_LIMIT = 40
FINAL_RESULTS = 12
RRF_K = 60


# ==========================================
# 2. ALL 114 SURAH NAMES
# ==========================================

SURAH_NAMES = {
    1: "Al-Fatiha",
    2: "Al-Baqarah",
    3: "Ali Imran",
    4: "An-Nisa",
    5: "Al-Maidah",
    6: "Al-Anam",
    7: "Al-Araf",
    8: "Al-Anfal",
    9: "At-Tawbah",
    10: "Yunus",
    11: "Hud",
    12: "Yusuf",
    13: "Ar-Rad",
    14: "Ibrahim",
    15: "Al-Hijr",
    16: "An-Nahl",
    17: "Al-Isra",
    18: "Al-Kahf",
    19: "Maryam",
    20: "Ta-Ha",
    21: "Al-Anbiya",
    22: "Al-Hajj",
    23: "Al-Muminun",
    24: "An-Nur",
    25: "Al-Furqan",
    26: "Ash-Shuara",
    27: "An-Naml",
    28: "Al-Qasas",
    29: "Al-Ankabut",
    30: "Ar-Rum",
    31: "Luqman",
    32: "As-Sajdah",
    33: "Al-Ahzab",
    34: "Saba",
    35: "Fatir",
    36: "Ya-Sin",
    37: "As-Saffat",
    38: "Sad",
    39: "Az-Zumar",
    40: "Ghafir",
    41: "Fussilat",
    42: "Ash-Shura",
    43: "Az-Zukhruf",
    44: "Ad-Dukhan",
    45: "Al-Jathiyah",
    46: "Al-Ahqaf",
    47: "Muhammad",
    48: "Al-Fath",
    49: "Al-Hujurat",
    50: "Qaf",
    51: "Adh-Dhariyat",
    52: "At-Tur",
    53: "An-Najm",
    54: "Al-Qamar",
    55: "Ar-Rahman",
    56: "Al-Waqiah",
    57: "Al-Hadid",
    58: "Al-Mujadilah",
    59: "Al-Hashr",
    60: "Al-Mumtahanah",
    61: "As-Saff",
    62: "Al-Jumuah",
    63: "Al-Munafiqun",
    64: "At-Taghabun",
    65: "At-Talaq",
    66: "At-Tahrim",
    67: "Al-Mulk",
    68: "Al-Qalam",
    69: "Al-Haqqah",
    70: "Al-Maarij",
    71: "Nuh",
    72: "Al-Jinn",
    73: "Al-Muzzammil",
    74: "Al-Muddaththir",
    75: "Al-Qiyamah",
    76: "Al-Insan",
    77: "Al-Mursalat",
    78: "An-Naba",
    79: "An-Naziat",
    80: "Abasa",
    81: "At-Takwir",
    82: "Al-Infitar",
    83: "Al-Mutaffifin",
    84: "Al-Inshiqaq",
    85: "Al-Buruj",
    86: "At-Tariq",
    87: "Al-Ala",
    88: "Al-Ghashiyah",
    89: "Al-Fajr",
    90: "Al-Balad",
    91: "Ash-Shams",
    92: "Al-Layl",
    93: "Ad-Duha",
    94: "Ash-Sharh",
    95: "At-Tin",
    96: "Al-Alaq",
    97: "Al-Qadr",
    98: "Al-Bayyinah",
    99: "Az-Zalzalah",
    100: "Al-Adiyat",
    101: "Al-Qariah",
    102: "At-Takathur",
    103: "Al-Asr",
    104: "Al-Humazah",
    105: "Al-Fil",
    106: "Quraysh",
    107: "Al-Maun",
    108: "Al-Kawthar",
    109: "Al-Kafirun",
    110: "An-Nasr",
    111: "Al-Masad",
    112: "Al-Ikhlas",
    113: "Al-Falaq",
    114: "An-Nas"
}


# ==========================================
# 3. SURAH ALIASES
# ==========================================

SURAH_ALIASES = {
    1: ["fatiha", "fatihah", "fat'ha"],
    2: ["baqarah", "baqara", "baqrah"],
    3: ["imran", "ali imran", "aal imran"],
    4: ["nisa", "nisaa", "nisaah"],
    5: ["maidah", "maida", "ma'idah"],
    6: ["anam", "an'aam"],
    7: ["araf", "a'raf"],
    8: ["anfal"],
    9: ["tawbah", "taubah", "tawba", "bara'ah"],
    10: ["younus", "yunus"],
    11: ["hood"],
    12: ["yousuf", "yusuf"],
    13: ["raad", "rad", "ra'd"],
    14: ["ibraheem", "ibrahim"],
    15: ["hijr"],
    16: ["nahl"],
    17: ["isra", "bani israel"],
    18: ["kahf", "kahaf", "kahfi"],
    19: ["mariam", "maryam"],
    20: ["taha", "ta ha"],
    21: ["anbiya", "anbiyaa"],
    22: ["hajj"],
    23: ["muminun", "muminoon", "momenoon"],
    24: ["nur", "noor"],
    25: ["furqan", "furqaan"],
    26: ["shuara", "shu'ara"],
    27: ["naml"],
    28: ["qasas", "qasas"],
    29: ["ankabut", "ankaboot"],
    30: ["rum", "room"],
    31: ["luqman", "lukman"],
    32: ["sajdah", "sajda"],
    33: ["ahzab", "ahzaab"],
    34: ["saba"],
    35: ["fatir", "faatir"],
    36: ["yaseen", "yasin", "ya sin", "ya seen", "yaaseen"],
    37: ["saffat", "saffaat"],
    38: ["saad"],
    39: ["zumar"],
    40: ["ghafir", "mumin", "mu'min"],
    41: ["fussilat", "ha mim sajdah"],
    42: ["shura", "shoora"],
    43: ["zukhruf"],
    44: ["dukhan", "dukhaan"],
    45: ["jathiyah"],
    46: ["ahqaf"],
    47: ["muhammad"],
    48: ["fath", "fat'h"],
    49: ["hujurat"],
    50: ["qaaf"],
    51: ["dhariyat", "dhariyat"],
    52: ["toor", "thur"],
    53: ["najm"],
    54: ["qamar"],
    55: ["rahman", "rehman"],
    56: ["waqiah", "waqia", "waqiya"],
    57: ["hadid"],
    58: ["mujadilah", "mujadila"],
    59: ["hashr"],
    60: ["mumtahanah"],
    61: ["saff"],
    62: ["jumuah", "jumah", "juma"],
    63: ["munafiqun"],
    64: ["taghabun"],
    65: ["talaq"],
    66: ["tahrim"],
    67: ["mulk"],
    68: ["qalam"],
    69: ["haqqah"],
    70: ["maarij", "ma'arij"],
    71: ["nooh", "nuh"],
    72: ["jinn", "jin"],
    73: ["muzzammil", "muzammil"],
    74: ["muddaththir", "mudathir"],
    75: ["qiyamah", "qiyama", "qiyamat"],
    76: ["insan", "dahr"],
    77: ["mursalat"],
    78: ["naba"],
    79: ["naziat", "nazi'at"],
    80: ["abasa"],
    81: ["takwir"],
    82: ["infitar"],
    83: ["mutaffifin"],
    84: ["inshiqaq"],
    85: ["buruj"],
    86: ["tariq", "taariq"],
    87: ["ala"],
    88: ["ghashiyah"],
    89: ["fajr"],
    90: ["balad"],
    91: ["shams"],
    92: ["layl"],
    93: ["duha", "dhuha"],
    94: ["sharh", "inshirah"],
    95: ["tin", "teen"],
    96: ["alaq"],
    97: ["qadr"],
    98: ["bayyinah"],
    99: ["zalzalah"],
    100: ["adiyat"],
    101: ["qariah", "qaria"],
    102: ["takathur"],
    103: ["asr"],
    104: ["humazah"],
    105: ["fil"],
    106: ["quraish", "quraysh"],
    107: ["maun", "maooun"],
    108: ["kawthar", "kauthar"],
    109: ["kafirun", "kafiroon"],
    110: ["nasr"],
    111: ["masad", "lahab"],
    112: ["ikhlas", "ikhlass"],
    113: ["falaq", "falak"],
    114: ["nas", "naas"]
}


# ==========================================
# 4. CONCEPT EXPANSION
# ==========================================

CONCEPT_EXPANSIONS = {

    "wazu": [
        "wudu",
        "ablution",
        "ritual purification",
        "washing before prayer",
        "wash your faces",
        "wash your hands and arms",
        "wipe your heads",
        "wash your feet",
        "purification before salah",
        "tayammum"
    ],

    "wuzu": [
        "wudu",
        "ablution",
        "ritual purification",
        "washing before prayer",
        "wash your face",
        "wash your arms",
        "wipe your head",
        "wash your feet"
    ],

    "wudu": [
        "ablution",
        "ritual purification",
        "washing before prayer",
        "wash your faces",
        "wash your hands and arms",
        "wipe your heads",
        "wash your feet"
    ],

    "ablution": [
        "wudu",
        "purification",
        "wash your faces",
        "wash your hands and arms",
        "wipe your heads",
        "wash your feet"
    ],

    "pardah": [
        "purdah",
        "hijab",
        "modesty",
        "covering",
        "khimar",
        "jilbab",
        "outer garments",
        "lower their gaze",
        "guard their chastity",
        "adornment",
        "believing women"
    ],

    "purdah": [
        "pardah",
        "hijab",
        "modesty",
        "covering",
        "khimar",
        "jilbab",
        "lower their gaze",
        "guard their chastity",
        "adornment"
    ],

    "hijab": [
        "modesty",
        "veil",
        "covering",
        "khimar",
        "jilbab",
        "lower their gaze",
        "guard their chastity",
        "adornment"
    ],

    "sex": [
        "sexual relations",
        "sexual intercourse",
        "intimacy",
        "spouses",
        "husband and wife",
        "wives",
        "marriage",
        "menstruation",
        "chastity",
        "private parts",
        "adultery",
        "fornication",
        "lawful relations"
    ],

    "sexual relations": [
        "intimacy",
        "spouses",
        "marriage",
        "wives",
        "chastity",
        "menstruation",
        "adultery",
        "fornication"
    ],

    "zina": [
        "adultery",
        "fornication",
        "sexual immorality",
        "do not approach unlawful sexual intercourse"
    ],

    "patience": [
        "patient",
        "persevere",
        "perseverance",
        "steadfast",
        "endure",
        "Allah is with the patient"
    ],

    "forgiveness": [
        "forgive",
        "forgiving",
        "mercy",
        "repentance",
        "Allah is forgiving",
        "pardon"
    ],

    "tawakkul": [
        "trust in Allah",
        "rely upon Allah",
        "put your trust in Allah",
        "Allah is sufficient",
        "reliance upon Allah"
    ],

    "prayer": [
        "salah",
        "salat",
        "establish prayer",
        "bow",
        "prostrate",
        "remembrance of Allah"
    ],

    "anger": [
        "restrain anger",
        "control anger",
        "forgive people",
        "patience",
        "suppress anger"
    ],

    "marriage": [
        "spouses",
        "husband",
        "wife",
        "marry",
        "affection",
        "mercy",
        "chastity"
    ],

    "parents": [
        "mother",
        "father",
        "parents",
        "kindness to parents",
        "honour your parents"
    ],

    "charity": [
        "spend in the way of Allah",
        "give to the poor",
        "alms",
        "zakat",
        "needy",
        "orphans"
    ],

    "death": [
        "every soul shall taste death",
        "resurrection",
        "hereafter",
        "Day of Judgment",
        "return to Allah"
    ],

    "heaven": [
        "paradise",
        "jannah",
        "gardens",
        "believers",
        "reward"
    ],

    "hell": [
        "hellfire",
        "fire",
        "punishment",
        "disbelievers",
        "Day of Judgment"
    ]
}


# ==========================================
# 5. NORMALIZATION
# ==========================================

def normalize_text(text):

    text = unicodedata.normalize("NFKC", str(text))

    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text
    )

    text = text.replace("\u0640", "")

    text = re.sub(
        r"[أإآٱ]",
        "ا",
        text
    )

    text = text.replace("ى", "ي")

    return text.casefold()


def compact_name(text):

    text = normalize_text(text)

    return re.sub(r"[^a-z0-9]", "", text)


# ==========================================
# 6. TOKENIZATION
# ==========================================

STOP_WORDS = {
    "what", "does", "the", "quran", "qur'an",
    "say", "about", "how", "why", "is", "are",
    "of", "to", "in", "and", "a", "an",
    "for", "on", "with", "me", "we", "it",
    "do", "can", "i", "my", "according",
    "teach", "tell", "explain", "please",
    "show", "find", "give", "mean", "means"
}


def tokenize(text):

    text = normalize_text(text)

    tokens = re.findall(
        r"[^\W_]+",
        text,
        flags=re.UNICODE
    )

    return [
        token for token in tokens
        if token not in STOP_WORDS
    ]


# ==========================================
# 7. BUILD SURAH LOOKUP
# ==========================================

SURAH_LOOKUP = {}

for number, name in SURAH_NAMES.items():

    names = [name]

    names.extend(SURAH_ALIASES.get(number, []))

    for item in names:

        SURAH_LOOKUP[compact_name(item)] = number


def resolve_surah_name(name):

    cleaned = re.sub(
        r"^(surah|sura|chapter)\s+",
        "",
        name.strip(),
        flags=re.IGNORECASE
    )

    key = compact_name(cleaned)

    if not key:
        return None

    if key in SURAH_LOOKUP:
        return SURAH_LOOKUP[key]

    if len(key) >= 5:

        matches = get_close_matches(
            key,
            list(SURAH_LOOKUP.keys()),
            n=1,
            cutoff=0.88
        )

        if matches:
            return SURAH_LOOKUP[matches[0]]

    return None


# ==========================================
# 8. EXACT REFERENCE DETECTION
# ==========================================

def detect_reference(question):

    text = question.strip()

    # 36:12 or 36/12
    match = re.search(
        r"(?<!\d)(\d{1,3})\s*[:/]\s*(\d{1,3})(?!\d)",
        text
    )

    if match:

        surah_number = int(match.group(1))
        ayah_number = int(match.group(2))

        if 1 <= surah_number <= 114:
            return surah_number, ayah_number

    # Surah 36 Ayah 12
    match = re.search(
        r"surah\s+(\d{1,3})\s+"
        r"(?:ayah|ayat|verse)\s+(\d+)",
        text,
        re.IGNORECASE
    )

    if match:

        return (
            int(match.group(1)),
            int(match.group(2))
        )

    # Surah Yaseen Ayat 12
    match = re.search(
        r"(?:surah|sura|chapter)\s+(.+?)\s+"
        r"(?:ayah|ayat|verse)\s+(\d+)",
        text,
        re.IGNORECASE
    )

    if match:

        surah_number = resolve_surah_name(
            match.group(1)
        )

        if surah_number:
            return surah_number, int(match.group(2))

    # Yaseen 12
    match = re.fullmatch(
        r"\s*(.+?)\s+(\d+)\s*",
        text,
        re.IGNORECASE
    )

    if match:

        surah_number = resolve_surah_name(
            match.group(1)
        )

        if surah_number:
            return surah_number, int(match.group(2))

    return None


# ==========================================
# 9. COMPLETE SURAH DETECTION
# ==========================================

def detect_surah_only(question):

    text = normalize_text(question).strip()

    prefixes = [
        "tell me about",
        "show me",
        "give me",
        "explain",
        "what is in",
        "what does",
        "read",
        "open",
        "recite",
        "surah",
        "sura",
        "chapter"
    ]

    for prefix in prefixes:

        if text.startswith(prefix + " "):

            text = text[len(prefix):].strip()

            break

    text = re.sub(
        r"^(surah|sura|chapter)\s+",
        "",
        text
    )

    text = re.sub(
        r"[?.!,]+$",
        "",
        text
    ).strip()

    return resolve_surah_name(text)


# ==========================================
# 10. QURAN RETRIEVER
# ==========================================

class QuranRetriever:

    def __init__(self):

        print("Loading Quran dataset...")

        if not QURAN_FILE.exists():

            raise FileNotFoundError(
                f"Quran dataset not found: {QURAN_FILE}"
            )

        self.records = []

        with open(
            QURAN_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                if line.strip():
                    self.records.append(json.loads(line))

        if not self.records:

            raise ValueError("Quran dataset is empty.")

        self.record_by_id = {}

        self.surah_records = defaultdict(list)

        for record in self.records:

            surah_number = int(record["surah_number"])

            ayah_number = int(record["ayah_number"])

            verse_id = f"{surah_number}:{ayah_number}"

            self.record_by_id[verse_id] = record

            self.surah_records[surah_number].append(record)

        # Sort every Surah by Ayah number.
        for number in self.surah_records:

            self.surah_records[number].sort(
                key=lambda item: int(item["ayah_number"])
            )

        print(f"Loaded {len(self.records)} Quran verses.")

        print("Building BM25 index...")

        corpus = []

        for record in self.records:

            surah_number = int(record["surah_number"])

            searchable_text = " ".join([

                record.get("english_translation", ""),

                record.get("arabic_text", ""),

                SURAH_NAMES.get(surah_number, ""),

                str(surah_number),

                str(record.get("surah_name", ""))

            ])

            corpus.append(tokenize(searchable_text))

        self.bm25 = BM25Okapi(corpus)

        print("BM25 index ready!")

    # ======================================
    # 11. FORMAT VERSE
    # ======================================

    def format_record(self, record, score=None):

        translation_source = record.get(
            "translation_source", {}
        )

        arabic_source = record.get(
            "arabic_source", {}
        )

        return {

            "surah_number": int(record["surah_number"]),

            "surah_name": SURAH_NAMES.get(
                int(record["surah_number"]),
                record.get("surah_name", "Unknown")
            ),

            "ayah_number": int(record["ayah_number"]),

            "arabic_text": record["arabic_text"],

            "english_translation": record["english_translation"],

            "footnotes": record.get("footnotes", ""),

            "translation_source": (
                translation_source.get("provider", "Not specified")
                if isinstance(translation_source, dict)
                else str(translation_source)
            ),

            "translation_version": (
                translation_source.get("version", "Not specified")
                if isinstance(translation_source, dict)
                else "Not specified"
            ),

            "translation_publisher": (
                translation_source.get("publisher", "Not specified")
                if isinstance(translation_source, dict)
                else "Not specified"
            ),

            "arabic_source": (
                arabic_source.get("provider", "Not specified")
                if isinstance(arabic_source, dict)
                else str(arabic_source)
            ),

            "retrieval_score": score

        }

    # ======================================
    # 12. EXACT AYAH LOOKUP
    # ======================================

    def get_exact_ayah(self, surah_number, ayah_number):

        if surah_number not in self.surah_records:

            raise ValueError(
                f"Surah {surah_number} was not found."
            )

        for record in self.surah_records[surah_number]:

            if int(record["ayah_number"]) == ayah_number:

                return [
                    self.format_record(record)
                ]

        raise ValueError(
            f"Surah {surah_number} does not contain "
            f"Ayah {ayah_number}."
        )

    # ======================================
    # 13. COMPLETE SURAH LOOKUP
    # ======================================

    def get_complete_surah(self, surah_number):

        if surah_number not in self.surah_records:

            raise ValueError(
                f"Surah {surah_number} was not found."
            )

        return [
            self.format_record(record)
            for record in self.surah_records[surah_number]
        ]

    # ======================================
    # 14. BM25 SEARCH
    # ======================================

    def keyword_search(self, query):

        query_tokens = tokenize(query)

        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True
        )

        results = []

        for index in ranked_indices:

            score = float(scores[index])

            if score <= 0:
                continue

            results.append((index, score))

            if len(results) >= RETRIEVAL_LIMIT:
                break

        return results

    # ======================================
    # 15. CONCEPT EXPANSION
    # ======================================

    def get_concept_queries(self, question):

        normalized = normalize_text(question)

        queries = []

        for concept, terms in CONCEPT_EXPANSIONS.items():

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(concept)
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, normalized):

                queries.extend(terms)

        return list(dict.fromkeys(queries))

    # ======================================
    # 16. RETRIEVAL
    # ======================================

    def retrieve(self, question, expanded_queries=None):

        if not question or not question.strip():

            raise ValueError(
                "Question cannot be empty."
            )

        print("\n========== QURAN RETRIEVAL ==========")

        print("Question:", question)

        # Exact Ayah request.
        reference = detect_reference(question)

        if reference:

            surah_number, ayah_number = reference

            results = self.get_exact_ayah(
                surah_number,
                ayah_number
            )

            for result in results:
                result["retrieval_mode"] = "exact_ayah"

            return results

        # Complete Surah request.
        surah_number = detect_surah_only(question)

        if surah_number:

            results = self.get_complete_surah(surah_number)

            for result in results:
                result["retrieval_mode"] = "complete_surah"

            return results

        # General question.
        queries = [question]

        queries.extend(
            self.get_concept_queries(question)
        )

        if expanded_queries:

            queries.extend(
                query.strip()
                for query in expanded_queries
                if isinstance(query, str) and query.strip()
            )

        queries = list(dict.fromkeys(queries))

        print("Search variants:", len(queries))

        combined_scores = defaultdict(float)

        matched_queries = defaultdict(list)

        best_ranks = {}

        for query in queries:

            results = self.keyword_search(query)

            for rank, (index, score) in enumerate(
                results,
                start=1
            ):

                record = self.records[index]

                verse_id = (
                    f"{record['surah_number']}:"
                    f"{record['ayah_number']}"
                )

                # Original question receives extra weight.
                weight = 2.0 if query == question else 1.0

                combined_scores[verse_id] += (
                    weight / (RRF_K + rank)
                )

                matched_queries[verse_id].append(query)

                if (
                    verse_id not in best_ranks
                    or rank < best_ranks[verse_id]
                ):

                    best_ranks[verse_id] = rank

        ranked = sorted(
            combined_scores.items(),
            key=lambda item: item[1],
            reverse=True
        )[:FINAL_RESULTS]

        final_results = []

        for verse_id, score in ranked:

            record = self.record_by_id[verse_id]

            result = self.format_record(
                record,
                round(score, 6)
            )

            result["keyword_rank"] = best_ranks[verse_id]

            result["matched_queries"] = (
                matched_queries[verse_id]
            )

            result["retrieval_mode"] = "general_question"

            final_results.append(result)

        print(
            "Final verses retrieved:",
            len(final_results)
        )

        print("====================================\n")

        return final_results
