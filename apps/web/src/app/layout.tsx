import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "VisionAI - Real-Time Computer Vision",
  description: "Production-grade real-time computer vision platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <Providers>{children}</Providers>
        <Script
          src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js"
          strategy="lazyOnload"
          data-name="bmc-button"
          data-slug="dhananiyash"
          data-color="#000000"
          data-emoji=""
          data-font="Cookie"
          data-text="Buy me a coffee"
          data-outline-color="#ffffff"
          data-font-color="#ffffff"
          data-coffee-color="#FFDD00"
        />
      </body>
    </html>
  );
}