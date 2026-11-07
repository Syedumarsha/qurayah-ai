
import os
import json
import re

from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ==========================================
# 1. ENVIRONMENT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing from backend/.env"
    )


# ==========================================
# 2. SYSTEM INSTRUCTIONS
# ==========================================

QUERY_SYSTEM_INSTRUCTION = """
You are the query-understanding component of QurAyah AI.

Your task is to understand the user's question and prepare
search terms for finding relevant verses in the Quran.

RULES:

1. Understand the user's intended meaning.
2. Recognise transliterations and alternative spellings.
3. Identify relevant Quran-related terminology.
4. Expand concepts into useful English search phrases.
5. Do not answer the religious question.
6. Do not invent Quranic references.
7. Do not claim that a concept is explicitly mentioned
   in the Quran merely because it is related.
8. Keep search terms concise and relevant.
9. Preserve the user's actual intent.
10. Do not introduce Hadith, Tafsir or external sources.

Return valid JSON only:

{
    "intent": "short description of the user's intent",
    "search_queries": [
        "search phrase one",
        "search phrase two"
    ]
}

Provide between 3 and 8 useful search queries.
"""


ANSWER_SYSTEM_INSTRUCTION = """
You are QurAyah AI, a Quran-focused assistant.

Answer the user's question using ONLY the Quranic evidence
provided in the context.

SOURCE RESTRICTIONS:

1. Use only the supplied Quranic evidence.
2. Do not use Hadith, Tafsir or external religious sources.
3. Do not invent historical details or interpretations.
4. Do not introduce claims unsupported by the supplied verses.

QURANIC ACCURACY:

1. Never invent Quranic verses.
2. Never invent Surah or Ayah references.
3. Never modify the supplied Arabic text.
4. Never modify the supplied English translation.
5. Never present a paraphrase as an exact quotation.

REFERENCE RULES:

1. Select only relevant evidence.
2. Use the exact supplied evidence_index.
3. Never invent an evidence_index.
4. Never duplicate evidence indexes.
5. Explain each selected Ayah separately.
6. Do not cite evidence that does not support your explanation.

EXPLANATION RULES:

1. Answer the actual question.
2. Use clear, understandable English.
3. Explain the context of the selected verses.
4. Distinguish what the verse explicitly states from
   your explanation of its meaning.
5. Do not issue unsupported religious or legal rulings.
6. Do not present yourself as a religious authority.
7. If evidence is insufficient, say so honestly.
8. Do not refuse merely because a question concerns
   a sensitive subject.
9. Discuss sensitive topics objectively and respectfully,
   while remaining within the supplied Quranic evidence.

Return valid JSON only:

{
    "direct_answer": "Your answer",
    "references": [
        {
            "evidence_index": 1,
            "explanation": "Explanation of this Ayah"
        }
    ],
    "key_takeaway": "A concise summary"
}

Do not reproduce Arabic or English quotations in explanations.
Python will add the verified Quranic text and references.

Your response is AI-generated and is not a definitive
or exhaustive interpretation of the Quran.
"""


# ==========================================
# 3. SURAH NAMES
# ==========================================

