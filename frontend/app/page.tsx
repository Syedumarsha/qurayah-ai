
"use client";

import Image from "next/image";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

// ==========================================
// CONFIGURATION
// ==========================================

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const COLORS = {
  background: "#002214",
  backgroundLight: "#063523",
  backgroundCard: "#0A3B2A",
  gold: "#D4AF65",
  goldLight: "#E5C785",
  ivory: "#F8F5E9",
  textLight: "#E5E0D2",
  darkText: "#123D2D",
};

const suggestedQuestions = [
  "What does the Quran say about patience?",
  "What does the Quran teach about respecting parents?",
  "What is Tawakkul?",
];

// ==========================================
// ENGLISH SURAH NAMES
// ==========================================

const surahNames: Record<number, string> = {
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
  114: "An-Nas",
};

// ==========================================
// TYPES
// ==========================================

interface QuranVerse {
  surah_number: number;
  surah_name: string;
  ayah_number: number;
  arabic_text: string;
  english_translation: string;
  footnotes: string;
  translation_source: string;
  translation_version: string;
  translation_publisher: string;
  arabic_source: string;
  semantic_rank: number | null;
  keyword_rank: number | null;
  semantic_distance: number | null;
  rrf_score: number;
}

interface AskResponse {
  question: string;
  answer: string;
  generation_model: string;
  retrieval_method: string;
  results: QuranVerse[];
  result_count: number;
}

// ==========================================
// MAIN COMPONENT
// ==========================================

