
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from quran_retriever import QuranRetriever
from answer_generator import GeminiAnswerGenerator


# --------------------------------
# 1. GLOBAL INSTANCES
# --------------------------------

retriever = None
answer_generator = None


# --------------------------------
# 2. APPLICATION LIFECYCLE
# --------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    global retriever, answer_generator

    print("\n====================================")
    print("Initializing Hikmah AI...")
    print("====================================")

    try:

        print("Loading Quran retriever...")

        retriever = QuranRetriever()

        print("Quran retriever initialized successfully!")

        print("Initializing Gemini...")

        answer_generator = GeminiAnswerGenerator()

        print("Gemini initialized successfully!")

        print("\nHikmah AI is ready!")
        print("====================================\n")

        yield

    except Exception:

        print("\n========== INITIALIZATION ERROR ==========")

        traceback.print_exc()

        print("==========================================\n")

        raise

    finally:

        print("\nHikmah AI shutting down...")


# --------------------------------
# 3. FASTAPI APPLICATION
# --------------------------------

app = FastAPI(

    title="Hikmah AI",

    description="Quran-based AI Assistant using RAG and Gemini",

    version="1.0.0",

    lifespan=lifespan
)


# --------------------------------
# 4. CORS CONFIGURATION
# --------------------------------

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# --------------------------------
# 5. REQUEST MODEL
# --------------------------------

class QuestionRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=1000
    )


# --------------------------------
# 6. HOME ENDPOINT
# --------------------------------

@app.get("/")
def home():

    return {

        "message": "Welcome to Hikmah AI!",

        "status": "Backend is running successfully"

    }


# --------------------------------
# 7. HEALTH ENDPOINT
# --------------------------------

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "retriever_ready": retriever is not None,

        "gemini_ready": answer_generator is not None

    }


# --------------------------------
# 8. ASK ENDPOINT
# --------------------------------

@app.post("/ask")
def ask_question(request: QuestionRequest):

    if retriever is None or answer_generator is None:

        raise HTTPException(

            status_code=503,

            detail="Hikmah AI is not ready."

        )

    try:

        print("\n========== NEW QUESTION ==========")

        print("Question:", request.question)

        # --------------------------------
        # STEP 1: QURAN RETRIEVAL
        # --------------------------------

        print("\nSTEP 1: Retrieving Quranic verses...")

        results = retriever.retrieve(
            request.question
        )

        print(
            "STEP 1 COMPLETE:",
            len(results),
            "verses retrieved."
        )

        # --------------------------------
        # STEP 2: GEMINI GENERATION
        # --------------------------------

        print("\nSTEP 2: Generating answer using Gemini...")

        answer = answer_generator.generate_answer(

            request.question,

            results

        )

        print("\nSTEP 2 COMPLETE: Gemini generated the answer.")

        # --------------------------------
        # STEP 3: RETURN RESPONSE
        # --------------------------------

        print("\nSTEP 3: Sending response to frontend.")

        return {

            "question": request.question,

            "answer": answer,

            "retrieval_method": (
                "Hybrid Search (BM25 + Semantic Search + RRF)"
            ),

            "generation_model": answer_generator.model,

            "results": results,

            "result_count": len(results)

        }

    # --------------------------------
    # VALIDATION ERROR
    # --------------------------------

    except ValueError as error:

        print("\n========== VALIDATION ERROR ==========")

        print("Error:", repr(error))

        traceback.print_exc()

        print("======================================\n")

        raise HTTPException(

            status_code=400,

            detail=str(error)

        )

    # --------------------------------
    # DEBUGGING: INTERNAL ERROR
    # --------------------------------

    except Exception as error:

        print("\n========== HIKMAH AI ERROR ==========")

        print("Error:", repr(error))

        traceback.print_exc()

        print("====================================\n")

        raise HTTPException(

            status_code=500,

            detail=f"DEBUG ERROR: {repr(error)}"

        )