SURAH_NAMES_ENGLISH = {
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
# 4. GEMINI CLASS
# ==========================================

class GeminiAnswerGenerator:

    def __init__(self):

        print("Initializing QurAyah AI Gemini...")

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        self.model = GEMINI_MODEL

        self.selected_verses = []

        print("Gemini model:", self.model)

    # ======================================
    # 5. JSON RESPONSE PARSER
    # ======================================

    def parse_response(self, response_text):

        if not response_text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        cleaned = response_text.strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned
        )

        result = json.loads(cleaned)

        if not isinstance(result, dict):
            raise ValueError(
                "Gemini response must be a JSON object."
            )

        return result

    # ======================================
    # 6. GEMINI QUERY UNDERSTANDING
    # ======================================

    def understand_query(self, question):

        if not question or not question.strip():
            return []

        prompt = f"""
USER QUESTION:

{question}

Understand the user's intended meaning.

Generate useful Quran-search phrases that could help
a keyword retrieval engine find relevant Quran verses.

Return valid JSON only.
"""

        try:

            print("Gemini is understanding the question...")

            response = self.client.models.generate_content(

                model=self.model,

                contents=prompt,

                config=types.GenerateContentConfig(

                    system_instruction=QUERY_SYSTEM_INSTRUCTION,

                    response_mime_type="application/json",

                    temperature=0.1,

                    max_output_tokens=700
                )
            )

            result = self.parse_response(response.text)

            queries = result.get("search_queries", [])

            if not isinstance(queries, list):
                return []

            cleaned_queries = []

            for query in queries:

                if isinstance(query, str):

                    query = query.strip()

                    if query and len(query) <= 150:
                        cleaned_queries.append(query)

            cleaned_queries = list(
                dict.fromkeys(cleaned_queries)
            )

            print(
                "Gemini generated search queries:",
                len(cleaned_queries)
            )

            return cleaned_queries[:8]

        except Exception as error:

            print(
                "Query understanding failed:",
                str(error)
            )

            # Retrieval can continue using the original question.
            return []

    # ======================================
    # 7. PREPARE QURAN EVIDENCE
    # ======================================

    def prepare_context(self, verses):

        context_parts = []

        for index, verse in enumerate(verses, start=1):

            context_parts.append(
                f"""
QURANIC EVIDENCE INDEX: {index}

Surah number: {verse.get('surah_number')}

Surah name: {verse.get('surah_name')}

Ayah number: {verse.get('ayah_number')}

Original Arabic:
{verse.get('arabic_text', '')}

Exact English translation:
{verse.get('english_translation', '')}

Translation source:
{verse.get('translation_source', 'Not specified')}

Translation version:
{verse.get('translation_version', 'Not specified')}

Translation publisher:
{verse.get('translation_publisher', 'Not specified')}

Arabic source:
{verse.get('arabic_source', 'Not specified')}

The supplied Quranic text is fixed source data.
Do not modify it.
"""
            )

        return "\n".join(context_parts)

    # ======================================
    # 8. VALIDATE GEMINI REFERENCES
    # ======================================

    def validate_references(self, references, verses):

        if not isinstance(references, list):
            return []

        validated = []
        used_indexes = set()

        for item in references:

            if not isinstance(item, dict):
                continue

            try:
                index = int(item.get("evidence_index"))
            except (TypeError, ValueError):
                continue

            if index < 1 or index > len(verses):
                continue

            if index in used_indexes:
                continue

            explanation = item.get("explanation", "")

            if not isinstance(explanation, str):
                explanation = ""

            used_indexes.add(index)

            validated.append({
                "evidence_index": index,
                "explanation": explanation.strip()
            })

        return validated

    # ======================================
    # 9. FORMAT FINAL ANSWER
    # ======================================

    def format_answer(self, result, verses):

        direct_answer = result.get("direct_answer", "")

        if not isinstance(direct_answer, str):
            direct_answer = ""

        references = self.validate_references(
            result.get("references", []),
            verses
        )

        key_takeaway = result.get("key_takeaway", "")

        if not isinstance(key_takeaway, str):
            key_takeaway = ""

        answer_parts = []

        answer_parts.append("### Direct Answer\n")

        answer_parts.append(
            direct_answer.strip()
            or (
                "The retrieved Quranic evidence does not "
                "provide a sufficiently clear answer."
            )
        )

        answer_parts.append(
            "\n\n### Relevant Quranic References\n"
        )

        selected_verses = []

        for item in references:

            verse = verses[item["evidence_index"] - 1]

            selected_verses.append(verse)

            surah_number = int(verse["surah_number"])

            ayah_number = int(verse["ayah_number"])

            surah_name = SURAH_NAMES_ENGLISH.get(
                surah_number,
                verse.get("surah_name", "Unknown")
            )

            explanation = item["explanation"]

            if not explanation:
                explanation = (
                    "No separate explanation was generated "
                    "for this verse."
                )

            answer_parts.append(
                f"**Surah {surah_name} "
                f"({surah_number}:{ayah_number})**\n\n"
                f"{verse.get('arabic_text', '')}\n\n"
                f"{verse.get('english_translation', '')}\n\n"
                f"**Explanation:**\n\n"
                f"{explanation}"
            )

        if not selected_verses:

            answer_parts.append(
                "No sufficiently relevant Ayah was selected "
                "from the retrieved evidence."
            )

        answer_parts.append("\n\n### Key Takeaway\n")

        answer_parts.append(
            key_takeaway.strip()
            or "Reflect on the Quranic evidence supplied above."
        )

        answer_parts.append(
            "\n\n*Arabic Quran text: Tanzil Uthmani. "
            "English translation: QuranEnc, "
            "English Translation - Noor International Center.*"
        )

        # Do not mutate the original retrieval list.
        self.selected_verses = selected_verses

        return "\n".join(answer_parts)

    # ======================================
    # 10. GENERATE ANSWER
    # ======================================

    def generate_answer(self, question, verses):

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        self.selected_verses = []

        if not verses:
            return (
                "I could not find sufficient Quranic evidence "
                "to answer this question."
            )

        context = self.prepare_context(verses)

        prompt = f"""
USER QUESTION:

{question}

RETRIEVED QURANIC EVIDENCE:

{context}

TASK:

Answer the user's question using only the supplied evidence.

Return JSON with:

1. direct_answer
2. references
3. key_takeaway

For references, use only the exact evidence_index values
provided in the evidence.

Explain each selected verse separately.

Do not invent references or quotations.

If the supplied evidence is insufficient, say so.

Return valid JSON only.
"""

        print("Sending Quran evidence to Gemini...")

        response = self.client.models.generate_content(

            model=self.model,

            contents=prompt,

            config=types.GenerateContentConfig(

                system_instruction=ANSWER_SYSTEM_INSTRUCTION,

                response_mime_type="application/json",

                temperature=0.2,

                max_output_tokens=2500
            )
        )

        result = self.parse_response(response.text)

        return self.format_answer(result, verses)
