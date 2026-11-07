
import json
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

from rank_bm25 import BM25Okapi


# --------------------------------
# 1. CONFIGURATION
# --------------------------------

BASE_DIR = Path(__file__).resolve().parent

QURAN_FILE = (
    BASE_DIR / "data" / "processed" / "quran_bilingual.jsonl"
)

RETRIEVAL_LIMIT = 30
FINAL_RESULTS = 8
RRF_K = 60

# Additional score for verses with direct lexical evidence.
EVIDENCE_BOOST = 0.05


# --------------------------------
# 2. STOP WORDS
# --------------------------------

STOP_WORDS = {
    "what", "does", "the", "quran", "say", "about",
    "how", "why", "is", "are", "of", "to", "in",
    "and", "a", "an", "for", "on", "with", "me",
    "we", "it", "do", "can", "i", "my", "according",
    "teach", "tell", "explain"
}


# --------------------------------
# 3. TOPIC QUERY EXPANSION
# --------------------------------

TOPIC_EXPANSIONS = {

    "tawakkul": {

        "aliases": [
            "tawakkul",
            "reliance on allah",
            "reliance upon allah",
            "trust in allah",
            "rely on allah",
            "rely upon allah",
            "put your trust in allah"
        ],

        "queries": [
            "put your trust in Allah",
            "rely upon Allah",
            "rely on Allah",
            "whoever relies upon Allah",
            "وَتَوَكَّلْ عَلَى اللَّهِ",
            "وَمَن يَتَوَكَّلْ عَلَى اللَّهِ",
            "وَعَلَى اللَّهِ فَلْيَتَوَكَّلِ الْمُؤْمِنُونَ",
            "حَسْبُنَا اللَّهُ"
        ],

        "evidence": {
            "arabic": [
                "توكل"
            ],

            "english": [
                "rely upon allah",
                "relies upon allah",
                "rely on allah",
                "relies on allah",
                "relying upon allah",
                "relying on allah",
                "put your trust in allah",
                "place your trust in allah",
                "trust in allah"
            ]
        }
    },

    "jihad": {

        "aliases": [
            "jihad"
        ],

        "queries": [
            "jihad",
            "striving",
            "strive",
            "those who strive",
            "strive in the cause of Allah",
            "strive with their wealth and lives",
            "exert their efforts",
            "جهاد",
            "جاهدوا",
            "يجاهدون",
            "جاهد"
        ]
    }
}


# --------------------------------
# 4. TEXT NORMALIZATION
# --------------------------------

def normalize_text(text):

    text = unicodedata.normalize("NFKC", str(text))

    # Remove Arabic diacritics.
    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text
    )

    # Remove Arabic elongation character.
    text = text.replace("\u0640", "")

    # Normalize common Arabic letter variants.
    text = re.sub(r"[أإآٱ]", "ا", text)

    text = text.replace("ى", "ي")

    return text.casefold()


# --------------------------------
# 5. TOKENIZATION
# --------------------------------

def tokenize(text):

    text = normalize_text(text)

    tokens = re.findall(
        r"[^\W_]+",
        text,
        flags=re.UNICODE
    )

    return [
        token
        for token in tokens
        if token not in STOP_WORDS
    ]


# --------------------------------
# 6. TOPIC DETECTION
# --------------------------------

def detect_topic(question):

    normalized_question = normalize_text(question)

    for topic, configuration in TOPIC_EXPANSIONS.items():

        aliases = configuration["aliases"]

        topic_found = any(
            normalize_text(alias) in normalized_question
            for alias in aliases
        )

        if topic_found:
            return topic

    return None


# --------------------------------
# 7. QUERY EXPANSION
# --------------------------------

def expand_query(question):

    variants = [question]

    topic = detect_topic(question)

    if topic:

        print(
            f"Query expansion activated for: {topic}"
        )

        variants.extend(
            TOPIC_EXPANSIONS[topic]["queries"]
        )

    # Remove duplicates while preserving order.
    return list(dict.fromkeys(variants))


# --------------------------------
# 8. DIRECT EVIDENCE MATCHING
# --------------------------------

def find_evidence_matches(record, topic):

    if not topic:
        return []

    configuration = TOPIC_EXPANSIONS.get(topic, {})

    evidence = configuration.get("evidence", {})

    arabic_text = normalize_text(
        record.get("arabic_text", "")
    )

    english_text = normalize_text(
        record.get("english_translation", "")
    )

    evidence_types = []

    # Arabic lexical evidence.
    for phrase in evidence.get("arabic", []):

        normalized_phrase = normalize_text(phrase)

        if normalized_phrase in arabic_text:

            evidence_types.append(
                "arabic_lexical_match"
            )

            break

    # English translation evidence.
    for phrase in evidence.get("english", []):

        normalized_phrase = normalize_text(phrase)

        pattern = (
            r"(?<!\w)"
            + re.escape(normalized_phrase)
            + r"(?!\w)"
        )

        if re.search(pattern, english_text):

            evidence_types.append(
                "english_phrase_match"
            )

            break

    return evidence_types


