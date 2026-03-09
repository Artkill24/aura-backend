import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AURA — Advanced Universal Reality Authentication',
  description: 'Forensic AI & Deepfake Video Detection for Insurance, Legal, and Compliance',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
