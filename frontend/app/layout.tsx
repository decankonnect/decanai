import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "Decan AI - Learn. Build. Ask. Create.", description: "An AI assistant grounded in your conversations, documents, images, and knowledge." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
