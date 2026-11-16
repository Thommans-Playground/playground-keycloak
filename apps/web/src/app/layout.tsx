import type { Metadata } from "next";
import { Inter, Roboto_Mono } from "next/font/google";
import { Masthead } from "@/components/masthead";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const robotoMono = Roboto_Mono({ variable: "--font-roboto-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Playground",
  description: "Keycloak sign in playground: Next.js, shadcn, FastAPI, styled with the Singapore Government Design System",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} ${robotoMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <Masthead />
        {children}
      </body>
    </html>
  );
}
