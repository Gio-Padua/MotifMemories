import type { Metadata } from 'next';
import localFont from 'next/font/local';
import './globals.css';

const inter = localFont({ src: '../public/fonts/inter-variable.woff2', variable: '--font-inter', display: 'swap' });
export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL || 'http://localhost:3000'),
  title: 'Motif Moments — Make it a motif. Keep the memory.',
  description: 'Your people. Your poses. Your little keepsake. Discover the Motif Moments self-photo booth, six curated frames, printed memories, and easy QR downloads.',
  openGraph: { title: 'Motif Moments', description: 'Make it a motif. Keep the memory.', type: 'website' },
  twitter: { card: 'summary_large_image' },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" className={inter.variable}><body>{children}</body></html>;
}
