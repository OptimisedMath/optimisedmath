import type { Metadata } from "next";
import { Geist, Geist_Mono, Inter } from "next/font/google";
import "./globals.css";
import "katex/dist/katex.min.css";
import { cn } from "@/lib/utils";
import ThemeProvider from "@/components/ThemeProvider";
import ConnectionOverlay from "@/components/ConnectionOverlay";

const inter = Inter({subsets:['latin'],variable:'--font-sans'});

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Optimised Math - Nauka Matematyki",
  description: "Interaktywna platforma do nauki matematyki z adaptacyjnym systemem zadań",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pl"
      className={cn("h-full dark", "antialiased", geistSans.variable, geistMono.variable, "font-sans", inter.variable)}
    >
      <body className="min-h-full flex flex-col">
        <ThemeProvider>
          <ConnectionOverlay>{children}</ConnectionOverlay>
        </ThemeProvider>
      </body>
    </html>
  );
}
