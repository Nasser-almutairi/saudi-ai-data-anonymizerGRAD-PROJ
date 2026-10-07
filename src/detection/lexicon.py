# -*- coding: utf-8 -*-
"""
Saudi / Arabic lexicons and column-name keywords used for CONTEXT-AWARE detection.

Context-aware = the system looks at the column header (and the words next to a value
inside free text) to decide how confident it should be.
"""
import re

# ---------------------------------------------------------------- normalisation
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def normalize_digits(s: str) -> str:
    """Arabic-Indic digits (٠١٢...) -> ASCII digits. Length is preserved so spans stay valid."""
    return s.translate(_AR_DIGITS)


def normalize_ar(s: str) -> str:
    """Light Arabic normalisation: remove diacritics/tatweel, unify alef/yaa/taa-marbuta, lowercase."""
    s = re.sub(r"[\u064B-\u0652\u0640]", "", s)
    s = re.sub("[إأآٱ]", "ا", s)
    s = s.replace("ى", "ي").replace("ة", "ه")
    return s.strip().lower()


def tokens(s: str):
    """Split a column name / phrase into normalised tokens (underscores & punctuation are separators)."""
    return [t for t in re.split(r"[\W_]+", normalize_ar(str(s))) if t]


# ---------------------------------------------------------------- name lexicons
AR_FIRST_NAMES = """محمد أحمد عبدالله عبدالرحمن عبدالعزيز خالد فهد سعود سلطان نايف تركي ماجد فيصل عمر ياسر بندر ناصر
سلمان سعد إبراهيم يوسف علي حسن صالح راشد مشعل بدر عادل وليد نورة سارة فاطمة ريم هند لينا مها العنود أمل منى هدى
ريما شهد لمى جود مريم عائشة خديجة اللولوة""".split()

AR_FAMILY_NAMES = """القحطاني العتيبي الدوسري الشمري الغامدي الزهراني الحربي المطيري السبيعي العنزي الشهري البقمي
الأحمدي الرشيدي التميمي الخالدي السالم العمري الحازمي الجهني البلوي الثقفي الشريف العسيري المالكي""".split()

EN_FIRST_NAMES = """mohammed muhammad ahmed ahmad abdullah abdulrahman abdulaziz khalid fahad saud sultan naif turki majed
faisal omar yasser bandar nasser salman saad ibrahim yousef youssef ali hassan saleh rashed mishaal badr adel waleed
noura sara sarah fatimah fatima reem hind lina maha alanoud amal mona huda rima shahd lama jood maryam aisha
khadijah""".split()

EN_FAMILY_NAMES = """qahtani otaibi dossari shammari ghamdi zahrani harbi mutairi subaie anazi shehri buqami ahmadi
rashidi tamimi khalidi salem omari hazmi juhani balawi thaqafi sharif asiri maliki""".split()

NAME_PARTICLES = {"بن", "ابن", "آل", "ابو", "أبو", "bin", "ibn", "abu", "abo", "bint", "بنت"}

_AR_FIRST_N = {normalize_ar(x) for x in AR_FIRST_NAMES}
_AR_FAMILY_N = {normalize_ar(x) for x in AR_FAMILY_NAMES}
_AR_FAMILY_NOAL = {x[2:] if x.startswith("ال") else x for x in _AR_FAMILY_N}
_EN_FIRST_N = set(EN_FIRST_NAMES)
_EN_FAMILY_N = set(EN_FAMILY_NAMES)
_PARTICLES_N = {normalize_ar(p) for p in NAME_PARTICLES}

# Faker pools used by the "Replacement (format-preserving)" mode
FAKE_AR_FIRST = ["سلمان", "ريان", "هشام", "طلال", "زياد", "مازن", "رغد", "جنى", "ديما", "رزان", "لجين", "تالا"]
FAKE_AR_FAMILY = ["الحمدان", "العبدلي", "الفيفي", "الربيعي", "النجدي", "الصاعدي", "الوادعي", "الحارثي"]
FAKE_EN_FIRST = ["Salman", "Rayan", "Hisham", "Talal", "Ziyad", "Mazen", "Raghad", "Jana", "Dima", "Razan", "Lujain", "Tala"]
FAKE_EN_FAMILY = ["Al-Hamdan", "Al-Abdali", "Al-Faifi", "Al-Rabiei", "Al-Najdi", "Al-Saidi", "Al-Wadei", "Al-Harthi"]


