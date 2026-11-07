
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://qurayah-ai.vercel.app"),

  title: {
    default: "QurAyah AI",
    template: "%s | QurAyah AI",
  },

  description:
    "QurAyah AI is an AI-powered Quran chatbot that helps you explore and understand the Holy Quran through questions, with answers grounded in Quranic verses.",

  applicationName: "QurAyah AI",

  openGraph: {
    title: "QurAyah AI",
    description:
      "Explore and understand the Holy Quran through natural-language questions. Let the Quran speak through its own verses.",
    url: "https://qurayah-ai.vercel.app",
    siteName: "QurAyah AI",
    locale: "en_IN",
    type: "website",
    images: [
      {
        url: "/qurayah-ai-banner.png",
        width: 2048,
        height: 682,
        alt: "QurAyah AI – Your Quran Companion",
      },
    ],
  },

  twitter: {
    card: "summary_large_image",
    title: "QurAyah AI",
    description:
      "Explore and understand the Holy Quran through your questions.",
    images: ["/qurayah-ai-banner.png"],
  },

  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