export default function Home() {
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [results, setResults] = useState<QuranVerse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  // ========================================
  // SUBMIT QUESTION
  // ========================================

  async function handleSubmit(
    e: React.FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || isLoading) return;

    setSubmittedQuestion(trimmedQuestion);
    setQuestion("");
    setAnswer("");
    setResults([]);
    setError("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmedQuestion,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to get a response from QurAyah AI."
        );
      }

      setAnswer(data.answer || "");
      setResults(data.results || []);

      if (!data.answer) {
        setError(
          "QurAyah AI could not generate an answer."
        );
      }
    } catch (err) {
      console.error("REQUEST ERROR:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  }

  // ========================================
  // SUGGESTED QUESTIONS
  // ========================================

  function handleSuggestedQuestion(value: string) {
    setQuestion(value);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  // ========================================
  // EXPLORE QURAN
  // ========================================

  function handleExploreQuran() {
    setQuestion(
      "Show me the opening verses of Surah Al-Fatiha."
    );

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  // ========================================
  // RENDER PAGE
  // ========================================

  return (
    <main
      className="relative flex min-h-screen flex-col overflow-hidden text-[#F8F5E9]"
      style={{
        backgroundColor: COLORS.background,
      }}
    >

      {/* ================================== */}
      {/* BACKGROUND DECORATION */}
      {/* ================================== */}

      <div
        className="pointer-events-none absolute inset-0 opacity-[0.08]"
        style={{
          backgroundImage:
            "radial-gradient(circle at center, #D4AF65 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at 50% 35%, rgba(10,65,43,0.22), transparent 65%)",
        }}
      />

      {/* ================================== */}
      {/* NAVIGATION */}
      {/* ================================== */}

      <nav
        className="relative z-10 flex items-center justify-between gap-3 border-b px-4 py-3 md:px-10 md:py-4"
        style={{
          borderColor: "rgba(212,175,101,0.22)",
          backgroundColor: COLORS.background,
        }}
      >

        {/* BRAND BANNER */}

        <div className="min-w-0 flex-1">
          <Image
            src="/qurayah-ai-banner.png"
            alt="QurAyah AI - Quran book logo by Syed Umar"
            width={2172}
            height={724}
            priority
            sizes="(max-width: 768px) 75vw, 700px"
            className="h-auto w-full max-w-[680px] object-contain object-left"
          />
        </div>

        {/* EXPLORE BUTTON */}

        <button
          type="button"
          onClick={handleExploreQuran}
          className="shrink-0 rounded-full border border-[#D4AF65] px-3 py-2 text-xs text-[#D4AF65] transition duration-300 hover:bg-[#D4AF65] hover:text-[#002214] sm:px-5 sm:text-sm"
        >
          Explore Quran
        </button>

      </nav>

      {/* ================================== */}
      {/* HERO SECTION */}
      {/* ================================== */}

      <section className="relative z-10 flex flex-1 flex-col items-center px-5 py-14 text-center md:py-20">

        {/* SECTION LABEL */}

        <div className="mb-7 flex items-center gap-4">

          <div className="h-px w-10 bg-[#D4AF65]" />

          <span className="text-xs uppercase tracking-[0.3em] text-[#D4AF65]">
            The Divine Guidance
          </span>

          <div className="h-px w-10 bg-[#D4AF65]" />

        </div>

        {/* BISMILLAH */}

        <p
          dir="rtl"
          lang="ar"
          className="mb-8 text-3xl leading-relaxed text-[#D4AF65] md:text-5xl"
        >
          بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
        </p>

        {/* HERO HEADING */}

        <h2 className="max-w-4xl text-4xl font-semibold leading-tight md:text-6xl">

          Discover the Wisdom of the{" "}

          <span className="text-[#D4AF65]">
            Holy Quran
          </span>

        </h2>

        <p className="mt-7 max-w-2xl text-base leading-8 text-[#E5E0D2] md:text-lg">

          Explore the Holy Quran through its original Arabic
          verses and English translation. Ask questions and
          discover relevant Quranic references with QurAyah AI.

        </p>

        {/* ================================== */}
        {/* CHAT INPUT */}
        {/* ================================== */}

        <form
          onSubmit={handleSubmit}
          className="mt-12 flex w-full max-w-2xl flex-col gap-3 rounded-2xl border border-[#D4AF65]/40 bg-[#F8F5E9] p-3 shadow-2xl sm:flex-row"
        >

          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything about the Quran..."
            disabled={isLoading}
            className="min-w-0 flex-1 bg-transparent px-4 py-3 text-sm text-[#123D2D] outline-none placeholder:text-gray-500 md:text-base"
          />

          <button
            type="submit"
            disabled={!question.trim() || isLoading}
            className="rounded-xl bg-[#D4AF65] px-7 py-3 font-semibold text-[#002214] transition hover:bg-[#E5C785] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? "Thinking..." : "Ask QurAyah AI"}
          </button>

        </form>

        {/* ================================== */}
        {/* SUGGESTED QUESTIONS */}
        {/* ================================== */}

        <div className="mt-9 flex max-w-3xl flex-wrap justify-center gap-3">

          {suggestedQuestions.map((item) => (

            <button
              key={item}
              type="button"
              disabled={isLoading}
              onClick={() => handleSuggestedQuestion(item)}
              className="rounded-full border border-[#D4AF65]/35 px-4 py-2.5 text-sm text-[#F8F5E9] transition duration-300 hover:border-[#D4AF65] hover:bg-[#D4AF65] hover:text-[#002214] disabled:opacity-50"
              style={{
                backgroundColor: COLORS.backgroundLight,
              }}
            >
              {item}
            </button>

          ))}

        </div>

        {/* ================================== */}
        {/* CHAT RESPONSE SECTION */}
        {/* ================================== */}

        {submittedQuestion && (

          <div className="mt-14 w-full max-w-4xl space-y-7 text-left">

            {/* USER QUESTION */}

            <div
              className="rounded-2xl border border-[#D4AF65]/30 p-5 md:p-6"
              style={{
                backgroundColor: COLORS.backgroundLight,
              }}
            >

              <p className="mb-3 text-xs font-bold uppercase tracking-widest text-[#D4AF65]">
                Your Question
              </p>

              <p className="text-base leading-7 text-[#F8F5E9]">
                {submittedQuestion}
              </p>

            </div>

            {/* LOADING */}

            {isLoading && (

              <div className="rounded-2xl border border-[#D4AF65]/30 bg-[#F8F5E9] p-7 text-center">

                <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-[#D4AF65]/30 border-t-[#245640]" />

                <p className="animate-pulse font-semibold text-[#245640]">
                  QurAyah AI is studying the Quranic evidence...
                </p>

                <p className="mt-2 text-sm text-[#245640]/70">
                  Preparing your answer. Please wait.
                </p>

              </div>

            )}

            {/* ERROR */}

            {!isLoading && error && (

              <div className="rounded-2xl border border-red-300/40 bg-[#F8F5E9] p-6">

                <p className="font-semibold text-red-700">
                  Unable to generate response
                </p>

                <p className="mt-2 text-sm leading-7 text-red-700">
                  {error}
                </p>

              </div>

            )}

            {/* ================================== */}
            {/* GEMINI ANSWER */}
            {/* ================================== */}

            {!isLoading && !error && answer && (

              <div className="overflow-hidden rounded-2xl border border-[#D4AF65]/40 bg-[#F8F5E9] shadow-xl">

                {/* ANSWER HEADER */}

                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D4AF65]/30 px-6 py-5">

                  <div>
                    <h3 className="text-xl font-bold text-[#123D2D]">
                      QurAyah AI
                    </h3>

                    <p className="mt-1 text-xs text-[#245640]/70">
                      Quran-based response
                    </p>
                  </div>

                  <span className="rounded-full bg-[#D4AF65]/20 px-3 py-1.5 text-xs font-semibold text-[#806020]">
                    Gemini Powered
                  </span>

                </div>

                {/* FORMATTED ANSWER */}

                <div className="space-y-5 px-6 py-7 text-base leading-8 text-[#123D2D] md:px-8 md:py-9">

                  <ReactMarkdown
                    components={{

                      h3: ({ children }) => (
                        <h3 className="border-b border-[#D4AF65]/40 pb-3 pt-3 text-xl font-bold text-[#245640] md:text-2xl">
                          {children}
                        </h3>
                      ),

                      p: ({ children }) => (
                        <p className="py-1 text-base leading-8 text-[#245640] md:text-lg">
                          {children}
                        </p>
                      ),

                      strong: ({ children }) => (
                        <strong className="font-bold text-[#123D2D]">
                          {children}
                        </strong>
                      ),

                      ol: ({ children }) => (
                        <ol className="space-y-5 pl-5">
                          {children}
                        </ol>
                      ),

                      ul: ({ children }) => (
                        <ul className="list-disc space-y-3 pl-6">
                          {children}
                        </ul>
                      ),

                      li: ({ children }) => (
                        <li className="pl-1 leading-8 text-[#245640]">
                          {children}
                        </li>
                      ),

                      em: ({ children }) => (
                        <em className="text-sm text-[#806020]">
                          {children}
                        </em>
                      ),

                    }}
                  >
                    {answer}
                  </ReactMarkdown>

                </div>

              </div>

            )}

            {/* ================================== */}
            {/* SUPPORTING QURANIC REFERENCES */}
            {/* ================================== */}

            {!isLoading && !error && results.length > 0 && (

              <div className="space-y-6">

                {/* REFERENCE HEADING */}

                <div className="px-1">

                  <div className="flex flex-wrap items-center justify-between gap-3">

                    <h3 className="text-xl font-semibold text-[#D4AF65] md:text-2xl">
                      Supporting Quranic References
                    </h3>

                    <span className="rounded-full border border-[#D4AF65]/40 px-3 py-1 text-xs text-[#D4AF65]">
                      {results.length}{" "}
                      {results.length === 1 ? "Ayah" : "Ayahs"}
                    </span>

                  </div>

                  <p className="mt-2 text-sm leading-6 text-[#E5E0D2]/70">
                    The original Quranic verses selected for this answer.
                  </p>

                </div>

                {/* VERSE CARDS */}

                {results.map((verse) => {

                  const englishSurahName =
                    surahNames[verse.surah_number] ||
                    `Surah ${verse.surah_number}`;

                  return (

                    <article
                      key={`${verse.surah_number}:${verse.ayah_number}`}
                      className="overflow-hidden rounded-2xl border border-[#D4AF65]/30 bg-[#F8F5E9] text-[#123D2D] shadow-lg transition duration-300 hover:border-[#D4AF65]/70"
                    >

                      {/* SURAH HEADER */}

                      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D4AF65]/30 bg-[#EEE9D9] px-5 py-4 md:px-7">

                        <div>

                          <p className="text-lg font-bold text-[#123D2D]">
                            Surah {englishSurahName}
                          </p>

                          <p
                            dir="rtl"
                            lang="ar"
                            className="mt-1 text-xl text-[#806020]"
                          >
                            {verse.surah_name}
                          </p>

                          <p className="mt-2 text-xs text-[#245640]">
                            Chapter {verse.surah_number} · Ayah{" "}
                            {verse.ayah_number}
                          </p>

                        </div>

                        <span className="rounded-full border border-[#D4AF65]/50 bg-[#F8F5E9] px-4 py-2 text-sm font-bold text-[#806020]">
                          {verse.surah_number}:{verse.ayah_number}
                        </span>

                      </div>

                      {/* ARABIC TEXT */}

                      <div className="border-b border-[#D4AF65]/20 px-5 py-8 md:px-8 md:py-10">

                        <p
                          dir="rtl"
                          lang="ar"
                          className="text-right text-3xl leading-[2.4] text-[#123D2D] md:text-4xl md:leading-[2.5]"
                        >
                          {verse.arabic_text}
                        </p>

                      </div>

                      {/* ENGLISH TRANSLATION */}

                      <div className="px-5 py-6 md:px-8 md:py-7">

                        <p className="text-base leading-8 text-[#245640] md:text-lg md:leading-9">
                          {verse.english_translation}
                        </p>

                      </div>

                      {/* FOOTNOTES */}

                      {verse.footnotes && (

                        <div className="border-t border-[#D4AF65]/20 bg-[#EEE9D9] px-5 py-5 md:px-8">

                          <p className="mb-2 text-xs font-bold uppercase tracking-wider text-[#9A7835]">
                            Translation Footnotes
                          </p>

                          <p className="whitespace-pre-wrap text-sm leading-7 text-[#245640]">
                            {verse.footnotes}
                          </p>

                        </div>

                      )}

                      {/* SOURCE INFORMATION */}

                      <div className="border-t border-[#D4AF65]/20 px-5 py-5 md:px-8">

                        <p className="mb-3 text-xs font-bold uppercase tracking-wider text-[#9A7835]">
                          Source Information
                        </p>

                        <div className="space-y-1.5">

                          <p className="text-xs leading-6 text-[#245640]">
                            Arabic text: {verse.arabic_source} (Uthmani)
                          </p>

                          <p className="text-xs leading-6 text-[#245640]">
                            English translation: {verse.translation_source}
                          </p>

                          <p className="text-xs leading-6 text-[#245640]">
                            Publisher: {verse.translation_publisher}
                          </p>

                          <p className="text-xs leading-6 text-[#245640]">
                            Translation version: {verse.translation_version}
                          </p>

                        </div>

                      </div>

                    </article>

                  );

                })}

                {/* DISCLAIMER */}

                <div className="rounded-xl border border-[#D4AF65]/20 bg-[#063523] px-5 py-4">

                  <p className="text-center text-xs leading-7 text-[#E5E0D2]/80">
                    Please refer to the original Quran and its
                    surrounding context. AI-generated explanations
                    may require further verification.
                  </p>

                </div>

              </div>

            )}

          </div>

        )}

      </section>

      {/* ================================== */}
      {/* FOOTER */}
      {/* ================================== */}

      <footer
        className="relative z-10 border-t px-5 py-8 text-center text-sm text-[#E5E0D2]/70"
        style={{
          borderColor: "rgba(212,175,101,0.22)",
          backgroundColor: COLORS.background,
        }}
      >

        <p>
          Built with the intention of spreading beneficial knowledge.
        </p>

        <p className="mt-2 text-xs text-[#D4AF65]/70">
          Quran Arabic and English Translation
        </p>

        <p className="mt-2 text-xs text-[#D4AF65]/70">
          © 2026 QurAyah AI
        </p>

      </footer>

    </main>
  );
}
