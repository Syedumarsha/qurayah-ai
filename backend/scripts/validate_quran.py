
import xml.etree.ElementTree as ET
from pathlib import Path

# Locate the Quran XML file
BASE_DIR = Path(__file__).resolve().parent.parent

QURAN_FILE = (
    BASE_DIR / "data" / "raw" / "quran" / "quran-uthmani.xml"
)

# Check whether the file exists
if not QURAN_FILE.exists():
    print("Error: Quran XML file not found!")
    raise SystemExit(1)

# Read and parse the XML file
try:
    tree = ET.parse(QURAN_FILE)
    root = tree.getroot()

    # Extract Surahs
    surahs = root.findall("sura")

    total_verses = 0

    for surah in surahs:
        verses = surah.findall("aya")
        total_verses += len(verses)

    print("Quran XML validation successful!")
    print("--------------------------------")
    print(f"Total Surahs: {len(surahs)}")
    print(f"Total Ayahs: {total_verses}")

    # Display the first Surah and Ayah
    if surahs and surahs[0].findall("aya"):
        first_ayah = surahs[0].findall("aya")[0]

        print("\nFirst Surah:", surahs[0].get("name"))
        print("First Ayah:", first_ayah.get("text"))

except ET.ParseError as error:
    print("Invalid XML file:", error)

except Exception as error:
    print("Unexpected error:", error)
