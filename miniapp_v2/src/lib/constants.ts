export const APP_ROUTES = {
  home: '/',
  profile: '/profile',
  cityCreate: '/city/create',
  cityMyOrders: '/city/my-orders',
  cityOffers: '/city/offers',
  currentTrip: '/trip/current',
  driverRegister: '/driver/register',
  driverOnline: '/driver/online',
  driverPaymentMethods: '/driver/payment-methods',
  account: '/account',
  support: '/support',
  donate: '/donate',
  admin: '/admin',
} as const;

export type AppLanguage = 'ru' | 'uz' | 'kz' | 'en';

export const SUPPORTED_LANGUAGES: AppLanguage[] = ['ru', 'uz', 'kz', 'en'];
