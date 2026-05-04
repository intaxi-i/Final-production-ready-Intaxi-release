'use client';

import { useEffect } from 'react';
import { initTelegramUi } from '@/lib/telegram';

export function TelegramBootstrap() {
  useEffect(() => {
    initTelegramUi();
  }, []);

  return null;
}
