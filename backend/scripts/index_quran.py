
import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# --------------------------------
# 1. DEFINE PROJECT PATHS
# --------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

QURAN_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "quran_bilingual.jsonl"
)

CHROMA_DIR = BASE_DIR / "data" / "chroma_db"


# --------------------------------
# 2. LOAD EMBEDDING MODEL
# --------------------------------

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded successfully!")


# --------------------------------
# 3. CONNECT TO CHROMADB
# --------------------------------

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_or_create_collection(
    name="quran_verses",
    metadata={"description": "Hikmah AI Quran collection"}
)

print("Connected to ChromaDB!")


# --------------------------------
# 4. READ QURAN JSONL
# --------------------------------

if not QURAN_FILE.exists():
    raise FileNotFoundError(
        f"Quran dataset not found: {QURAN_FILE}"
    )

records = []

with open(QURAN_FILE, "r", encoding="utf-8") as file:
    for line in file:
        if line.strip():
            records.append(json.loads(line))

print(f"Total Quran records loaded: {len(records)}")


# --------------------------------
# 5. PREPARE DOCUMENTS AND METADATA
# --------------------------------

documents = []
metadatas = []
ids = []

for record in records:

    arabic_text = record["arabic_text"]
    english_text = record["english_translation"]

    document = (
        f"English translation: {english_text}\n"
        f"Arabic Quran: {arabic_text}"
    )

    document_id = (
        f"{record['surah_number']}:"
        f"{record['ayah_number']}"
    )

    documents.append(document)
    ids.append(document_id)

    metadatas.append({
        "surah_number": record["surah_number"],
        "surah_name": record["surah_name"],
        "ayah_number": record["ayah_number"],

        "arabic_text": arabic_text,
        "english_translation": english_text,

        # Preserve Quran translation footnotes
        "footnotes": record.get("footnotes", ""),

        # English translation attribution
        "translation_source": (
            record["translation_source"]["provider"]
        ),
        "translation_version": (
            record["translation_source"]["version"]
        ),
        "translation_publisher": (
            record["translation_source"]["publisher"]
        ),

        # Arabic Quran attribution
        "arabic_source": (
            record["arabic_source"]["provider"]
        )
    })


# --------------------------------
# 6. GENERATE EMBEDDINGS
# --------------------------------

print("\nGenerating Quran embeddings...")

embeddings = model.encode(
    documents,
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True
)

print("Embeddings generated successfully!")


# --------------------------------
# 7. STORE DATA IN CHROMADB
# --------------------------------

print("\nStoring Quran records in ChromaDB...")

batch_size = 100

for start in range(0, len(documents), batch_size):

    end = start + batch_size

    collection.upsert(
        ids=ids[start:end],
        documents=documents[start:end],
        metadatas=metadatas[start:end],
        embeddings=embeddings[start:end].tolist()
    )

    print(
        f"Stored {min(end, len(documents))} "
        f"/ {len(documents)} records"
    )


# --------------------------------
# 8. VERIFY INDEXING
# --------------------------------

print("\nINDEXING COMPLETED")
print("------------------")

print("Total indexed Quran verses:", collection.count())

print("ChromaDB location:", CHROMA_DIR)

print("\nQuran Arabic, English translations,")
print("footnotes and source metadata are indexed.")

print("\nHikmah AI indexing completed successfully!")
