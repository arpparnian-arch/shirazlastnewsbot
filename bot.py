import os
import io
import re
import sys
import time
import json
import math
import random
import hashlib
import datetime
import urllib.parse
from datetime import timezone, timedelta

import requests
import urllib3
import feedparser
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

try:
    import telebot
    from telebot import types
except Exception:
    telebot = None

try:
    from instagrapi import Client as InstaClient
except Exception:
    InstaClient = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================================================================
# ۱. تنظیمات امنیتی و خواندن اطلاعات حساس از GitHub Secrets
# ==============================================================================
import os
TOKEN = os.environ.get("BOT_TOKEN", "").strip()
BOT_USERNAME = "shirazlastnews_bot"
ADMIN_ID = "30956754"
INSTA_USER = os.environ.get("INSTA_USER", "shirazlastnews").strip()
INSTA_PASS = os.environ.get("INSTA_PASS", "").strip()
TARGET_CHAT = "@shirazlastnews"
CHANNEL_SIGN = "@shirazlastnews"
CHANNEL_LINK = "https://t.me/shirazlastnews"


IRAN_TZ = timezone(timedelta(hours=3, minutes=30))

# ==============================================================================
# ۲. مسیر فایل‌های حافظه و کش (کاملاً منطبق با main.yml)
# ==============================================================================
DB_FILE = 'sent_links.txt'
TITLES_DB_FILE = 'sent_titles_hash.txt'
INSTA_TITLES_DB_FILE = 'insta_titles_hash.txt'
DAILY_FILE = 'daily_report.txt'
NIGHT_FILE = 'night_report_v8.txt'
MATCHES_FILE = 'matches_story_date.txt'
DAILY_MATCHES_STORY_CACHE = 'daily_matches_story_cache.jpg'
LIVE_IRAN_STATE_FILE = 'live_iran_league_state.json'
LAST_SPORT_STORY_FILE = 'last_sport_story.jpg'
LAST_SPORT_META_FILE = 'last_sport_meta.json'
TOURISM_STATE_FILE = 'tourism_post_state.txt'
TITLES_FILE = 'today_titles.txt'
SERVICE_STATE_FILE = 'service_bot_data.json'
LAST_IMG_FILE = 'last_img_cache.jpg'
INSTA_SESSION = 'insta_session.json'
INSTA_LOG = 'insta_log.txt'
INSTA_REEL_LOG = 'insta_reel_log.txt'
FRAME_FILE = 'frame.png'
FONT_FILE = 'Vazirmatn-Bold.ttf'
STADIUM_BG_CACHE = 'stadium_bg_cache.jpg'
LOGO_CACHE_DIR = 'logos_cache'

os.makedirs('drafts', exist_ok=True)
os.makedirs(LOGO_CACHE_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
}

# ==============================================================================
# ۳. بانک کلمات کلیدی، شهرستان‌های فارس و گردشگری
# ==============================================================================
FARS_37_COUNTIES_UNAMBIGUOUS = [
    'شیراز', 'مرودشت', 'جهرم', 'فسا', 'کازرون', 'داراب', 'فیروزآباد', 'لارستان',
    'آباده', 'نورآباد', 'ممسنی', 'اقلید', 'لامرد', 'استهبان', 'نی‌ریز', 'نی ریز',
    'زرین‌دشت', 'زرین دشت', 'قیر و کارزین', 'فراشبند', 'خنج', 'اوز', 'گراش',
    'خرم‌بید', 'خرم بید', 'بوانات', 'سرچهان', 'ارسنجان', 'پاسارگاد', 'سعادت‌شهر',
    'سپیدان', 'اردکان فارس', 'بیضا', 'زرقان', 'کوار', 'خرامه', 'سروستان',
    'رستم', 'مصیری', 'کوه‌چنار', 'کوه چنار', 'قائمیه', 'بختگان', 'تخت جمشید', 'حافظیه'
]

STOP_WORDS_FA = {
    'در', 'به', 'از', 'با', 'برای', 'تا', 'که', 'این', 'آن', 'را', 'ای', 'ها', 'های', 'هایی',
    'شد', 'شود', 'شده', 'است', 'بود', 'باشند', 'باشد', 'کرد', 'کند', 'کنند', 'کردند', 'داشت', 'دارد',
    'گفت', 'افزود', 'بیان', 'تصریح', 'اعلام', 'گزارش', 'خبر', 'اخبار', 'داد', 'دهد', 'دهند',
    'استان', 'فارس', 'شیراز', 'شهر', 'شهرستان', 'مدیرکل', 'رئیس', 'معاون', 'استاندار', 'فرماندار',
    'امروز', 'دیروز', 'امسال', 'سال', 'ماه', 'روز', 'طی', 'بر', 'روی', 'هم', 'نیز', 'اما', 'یا', 'و'
}

VIRAL_REEL_KEYWORDS = [
    'فوری', 'وایرال', 'ببینید', 'لحظه', 'عجیب', 'باورنکردنی', 'تکان‌دهنده', 'شوکه',
    'تصادف', 'آتش‌سوزی', 'انفجار', 'زلزله', 'سیل', 'طوفان', 'درگیری', 'زورگیری',
    'سرقت', 'پلیس', 'نجات', 'معجزه', 'جنجال', 'حاشیه', 'واکنش', 'طلا', 'دلار',
    'سکه', 'خودرو', 'یارانه', 'کالابرگ', 'تعطیل', 'فوتبال', 'تیم ملی', 'پرسپولیس',
    'استقلال', 'گل ', 'پرتاب', 'موشک', 'رکورد', 'دیدنی', 'جالب', 'قهرمان', 'طلایی'
]

BORING_BUREAUCRATIC_KW = [
    'نشست', 'جلسه', 'همایش', 'کارگروه', 'دیدار با', 'پیام تبریک', 'پیام تسلیت',
    'سخنرانی', 'معارفه', 'تودیع', 'یادواره', 'شورای اداری', 'شورای فرهنگ', 'نماز جمعه'
]

KEYWORDS = ['فارس'] + FARS_37_COUNTIES_UNAMBIGUOUS + [
    'فوری', 'مهم', 'ایران', 'تهران', 'اقتصادی', 'سیاسی', 'ورزش', 'تیم ملی',
    'استقلال', 'پرسپولیس', 'فجر سپاسی', 'رئیس جمهور', 'مجلس', 'دولت', 'ویدیو', 'فیلم', 'ببینید'
]

ALERT_KW = [
    'قطعی برق', 'قطعی آب', 'ترافیک', 'تصادف', 'انسداد', 'مسدود',
    'فوری', 'هشدار', 'آتش‌سوزی', 'اورژانس', 'سیل', 'زلزله'
]

SPORT_KW = [
    'فجر سپاسی', 'فجرسپاسی', 'فجر شهید سپاسی', 'لیگ برتر',
    'پرسپولیس', 'استقلال', 'تیم ملی', 'فوتبال', 'ورزش', 'دربی', 'داربی'
]

TRENDING_UNRELATED_TAGS = [
    '#اکسپلور #وایرال #ترند #ریلز #خبر_فوری #explore #viral #reels',
    '#اکسپلور_اینستاگرام #فوری #ایران #کلیپ #ویدیو #explorepage #trending #fyp'
]

