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

// export default function RootLayout({ children }) {
//   return (
//     <html lang="en">
//       <body className={`${inter.variable} ${robotoMono.variable}`}>
//         {children}
//       </body>
//     </html>
//   );
// }


export const metadata = {
  title: "ScrumAI Dashboard",
  description: "Team collaboration and meeting notes",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="flex bg-gray-50 h-screen">
        <Sidebar />
        <div className="flex flex-col flex-1">
          <Topbar />
          <main className="p-6 overflow-y-auto flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
