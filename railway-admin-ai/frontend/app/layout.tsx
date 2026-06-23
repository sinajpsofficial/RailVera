import "./globals.css"
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Railway Admin AI Assessment Portal",
  description: "Indian Railways Departmental Decision Support & Eligibility System",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        {/* System font stack — avoids Google Fonts network call blocking render */}
        <style dangerouslySetInnerHTML={{ __html: `
          :root { --font-sans: 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif; }
          body { font-family: var(--font-sans); }
        ` }} />

      </head>
      <body className="font-sans antialiased text-slate-800 bg-slate-50 min-h-screen">
        {children}
      </body>
    </html>
  )
}