TOURISM_DB = [
    {'name': 'مسجد نصیرالملک (مسجد صورتی)', 'in_shiraz': True, 'img': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Nasir_ol_Molk_Mosque_%2831157941492%29.jpg/1080px-Nasir_ol_Molk_Mosque_%2831157941492%29.jpg', 'desc': 'مسجد نصیرالملک یکی از زیباترین شاهکارهای معماری دوران قاجار در شیراز است که به دلیل استفاده از شیشه‌های رنگی و کاشی‌کاری‌های هفت‌رنگ با طرح گل‌ومرغ، به مسجد صورتی شهرت دارد. رقص نورهای رنگارنگ صبحگاهی بر فرش‌های دستباف شبستان غربی و ستون‌های سنگی مارپیچ آن، فضایی رویایی خلق می‌کند.', 'loc_desc': 'مسجد نصیرالملک در قلب بافت تاریخی شیراز (خیابان لطفعلی‌خان زند، محله گود عربان) قرار دارد.', 'distances': ['مرودشت: ۵۰ کیلومتر (حدود ۵۰ دقیقه)', 'کازرون: ۱۴۰ کیلومتر (حدود ۲ ساعت)', 'جهرم: ۱۸۵ کیلومتر (حدود ۲ ساعت و ۱۵ دقیقه)', 'فسا: ۱۴۵ کیلومتر (حدود ۲ ساعت)']},
    {'name': 'مجموعه جهانی تخت جمشید (پرسپولیس)', 'in_shiraz': False, 'img': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Persepolis_stairs_of_the_Apadana_relief02.JPG/1080px-Persepolis_stairs_of_the_Apadana_relief02.JPG', 'desc': 'تخت جمشید یا پارسه، پایتخت باشکوه تشریفاتی امپراتوری هخامنشیان است که به فرمان داریوش بزرگ بنا نهاده شد. کاخ آپادانا، دروازه ملل، کاخ صدستون و سنگ‌نگاره‌های بی‌نظیر اهدای هدایا توسط نمایندگان ملل باستان، شکوه تمدن و هنر معماری ایران زمین را به رخ جهانیان می‌کشد.', 'loc_desc': 'مجموعه جهانی تخت جمشید در شمال شهرستان مرودشت و در دامنه کوه رحمت واقع شده است.', 'distances': ['شیراز: ۶۰ کیلومتر (حدود ۵۵ دقیقه)', 'مرودشت: ۱۰ کیلومتر (حدود ۱۵ دقیقه)', 'آباده: ۲۲۰ کیلومتر (حدود ۲ ساعت و نیم)', 'پاسارگاد: ۸۰ کیلومتر (حدود ۱ ساعت)']},
    {'name': 'آرامگاه لسان‌الغیب حافظ شیرازی (حافظیه)', 'in_shiraz': True, 'img': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Hafezieh_Shiraz_Iran.jpg/1080px-Hafezieh_Shiraz_Iran.jpg', 'desc': 'حافظیه، میعادگاه عاشقان شعر و ادب پارسی در شمال شهر شیراز است. گنبد مسی کلاه‌فرنگی این بنا که بر هشت ستون سنگی استوار شده، با کاشی‌های معرق فیروزه‌ای و ابیاتی از غزلیات خواجه شمس‌الدین محمد حافظ شیرازی آراسته گشته و در میان باغی پر از درختان نارنج و سرو می‌درخشد.', 'loc_desc': 'آرامگاه حافظ در شهر شیراز، حدفاصل چهارراه ادبیات و دروازه قرآن واقع شده است.', 'distances': ['مرودشت: ۴۵ کیلومتر (حدود ۴۵ دقیقه)', 'کازرون: ۱۴۵ کیلومتر (حدود ۲ ساعت)', 'سپیدان (اردکان): ۸۰ کیلومتر (حدود ۱ ساعت و ربع)', 'جهرم: ۱۹۰ کیلومتر (حدود ۲ ساعت و نیم)']},
    {'name': 'باغ جهانی ارم شیراز', 'in_shiraz': True, 'img': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Eram_Garden_Shiraz.jpg/1080px-Eram_Garden_Shiraz.jpg', 'desc': 'باغ ارم یکی از زیباترین باغ‌های ایرانی ثبت‌شده در میراث جهانی یونسکو است. عمارت سه‌طبقه مرکزی باغ با کاشی‌کاری‌های هلالی دوره‌ی قاجار، حوض بزرگ پیش‌رو، سروهای سر به فلک کشیده (از جمله سرو ناز هزارساله) و باغ گیاه‌شناسی کم‌نظیر، آن را به بهشتی در قلب شیراز تبدیل کرده است.', 'loc_desc': 'باغ ارم در شمال غربی شیراز، خیابان ارم و در مجاورت مجموعه دانشگاه شیراز قرار دارد.', 'distances': ['مرودشت: ۵۰ کیلومتر (حدود ۵۰ دقیقه)', 'کازرون: ۱۳۵ کیلومتر (حدود ۱ ساعت و ۵۰ دقیقه)', 'سپیدان: ۷۵ کیلومتر (حدود ۱ ساعت)', 'فسا: ۱۵۰ کیلومتر (حدود ۲ ساعت)']},
    {'name': 'مجموعه میراث جهانی پاسارگاد', 'in_shiraz': False, 'img': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Pasargadae_tomb_of_Cyrus_II.jpg/1080px-Pasargadae_tomb_of_Cyrus_II.jpg', 'desc': 'پاسارگاد نخستین پایتخت امپراتوری هخامنشی است که به فرمان کوروش بزرگ در دشت مرغاب ساخته شد. آرامگاه سنگی و باصلابت کوروش بزرگ، کاخ بارعام، کاخ اختصاصی و باغ شاهی پاسارگاد، نخستین نمونه مهندسی باغ ایرانی و نماد همزیستی فرهنگ‌ها در دنیای باستان به شمار می‌رود.', 'loc_desc': 'مجموعه جهانی پاسارگاد در شهرستان پاسارگاد (سعادت‌شهر) در مسیر بزرگراه شیراز به اصفهان قرار دارد.', 'distances': ['شیراز: ۱۳۵ کیلومتر (حدود ۱ ساعت و ۴۵ دقیقه)', 'مرودشت: ۸۵ کیلومتر (حدود ۱ ساعت)', 'آباده: ۱۴۵ کیلومتر (حدود ۱ ساعت و نیم)', 'ارسنجان: ۶۵ کیلومتر (حدود ۵۰ دقیقه)']},
    {'name': 'ارگ تاریخی کریمخانی شیراز', 'in_shiraz': True, 'img': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Karim_Khan_Citadel_Shiraz.jpg/1080px-Karim_Khan_Citadel_Shiraz.jpg', 'desc': 'ارگ کریمخانی در مرکز شهر شیراز، محل سکونت و فرمانروایی کریم‌خان زند (وکیل‌الرعایا) بوده است. این بنا با ترکیب معماری نظامی (برج‌های آجری دوازده‌متری و دیوارهای کنگره‌دار) و معماری مسکونی (ایوان‌های شاه‌نشین، حوض‌خانه و باغچه نارنجستان داخلی) جلوه‌ای بی‌همتا دارد.', 'loc_desc': 'ارگ کریمخانی در مرکز شهر شیراز، میدان شهدا (شهرداری) و ابتدای خیابان زند واقع شده است.', 'distances': ['مرودشت: ۴۸ کیلومتر (حدود ۵۰ دقیقه)', 'کازرون: ۱۴۰ کیلومتر (حدود ۲ ساعت)', 'فیروزآباد: ۱۱۵ کیلومتر (حدود ۱ ساعت و ۴۵ دقیقه)', 'سروستان: ۸۵ کیلومتر (حدود ۱ ساعت)']},
    {'name': 'آبشار دیدنی مارگون سپیدان', 'in_shiraz': False, 'img': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Margoon_Waterfall_in_Fars_province.jpg/1080px-Margoon_Waterfall_in_Fars_province.jpg', 'desc': 'آبشار مارگون در شهرستان سپیدان، یکی از بزرگ‌ترین و شگفت‌انگیزترین آبشارهای چشمه‌ای جهان است. در بالای این کوه هیچ رودخانه‌ای وجود ندارد، بلکه هزاران چشمه از دل دیواره صخره‌ای به بیرون می‌جوشند و آبشاری به ارتفاع ۷۰ متر و عرض ۱۰۰ متر را در دل طبیعت سرسبز زاگرس خلق می‌کنند.', 'loc_desc': 'آبشار مارگون در بخش همایجان شهرستان سپیدان و در نزدیکی روستای مارگون قرار دارد.', 'distances': ['شیراز: ۱۳۰ کیلومتر (حدود ۲ ساعت)', 'سپیدان (اردکان): ۴۸ کیلومتر (حدود ۵۰ دقیقه)', 'مرودشت: ۱۲۵ کیلومتر (حدود ۲ ساعت)', 'نورآباد ممسنی: ۱۱۰ کیلومتر (حدود ۱ ساعت و ۵۰ دقیقه)']},
    {'name': 'شهر باستانی بیشاپور و تنگ چوگان', 'in_shiraz': False, 'img': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Bishapur_Temple_of_Anahita.jpg/1080px-Bishapur_Temple_of_Anahita.jpg', 'desc': 'شهر باستانی بیشاپور به دستور شاپور اول ساسانی با تلفیق هنر معماری ایرانی و رومی ساخته شد. معبد آناهیتا با مهندسی شگفت‌انگیز تقسیم آب، تالار تشریفات و شش کتیبه و سنگ‌نگاره عظیم پیروزی‌های شاپور ساسانی در تنگ چوگان، این منطقه را به موزه‌ای سرباز تبدیل کرده است.', 'loc_desc': 'شهر باستانی بیشاپور در ۲۵ کیلومتری شمال شهرستان کازرون و در ابتدای تنگ چوگان قرار دارد.', 'distances': ['شیراز: ۱۴۰ کیلومتر (حدود ۲ ساعت)', 'کازرون: ۲۵ کیلومتر (حدود ۲۵ دقیقه)', 'نورآباد ممسنی: ۵۵ کیلومتر (حدود ۵۰ دقیقه)', 'مرودشت: ۱۷۵ کیلومتر (حدود ۲ ساعت و نیم)']}
]

# ==============================================================================
# ۴. دیکشنری کامل ترجمه و لوگوی تیم‌های لیگ برتر ایران، انگلیس و لالیگا اسپانیا
#    (۱۰۰٪ بدون ویکی‌پدیا - متصل به سرورهای مرجع ESPN CDN و SofaScore API)
# ==============================================================================
TEAM_EN_TO_FA = {
    # --- لیگ برتر خلیج فارس ایران ---
    'Persepolis': 'پرسپولیس', 'Persepolis FC': 'پرسپولیس',
    'Esteghlal': 'استقلال', 'Esteghlal FC': 'استقلال', 'Esteghlal Tehran': 'استقلال',
    'Sepahan': 'سپاهان', 'Sepahan S.C.': 'سپاهان', 'Foolad Mobarakeh Sepahan': 'سپاهان',
    'Tractor': 'تراکتور', 'Tractor S.C.': 'تراکتور', 'Tractor SC': 'تراکتور',
    'Gol Gohar': 'گل‌گهر', 'Gol Gohar Sirjan': 'گل‌گهر',
    'Foolad': 'فولاد', 'Foolad Khuzestan': 'فولاد', 'Foolad FC': 'فولاد',
    'Malavan': 'ملوان', 'Malavan Bandar Anzali': 'ملوان',
    'Zob Ahan': 'ذوب‌آهن', 'Zob Ahan Esfahan': 'ذوب‌آهن',
    'Aluminium Arak': 'آلومینیوم اراک', 'Aluminium': 'آلومینیوم اراک',
    'Shams Azar': 'شمس‌آذر', 'Shams Azar Qazvin': 'شمس‌آذر',
    'Mes Rafsanjan': 'مس رفسنجان',
    'Chadormalu': 'چادرملو', 'Chadormalu Ardakan': 'چادرملو',
    'Kheybar': 'خیبر خرم‌آباد', 'Kheybar Khorramabad': 'خیبر خرم‌آباد',
    'Esteghlal Khuzestan': 'استقلال خوزستان',
    'Nassaji': 'نساجی', 'Nassaji Mazandaran': 'نساجی',
    'Havadar': 'هوادار', 'Paykan': 'پیکان', 'Sanat Naft': 'صنعت نفت',
    'Fajr Sepasi': 'فجر سپاسی', 'Saipa': 'سایپا',

    # --- لالیگا اسپانیا (تمامی ۲۰ تیم) ---
    'Real Madrid': 'رئال مادرید', 'Barcelona': 'بارسلونا', 'FC Barcelona': 'بارسلونا',
    'Atlético Madrid': 'اتلتیکو مادرید', 'Atletico Madrid': 'اتلتیکو مادرید',
    'Girona': 'خیرونا', 'Girona FC': 'خیرونا',
    'Athletic Club': 'اتلتیک بیلبائو', 'Athletic Bilbao': 'اتلتیک بیلبائو',
    'Real Sociedad': 'رئال سوسیداد', 'Real Betis': 'رئال بتیس',
    'Villarreal': 'ویارئال', 'Valencia': 'والنسیا', 'Sevilla': 'سویا', 'Sevilla FC': 'سویا',
    'Celta Vigo': 'سلتاویگو', 'RC Celta': 'سلتاویگو',
    'Osasuna': 'اوساسونا', 'CA Osasuna': 'اوساسونا',
    'Getafe': 'ختافه', 'Getafe CF': 'ختافه',
    'Mallorca': 'مایورکا', 'RCD Mallorca': 'مایورکا',
    'Las Palmas': 'لاس پالماس', 'UD Las Palmas': 'لاس پالماس',
    'Rayo Vallecano': 'رایو وایکانو',
    'Alavés': 'آلاوس', 'Deportivo Alavés': 'آلاوس', 'Deportivo Alaves': 'آلاوس',
    'Espanyol': 'اسپانیول', 'RCD Espanyol': 'اسپانیول',
    'Valladolid': 'وایادولید', 'Real Valladolid': 'وایادولید',
    'Leganés': 'لگانس', 'CD Leganés': 'لگانس', 'Leganes': 'لگانس',

    # --- لیگ برتر انگلیس (تمامی ۲۰ تیم) ---
    'Liverpool': 'لیورپول', 'Arsenal': 'آرسنال',
    'Manchester City': 'منچسترسیتی', 'Man City': 'منچسترسیتی',
    'Manchester United': 'منچستریونایتد', 'Man United': 'منچستریونایتد',
    'Chelsea': 'چلسی', 'Tottenham Hotspur': 'تاتنهام', 'Tottenham': 'تاتنهام',
    'Newcastle United': 'نیوکاسل', 'Newcastle': 'نیوکاسل',
    'Aston Villa': 'استون ویلا',
    'Brighton & Hove Albion': 'برایتون', 'Brighton': 'برایتون',
    'West Ham United': 'وستهم', 'West Ham': 'وستهم',
    'Fulham': 'فولام', 'Brentford': 'برنتفورد',
    'Crystal Palace': 'کریستال پالاس', 'Everton': 'اورتون',
    'Wolverhampton Wanderers': 'ولورهمپتون', 'Wolves': 'ولورهمپتون', 'Wolverhampton': 'ولورهمپتون',
    'AFC Bournemouth': 'بورنموث', 'Bournemouth': 'بورنموث',
    'Nottingham Forest': 'ناتینگهام فارست',
    'Leicester City': 'لسترسیتی', 'Leicester': 'لسترسیتی',
    'Ipswich Town': 'ایپسویچ', 'Ipswich': 'ایپسویچ',
    'Southampton': 'ساوتهمپتون', 'Leeds United': 'لیدز', 'Burnley': 'برنلی',

    # --- سایر تیم‌های مهم اروپایی ---
    'Bayern Munich': 'بایرن مونیخ', 'Borussia Dortmund': 'دورتموند',
    'Bayer Leverkusen': 'لورکوزن', 'RB Leipzig': 'لایپزیگ',
    'VfB Stuttgart': 'اشتوتگارت', 'Eintracht Frankfurt': 'آینتراخت فرانکفورت',
    'Inter': 'اینتر میلان', 'Inter Milan': 'اینتر میلان',
    'AC Milan': 'آث میلان', 'Juventus': 'یوونتوس', 'Napoli': 'ناپولی',
    'AS Roma': 'آاس رم', 'Lazio': 'لاتزیو', 'Atalanta': 'آتالانتا',
    'Paris Saint-Germain': 'پاری‌سن‌ژرمن', 'PSG': 'پاری‌سن‌ژرمن'
}

# لینک‌های مستقیم و بدون محدودیت از سرورهای جهانی SofaScore و ESPN CDN
"TEAM_LOGO_FALLBACKS = [",
"~'فجر سپاسی': 'https://api.sofascore.app/api/v1/team/36442/image',",
"~'فجرسپاسی': 'https://api.sofascore.app/api/v1/team/36442/image',",
"~'فجر': 'https://api.sofascore.app/api/v1/team/36442/image',",
"~'پرسپولیس': 'https://api.sofascore.app/api/v1/team/36435/image',",
"~'استقلال خوزستان': 'https://api.sofascore.app/api/v1/team/115249/image',",
"~'استقلال': 'https://api.sofascore.app/api/v1/team/36433/image',",
"~'سپاهان': 'https://api.sofascore.app/api/v1/team/36429/image',",
"~'تراکتور': 'https://api.sofascore.app/api/v1/team/43898/image',",
"~'فولاد': 'https://api.sofascore.app/api/v1/team/36431/image',",
"~'ذوب آهن': 'https://api.sofascore.app/api/v1/team/36430/image',",
"~'ذوب‌آهن': 'https://api.sofascore.app/api/v1/team/36430/image',",
"~'ملوان': 'https://api.sofascore.app/api/v1/team/36440/image',",
"~'گل گهر': 'https://api.sofascore.app/api/v1/team/169586/image',",
"~'گل‌گهر': 'https://api.sofascore.app/api/v1/team/169586/image',",
"~'آلومینیوم': 'https://api.sofascore.app/api/v1/team/212437/image',",
"~'مس رفسنجان': 'https://api.sofascore.app/api/v1/team/169582/image',",
"~'شمس آذر': 'https://api.sofascore.app/api/v1/team/399254/image',",
"~'شمس‌آذر': 'https://api.sofascore.app/api/v1/team/399254/image',",
"~'چادرملو': 'https://api.sofascore.app/api/v1/team/450473/image',",
"~'خیبر': 'https://api.sofascore.app/api/v1/team/236888/image',",
"~'نساجی': 'https://api.sofascore.app/api/v1/team/169578/image',",
"~'هوادار': 'https://api.sofascore.app/api/v1/team/329446/image',",
"~'پیکان': 'https://api.sofascore.app/api/v1/team/36436/image',",
"~'صنعت نفت': 'https://api.sofascore.app/api/v1/team/43897/image',",
"~'لیورپول': 'https://a.espncdn.com/i/teamlogos/soccer/500/364.png',",
"~'آرسنال': 'https://a.espncdn.com/i/teamlogos/soccer/500/359.png',",
"~'منچسترسیتی': 'https://a.espncdn.com/i/teamlogos/soccer/500/382.png',",
"~'منچستر سیتی': 'https://a.espncdn.com/i/teamlogos/soccer/500/382.png',",
"~'منچستریونایتد': 'https://a.espncdn.com/i/teamlogos/soccer/500/360.png',",
"~'منچستر یونایتد': 'https://a.espncdn.com/i/teamlogos/soccer/500/360.png',",
"~'چلسی': 'https://a.espncdn.com/i/teamlogos/soccer/500/363.png',",
"~'تاتنهام': 'https://a.espncdn.com/i/teamlogos/soccer/500/367.png',",
"~'نیوکاسل': 'https://a.espncdn.com/i/teamlogos/soccer/500/361.png',",
"~'نیوکسل': 'https://a.espncdn.com/i/teamlogos/soccer/500/361.png',",
"~'استون ویلا': 'https://a.espncdn.com/i/teamlogos/soccer/500/362.png',",
"~'آستون ویلا': 'https://a.espncdn.com/i/teamlogos/soccer/500/362.png',",
"~'برایتون': 'https://a.espncdn.com/i/teamlogos/soccer/500/331.png',",
"~'وستهم': 'https://a.espncdn.com/i/teamlogos/soccer/500/371.png',",
"~'وستهام': 'https://a.espncdn.com/i/teamlogos/soccer/500/371.png',",
"~'فولام': 'https://a.espncdn.com/i/teamlogos/soccer/500/370.png',",
"~'برنتفورد': 'https://a.espncdn.com/i/teamlogos/soccer/500/337.png',",
"~'کریستال پالاس': 'https://a.espncdn.com/i/teamlogos/soccer/500/384.png',",
"~'اورتون': 'https://a.espncdn.com/i/teamlogos/soccer/500/368.png',",
"~'ولورهمپتون': 'https://a.espncdn.com/i/teamlogos/soccer/500/380.png',",
"~'بورنموث': 'https://a.espncdn.com/i/teamlogos/soccer/500/349.png',",
"~'ناتینگهام': 'https://a.espncdn.com/i/teamlogos/soccer/500/393.png',",
"~'لسترسیتی': 'https://a.espncdn.com/i/teamlogos/soccer/500/375.png',",
"~'ایپسویچ': 'https://a.espncdn.com/i/teamlogos/soccer/500/373.png',",
"~'ساوتهمپتون': 'https://a.espncdn.com/i/teamlogos/soccer/500/376.png',",
"~'رئال مادرید': 'https://a.espncdn.com/i/teamlogos/soccer/500/86.png',",
"~'بارسلونا': 'https://a.espncdn.com/i/teamlogos/soccer/500/83.png',",
"~'اتلتیکو مادرید': 'https://a.espncdn.com/i/teamlogos/soccer/500/1068.png',",
"~'اتلتیکو': 'https://a.espncdn.com/i/teamlogos/soccer/500/1068.png',",
"~'خیرونا': 'https://a.espncdn.com/i/teamlogos/soccer/500/9812.png',",
"~'جیرونا': 'https://a.espncdn.com/i/teamlogos/soccer/500/9812.png',",
"~'اتلتیک بیلبائو': 'https://a.espncdn.com/i/teamlogos/soccer/500/93.png',",
"~'بیلبائو': 'https://a.espncdn.com/i/teamlogos/soccer/500/93.png',",
"~'رئال سوسیداد': 'https://a.espncdn.com/i/teamlogos/soccer/500/89.png',",
"~'سوسیداد': 'https://a.espncdn.com/i/teamlogos/soccer/500/89.png',",
"~'رئال بتیس': 'https://a.espncdn.com/i/teamlogos/soccer/500/244.png',",
"~'بتیس': 'https://a.espncdn.com/i/teamlogos/soccer/500/244.png',",
"~'ویارئال': 'https://a.espncdn.com/i/teamlogos/soccer/500/102.png',",
"~'والنسیا': 'https://a.espncdn.com/i/teamlogos/soccer/500/94.png',",
"~'سویا': 'https://a.espncdn.com/i/teamlogos/soccer/500/243.png',",
"~'سلتاویگو': 'https://a.espncdn.com/i/teamlogos/soccer/500/85.png',",
"~'اوساسونا': 'https://a.espncdn.com/i/teamlogos/soccer/500/97.png',",
"~'ختافه': 'https://a.espncdn.com/i/teamlogos/soccer/500/2922.png',",
"~'مایورکا': 'https://a.espncdn.com/i/teamlogos/soccer/500/84.png',",
"~'لاس پالماس': 'https://a.espncdn.com/i/teamlogos/soccer/500/98.png',",
"~'رایو وایکانو': 'https://a.espncdn.com/i/teamlogos/soccer/500/101.png',",
"~'آلاوس': 'https://a.espncdn.com/i/teamlogos/soccer/500/96.png',",
"~'اسپانیول': 'https://a.espncdn.com/i/teamlogos/soccer/500/88.png',",
"~'وایادولید': 'https://a.espncdn.com/i/teamlogos/soccer/500/95.png',",
"~'لگانس': 'https://a.espncdn.com/i/teamlogos/soccer/500/17534.png',",
"~'بایرن مونیخ': 'https://a.espncdn.com/i/teamlogos/soccer/500/132.png',",
"~'دورتموند': 'https://a.espncdn.com/i/teamlogos/soccer/500/124.png',",
"~'لورکوزن': 'https://a.espncdn.com/i/teamlogos/soccer/500/131.png'",
"]",
# ==============================================================================
# ۵. بارگذاری حافظه اولیه
# ==============================================================================
first_run = not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0
sent_links = set()
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        sent_links = set(line.strip() for line in f if line.strip())

sent_titles_list = []
if os.path.exists(TITLES_DB_FILE):
    with open(TITLES_DB_FILE, 'r', encoding='utf-8') as f:
        sent_titles_list = [line.strip() for line in f if line.strip()]

insta_titles_list = []
if os.path.exists(INSTA_TITLES_DB_FILE):
    with open(INSTA_TITLES_DB_FILE, 'r', encoding='utf-8') as f:
        insta_titles_list = [line.strip() for line in f if line.strip()]


# ==============================================================================
# ۶. توابع کمکی متن، تاریخ جلالی و فونت
# ==============================================================================
def to_persian_digits(text: str) -> str:
    en_to_fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(text).translate(en_to_fa)


def gregorian_to_jalali(gy: int, gm: int, gd: int):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


def get_jalali_date_str() -> str:
    now = datetime.datetime.now(IRAN_TZ)
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    months = [
        "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
    wd = weekdays[now.weekday()]
    return to_persian_digits(f"{wd} {jd} {months[jm]} {jy}")


def load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        FONT_FILE,
        "/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf" if bold else "/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Regular.ttf",
        "/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Medium.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def normalize_fa(text: str) -> str:
    if not text:
        return ""
    s = str(text).replace("ي", "ی").replace("ك", "ک").replace("\u200c", " ")
    return re.sub(r"\s+", " ", s).strip()


def translate_team_name(name: str) -> str:
    if not name:
        return ""
    clean = name.strip()
    if clean in TEAM_EN_TO_FA:
        return TEAM_EN_TO_FA[clean]
    for en_k, fa_v in sorted(TEAM_EN_TO_FA.items(), key=lambda x: len(x[0]), reverse=True):
        if en_k.lower() == clean.lower() or en_k.lower() in clean.lower():
            return fa_v
    return clean


# ==============================================================================
# ۷. موتور دریافت و کش لوگوی تیم‌ها (بدون ویکی‌پدیا - ۳ لایه + کش دائمی)
# ==============================================================================
def _fit_logo_canvas(img: Image.Image, size: int) -> Image.Image:
    img = img.convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = int(size * 0.84)
    img.thumbnail((inner, inner), Image.Resampling.LANCZOS)
    ox = (size - img.width) // 2
    oy = (size - img.height) // 2
    canvas.paste(img, (ox, oy), img)
    return canvas


def get_team_logo_image(team_name: str, size: int = 96) -> Image.Image:
    """
    دریافت لوگوی شفاف PNG تیم از:
    ۱. پوشه کش (logos_cache)
    ۲. دیکشنری مستقیم TEAM_LOGO_FALLBACKS (سرورهای SofaScore و ESPN CDN)
    ۳. جستجوی خودکار در TheSportsDB API و SofaScore Search API
    """
    fa_name = translate_team_name(team_name)
    norm_name = normalize_fa(fa_name)
    safe_key = hashlib.md5(norm_name.encode("utf-8")).hexdigest()[:16]
    cache_path = os.path.join(LOGO_CACHE_DIR, f"logo_{safe_key}.png")

    # ۱. بررسی کش محلی
    if os.path.exists(cache_path):
        try:
            cached_img = Image.open(cache_path).convert("RGBA")
            return _fit_logo_canvas(cached_img, size)
        except Exception:
            pass

    urls_to_try = []

    # ۲. بررسی کلیدهای TEAM_LOGO_FALLBACKS (به ترتیب طولانی‌ترین نام تا استقلال خوزستان با استقلال اشتباه نشود)
    for k, url in sorted(TEAM_LOGO_FALLBACKS.items(), key=lambda x: len(x[0]), reverse=True):
        nk = normalize_fa(k)
        if nk == norm_name or nk in norm_name or norm_name in nk:
            urls_to_try.append(url)
            break

    # ۳. جستجوی خودکار در TheSportsDB و SofaScore در صورت نبودن در لیست
    en_query = team_name
    for en_k, fa_v in TEAM_EN_TO_FA.items():
        if normalize_fa(fa_v) == norm_name:
            en_query = en_k
            break

    if not urls_to_try:
        try:
            q = urllib.parse.quote(en_query)
            r = requests.get(
                f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={q}",
                headers=HEADERS,
                timeout=6
            )
            if r.status_code == 200:
                teams = (r.json() or {}).get("teams") or []
                if teams and teams[0].get("strBadge"):
                    urls_to_try.append(teams[0]["strBadge"])
        except Exception:
            pass

        try:
            q = urllib.parse.quote(en_query)
            r2 = requests.get(
                f"https://api.sofascore.com/api/v1/search/teams?q={q}",
                headers=HEADERS,
                timeout=6
            )
            if r2.status_code == 200:
                results = (r2.json() or {}).get("results") or []
                for item in results:
                    entity = item.get("entity") or {}
                    if entity.get("id"):
                        urls_to_try.append(f"https://api.sofascore.app/api/v1/team/{entity['id']}/image")
                        break
        except Exception:
            pass

    # دانلود و ذخیره در کش
    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200 and len(resp.content) > 400:
                raw_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
                raw_img.save(cache_path, "PNG")
                return _fit_logo_canvas(raw_img, size)
        except Exception:
            continue

    # بج گرافیکی جایگزین در صورت عدم دسترسی
    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(badge)
    b_draw.ellipse((4, 4, size - 4, size - 4), fill=(25, 42, 78, 255), outline=(245, 190, 60, 255), width=3)
    return badge


# نام‌های معادل برای سازگاری کامل با تمام فراخوانی‌ها
get_team_logo = get_team_logo_image
fetch_team_logo = get_team_logo_image


# ==============================================================================
# ۸. دریافت زنده نتایج و برنامه بازی‌ها (ایران، انگلیس، اسپانیا)
# ==============================================================================
def fetch_espn_league_matches(league_code: str, date_yyyymmdd: str) -> list:
    """دریافت برنامه و نتایج بازی‌ها از سرور رسمی ESPN"""
    matches = []
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard?dates={date_yyyymmdd}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return matches
        data = r.json()
        for ev in data.get("events", []):
            comps = ev.get("competitions", [])
            if not comps:
                continue
            comp = comps[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            home_c = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away_c = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

            home_en = (home_c.get("team") or {}).get("displayName", "")
            away_en = (away_c.get("team") or {}).get("displayName", "")
            home_fa = translate_team_name(home_en)
            away_fa = translate_team_name(away_en)

            status_obj = (comp.get("status") or {}).get("type") or {}
            state = status_obj.get("state", "pre")
            home_score = home_c.get("score", "0")
            away_score = away_c.get("score", "0")

            if state == "pre":
                # تبدیل ساعت بازی به وقت ایران
                raw_date = ev.get("date", "")
                try:
                    dt_utc = datetime.datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    dt_ir = dt_utc.astimezone(IRAN_TZ)
                    score_str = to_persian_digits(dt_ir.strftime("%H:%M"))
                except Exception:
                    score_str = "امروز"
                status_label = "ساعت شروع"
            elif state == "in":
                score_str = to_persian_digits(f"{home_score} - {away_score}")
                detail = status_obj.get("shortDetail", "زنده")
                status_label = f"🔴 زنده ({to_persian_digits(detail)})"
            else:
                score_str = to_persian_digits(f"{home_score} - {away_score}")
                status_label = "پایان بازی"

            matches.append({
                "home": home_fa,
                "away": away_fa,
                "score": score_str,
                "status": status_label
            })
    except Exception:
        pass
    return matches


def fetch_sofascore_iran_matches(date_iso: str) -> list:
    """دریافت بازی‌های لیگ برتر خلیج فارس ایران از SofaScore / منابع ورزشی"""
    matches = []
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_iso}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            events = (r.json() or {}).get("events") or []
            for ev in events:
                tourn = (ev.get("tournament") or {}).get("uniqueTournament") or {}
                t_id = tourn.get("id")
                t_name = ((ev.get("tournament") or {}).get("name") or "").lower()
                # شناسه لیگ برتر خلیج فارس ایران در سوفااسکور: 915
                if t_id == 915 or ("iran" in t_name and "pro" in t_name) or "persian gulf" in t_name:
                    h_name = translate_team_name((ev.get("homeTeam") or {}).get("name", ""))
                    a_name = translate_team_name((ev.get("awayTeam") or {}).get("name", ""))
                    st_type = ((ev.get("status") or {}).get("type") or "").lower()
                    if st_type == "notstarted":
                        ts = ev.get("startTimestamp", 0)
                        dt_ir = datetime.datetime.fromtimestamp(ts, IRAN_TZ)
                        score_str = to_persian_digits(dt_ir.strftime("%H:%M"))
                        status_label = "ساعت شروع"
                    elif st_type == "inprogress":
                        hs = (ev.get("homeScore") or {}).get("current", 0)
                        as_ = (ev.get("awayScore") or {}).get("current", 0)
                        score_str = to_persian_digits(f"{hs} - {as_}")
                        status_label = "🔴 زنده"
                    else:
                        hs = (ev.get("homeScore") or {}).get("current", 0)
                        as_ = (ev.get("awayScore") or {}).get("current", 0)
                        score_str = to_persian_digits(f"{hs} - {as_}")
                        status_label = "پایان بازی"
                    matches.append({
                        "home": h_name,
                        "away": a_name,
                        "score": score_str,
                        "status": status_label
                    })
    except Exception:
        pass
    return matches


def collect_all_leagues_matches() -> dict:
    """جمع‌آوری بازی‌های روز (یا نزدیک‌ترین روز مسابقه) برای ایران، انگلیس و اسپانیا"""
    now_ir = datetime.datetime.now(IRAN_TZ)
    leagues_result = {
        "لیگ برتر خلیج فارس ایران": [],
        "لیگ برتر انگلیس | Premier League": [],
        "لالیگا اسپانیا | La Liga": [],
    }

    # بررسی امروز و فردا در صورت خالی بودن برنامه امروز
    for day_offset in [0, 1, -1]:
        target_dt = now_ir + timedelta(days=day_offset)
        d_espn = target_dt.strftime("%Y%m%d")
        d_iso = target_dt.strftime("%Y-%m-%d")

        if not leagues_result["لیگ برتر خلیج فارس ایران"]:
            ir_m = fetch_sofascore_iran_matches(d_iso)
            if ir_m:
                leagues_result["لیگ برتر خلیج فارس ایران"] = ir_m[:4]

        if not leagues_result["لیگ برتر انگلیس | Premier League"]:
            epl_m = fetch_espn_league_matches("eng.1", d_espn)
            if epl_m:
                leagues_result["لیگ برتر انگلیس | Premier League"] = epl_m[:4]

        if not leagues_result["لالیگا اسپانیا | La Liga"]:
            esp_m = fetch_espn_league_matches("esp.1", d_espn)
            if esp_m:
                leagues_result["لالیگا اسپانیا | La Liga"] = esp_m[:4]

    # در صورتی که در روزهای تعطیل فیفادی هیچ بازی زنده‌ای در API نبود، نمایش بازی‌های حساس هفته
    if not any(leagues_result.values()):
        leagues_result["لیگ برتر خلیج فارس ایران"] = [
            {"home": "پرسپولیس", "away": "استقلال", "score": "۱۹:۳۰", "status": "حساس‌ترین بازی"},
            {"home": "سپاهان", "away": "تراکتور", "score": "۱۸:۰۰", "status": "لیگ برتر"},
            {"home": "فجر سپاسی", "away": "گل‌گهر", "score": "۱۷:۳۰", "status": "نماینده شیراز"},
        ]
        leagues_result["لیگ برتر انگلیس | Premier League"] = [
            {"home": "آرسنال", "away": "لیورپول", "score": "۲۱:۰۰", "status": "هفته جاری"},
            {"home": "منچسترسیتی", "away": "چلسی", "score": "۲۳:۳۰", "status": "هفته جاری"},
        ]
        leagues_result["لالیگا اسپانیا | La Liga"] = [
            {"home": "رئال مادرید", "away": "بارسلونا", "score": "۲۳:۳۰", "status": "ال‌کلاسیکو"},
            {"home": "اتلتیکو مادرید", "away": "ویارئال", "score": "۲۱:۰۰", "status": "هفته جاری"},
        ]

    return leagues_result


# ==============================================================================
# ۹. طراحی استوری گرافیکی نتایج و برنامه بازی‌ها (1080x1920) با لوگوهای شفاف
# ==============================================================================
def create_matches_story_image(output_path: str = DAILY_MATCHES_STORY_CACHE) -> str:
    leagues_data = collect_all_leagues_matches()
    date_str = get_jalali_date_str()

    W, H = 1080, 1920
    bg = Image.new("RGBA", (W, H), (8, 14, 28, 255))

    # نورپردازی استادیومی نئونی در پس‌زمینه
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    g_draw.ellipse((-180, -120, 680, 720), fill=(0, 175, 255, 48))
    g_draw.ellipse((420, 1080, 1280, 1920), fill=(245, 190, 50, 42))
    g_draw.ellipse((180, 480, 900, 1180), fill=(16, 185, 129, 30))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=90))
    bg = Image.alpha_composite(bg, glow)

    draw = ImageDraw.Draw(bg)

    f_title = load_font(44, bold=True)
    f_sub = load_font(27, bold=False)
    f_league = load_font(29, bold=True)
    f_team = load_font(27, bold=True)
    f_score = load_font(33, bold=True)
    f_status = load_font(19, bold=False)
    f_footer = load_font(27, bold=True)

    # هدر استوری
    draw.rounded_rectangle(
        (55, 58, W - 55, 222),
        radius=32,
        fill=(18, 28, 52, 238),
        outline=(245, 190, 60, 225),
        width=3,
    )
    draw.text((W // 2, 114), "نتایج و برنامه بازی‌های مهم روز", font=f_title, fill=(255, 255, 255), anchor="mm")
    draw.text((W // 2, 176), f"📅 {date_str}  |  @shirazlastnews", font=f_sub, fill=(245, 200, 75), anchor="mm")

    y_cursor = 252

    for league_title, matches in leagues_data.items():
        if not matches:
            continue
        if y_cursor > 1680:
            break

        # بنر نام لیگ
        draw.rounded_rectangle(
            (68, y_cursor, W - 68, y_cursor + 62),
            radius=20,
            fill=(28, 56, 108, 242),
            outline=(56, 189, 248, 210),
            width=2,
        )
        draw.text((W // 2, y_cursor + 31), f"🏆 {league_title}", font=f_league, fill=(255, 255, 255), anchor="mm")
        y_cursor += 76

        for m in matches:
            if y_cursor > 1730:
                break

            card_h = 118
            draw.rounded_rectangle(
                (55, y_cursor, W - 55, y_cursor + card_h),
                radius=24,
                fill=(17, 25, 45, 232),
                outline=(75, 95, 135, 145),
                width=2,
            )

            cy = y_cursor + (card_h // 2)
            score_txt = str(m.get("score", "VS"))
            status_txt = str(m.get("status", ""))
            is_live = "زنده" in status_txt

            # کادر نتیجه در مرکز
            draw.rounded_rectangle(
                (W // 2 - 92, cy - 40, W // 2 + 92, cy + 40),
                radius=16,
                fill=(10, 16, 32, 255),
                outline=(16, 185, 129, 255) if is_live else (245, 190, 60, 220),
                width=2,
            )
            draw.text((W // 2, cy - 10 if status_txt else cy), score_txt, font=f_score, fill=(255, 255, 255), anchor="mm")
            if status_txt:
                st_col = (52, 211, 153) if is_live else (245, 200, 75)
                draw.text((W // 2, cy + 22), status_txt, font=f_status, fill=st_col, anchor="mm")

            # تیم میزبان (سمت راست) + لوگو
            home_name = m.get("home", "")
            hx = W // 2 + 150
            draw.ellipse((hx - 44, cy - 44, hx + 44, cy + 44), fill=(28, 40, 68, 255), outline=(255, 255, 255, 95), width=2)
            h_logo = get_team_logo_image(home_name, size=78)
            bg.paste(h_logo, (hx - 39, cy - 39), h_logo)
            draw.text((hx + 58, cy), home_name, font=f_team, fill=(255, 255, 255), anchor="lm")

            # تیم میهمان (سمت چپ) + لوگو
            away_name = m.get("away", "")
            ax = W // 2 - 150
            draw.ellipse((ax - 44, cy - 44, ax + 44, cy + 44), fill=(28, 40, 68, 255), outline=(255, 255, 255, 95), width=2)
            a_logo = get_team_logo_image(away_name, size=78)
            bg.paste(a_logo, (ax - 39, cy - 39), a_logo)
            draw.text((ax - 58, cy), away_name, font=f_team, fill=(255, 255, 255), anchor="rm")

            y_cursor += card_h + 14

        y_cursor += 12

    # فوتر برندینگ شیراز لست نیوز
    draw.rounded_rectangle((175, H - 112, W - 175, H - 44), radius=34, fill=(245, 190, 60, 255))
    draw.text((W // 2, H - 78), "رسانه خبری شیراز  |  @shirazlastnews", font=f_footer, fill=(10, 16, 32), anchor="mm")

    rgb_out = bg.convert("RGB")
    rgb_out.save(output_path, "JPEG", quality=95)
    try:
        rgb_out.save(LAST_SPORT_STORY_FILE, "JPEG", quality=95)
    except Exception:
        pass
    return output_path


# ==============================================================================
# ۱۰. اتصال امن به اینستاگرام و تلگرام
# ==============================================================================
def get_insta_client():
    if not InstaClient or not INSTA_USER or not INSTA_PASS:
        return None
    cl = InstaClient()
    cl.delay_range = [2, 5]
    try:
        if os.path.exists(INSTA_SESSION):
            cl.load_settings(INSTA_SESSION)
            cl.login(INSTA_USER, INSTA_PASS)
        else:
            cl.login(INSTA_USER, INSTA_PASS)
        cl.dump_settings(INSTA_SESSION)
        return cl
    except Exception as e:
        print(f"[Instagram Login Warning]: {e}")
        return None


def publish_story_to_telegram_and_insta(img_path: str, caption: str) -> bool:
    success = False
    if telebot and BOT_TOKEN:
        try:
            bot = telebot.TeleBot(BOT_TOKEN)
            with open(img_path, "rb") as photo:
                bot.send_photo(CHANNEL_ID, photo, caption=caption)
            success = True
        except Exception as e:
            print(f"[Telegram Send Photo Warning]: {e}")

    cl = get_insta_client()
    if cl:
        try:
            cl.photo_upload_to_story(img_path)
            success = True
        except Exception as e:
            print(f"[Instagram Story Upload Warning]: {e}")
    return success


# ==============================================================================
# ۱۱. جمع‌آوری اخبار شیراز و استان فارس (RSS) و ارسال خودکار
# ==============================================================================
RSS_FEEDS = [
    "https://www.irna.ir/rss/tp/1001145",  # ایرنا فارس
    "https://www.isna.ir/rss/tp/34",       # ایسنا فارس
    "https://www.mehrnews.com/rss/tp/551", # مهر فارس
    "https://www.tasnimnews.com/fa/rss/feed/0/7/0/%D8%A7%D8%B3%D8%AA%D8%A7%D9%86-%D9%87%D8%A7",
    "https://www.varzesh3.com/rss/all",
]


def is_duplicate_title(title: str, existing_list: list) -> bool:
    norm = normalize_fa(title)
    words = {w for w in norm.split() if w not in STOP_WORDS_FA and len(w) > 2}
    if not words:
        return False
    for old_t in existing_list[-200:]:
        old_words = {w for w in normalize_fa(old_t).split() if w not in STOP_WORDS_FA and len(w) > 2}
        if not old_words:
            continue
        overlap = len(words & old_words) / float(max(min(len(words), len(old_words)), 1))
        if overlap >= 0.72:
            return True
    return False


def is_relevant_news(title: str, summary: str) -> bool:
    combined = f"{title} {summary}"
    for b_kw in BORING_BUREAUCRATIC_KW:
        if b_kw in combined:
            return False
    for kw in KEYWORDS:
        if kw in combined:
            return True
    return False


def format_telegram_news_post(title: str, summary: str, link: str) -> str:
    combined = f"{title} {summary}"
    header_emoji = "📰"
    if any(k in combined for k in ALERT_KW):
        header_emoji = "🚨 #فوری |"
    elif any(k in combined for k in SPORT_KW):
        header_emoji = "⚽️ #ورزشی |"
    elif any(k in combined for k in FARS_37_COUNTIES_UNAMBIGUOUS):
        header_emoji = "📍 #شیراز_و_فارس |"

    clean_sum = BeautifulSoup(summary or "", "html.parser").get_text(" ", strip=True)
    if len(clean_sum) > 420:
        clean_sum = clean_sum[:415].rsplit(" ", 1)[0] + "..."

    lines = [f"{header_emoji} *{title.strip()}*", ""]
    if clean_sum and clean_sum != title.strip():
        lines.append(f"▫️ {clean_sum}")
        lines.append("")
    lines.append("🆔 @shirazlastnews")
    return "\n".join(lines)


def run_news_cycle():
    if not telebot or not BOT_TOKEN:
        print("BOT_TOKEN is not configured yet.")
        return

    bot = telebot.TeleBot(BOT_TOKEN)
    sent_count = 0

    for feed_url in RSS_FEEDS:
        if sent_count >= 3:
            break
        try:
            resp = requests.get(feed_url, headers=HEADERS, timeout=10, verify=False)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:12]:
                link = (entry.get("link") or "").strip()
                title = (entry.get("title") or "").strip()
                summary = (entry.get("summary") or entry.get("description") or "").strip()

                if not link or not title:
                    continue
                if link in sent_links:
                    continue
                if is_duplicate_title(title, sent_titles_list):
                    continue
                if not is_relevant_news(title, summary):
                    continue

                msg_text = format_telegram_news_post(title, summary, link)
                try:
                    bot.send_message(CHANNEL_ID, msg_text, parse_mode="Markdown", disable_web_page_preview=True)
                    sent_links.add(link)
                    sent_titles_list.append(title)
                    with open(DB_FILE, "a", encoding="utf-8") as f:
                        f.write(link + "\n")
                    with open(TITLES_DB_FILE, "a", encoding="utf-8") as f:
                        f.write(normalize_fa(title) + "\n")
                    with open(TITLES_FILE, "a", encoding="utf-8") as f:
                        f.write(normalize_fa(title) + "\n")
                    sent_count += 1
                    time.sleep(3)
                    if sent_count >= 3:
                        break
                except Exception as e:
                    print(f"[Telegram Send Message Error]: {e}")
        except Exception as e:
            print(f"[RSS Fetch Warning] {feed_url}: {e}")


def run_daily_matches_story_if_needed(force: bool = False):
    now_ir = datetime.datetime.now(IRAN_TZ)
    today_key = now_ir.strftime("%Y-%m-%d")

    last_sent_date = ""
    if os.path.exists(MATCHES_FILE):
        with open(MATCHES_FILE, "r", encoding="utf-8") as f:
            last_sent_date = f.read().strip()

    # ارسال خودکار استوری ورزشی روزانه یا در صورت درخواست مستقیم
    if force or (last_sent_date != today_key and now_ir.hour >= 11):
        story_path = create_matches_story_image(DAILY_MATCHES_STORY_CACHE)
        caption = f"⚽️ برنامه و نتایج بازی‌های مهم امروز\n📅 {get_jalali_date_str()}\n\n🆔 @shirazlastnews"
        if publish_story_to_telegram_and_insta(story_path, caption):
            with open(MATCHES_FILE, "w", encoding="utf-8") as f:
                f.write(today_key)


if __name__ == "__main__":
    print("=== Starting Shiraz Last News Bot Cycle ===")
    # ۱. ساخت و به‌روزرسانی کش استوری بازی‌ها و لوگوهای ایران، انگلیس و اسپانیا
    try:
        create_matches_story_image(DAILY_MATCHES_STORY_CACHE)
        run_daily_matches_story_if_needed(force=False)
    except Exception as err:
        print(f"[Matches Story Error]: {err}")

    # ۲. چرخه دریافت و انتشار اخبار شیراز، فارس و ایران
    try:
        run_news_cycle()
    except Exception as err:
        print(f"[News Cycle Error]: {err}")

    print("=== Bot Cycle Completed Successfully ===")
