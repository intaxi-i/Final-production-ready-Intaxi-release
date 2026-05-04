import "./globals.css";
import Script from "next/script";
import { AppProvider } from "@/context/AppContext";

export const metadata = {
  title: "Intaxi",
  description: "Intaxi Mini App",
};

const initThemeScript = `
(function () {
  try {
    var saved = localStorage.getItem("intaxi_theme");
    var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.dataset.theme = saved || (prefersDark ? "dark" : "light");
  } catch (e) {
    document.documentElement.dataset.theme = "light";
  }
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
        />
        <script dangerouslySetInnerHTML={{ __html: initThemeScript }} />
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
