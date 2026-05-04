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
    intercityLabel: "Межгород", international: "Международный", passportAlert: "Проверьте наличие загранпаспорта"
  },
  uz: {
    appName: 'Intaxi', home: 'Bosh sahifa', profile: 'Profil', city: 'Shahar', intercity: 'Shaharlararo', wallet: 'Balans', support: 'Yordam', admin: 'Admin', back: 'Orqaga', country: 'Davlat', region: 'Viloyat / hudud', cityField: 'Shahar / tuman', chooseRegion: 'Viloyatni tanlang', chooseCity: 'Shahar / tumanni tanlang',
    createOrder: 'Buyurtma yaratish', myOrders: 'Mening buyurtmalarim', availableOffers: 'Mavjud buyurtmalar', currentTrip: 'Joriy safar', passengerMode: 'Yo‘lovchi rejimi', driverMode: 'Haydovchi rejimi',
    fromAddress: 'Qayerdan manzil', toAddress: 'Qayerga manzil', seats: 'Joylar', price: 'Narx', yourPrice: 'Sizning narxingiz', recommendedPrice: 'Tavsiya narx', useRecommendedPrice: 'Tavsiya narxni qo‘yish', comment: 'Izoh', writeComment: 'Qo‘shimcha ma’lumot',
    status: 'Holat', loading: 'Yuklanmoqda...', noData: 'Hozircha ma’lumot yo‘q', noOrders: 'Buyurtma topilmadi', noOffers: 'Buyurtma topilmadi', save: 'Saqlash', submit: 'Yuborish', updatedSuccessfully: 'O‘zgarishlar saqlandi', operationFailed: 'Amal bajarilmadi',
    driversSeen: 'Buyurtmani ko‘rgan haydovchilar', raisePrice: 'Narxni oshirish', raisePriceHint: 'Bo‘sh hayдovchilar kam yoki narx past.', searchStarted: 'Haydovchi qidirish davom etmoqda.', tripDistance: 'Yo‘l masofasi', distance: 'Masofa', eta: 'Yetib kelish',
    driverOnline: 'Haydovchi online', driverRegister: 'Haydovchi ro‘yxati', paymentMethods: 'Rekvizitlar', account: 'Akkaunt', donate: 'Loyihani qo‘llab-quvvatlash',
    intercityLabel: "Shaharlararo", international: "Xalqaro", passportAlert: "Xalqaro safarlar uchun pasportni tekshiring"
  },
  kz: {
    appName: 'Intaxi', home: 'Басты бет', profile: 'Профиль', city: 'Қала', intercity: 'Қалааралық', wallet: 'Баланс', support: 'Қолдау', admin: 'Админ', back: 'Артқа', country: 'Ел', region: 'Облыс / өңір', cityField: 'Қала / аудан', chooseRegion: 'Облысты таңдаңыз', chooseCity: 'Қала / ауданды таңдаңыз',
    createOrder: 'Тапсырыс құру', myOrders: 'Менің тапсырыстарым', availableOffers: 'Қолжетімді тапсырыстар', currentTrip: 'Ағымдағы сапар', passengerMode: 'Жолаушы режимі', driverMode: 'Жүргізуші режимі',
    fromAddress: 'Қайдан мекенжай', toAddress: 'Қайда мекенжай', seats: 'Орындар', price: 'Баға', yourPrice: 'Сіздің бағаңыз', recommendedPrice: 'Ұсынылған баға', useRecommendedPrice: 'Ұсынылған бағаны қою', comment: 'Түсініктеме', writeComment: 'Қосымша ақпарат',
    status: 'Күйі', loading: 'Жүктелуде...', noData: 'Әзірге мәлімет жоқ', noOrders: 'Тапсырыс жоқ', noOffers: 'Тапсырыс жоқ', save: 'Сақтау', submit: 'Жіберу', updatedSuccessfully: 'Өзгерістер сақталды', operationFailed: 'Әрекет орындалмады',
    driversSeen: 'Тапсырысты көрген жүргізушілер', raisePrice: 'Бағаны көтеру', raisePriceHint: 'Бос жүргізуші аз немесе баға төмен.', searchStarted: 'Жүргізушіні іздеу жалғасады.', tripDistance: 'Маршрут қашықтығы', distance: 'Қашықтық', eta: 'Келу уақыты',
    driverOnline: 'Жүргізуші online', driverRegister: 'Жүргізуші тіркеуі', paymentMethods: 'Реквизиттер', account: 'Аккаунт', donate: 'Жобаны қолдау',
    intercityLabel: "Қалааралық", international: "Халықаралық", passportAlert: "Халықаралық сапарлар үшін төлқұжатты тексеріңіз"
  },
  en: {
    appName: 'Intaxi', home: 'Home', profile: 'Profile', city: 'City', intercity: 'Intercity', wallet: 'Balance', support: 'Support', admin: 'Admin', back: 'Back', country: 'Country', region: 'Region', cityField: 'City / district', chooseRegion: 'Choose region', chooseCity: 'Choose city / district',
    createOrder: 'Create order', myOrders: 'My orders', availableOffers: 'Available orders', currentTrip: 'Current trip', passengerMode: 'Passenger mode', driverMode: 'Driver mode',
    fromAddress: 'Pickup address', toAddress: 'Destination address', seats: 'Seats', price: 'Price', yourPrice: 'Your price', recommendedPrice: 'Recommended price', useRecommendedPrice: 'Use recommended price', comment: 'Comment', writeComment: 'Additional information',
    status: 'Status', loading: 'Loading...', noData: 'No data yet', noOrders: 'No orders found', noOffers: 'No orders found', save: 'Save', submit: 'Submit', updatedSuccessfully: 'Changes saved', operationFailed: 'Action failed',
    driversSeen: 'Drivers who saw the order', raisePrice: 'Increase price', raisePriceHint: 'Few drivers are free or current price is low.', searchStarted: 'Driver search is running.', tripDistance: 'Route distance', distance: 'Distance', eta: 'ETA',
    driverOnline: 'Driver online', driverRegister: 'Driver registration', paymentMethods: 'Payment methods', account: 'Account', donate: 'Support project',
    intercityLabel: "Intercity", international: "International", passportAlert: "Check international travel documents"
  },
  ar: {
    appName: 'Intaxi', home: 'الرئيسية', profile: 'الملف الشخصي', city: 'المدينة', intercity: 'بين المدن', wallet: 'الرصيد', support: 'الدعم', admin: 'مسؤول', back: 'رجوع', country: 'الدولة', region: 'المنطقة', cityField: 'المدينة / الحي', chooseRegion: 'اختر المنطقة', chooseCity: 'اختر المدينة',
    createOrder: 'إنشاء طلب', myOrders: 'طلباتي', availableOffers: 'الطلبات المتاحة', currentTrip: 'الرحلة الحالية', passengerMode: 'وضع الراكب', driverMode: 'وضع السائق',
    fromAddress: 'عنوان الانطلاق', toAddress: 'عنوان الوصول', seats: 'مقاعد', price: 'السعر', yourPrice: 'سعرك', recommendedPrice: 'السعر المقترح', useRecommendedPrice: 'استخدام السعر المقترح', comment: 'تعليق', writeComment: 'معلومات إضافية',
    status: 'الحالة', loading: 'جاري التحميل...', noData: 'لا توجد بيانات', noOrders: 'لا توجد طلبات', noOffers: 'لا توجد طلبات', save: 'حفظ', submit: 'إرسال', updatedSuccessfully: 'تم الحفظ', operationFailed: 'فشلت العملية',
    driversSeen: 'السائقون الذين شاهدوا الطلب', raisePrice: 'رفع السعر', raisePriceHint: 'السائقون قليلون حالياً', searchStarted: 'جاري البحث عن سائق', tripDistance: 'مسافة الرحلة', distance: 'المسافة', eta: 'وقت الوصول',
    driverOnline: 'سائق متاح', driverRegister: 'تسجيل السائق', paymentMethods: 'طرق الدفع', account: 'الحساب', donate: 'دعم المشروع',
    intercityLabel: "بين المدن", international: "دولي", passportAlert: "تأكد من وجود جواز السفر للمواد الدولية", dir: "rtl", currency: "SAR"
  },
  tr: {
    appName: 'Intaxi', home: 'Ana Sayfa', profile: 'Profil', city: 'Şehir', intercity: 'Şehirlerarası', wallet: 'Cüzdan', support: 'Destek', admin: 'Admin', back: 'Geri', country: 'Ülke', region: 'Bölge', cityField: 'Şehir / İlçe', chooseRegion: 'Bölge Seç', chooseCity: 'Şehir Seç',
    createOrder: 'Sipariş Oluştur', myOrders: 'Siparişlerim', availableOffers: 'Mevcut Siparişler', currentTrip: 'Mevcut Yolculuk', passengerMode: 'Yolcu Modu', driverMode: 'Sürücü Modu',
    fromAddress: 'Kalkış Adresi', toAddress: 'Varış Adresi', seats: 'Koltuk', price: 'Fiyat', yourPrice: 'Sizin Fiyatınız', recommendedPrice: 'Önerilen Fiyat', useRecommendedPrice: 'Önerilen Fiyatı Kullan', comment: 'Yorum', writeComment: 'Ek Bilgi',
    status: 'Durum', loading: 'Yükleniyor...', noData: 'Veri yok', noOrders: 'Sipariş bulunamadı', noOffers: 'Sipariş bulunamadı', save: 'Kaydet', submit: 'Gönder', updatedSuccessfully: 'Kaydedildi', operationFailed: 'İşlem başarısız',
    driversSeen: 'Siparişi gören sürücüler', raisePrice: 'Fiyatı Artır', raisePriceHint: 'Sürücü az veya fiyat düşük', searchStarted: 'Sürücü aranıyor', tripDistance: 'Rota mesafesi', distance: 'Mesafe', eta: 'Varış süresi',
    driverOnline: 'Sürücü çevrimiçi', driverRegister: 'Sürücü kaydı', paymentMethods: 'Ödeme yöntemleri', account: 'Hesap', donate: 'Projeyi destekle',
    intercityLabel: "Şehirlerarası", international: "Uluslararası", passportAlert: "Uluslararası yolculuk için pasaportu kontrol edin"
  }
};

export function normalizeLanguage(value?: string | null): AppLanguage {
  const v = value?.toLowerCase();
  if (v === 'uz' || v === 'kz' || v === 'en' || v === 'ar' || v === 'tr') return v as AppLanguage;
  return 'ru';
}

export function t(lang: string | undefined | null, key: string): string {
  const normalized = normalizeLanguage(lang);
  return messages[normalized][key] || messages.ru[key] || key;
}