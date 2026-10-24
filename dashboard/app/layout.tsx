import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Counterfoil · gate decisions',
  description: 'What the AI transaction agent tried to do with the money, and what Counterfoil let through',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
