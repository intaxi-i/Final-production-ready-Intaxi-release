from __future__ import annotations

from aiogram.utils.keyboard import InlineKeyboardBuilder

REGIONS = {
    "astana_city": {"ru": "Астана", "uz": "Astana", "en": "Astana", "ar": "أستانا", "localities": {"ru": ["Астана", "Алматы", "Байконыр", "Есиль", "Нура", "Сарыарка"], "uz": ["Astana", "Almaty", "Baykonyr", "Esil", "Nura", "Saryarqa"], "en": ["Astana", "Almaty", "Baikonyr", "Esil", "Nura", "Saryarka"], "ar": ["أستانا", "ألماتي", "بايكونير", "إسيل", "نورا", "سارياركا"]}},
    "almaty_city": {"ru": "Алматы", "uz": "Almaty", "en": "Almaty", "ar": "ألماتي", "localities": {"ru": ["Алматы", "Алатау", "Алмалы", "Ауэзовский", "Бостандыкский", "Медеуский", "Наурызбайский", "Турксибский", "Жетысуский"], "uz": ["Almaty", "Alatau", "Almaly", "Auezov", "Bostandyk", "Medeu", "Nauryzbay", "Turksib", "Zhetysu"], "en": ["Almaty", "Alatau", "Almaly", "Auezov", "Bostandyk", "Medeu", "Nauryzbay", "Turksib", "Zhetysu"], "ar": ["ألماتي", "ألاتاو", "ألمالي", "أويزوف", "بوستانديك", "ميديو", "ناوريزباي", "توركسيب", "جيتيسو"]}},
    "shymkent_city": {"ru": "Шымкент", "uz": "Shymkent", "en": "Shymkent", "ar": "شيمكنت", "localities": {"ru": ["Шымкент", "Абайский", "Аль-Фарабийский", "Енбекшинский", "Каратауский", "Наурыз"], "uz": ["Shymkent", "Abay", "Al-Farabi", "Enbekshi", "Karatau", "Nauryz"], "en": ["Shymkent", "Abay", "Al-Farabi", "Enbekshi", "Karatau", "Nauryz"], "ar": ["شيمكنت", "أباي", "الفارابي", "ينبكشي", "كارا تاو", "ناوريز"]}},
    "akmola": {"ru": "Акмолинская область", "uz": "Aqmola viloyati", "en": "Akmola Region", "ar": "منطقة أكمولا", "localities": {"ru": ["Кокшетау", "Косшы", "Степногорск", "Акколь", "Атбасар", "Бурабай", "Ерейментау", "Зеренда"], "uz": ["Kokshetau", "Kosshy", "Stepnogorsk", "Akkol", "Atbasar", "Burabay", "Ereymentau", "Zerendi"], "en": ["Kokshetau", "Kosshy", "Stepnogorsk", "Akkol", "Atbasar", "Burabay", "Ereymentau", "Zerendi"], "ar": ["كوكشيتاو", "كوشي", "ستيبنوغورسك", "أككول", "أتباسار", "بوراباي", "يريمينتاو", "زيريندي"]}},
    "aktobe": {"ru": "Актюбинская область", "uz": "Aqtobe viloyati", "en": "Aktobe Region", "ar": "منطقة أكتوبه", "localities": {"ru": ["Актобе", "Хромтау", "Шалкар", "Кандыагаш", "Эмба", "Алга", "Айтеке би", "Мугалжар"], "uz": ["Aktobe", "Khromtau", "Shalkar", "Kandyagash", "Embi", "Alga", "Aitekebi", "Mugalzhar"], "en": ["Aktobe", "Khromtau", "Shalkar", "Kandyagash", "Embi", "Alga", "Aitekebi", "Mugalzhar"], "ar": ["أكتوبه", "خرومتاو", "شالكار", "كاندياكاش", "إمبي", "ألغا", "آيتيكي بي", "موغالجار"]}},
    "almaty_region": {"ru": "Алматинская область", "uz": "Almaty viloyati", "en": "Almaty Region", "ar": "منطقة ألماتي", "localities": {"ru": ["Конаев", "Талгар", "Каскелен", "Есик", "Шелек", "Ушконыр", "Жаркент"], "uz": ["Konaev", "Talgar", "Kaskelen", "Esik", "Shelek", "Ushkonyr", "Zharkent"], "en": ["Konaev", "Talgar", "Kaskelen", "Esik", "Shelek", "Ushkonyr", "Zharkent"], "ar": ["قوناييف", "تالغار", "كاسكيلين", "إيسيك", "شيليك", "أوشكونير", "جاركنت"]}},
    "atyrau": {"ru": "Атырауская область", "uz": "Atyrau viloyati", "en": "Atyrau Region", "ar": "منطقة أتيراو", "localities": {"ru": ["Атырау", "Кульсары", "Аккистау", "Махамбет", "Доссор", "Индербор"], "uz": ["Atyrau", "Kulsary", "Akkistau", "Makhambet", "Dossor", "Inderbor"], "en": ["Atyrau", "Kulsary", "Akkistau", "Makhambet", "Dossor", "Inderbor"], "ar": ["أتيراو", "كولساري", "أكيستاو", "مخامبيت", "دوسور", "إندربور"]}},
    "abay": {"ru": "Абайская область", "uz": "Abay viloyati", "en": "Abay Region", "ar": "منطقة أباي", "localities": {"ru": ["Семей", "Аягоз", "Курчатов", "Маканчи", "Аксуат", "Бородулиха", "Жарма", "Урджар"], "uz": ["Semey", "Ayagoz", "Kurchatov", "Makanchi", "Aksuat", "Borodulikha", "Zharma", "Urdzhar"], "en": ["Semey", "Ayagoz", "Kurchatov", "Makanchi", "Aksuat", "Borodulikha", "Zharma", "Urdzhar"], "ar": ["سيمي", "أياكوز", "كورشاتوف", "ماكانشي", "أكسوات", "بورودوليخا", "جارما", "أوردجار"]}},
    "karaganda": {"ru": "Карагандинская область", "uz": "Qarag‘anda viloyati", "en": "Karaganda Region", "ar": "منطقة كاراغاندا", "localities": {"ru": ["Караганда", "Темиртау", "Балхаш", "Сарань", "Шахтинск", "Абай", "Каркаралы", "Осакаровка"], "uz": ["Karaganda", "Temirtau", "Balkhash", "Saran", "Shakhtinsk", "Abai", "Karkaraly", "Osakarovka"], "en": ["Karaganda", "Temirtau", "Balkhash", "Saran", "Shakhtinsk", "Abai", "Karkaraly", "Osakarovka"], "ar": ["كاراغاندا", "تميرتاو", "بالخاش", "ساران", "شاختينسك", "أباي", "كاركارالي", "أوساكاروفكا"]}},
    "kostanay": {"ru": "Костанайская область", "uz": "Qostanay viloyati", "en": "Kostanay Region", "ar": "منطقة كوستاناي", "localities": {"ru": ["Костанай", "Рудный", "Лисаковск", "Тобыл", "Аркалык", "Житикара", "Аулиеколь"], "uz": ["Kostanay", "Rudny", "Lisakovsk", "Tobyl", "Arkalyk", "Zhitiqara", "Auliekol"], "en": ["Kostanay", "Rudny", "Lisakovsk", "Tobyl", "Arkalyk", "Zhitiqara", "Auliekol"], "ar": ["كوستاناي", "رودني", "ليساكوفسك", "توبيل", "أركاليك", "جيتيكارا", "أوليكول"]}},
    "mangystau": {"ru": "Мангистауская область", "uz": "Mang‘ystau viloyati", "en": "Mangystau Region", "ar": "منطقة مانغيستاو", "localities": {"ru": ["Актау", "Жанаозен", "Форт-Шевченко", "Бейнеу", "Курык", "Мунайлы"], "uz": ["Aktau", "Zhanaozen", "Fort-Shevchenko", "Beyneu", "Kuryk", "Munaily"], "en": ["Aktau", "Zhanaozen", "Fort-Shevchenko", "Beyneu", "Kuryk", "Munaily"], "ar": ["أكتاو", "جاناوزين", "فورت شيفتشينكو", "بينيو", "كوريك", "مونايلي"]}},
    "pavlodar": {"ru": "Павлодарская область", "uz": "Pavlodar viloyati", "en": "Pavlodar Region", "ar": "منطقة بافلودار", "localities": {"ru": ["Павлодар", "Экибастуз", "Аксу", "Щербакты", "Иртышск", "Баянаул"], "uz": ["Pavlodar", "Ekibastuz", "Aksu", "Shcherbakty", "Irtyshsk", "Bayanaul"], "en": ["Pavlodar", "Ekibastuz", "Aksu", "Shcherbakty", "Irtyshsk", "Bayanaul"], "ar": ["بافلودار", "إيكيباستوز", "أكسو", "شيرباكتي", "إرتيشسك", "باياناول"]}},
    "turkistan": {"ru": "Туркестанская область", "uz": "Turkiston viloyati", "en": "Turkistan Region", "ar": "منطقة تركستان", "localities": {"ru": ["Туркестан", "Кентау", "Арыс", "Сарыагаш", "Жетысай", "Шардара", "Ленгер", "Келес"], "uz": ["Turkistan", "Kentau", "Arys", "Saryagash", "Zhetysai", "Shardara", "Lenger", "Keles"], "en": ["Turkistan", "Kentau", "Arys", "Saryagash", "Zhetysai", "Shardara", "Lenger", "Keles"], "ar": ["تركستان", "كينتاو", "أريس", "سارياغاش", "جيتيساي", "شاردارا", "لينغير", "كيليس"]}},
}