def name_score(value: str):
    """
    Returns (shape_ok, lexicon_hit, is_arabic) for one cell.
    shape_ok   : looks like a 2-5 word personal name (letters only, no digits/@)
    lexicon_hit: at least one word is a known Saudi first/family name or a name particle (bin / آل ...)
    """
    v = str(value).strip()
    if not v or re.search(r"[\d@/\\:_]", v):
        return False, False, False
    toks = [t for t in re.split(r"[\s\-]+", v) if t]
    if not 2 <= len(toks) <= 5 or not all(re.fullmatch(r"[^\W\d_]+", t) for t in toks):
        return False, False, False
    is_ar = bool(re.search(r"[\u0600-\u06FF]", v))
    hit = False
    for t in toks:
        n = normalize_ar(t)
        n_noal = n[2:] if n.startswith("ال") else n
        if (n in _AR_FIRST_N or n in _AR_FAMILY_N or n_noal in _AR_FAMILY_NOAL
                or n in _EN_FIRST_N or n in _EN_FAMILY_N or n in _PARTICLES_N):
            hit = True
    return True, hit, is_ar


# ---------------------------------------------------------------- places
SAUDI_CITIES_EN = ["riyadh", "jeddah", "dammam", "al kharj", "abha", "makkah", "mecca", "madinah", "medina", "khobar",
                   "dhahran", "tabuk", "buraidah", "hail", "taif", "jazan", "najran", "yanbu", "jubail", "al ahsa"]
SAUDI_CITIES_AR = ["الرياض", "جدة", "الدمام", "الخرج", "أبها", "مكة", "المدينة", "الخبر", "الظهران", "تبوك", "بريدة",
                   "حائل", "الطائف", "جازان", "نجران", "ينبع", "الجبيل", "الأحساء"]
SAUDI_CITIES = {normalize_ar(c) for c in SAUDI_CITIES_EN + SAUDI_CITIES_AR}

# Used by Generalization of the CITY column (city -> region)
CITY_TO_REGION = {
    "riyadh": "Central Region", "al kharj": "Central Region", "buraidah": "Central Region",
    "jeddah": "Western Region", "makkah": "Western Region", "mecca": "Western Region", "madinah": "Western Region",
    "medina": "Western Region", "taif": "Western Region", "yanbu": "Western Region",
    "dammam": "Eastern Region", "khobar": "Eastern Region", "dhahran": "Eastern Region", "jubail": "Eastern Region",
    "al ahsa": "Eastern Region",
    "abha": "Southern Region", "jazan": "Southern Region", "najran": "Southern Region",
    "tabuk": "Northern Region", "hail": "Northern Region",
    normalize_ar("الرياض"): "Central Region", normalize_ar("الخرج"): "Central Region",
    normalize_ar("جدة"): "Western Region", normalize_ar("الدمام"): "Eastern Region",
    normalize_ar("أبها"): "Southern Region",
}

ADDRESS_KEYWORDS = ["حي", "شارع", "طريق", "ص.ب", "مبنى", "رقم المبنى", "الرمز البريدي", "تقاطع",
                    "street", "st.", "road", "rd.", "district", "building", "p.o. box", "po box", "avenue", "postal code"]

