import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { ApiLoadingProvider } from "@/components/layout/ApiLoadingProvider";
import { AuthProvider } from "@/components/layout/AuthProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ISHA Ayush",
  description: "Intelligent AYUSH Health System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased text-foreground bg-background`}
      >
        <ApiLoadingProvider>
          <AuthProvider>
            <div className="flex min-h-screen w-full">
              <AppSidebar />
              <main className="flex-1 min-w-0 overflow-auto w-full">
                {/* pt-20 clears the floating mobile hamburger; desktop shows the sidebar in-flow so it needs no extra offset */}
                <div className="p-4 pt-20 md:p-8">
                  {children}
                </div>
              </main>
            </div>
          </AuthProvider>
        </ApiLoadingProvider>
      </body>
    </html>
  );
}
