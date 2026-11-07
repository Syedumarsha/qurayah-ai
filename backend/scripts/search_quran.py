
import json
import re
from pathlib import Path
from collections import defaultdict

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


# --------------------------------
# 1. CONFIGURATION
# --------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

QURAN_FILE = BASE_DIR / "data" / "processed" / "quran_bilingual.jsonl"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

RETRIEVAL_LIMIT = 20
FINAL_RESULTS = 5
RRF_K = 60


# --------------------------------
# 2. TEXT TOKENIZATION
# --------------------------------

def tokenize(text):
    return re.findall(r"[^\W_]+", text.casefold())


# --------------------------------
# 3. LOAD QURAN DATASET
# --------------------------------

print("Loading Quran dataset...")

records = []

with open(QURAN_FILE, "r", encoding="utf-8") as file:
    for line in file:
        if line.strip():
            records.append(json.loads(line))

record_by_id = {
    f"{record['surah_number']}:{record['ayah_number']}": record
    for record in records
}

print(f"Loaded {len(records)} Quran verses.")


# --------------------------------
# 4. BUILD BM25 INDEX
# --------------------------------

print("\nBuilding BM25 keyword index...")

corpus = [
    tokenize(
        record["english_translation"] + " " + record["arabic_text"]
    )
    for record in records
]

bm25 = BM25Okapi(corpus)

print("BM25 index ready!")


# --------------------------------
# 5. LOAD SEMANTIC SEARCH MODEL
# --------------------------------

print("\nLoading embedding model...")

model = SentenceTransformer(MODEL_NAME)

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_collection(
    name="quran_verses"
)

print("ChromaDB connected!")


# --------------------------------
# 6. GET USER QUESTION
# --------------------------------

question = input("\nAsk a question about the Quran: ").strip()

if not question:
    raise ValueError("Question cannot be empty.")


# --------------------------------
# 7. SEMANTIC SEARCH
# --------------------------------

print("\nRunning semantic search...")

query_embedding = model.encode(
    question,
    normalize_embeddings=True
)

semantic_results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=min(RETRIEVAL_LIMIT, collection.count())
)

semantic_ids = semantic_results["ids"][0]
semantic_distances = semantic_results["distances"][0]

semantic_ranks = {
    verse_id: rank
    for rank, verse_id in enumerate(semantic_ids, start=1)
}

distance_by_id = dict(zip(semantic_ids, semantic_distances))


# --------------------------------
# 8. KEYWORD SEARCH USING BM25
# --------------------------------

print("Running BM25 keyword search...")

query_tokens = tokenize(question)

bm25_scores = bm25.get_scores(query_tokens)

keyword_indices = sorted(
    range(len(bm25_scores)),
    key=lambda index: bm25_scores[index],
    reverse=True
)[:RETRIEVAL_LIMIT]

keyword_ids = [
    f"{records[index]['surah_number']}:{records[index]['ayah_number']}"
    for index in keyword_indices
]

keyword_ranks = {
    verse_id: rank
    for rank, verse_id in enumerate(keyword_ids, start=1)
}


# --------------------------------
# 9. RECIPROCAL RANK FUSION
# --------------------------------

print("Combining search rankings...")

rrf_scores = defaultdict(float)

for verse_id, rank in semantic_ranks.items():
    rrf_scores[verse_id] += 1 / (RRF_K + rank)

for verse_id, rank in keyword_ranks.items():
    rrf_scores[verse_id] += 1 / (RRF_K + rank)

ranked_verses = sorted(
    rrf_scores.items(),
    key=lambda item: item[1],
    reverse=True
)[:FINAL_RESULTS]


# --------------------------------
# 10. DISPLAY FINAL RESULTS
# --------------------------------

print("\nHYBRID SEARCH RESULTS")
print("=====================")

for index, (verse_id, score) in enumerate(ranked_verses, start=1):

    record = record_by_id[verse_id]

    print(f"\nResult {index}")
    print("-" * 40)

    print(
        f"Surah: {record['surah_name']} "
        f"({record['surah_number']})"
    )

    print(f"Ayah: {record['ayah_number']}")

    print("\nArabic:")
    print(record["arabic_text"])

    print("\nEnglish:")
    print(record["english_translation"])

    print("\nFootnotes:")
    print(record.get("footnotes") or "No footnote available.")

    print("\nRetrieval details:")
    print("Semantic rank:", semantic_ranks.get(verse_id, "Not found"))
    print("Keyword rank:", keyword_ranks.get(verse_id, "Not found"))
    print("Semantic distance:", distance_by_id.get(verse_id, "Not found"))
    print("RRF score:", round(score, 6))

print("\nHYBRID SEARCH COMPLETED!")
