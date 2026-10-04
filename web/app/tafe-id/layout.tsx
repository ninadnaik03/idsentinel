import type { Metadata } from "next";
import "./retro.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://ninadnaik.dev"),
  title: { default: "TAFE-ID — Document Forensics Lab", template: "%s | TAFE-ID" },
  description: "Ninad Naik’s document-tampering research: verified ASCFormer reference inference, custom experiments, methods and limitations.",
  icons: { icon: "/tafe-id/icon.svg" },
  openGraph: { title: "TAFE-ID — Document Forensics Lab", description: "Reference inference, custom experiments and an inspectable research record.", images: ["/tafe-id/share.svg"] },
  twitter: { card: "summary", title: "TAFE-ID — Document Forensics Lab", images: ["/tafe-id/icon.svg"] },
};

export default function TafeLayout({ children }: { children: React.ReactNode }) {
  return children;
}
