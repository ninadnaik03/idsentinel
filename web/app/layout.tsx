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
  metadataBase: new URL("https://idsentinel.vercel.app"),
  title: { default: "IDSentinel | Document Presentation Attack Detection", template: "%s | IDSentinel" },
  description: "IDSentinel is a 24-hour research implementation exploring semantic, texture and edge representations for identity-document presentation attack detection.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
  openGraph: { title: "IDSentinel", description: "Semantic. Texture. Edge. Three views of document authenticity.", type: "website", images:["/og.png"] },
  twitter: { card: "summary_large_image", title: "IDSentinel", description: "A 24-hour presentation-attack detection research sprint.", images:["/og.png"] },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
