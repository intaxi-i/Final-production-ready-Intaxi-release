import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { ActiveRideBar } from '@/components/ActiveRideBar';
import { AppBackButton } from '@/components/AppBackButton';
import { BottomNav } from '@/components/BottomNav';
import { TelegramBootstrap } from '@/components/TelegramBootstrap';
import './globals.css';

export const metadata: Metadata = {
  title: 'Intaxi V2',
  description: 'Intaxi Mini App V2',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <TelegramBootstrap />
        <AppBackButton />
        <ActiveRideBar />
        {children}
        <BottomNav />
      </body>
    </html>
  );
}
