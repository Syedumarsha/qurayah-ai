
import os
import traceback

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from quran_retriever import (
    QuranRetriever,
    detect_reference,
    detect_surah_only,
    SURAH_NAMES
)

from answer_generator import GeminiAnswerGenerator


# ==========================================
# 1. GLOBAL INSTANCES
# ==========================================

retriever = None
answer_generator = None


# ==========================================
# 2. APPLICATION LIFECYCLE
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    global retriever, answer_generator

    print("\nInitializing QurAyah AI...")

    try:

        retriever = QuranRetriever()

        print("Quran retriever ready!")

        answer_generator = GeminiAnswerGenerator()

        print("Gemini ready!")

        print("QurAyah AI initialized successfully.\n")

        yield

    except Exception:

        traceback.print_exc()

        raise

    finally:

        print("QurAyah AI shutting down...")


# ==========================================
# 3. FASTAPI APPLICATION
# ==========================================

app = FastAPI(

    title="QurAyah AI",

    description=(
        "Quran-only AI assistant with intelligent "
        "query understanding and evidence retrieval."
    ),

    version="3.0.0",

    lifespan=lifespan
)


# ==========================================
# 4. CORS
# ==========================================

frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:3000"
)

allowed_origins = [
    origin.strip()
    for origin in frontend_origins.split(",")
    if origin.strip()
]

app.add_middleware(

    CORSMiddleware,

    allow_origins=allowed_origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ==========================================
# 5. REQUEST MODEL
# ==========================================

class QuestionRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=1000
    )


# ==========================================
# 6. HOME
# ==========================================

@app.get("/")
def home():

    return {

        "message": "Welcome to QurAyah AI!",

        "status": "Backend is running successfully",

        "version": "3.0.0"

    }


# ==========================================
# 7. HEALTH
# ==========================================

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "retriever_ready": retriever is not None,

        "gemini_ready": answer_generator is not None

    }


# ==========================================
# 8. ASK QUESTION
# ==========================================

@app.post("/ask")
def ask_question(request: QuestionRequest):

    if retriever is None or answer_generator is None:

        raise HTTPException(
            status_code=503,
            detail="QurAyah AI is not ready."
        )

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Please enter a valid question."
        )

    try:

        print("\n========== NEW QUESTION ==========")

        print("Question:", question)

        # ----------------------------------
        # STEP 1: DETECT QUERY TYPE
        # ----------------------------------

        reference = detect_reference(question)

        surah_number = detect_surah_only(question)

        if reference:

            query_type = "exact_ayah"

        elif surah_number:

            query_type = "complete_surah"

        else:

            query_type = "general_question"

        print("Query type:", query_type)

        # ----------------------------------
        # STEP 2: GEMINI QUERY UNDERSTANDING
        # ----------------------------------

        expanded_queries = []

        if query_type == "general_question":

            print("\nGemini query understanding started...")

            expanded_queries = (
                answer_generator.understand_query(question)
            )

            print(
                "Expanded queries:",
                len(expanded_queries)
            )

        # ----------------------------------
        # STEP 3: QURAN RETRIEVAL
        # ----------------------------------

        print("\nRetrieving Quranic evidence...")

        results = retriever.retrieve(
            question,
            expanded_queries=expanded_queries
        )

        print(
            "Retrieved Quranic records:",
            len(results)
        )

        if not results:

            return {

                "question": question,

                "answer": (
                    "I could not find sufficient Quranic "
                    "evidence to answer this question. "
                    "Please try rephrasing your question."
                ),

                "retrieval_method": "BM25 + Gemini Query Understanding",

                "query_type": query_type,

                "generation_model": answer_generator.model,

                "results": [],

                "retrieved_count": 0,

                "result_count": 0

            }

        # ----------------------------------
        # STEP 4: EXACT AYAH
        # ----------------------------------

        if query_type == "exact_ayah":

            answer = answer_generator.generate_answer(
                question,
                results
            )

            selected_results = (
                answer_generator.selected_verses
            )

        # ----------------------------------
        # STEP 5: COMPLETE SURAH
        # ----------------------------------

        elif query_type == "complete_surah":

            surah_name = SURAH_NAMES[surah_number]

            total_ayahs = len(results)

            answer = (
                f"## Surah {surah_name} "
                f"({surah_number})\n\n"
                f"This Surah contains {total_ayahs} Ayahs. "
                f"The complete Arabic text and English "
                f"translation are included in the Quranic "
                f"references below.\n\n"
                f"Arabic Quran text: Tanzil Uthmani. "
                f"English translation: QuranEnc, "
                f"Noor International Center."
            )

            # Preserve every Ayah in the Surah.
            selected_results = results

        # ----------------------------------
        # STEP 6: GENERAL QUESTION
        # ----------------------------------

        else:

            answer = answer_generator.generate_answer(
                question,
                results
            )

            selected_results = (
                answer_generator.selected_verses
            )

        # ----------------------------------
        # STEP 7: API RESPONSE
        # ----------------------------------

        print("\nAnswer generated successfully.")

        print(
            "Final references:",
            len(selected_results)
        )

        print("====================================\n")

        return {

            "question": question,

            "answer": answer,

            "retrieval_method": (
                "Direct Lookup + Gemini Query Understanding "
                "+ BM25 + Reciprocal Rank Fusion"
            ),

            "query_type": query_type,

            "generation_model": answer_generator.model,

            "results": selected_results,

            "retrieved_count": len(results),

            "result_count": len(selected_results)

        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:

        traceback.print_exc()

        raise HTTPException(

            status_code=500,

            detail=(
                "An internal error occurred. "
                "Please try again later."
            )

        )
