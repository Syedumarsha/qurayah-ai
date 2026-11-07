
import os
import json
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ==========================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing from the .env file."
    )


# ==========================================
# 2. ENGLISH SURAH NAMES
# ==========================================

SURAH_NAMES_ENGLISH = {
    1: "Al-Fatiha",
    2: "Al-Baqarah",
    3: "Ali 'Imran",
    4: "An-Nisa",
    5: "Al-Ma'idah",
    6: "Al-An'am",
    7: "Al-A'raf",
    8: "Al-Anfal",
    9: "At-Tawbah",
    10: "Yunus",
    11: "Hud",
    12: "Yusuf",
    13: "Ar-Ra'd",
    14: "Ibrahim",
    15: "Al-Hijr",
    16: "An-Nahl",
    17: "Al-Isra",
    18: "Al-Kahf",
    19: "Maryam",
    20: "Ta-Ha",
    21: "Al-Anbiya",
    22: "Al-Hajj",
    23: "Al-Mu'minun",
    24: "An-Nur",
    25: "Al-Furqan",
    26: "Ash-Shu'ara",
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
    56: "Al-Waqi'ah",
    57: "Al-Hadid",
    58: "Al-Mujadilah",
    59: "Al-Hashr",
    60: "Al-Mumtahanah",
    61: "As-Saff",
    62: "Al-Jumu'ah",
    63: "Al-Munafiqun",
    64: "At-Taghabun",
    65: "At-Talaq",
    66: "At-Tahrim",
    67: "Al-Mulk",
    68: "Al-Qalam",
    69: "Al-Haqqah",
    70: "Al-Ma'arij",
    71: "Nuh",
    72: "Al-Jinn",
    73: "Al-Muzzammil",
    74: "Al-Muddaththir",
    75: "Al-Qiyamah",
    76: "Al-Insan",
    77: "Al-Mursalat",
    78: "An-Naba",
    79: "An-Nazi'at",
    80: "Abasa",
    81: "At-Takwir",
    82: "Al-Infitar",
    83: "Al-Mutaffifin",
    84: "Al-Inshiqaq",
    85: "Al-Buruj",
    86: "At-Tariq",
    87: "Al-A'la",
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
    101: "Al-Qari'ah",
    102: "At-Takathur",
    103: "Al-Asr",
    104: "Al-Humazah",
    105: "Al-Fil",
    106: "Quraysh",
    107: "Al-Ma'un",
    108: "Al-Kawthar",
    109: "Al-Kafirun",
    110: "An-Nasr",
    111: "Al-Masad",
    112: "Al-Ikhlas",
    113: "Al-Falaq",
    114: "An-Nas"
}


# ==========================================
# 3. GEMINI SYSTEM INSTRUCTION
# ==========================================

SYSTEM_INSTRUCTION = """
You are Hikmah AI, a Quran-focused assistant.

Answer the user's question using ONLY the
Quranic evidence supplied in the context.

STRICT RULES:

1. SOURCE RESTRICTION

- Use only the supplied Quranic evidence.
- Do not introduce outside religious information.
- Do not invent historical details or interpretations.

2. QURANIC ACCURACY

- Never invent Quranic verses.
- Never invent Surah or Ayah references.
- Never modify Quranic Arabic or English translations.
- Never present a paraphrase as an exact quotation.

3. REFERENCE SELECTION

- Select only Ayahs relevant to the question.
- Each selected Ayah must use its supplied evidence_index.
- Never invent an evidence_index.
- Do not duplicate evidence indexes.
- Explain each selected Ayah separately.

4. EXPLANATIONS

- Keep explanations connected to the supplied verse.
- Avoid unsupported theological conclusions.
- Do not issue religious or legal rulings.
- Do not present yourself as a religious authority.
- Acknowledge insufficient evidence when necessary.

5. RESPONSE FORMAT

Return valid JSON only.

Required structure:

{
    "direct_answer": "Your concise answer.",
    "references": [
        {
            "evidence_index": 1,
            "explanation": "Explanation of this Ayah."
        }
    ],
    "key_takeaway": "A concise summary."
}

The evidence_index must exactly match one of the
numbered Quranic evidence entries.

Do not include Arabic or English Quranic quotations
in your explanations.

Do not include Surah names or references in your
explanations. Python will add the verified references.

Your response is AI-generated, not a definitive
or exhaustive interpretation of the Quran.
"""


# ==========================================
# 4. GEMINI ANSWER GENERATOR
# ==========================================

class GeminiAnswerGenerator:

    def __init__(self):

        print("Initializing Gemini Answer Generator...")

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        self.model = GEMINI_MODEL

        self.selected_verses = []

        print(
            "Gemini model initialized:",
            self.model
        )

    # ======================================
    # 5. PREPARE QURAN CONTEXT
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

