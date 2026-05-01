import type { AppLanguage } from './constants';

type Dict = Record<string, string>;

export const messages: Record<AppLanguage, Dict> = {
  ru: {
    appName: 'Intaxi', home: 'Главная', profile: 'Профиль', city: 'Город', intercity: 'Межгород', wallet: 'Баланс', support: 'Поддержка', admin: 'Админ', back: 'Назад', country: 'Страна', region: 'Область / регион', cityField: 'Город / район', chooseRegion: 'Выберите область', chooseCity: 'Выберите город / район',
    createOrder: 'Создать заказ', myOrders: 'Мои заказы', availableOffers: 'Доступные заказы', currentTrip: 'Текущая поездка', passengerMode: 'Режим пассажира', driverMode: 'Режим водителя',
    fromAddress: 'Адрес откуда', toAddress: 'Адрес куда', seats: 'Места', price: 'Цена', yourPrice: 'Ваша цена', recommendedPrice: 'Рекомендованная цена', useRecommendedPrice: 'Поставить рекомендованную цену', comment: 'Комментарий', writeComment: 'Дополнительная информация',
    status: 'Статус', loading: 'Загрузка...', noData: 'Пока нет данных', noOrders: 'Заказы не найдены', noOffers: 'Заказы не найдены', save: 'Сохранить', submit: 'Отправить', updatedSuccessfully: 'Изменения сохранены', operationFailed: 'Не удалось выполнить действие',
    driversSeen: 'Водителей увидели заказ', raisePrice: 'Повысить цену', raisePriceHint: 'Свободных водителей мало или текущая цена ниже ожидаемой.', searchStarted: 'Поиск водителей уже запущен и не останавливается.', tripDistance: 'Длина маршрута', distance: 'Расстояние', eta: 'ETA',
    driverOnline: 'Водитель online', driverRegister: 'Регистрация водителя', paymentMethods: 'Реквизиты', account: 'Аккаунт', donate: 'Поддержать проект',
  },
  uz: {
    appName: 'Intaxi', home: 'Bosh sahifa', profile: 'Profil', city: 'Shahar', intercity: 'Shaharlararo', wallet: 'Balans', support: 'Yordam', admin: 'Admin', back: 'Orqaga', country: 'Davlat', region: 'Viloyat / hudud', cityField: 'Shahar / tuman', chooseRegion: 'Viloyatni tanlang', chooseCity: 'Shahar / tumanni tanlang',
    createOrder: 'Buyurtma yaratish', myOrders: 'Mening buyurtmalarim', availableOffers: 'Mavjud buyurtmalar', currentTrip: 'Joriy safar', passengerMode: 'Yo‘lovchi rejimi', driverMode: 'Haydovchi rejimi',
    fromAddress: 'Qayerdan manzil', toAddress: 'Qayerga manzil', seats: 'Joylar', price: 'Narx', yourPrice: 'Sizning narxingiz', recommendedPrice: 'Tavsiya narx', useRecommendedPrice: 'Tavsiya narxni qo‘yish', comment: 'Izoh', writeComment: 'Qo‘shimcha ma’lumot',
    status: 'Holat', loading: 'Yuklanmoqda...', noData: 'Hozircha ma’lumot yo‘q', noOrders: 'Buyurtma topilmadi', noOffers: 'Buyurtma topilmadi', save: 'Saqlash', submit: 'Yuborish', updatedSuccessfully: 'O‘zgarishlar saqlandi', operationFailed: 'Amal bajarilmadi',
    driversSeen: 'Buyurtmani ko‘rgan haydovchilar', raisePrice: 'Narxni oshirish', raisePriceHint: 'Bo‘sh haydovchilar kam yoki narx past.', searchStarted: 'Haydovchi qidirish davom etmoqda.', tripDistance: 'Yo‘l masofasi', distance: 'Masofa', eta: 'Yetib kelish',
    driverOnline: 'Haydovchi online', driverRegister: 'Haydovchi ro‘yxati', paymentMethods: 'Rekvizitlar', account: 'Akkaunt', donate: 'Loyihani qo‘llab-quvvatlash',
  },
  kz: {
    appName: 'Intaxi', home: 'Басты бет', profile: 'Профиль', city: 'Қала', intercity: 'Қалааралық', wallet: 'Баланс', support: 'Қолдау', admin: 'Админ', back: 'Артқа', country: 'Ел', region: 'Облыс / өңір', cityField: 'Қала / аудан', chooseRegion: 'Облысты таңдаңыз', chooseCity: 'Қала / ауданды таңдаңыз',
    createOrder: 'Тапсырыс құру', myOrders: 'Менің тапсырыстарым', availableOffers: 'Қолжетімді тапсырыстар', currentTrip: 'Ағымдағы сапар', passengerMode: 'Жолаушы режимі', driverMode: 'Жүргізуші режимі',
    fromAddress: 'Қайдан мекенжай', toAddress: 'Қайда мекенжай', seats: 'Орындар', price: 'Баға', yourPrice: 'Сіздің бағаңыз', recommendedPrice: 'Ұсынылған баға', useRecommendedPrice: 'Ұсынылған бағаны қою', comment: 'Түсініктеме', writeComment: 'Қосымша ақпарат',
    status: 'Күйі', loading: 'Жүктелуде...', noData: 'Әзірге мәлімет жоқ', noOrders: 'Тапсырыс жоқ', noOffers: 'Тапсырыс жоқ', save: 'Сақтау', submit: 'Жіберу', updatedSuccessfully: 'Өзгерістер сақталды', operationFailed: 'Әрекет орындалмады',
    driversSeen: 'Тапсырысты көрген жүргізушілер', raisePrice: 'Бағаны көтеру', raisePriceHint: 'Бос жүргізуші аз немесе баға төмен.', searchStarted: 'Жүргізушіні іздеу жалғасады.', tripDistance: 'Маршрут қашықтығы', distance: 'Қашықтық', eta: 'Келу уақыты',
    driverOnline: 'Жүргізуші online', driverRegister: 'Жүргізуші тіркеуі', paymentMethods: 'Реквизиттер', account: 'Аккаунт', donate: 'Жобаны қолдау',
  },
  en: {
    appName: 'Intaxi', home: 'Home', profile: 'Profile', city: 'City', intercity: 'Intercity', wallet: 'Balance', support: 'Support', admin: 'Admin', back: 'Back', country: 'Country', region: 'Region', cityField: 'City / district', chooseRegion: 'Choose region', chooseCity: 'Choose city / district',
    createOrder: 'Create order', myOrders: 'My orders', availableOffers: 'Available orders', currentTrip: 'Current trip', passengerMode: 'Passenger mode', driverMode: 'Driver mode',
    fromAddress: 'Pickup address', toAddress: 'Destination address', seats: 'Seats', price: 'Price', yourPrice: 'Your price', recommendedPrice: 'Recommended price', useRecommendedPrice: 'Use recommended price', comment: 'Comment', writeComment: 'Additional information',
    status: 'Status', loading: 'Loading...', noData: 'No data yet', noOrders: 'No orders found', noOffers: 'No orders found', save: 'Save', submit: 'Submit', updatedSuccessfully: 'Changes saved', operationFailed: 'Action failed',
    driversSeen: 'Drivers who saw the order', raisePrice: 'Increase price', raisePriceHint: 'Few drivers are free or current price is low.', searchStarted: 'Driver search is running.', tripDistance: 'Route distance', distance: 'Distance', eta: 'ETA',
    driverOnline: 'Driver online', driverRegister: 'Driver registration', paymentMethods: 'Payment methods', account: 'Account', donate: 'Support project',
  },
};

export function normalizeLanguage(value?: string | null): AppLanguage {
  return value === 'uz' || value === 'kz' || value === 'en' ? value : 'ru';
}

export function t(lang: string | undefined | null, key: string): string {
  const normalized = normalizeLanguage(lang);
  return messages[normalized][key] || messages.ru[key] || key;
}
