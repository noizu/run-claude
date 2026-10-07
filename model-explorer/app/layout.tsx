import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "run-claude · model explorer",
  description:
    "Browse run-claude model definitions (installation + user override) and profiles: pricing, token limits, thinking support, throughput.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