IMPORTANT:
The supplied Quranic text and metadata are fixed source data.
Do not modify them.
"""
            )

        return "\n".join(context_parts)

    # ======================================
    # 6. PARSE GEMINI RESPONSE
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

        try:

            result = json.loads(cleaned)

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Gemini returned invalid JSON: {error}"
            )

        if not isinstance(result, dict):
            raise ValueError(
                "Gemini response must be a JSON object."
            )

        return result

    # ======================================
    # 7. FORMAT FINAL ANSWER
    # ======================================

    def format_answer(self, result, verses):

        direct_answer = result.get(
            "direct_answer", ""
        )

        references = result.get(
            "references", []
        )

        key_takeaway = result.get(
            "key_takeaway", ""
        )

        if not isinstance(direct_answer, str):
            direct_answer = ""

        if not isinstance(references, list):
            references = []

        if not isinstance(key_takeaway, str):
            key_takeaway = ""

        answer_parts = []

        # Direct answer
        answer_parts.append("### Direct Answer\n")

        answer_parts.append(
            direct_answer.strip()
            if direct_answer.strip()
            else "The retrieved Quranic evidence does not "
                 "provide a sufficiently clear answer."
        )

        # Quranic references
        answer_parts.append(
            "\n\n### Relevant Quranic References\n"
        )

        selected_verses = []
        used_indexes = set()

        for item in references:

            if not isinstance(item, dict):
                continue

            try:
                evidence_index = int(
                    item.get("evidence_index")
                )
            except (TypeError, ValueError):
                continue

            if evidence_index < 1 or evidence_index > len(verses):
                continue

            if evidence_index in used_indexes:
                continue

            used_indexes.add(evidence_index)

            verse = verses[evidence_index - 1]

            explanation = item.get(
                "explanation", ""
            )

            if not isinstance(explanation, str):
                explanation = ""

            explanation = explanation.strip()

            if not explanation:
                explanation = (
                    "The supplied verse is relevant to "
                    "the question, but no explanation "
                    "was generated."
                )

            selected_verses.append(verse)

            surah_number = int(
                verse["surah_number"]
            )

            ayah_number = int(
                verse["ayah_number"]
            )

            surah_name = SURAH_NAMES_ENGLISH.get(
                surah_number,
                verse.get("surah_name", "Unknown")
            )

            arabic_text = verse.get(
                "arabic_text", ""
            )

            english_translation = verse.get(
                "english_translation", ""
            )

            # Exact requested format.
            answer_parts.append(
                f"**Surah {surah_name} "
                f"({surah_number}:{ayah_number})**\n\n"
                f"{arabic_text}\n\n"
                f"{english_translation}\n\n"
                f"**Explanation:**\n\n"
                f"{explanation}"
            )

        if not selected_verses:

            answer_parts.append(
                "No sufficiently relevant Ayah was selected "
                "from the retrieved Quranic evidence."
            )

        # Key takeaway
        answer_parts.append(
            "\n\n### Key Takeaway\n"
        )

        answer_parts.append(
            key_takeaway.strip()
            if key_takeaway.strip()
            else "Reflect on the Quranic evidence supplied above."
        )

        # Source attribution
        answer_parts.append(
            "\n\n*Arabic Quran text: Tanzil Uthmani. "
            "English translation: QuranEnc, "
            "English Translation - Noor International Center.*"
        )

        # Keep only the Ayahs selected by Gemini.
        # This also synchronizes the frontend reference list
        # when main.py returns the same verses list.
        verses[:] = selected_verses

        self.selected_verses = selected_verses

        return "\n".join(answer_parts)

    # ======================================
    # 8. GENERATE ANSWER
    # ======================================

    def generate_answer(self, question, verses):

        if not question or not question.strip():

            raise ValueError(
                "Question cannot be empty."
            )

        self.selected_verses = []

        if not verses:

            return (
                "I could not find sufficient Quranic evidence "
                "to answer this question. Please try asking "
                "in a different way."
            )

        print("Preparing Quranic evidence...")

        context = self.prepare_context(verses)

        prompt = f"""
USER QUESTION:

{question}


RETRIEVED QURANIC EVIDENCE:

{context}


YOUR TASK:

Answer the user's question using only the
supplied Quranic evidence.

Return valid JSON with these fields:

1. direct_answer:
   Give a clear and concise answer.

2. references:
   Select relevant Ayahs.
   For each selected Ayah, provide:
   - evidence_index
   - explanation

3. key_takeaway:
   Give a short summary.

IMPORTANT:

- Use only supplied evidence.
- Select only relevant verses.
- Use the exact evidence_index.
- Do not invent references.
- Do not duplicate references.
- Explain each selected Ayah separately.
- Do not reproduce Arabic or English quotations.
- Do not include Surah names in explanations.
- Do not give unsupported religious conclusions.
- Acknowledge insufficient evidence.

Return valid JSON only.
"""

        print("Sending request to Gemini...")

        response = self.client.models.generate_content(

            model=self.model,

            contents=prompt,

            config=types.GenerateContentConfig(

                system_instruction=SYSTEM_INSTRUCTION,

                response_mime_type="application/json",

                temperature=0.2,

                max_output_tokens=2500
            )
        )

        print("Processing Gemini response...")

        result = self.parse_response(
            response.text
        )

        answer = self.format_answer(
            result,
            verses
        )

        print(
            "Selected Quranic references:",
            len(self.selected_verses)
        )

        print("Gemini answer generated successfully.")

        return answer