def _lang(lang: str) -> str:
    return lang if lang in {"ru", "uz", "en", "ar"} else "ru"


def region_items(lang: str):
    code = _lang(lang)
    return [(key, value[code]) for key, value in REGIONS.items()]


def build_regions_keyboard(lang: str, prefix: str = "kzregion_"):
    builder = InlineKeyboardBuilder()
    for key, label in region_items(lang):
        builder.button(text=label, callback_data=f"{prefix}{key}")
    return builder.adjust(1)


def build_localities_keyboard(region_key: str, lang: str, prefix: str = "kzcity_"):
    builder = InlineKeyboardBuilder()
    region = REGIONS.get(region_key)
    if not region:
        return builder
    labels = region["localities"][_lang(lang)]
    for idx, label in enumerate(labels):
        builder.button(text=label, callback_data=f"{prefix}{region_key}:{idx}")
    return builder.adjust(2)


def get_locality_by_index(region_key: str, lang: str, idx: int) -> str:
    region = REGIONS.get(region_key)
    labels = (region or {}).get("localities", {}).get(_lang(lang), [])
    if idx < 0 or idx >= len(labels):
        return ""
    return labels[idx]


def format_kz_location(region_key: str, locality: str, lang: str) -> str:
    region = REGIONS.get(region_key)
    region_name = (region or {}).get(_lang(lang), region_key)
    if locality:
        return f"{region_name} / {locality}"
    return region_name
