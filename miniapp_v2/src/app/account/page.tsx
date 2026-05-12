import { redirect } from 'next/navigation';
import { APP_ROUTES } from '@/lib/constants';

export default function AccountPage() {
  redirect(APP_ROUTES.wallet);
}
