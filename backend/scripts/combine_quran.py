
import json
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

# --------------------------------
# 1. Define file locations
# --------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

QURAN_FILE = BASE_DIR / "data" / "raw" / "quran" / "quran-uthmani.xml"

TRANSLATION_DB = (
    BASE_DIR
    / "data"
    / "raw"
    / "translations"
    / "english_saheeh.sqlite"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "quran_bilingual.jsonl"
)

# --------------------------------
# 2. Check source files
# --------------------------------

if not QURAN_FILE.exists():
    raise FileNotFoundError(f"Quran file not found: {QURAN_FILE}")

if not TRANSLATION_DB.exists():
    raise FileNotFoundError(
        f"Translation database not found: {TRANSLATION_DB}"
    )

# --------------------------------
# 3. Read Arabic Quran XML
# --------------------------------

print("Reading Arabic Quran...")

tree = ET.parse(QURAN_FILE)
root = tree.getroot()

arabic_verses = {}

for surah in root.findall("sura"):
    surah_number = int(surah.get("index"))
    surah_name = surah.get("name")

    for ayah in surah.findall("aya"):
        ayah_number = int(ayah.get("index"))
        arabic_text = ayah.get("text")

        key = (surah_number, ayah_number)

        if not arabic_text or key in arabic_verses:
            raise ValueError(f"Invalid or duplicate Arabic Ayah: {key}")

        arabic_verses[key] = {
            "surah_name": surah_name,
            "arabic_text": arabic_text
        }

print(f"Arabic Ayahs loaded: {len(arabic_verses)}")

# --------------------------------
# 4. Read English translation
# --------------------------------

print("\nReading English translation...")

connection = sqlite3.connect(
    TRANSLATION_DB.as_uri() + "?mode=ro",
    uri=True
)

cursor = connection.cursor()

cursor.execute("""
    SELECT id, sura, aya, translation, footnotes
    FROM translations
    ORDER BY sura, aya
""")

translation_rows = cursor.fetchall()
connection.close()

english_verses = {}

for row in translation_rows:
    record_id, surah, ayah, translation, footnotes = row

    key = (surah, ayah)

    if key in english_verses:
        raise ValueError(f"Duplicate English Ayah: {key}")

    english_verses[key] = {
        "translation_id": record_id,
        "translation": translation,
        "footnotes": footnotes or ""
    }

print(f"English Ayahs loaded: {len(english_verses)}")

# --------------------------------
# 5. Verify both datasets
# --------------------------------

arabic_keys = set(arabic_verses.keys())
english_keys = set(english_verses.keys())

missing_english = arabic_keys - english_keys
missing_arabic = english_keys - arabic_keys

if missing_english or missing_arabic:
    raise ValueError(
        f"Mismatch detected!\n"
        f"Missing English Ayahs: {len(missing_english)}\n"
        f"Missing Arabic Ayahs: {len(missing_arabic)}"
    )

if len(arabic_verses) != 6236:
    raise ValueError("Unexpected Arabic Quran Ayah count.")

if len(english_verses) != 6236:
    raise ValueError("Unexpected English translation Ayah count.")

print("\nBoth datasets match successfully!")

# --------------------------------
# 6. Combine Arabic and English
# --------------------------------

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open("w", encoding="utf-8") as file:

    for key in sorted(arabic_keys):

        arabic = arabic_verses[key]
        english = english_verses[key]

        record = {
            "surah_number": key[0],
            "surah_name": arabic["surah_name"],
            "ayah_number": key[1],
            "arabic_text": arabic["arabic_text"],
            "english_translation": english["translation"],
            "footnotes": english["footnotes"],
            "translation_source": {
                "provider": "QuranEnc",
                "translation_key": "english_saheeh",
                "version": "1.1.2",
                "publisher": "Noor International Center"
            },
            "arabic_source": {
                "provider": "Tanzil",
                "text_type": "Uthmani"
            }
        }

        file.write(
            json.dumps(record, ensure_ascii=False) + "\n"
        )

# --------------------------------
# 7. Display final result
# --------------------------------

print("\nBilingual Quran dataset created!")
print("--------------------------------")
print(f"Total combined Ayahs: {len(arabic_keys)}")
print(f"Output file: {OUTPUT_FILE}")

print("\nFirst Ayah preview:")

first_key = (1, 1)

print("Arabic:", arabic_verses[first_key]["arabic_text"])
print("English:", english_verses[first_key]["translation"])
