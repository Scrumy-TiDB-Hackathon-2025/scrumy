import { Inter, Roboto_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const robotoMono = Roboto_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "ScrumAI Dashboard",
  description: "Team collaboration and meeting notes",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${robotoMono.variable} flex bg-gray-50 h-screen overflow-hidden`}>
        {/* Sidebar - Fixed width */}
        <div className="w-56 flex-shrink-0">
          <Sidebar />
        </div>
        
        {/* Main content area */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Topbar - Fixed at top */}
          <Topbar />
          
          {/* Page content - Scrollable */}
          <main className="flex-1 overflow-hidden">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}