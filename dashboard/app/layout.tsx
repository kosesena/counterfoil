import type { Metadata } from 'next';
import { Baloo_2, Fraunces, IBM_Plex_Mono, Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const fraunces = Fraunces({ subsets: ['latin'], variable: '--font-fraunces', style: ['normal', 'italic'], axes: ['opsz'] });
const mono = IBM_Plex_Mono({ subsets: ['latin'], variable: '--font-mono', weight: ['400', '500'] });
// the felt look: a round, heavy display face for HOMI's headlines (Codex's design, 25 Oct)
const baloo = Baloo_2({ subsets: ['latin'], variable: '--font-baloo', weight: ['600', '700', '800'] });

export const metadata: Metadata = {
  title: 'HOMI · A little trust, a firm boundary',
  description: 'What the AI transaction agent tried to do with the money, and what Counterfoil let through to Braintree',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable} ${mono.variable} ${baloo.variable}`}>
      <body>{children}</body>
    </html>
  );
}