# --------------------------------
# 9. QURAN RETRIEVER
# --------------------------------

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

                    self.records.append(
                        json.loads(line)
                    )

        if not self.records:

            raise ValueError(
                "Quran dataset is empty."
            )

        print(
            f"Loaded {len(self.records)} Quran verses."
        )

        # Map each verse to its Surah and Ayah ID.
        self.record_by_id = {

            f"{record['surah_number']}:{record['ayah_number']}":
            record

            for record in self.records
        }

        # Build BM25 keyword index.
        print("Building BM25 keyword index...")

        corpus = [

            tokenize(
                record["english_translation"]
                + " "
                + record["arabic_text"]
            )

            for record in self.records
        ]

        self.bm25 = BM25Okapi(corpus)

        print("BM25 index ready!")

        print("QurAyah AI retriever is ready!")


    # --------------------------------
    # 10. KEYWORD SEARCH
    # --------------------------------

    def keyword_search(self, query):

        query_tokens = tokenize(query)

        if not query_tokens:
            return {}

        scores = self.bm25.get_scores(
            query_tokens
        )

        ranked_indices = sorted(

            range(len(scores)),

            key=lambda index: scores[index],

            reverse=True
        )

        keyword_ranks = {}

        for index in ranked_indices:

            if scores[index] <= 0:
                continue

            record = self.records[index]

            verse_id = (
                f"{record['surah_number']}:"
                f"{record['ayah_number']}"
            )

            keyword_ranks[verse_id] = (
                len(keyword_ranks) + 1
            )

            if len(keyword_ranks) >= RETRIEVAL_LIMIT:
                break

        return keyword_ranks


    # --------------------------------
    # 11. BM25-BASED RETRIEVAL
    # --------------------------------

    def retrieve(self, question):

        if not question.strip():

            raise ValueError(
                "Question cannot be empty."
            )

        query_variants = expand_query(question)

        detected_topic = detect_topic(question)

        print(
            "Detected topic:",
            detected_topic or "General Quran question"
        )

        print(
            "Number of search queries:",
            len(query_variants)
        )

        retrieval_scores = defaultdict(float)

        best_keyword_ranks = {}

        matched_queries = defaultdict(list)

        evidence_matches = {}

        # --------------------------------
        # Search all query variants.
        # --------------------------------

        for query_index, query in enumerate(query_variants):

            print(
                f"Searching query {query_index + 1}: {query}"
            )

            # Give the original question higher weight.
            weight = (
                2.0 if query_index == 0 else 1.0
            )

            keyword_ranks = self.keyword_search(query)

            # Combine rankings using Reciprocal Rank Fusion.
            for verse_id, rank in keyword_ranks.items():

                retrieval_scores[verse_id] += (
                    weight / (RRF_K + rank)
                )

                if (
                    verse_id not in best_keyword_ranks
                    or rank < best_keyword_ranks[verse_id]
                ):

                    best_keyword_ranks[verse_id] = rank

                if query not in matched_queries[verse_id]:

                    matched_queries[verse_id].append(query)


        # --------------------------------
        # 12. EVIDENCE-AWARE RANKING
        # --------------------------------

        if detected_topic:

            print(
                f"Checking direct evidence for: {detected_topic}"
            )

            for record in self.records:

                verse_id = (
                    f"{record['surah_number']}:"
                    f"{record['ayah_number']}"
                )

                matches = find_evidence_matches(
                    record,
                    detected_topic
                )

                if matches:

                    evidence_matches[verse_id] = matches

                    # Include direct evidence matches even if
                    # BM25 did not retrieve them initially.
                    retrieval_scores[verse_id] += EVIDENCE_BOOST

            print(
                "Verses with direct lexical evidence:",
                len(evidence_matches)
            )


        # --------------------------------
        # 13. FINAL RANKING
        # --------------------------------

        ranked_verses = sorted(

            retrieval_scores.items(),

            key=lambda item: item[1],

            reverse=True

        )[:FINAL_RESULTS]

        final_results = []

        for verse_id, score in ranked_verses:

            record = self.record_by_id[verse_id]

            final_results.append({

                "surah_number": record["surah_number"],

                "surah_name": record["surah_name"],

                "ayah_number": record["ayah_number"],

                "arabic_text": record["arabic_text"],

                "english_translation": (
                    record["english_translation"]
                ),

                "footnotes": record.get(
                    "footnotes",
                    ""
                ),

                "translation_source": (
                    record["translation_source"]["provider"]
                ),

                "translation_version": (
                    record["translation_source"]["version"]
                ),

                "translation_publisher": (
                    record["translation_source"]["publisher"]
                ),

                "arabic_source": (
                    record["arabic_source"]["provider"]
                ),

                # Semantic search is disabled in this version.
                "semantic_rank": None,

                "keyword_rank": (
                    best_keyword_ranks.get(verse_id)
                ),

                "semantic_distance": None,

                "rrf_score": round(score, 6),

                "matched_queries": (
                    matched_queries[verse_id]
                ),

                "exact_evidence_match": (
                    verse_id in evidence_matches
                ),

                "evidence_match_types": (
                    evidence_matches.get(verse_id, [])
                )

            })

        print(
            "BM25 retrieval completed.",
            "Final verses:",
            len(final_results)
        )

        return final_results
