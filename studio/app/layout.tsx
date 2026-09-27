import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aura Studio",
  description: "Ambiente local de desenvolvimento assistido e verificável.",
};

export default function RootLayout({children}: Readonly<{children: ReactNode}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