# ---------------------------------------------------------------- column-name hints (Arabic + English)
# Matching is token-based, so "tel" does not fire on "hotel".
COLUMN_HINTS = {
    "SAUDI_NATIONAL_ID": ["national id", "nationalid", "national id number", "iqama", "iqama number", "id number",
                          "identity number", "nid", "رقم الهوية", "الهوية", "هوية", "رقم الإقامة", "الإقامة",
                          "رقم الهويه", "رقم الاقامة", "السجل المدني"],
    "SAUDI_MOBILE": ["mobile", "mobile number", "phone", "phone number", "tel", "telephone", "cell", "whatsapp",
                     "جوال", "الجوال", "رقم الجوال", "هاتف", "الهاتف", "رقم الهاتف", "موبايل", "واتساب"],
    "SAUDI_IBAN": ["iban", "bank account", "account number", "account no", "acct", "الآيبان", "الايبان", "ايبان", "آيبان",
                   "رقم الحساب", "الحساب البنكي", "حساب بنكي"],
    "EMAIL_ADDRESS": ["email", "e mail", "mail", "email address", "البريد الإلكتروني", "البريد", "بريد", "ايميل", "الايميل"],
    "PERSON_NAME": ["name", "full name", "customer name", "client name", "employee name", "firstname", "first name",
                    "last name", "surname", "الاسم", "اسم", "اسم العميل", "اسم الموظف", "الاسم الكامل", "اسم المريض"],
    "SAUDI_ADDRESS": ["address", "home address", "street address", "location", "العنوان", "عنوان", "عنوان السكن", "الموقع", "شارع"],
    "CUSTOMER_ID": ["customer id", "cust id", "client id", "user id", "member id", "patient id", "employee id",
                    "customerid", "معرف العميل", "رقم العميل", "رقم الموظف", "رقم المريض"],
    # indirect identifiers (quasi-identifiers)
    "AGE": ["age", "العمر", "عمر"],
    "DATE_OF_BIRTH": ["dob", "birth", "birthdate", "date of birth", "birth date", "تاريخ الميلاد", "الميلاد", "ميلاد"],
    "CITY": ["city", "town", "المدينة", "مدينة"],
    "DISTRICT": ["district", "neighborhood", "neighbourhood", "area", "الحي", "حي", "المنطقة"],
    "GENDER": ["gender", "sex", "الجنس", "جنس", "النوع"],
    "JOB_TITLE": ["job", "job title", "occupation", "profession", "position", "title", "الوظيفة", "وظيفة", "المهنة", "مهنة", "المسمى الوظيفي"],
    "SALARY": ["salary", "income", "wage", "pay", "monthly salary", "الراتب", "راتب", "الدخل", "دخل"],
    "NATIONALITY": ["nationality", "الجنسية", "جنسية"],
}

# Words that, when found NEXT TO a value inside free text, boost confidence.
TEXT_CONTEXT = {
    "SAUDI_NATIONAL_ID": ["رقم الهوية", "الهوية", "رقم الإقامة", "الإقامة", "هوية", "national id", "iqama", "identity", "id number", "id:"],
    "SAUDI_MOBILE": ["الجوال", "جوال", "رقم الجوال", "موبايل", "هاتف", "اتصال", "واتساب", "mobile", "phone", "tel", "call", "whatsapp"],
    "SAUDI_IBAN": ["iban", "الآيبان", "الايبان", "ايبان", "رقم الحساب", "الحساب", "account"],
    "EMAIL_ADDRESS": ["email", "e-mail", "mail", "البريد", "بريد", "ايميل"],
}


def column_hint(colname: str, entity: str):
    """Return the keyword that matched the column name (or None). Token-sequence matching."""
    ctoks = tokens(colname)
    joined = "".join(ctoks)
    for kw in COLUMN_HINTS.get(entity, []):
        ktoks = tokens(kw)
        if not ktoks:
            continue
        n = len(ktoks)
        for i in range(len(ctoks) - n + 1):
            if ctoks[i:i + n] == ktoks:
                return kw
        # compact forms like "nationalid" / "customerid"
        if len("".join(ktoks)) >= 6 and "".join(ktoks) == joined:
            return kw
    return None


def context_near(text: str, start: int, end: int, entity: str, window: int = 30):
    """Look for a context keyword in the `window` characters BEFORE the value (and 8 after)."""
    seg = normalize_ar(text[max(0, start - window):start] + " " + text[end:end + 8])
    for kw in TEXT_CONTEXT.get(entity, []):
        if normalize_ar(kw) in seg:
            return kw
    return None
