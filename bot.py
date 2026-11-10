import os
import re
import time
import io
import html
import json
import random
import shutil
import subprocess
import textwrap
import urllib.parse
from datetime import datetime, timedelta
from difflib import SequenceMatcher

import telebot
import requests
import feedparser
import urllib3
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputMediaPhoto,
)

try:
    from instagrapi import Client as OrigInstaClient
except Exception:
    OrigInstaClient = None

try:
    from instagrapi.types import StoryPoll, StoryTallie
    HAS_STORY_POLL = True
except Exception:
    HAS_STORY_POLL = False

urllib3.disable_warnings()

# ==========================================
# ۱. تنظیمات پایه و متغیرهای محیطی
# ==========================================
TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = "shirazlastnews_bot"
ADMIN_ID = "30956754"
INSTA_USER = os.environ.get("INSTA_USER", "shirazlastnews")
INSTA_PASS = os.environ.get("INSTA_PASS", "")
TARGET_CHAT = "@shirazlastnews"
CHANNEL_SIGN = "@shirazlastnews"
CHANNEL_LINK = "https://t.me/shirazlastnews"

bot = telebot.TeleBot(TOKEN.strip())
os.makedirs("drafts", exist_ok=True)
os.makedirs("logos_cache", exist_ok=True)

# ==========================================
# ۲. سیستم هوشمند کش لوگوهای ورزشی (متصل به گیت‌هاب LordArma)
# ==========================================
NEW_TEAM_LOGOS = {
    # لیگ برتر خلیج فارس ایران و فجر سپاسی (بدون تحریم روی گیت‌هاب)
    'فجر سپاسی': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D8%AC%D8%B1%20%D8%B4%D9%87%DB%8C%D8%AF%20%D8%B3%D9%BE%D8%A7%D8%B3%DB%8C.png',
    'فجرسپاسی': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D8%AC%D8%B1%20%D8%B4%D9%87%DB%8C%D8%AF%20%D8%B3%D9%BE%D8%A7%D8%B3%DB%8C.png',
    'فجر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D8%AC%D8%B1%20%D8%B4%D9%87%DB%8C%D8%AF%20%D8%B3%D9%BE%D8%A7%D8%B3%DB%8C.png',
    'پرسپولیس': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%BE%D8%B1%D8%B3%D9%BE%D9%88%D9%84%DB%8C%D8%B3%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86.png',
    'استقلال خوزستان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%A7%D8%B3%D8%AA%D9%82%D9%84%D8%A7%D9%84%20%D8%AE%D9%88%D8%B2%D8%B3%D8%AA%D8%A7%D9%86.png',
    'استقلال': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%A7%D8%B3%D8%AA%D9%82%D9%84%D8%A7%D9%84%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86.png',
    'سپاهان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B3%D9%BE%D8%A7%D9%87%D8%A7%D9%86%20%D8%A7%D8%B5%D9%81%D9%87%D8%A7%D9%86.png',
    'تراکتور': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%AA%D8%B1%D8%A7%DA%A9%D8%AA%D9%88%D8%B1%20%D8%AA%D8%A8%D8%B1%DB%8C%D8%B2.png',
    'فولاد': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D9%88%D9%84%D8%A7%D8%AF%20%D8%AE%D9%88%D8%B2%D8%B3%D8%AA%D8%A7%D9%86.png',
    'ذوب آهن': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B0%D9%88%D8%A8%20%D8%A2%D9%87%D9%86%20%D8%A7%D8%B5%D9%81%D9%87%D8%A7%D9%86.png',
    'ذوب‌آهن': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B0%D9%88%D8%A8%20%D8%A2%D9%87%D9%86%20%D8%A7%D8%B5%D9%81%D9%87%D8%A7%D9%86.png',
    'ملوان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%85%D9%84%D9%88%D8%A7%D9%86%20%D8%A8%D9%86%D8%AF%D8%B1%D8%A7%D9%86%D8%B2%D9%84%DB%8C.png',
    'گل گهر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%DA%AF%D9%84%20%DA%AF%D9%87%D8%B1%20%D8%B3%DB%8C%D8%B1%D8%AC%D8%A7%D9%86.png',
    'گل‌گهر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%DA%AF%D9%84%20%DA%AF%D9%87%D8%B1%20%D8%B3%DB%8C%D8%B1%D8%AC%D8%A7%D9%86.png',
    'آلومینیوم': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%A2%D9%84%D9%88%D9%85%DB%8C%D9%86%DB%8C%D9%88%D9%85%20%D8%A7%D8%B1%D8%A7%DA%A9.png',
    'مس شهر بابک': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%85%D8%B3%20%D8%B4%D9%87%D8%B1%20%D8%A8%D8%A7%D8%A8%DA%A9.png',
    'شمس آذر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B4%D9%85%D8%B3%20%D8%A2%D8%B0%D8%B1%20%D9%82%D8%B2%D9%88%DB%8C%D9%86.png',
    'شمس‌آذر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B4%D9%85%D8%B3%20%D8%A2%D8%B0%D8%B1%20%D9%82%D8%B2%D9%88%DB%8C%D9%86.png',
    'چادرملو': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%DA%86%D8%A7%D8%AF%D8%B1%D9%85%D9%84%D9%88%20%D8%A7%D8%B1%D8%AF%DA%A9%D8%A7%D9%86.png',
    'خیبر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%AE%DB%8C%D8%A8%D8%B1%20%D8%AE%D8%B1%D9%85%E2%80%8C%D8%A2%D8%A8%D8%A7%D8%AF.png',
    'نساجی': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%86%D8%B3%D8%A7%D8%AC%DB%8C%20%D9%85%D8%A7%D8%B2%D9%86%D8%AF%D8%B1%D8%A7%D9%86.png',
    'هوادار': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/main/Logos/Havadar.png',
    'پیکان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%BE%DB%8C%DA%A9%D8%A7%D9%86%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86.png',
    'صنعت نفت': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B5%D9%86%D8%B9%D8%AA%20%D9%86%D9%81%D8%AA%20%D8%A2%D8%A8%D8%A7%D8%AF%D8%A7%D9%86.png',
    'سایپا': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/main/Logos/Saipa.png',

    # لیگ برتر انگلیس (تمامی ۲۰ تیم - دست‌نخورده)
    'لیورپول': 'https://a.espncdn.com/i/teamlogos/soccer/500/364.png',
    'آرسنال': 'https://a.espncdn.com/i/teamlogos/soccer/500/359.png',
    'منچسترسیتی': 'https://a.espncdn.com/i/teamlogos/soccer/500/382.png',
    'منچستر سیتی': 'https://a.espncdn.com/i/teamlogos/soccer/500/382.png',
    'منچستریونایتد': 'https://a.espncdn.com/i/teamlogos/soccer/500/360.png',
    'منچستر یونایتد': 'https://a.espncdn.com/i/teamlogos/soccer/500/360.png',
    'چلسی': 'https://a.espncdn.com/i/teamlogos/soccer/500/363.png',
    'تاتنهام': 'https://a.espncdn.com/i/teamlogos/soccer/500/367.png',
    'نیوکاسل': 'https://a.espncdn.com/i/teamlogos/soccer/500/361.png',
    'نیوکسل': 'https://a.espncdn.com/i/teamlogos/soccer/500/361.png',
    'استون ویلا': 'https://a.espncdn.com/i/teamlogos/soccer/500/362.png',
    'آستون ویلا': 'https://a.espncdn.com/i/teamlogos/soccer/500/362.png',
    'برایتون': 'https://a.espncdn.com/i/teamlogos/soccer/500/331.png',
    'وستهم': 'https://a.espncdn.com/i/teamlogos/soccer/500/371.png',
    'وستهام': 'https://a.espncdn.com/i/teamlogos/soccer/500/371.png',
    'وست هم': 'https://a.espncdn.com/i/teamlogos/soccer/500/371.png',
    'فولام': 'https://a.espncdn.com/i/teamlogos/soccer/500/370.png',
    'برنتفورد': 'https://a.espncdn.com/i/teamlogos/soccer/500/337.png',
    'کریستال پالاس': 'https://a.espncdn.com/i/teamlogos/soccer/500/384.png',
    'اورتون': 'https://a.espncdn.com/i/teamlogos/soccer/500/368.png',
    'ولورهمپتون': 'https://a.espncdn.com/i/teamlogos/soccer/500/380.png',
    'ولوز': 'https://a.espncdn.com/i/teamlogos/soccer/500/380.png',
    'بورنموث': 'https://a.espncdn.com/i/teamlogos/soccer/500/349.png',
    'ناتینگهام فارست': 'https://a.espncdn.com/i/teamlogos/soccer/500/393.png',
    'ناتینگهام': 'https://a.espncdn.com/i/teamlogos/soccer/500/393.png',
    'لسترسیتی': 'https://a.espncdn.com/i/teamlogos/soccer/500/375.png',
    'لستر سیتی': 'https://a.espncdn.com/i/teamlogos/soccer/500/375.png',
    'ایپسویچ': 'https://a.espncdn.com/i/teamlogos/soccer/500/373.png',
    'ساوتهمپتون': 'https://a.espncdn.com/i/teamlogos/soccer/500/376.png',

    # لالیگا اسپانیا (تمامی ۲۰ تیم - دست‌نخورده)
    'رئال مادرید': 'https://a.espncdn.com/i/teamlogos/soccer/500/86.png',
    'بارسلونا': 'https://a.espncdn.com/i/teamlogos/soccer/500/83.png',
    'اتلتیکو مادرید': 'https://a.espncdn.com/i/teamlogos/soccer/500/1068.png',
    'اتلتیکومادرید': 'https://a.espncdn.com/i/teamlogos/soccer/500/1068.png',
    'اتلتیکو': 'https://a.espncdn.com/i/teamlogos/soccer/500/1068.png',
    'خیرونا': 'https://a.espncdn.com/i/teamlogos/soccer/500/9812.png',
    'جیرونا': 'https://a.espncdn.com/i/teamlogos/soccer/500/9812.png',
    'اتلتیک بیلبائو': 'https://a.espncdn.com/i/teamlogos/soccer/500/93.png',
    'بیلبائو': 'https://a.espncdn.com/i/teamlogos/soccer/500/93.png',
    'رئال سوسیداد': 'https://a.espncdn.com/i/teamlogos/soccer/500/89.png',
    'سوسیداد': 'https://a.espncdn.com/i/teamlogos/soccer/500/89.png',
    'رئال بتیس': 'https://a.espncdn.com/i/teamlogos/soccer/500/244.png',
    'بتیس': 'https://a.espncdn.com/i/teamlogos/soccer/500/244.png',
    'ویارئال': 'https://a.espncdn.com/i/teamlogos/soccer/500/102.png',
    'والنسیا': 'https://a.espncdn.com/i/teamlogos/soccer/500/94.png',
    'سویا': 'https://a.espncdn.com/i/teamlogos/soccer/500/243.png',
    'سلتاویگو': 'https://a.espncdn.com/i/teamlogos/soccer/500/85.png',
    'سلتا ویگو': 'https://a.espncdn.com/i/teamlogos/soccer/500/85.png',
    'اوساسونا': 'https://a.espncdn.com/i/teamlogos/soccer/500/97.png',
    'ختافه': 'https://a.espncdn.com/i/teamlogos/soccer/500/2922.png',
    'مایورکا': 'https://a.espncdn.com/i/teamlogos/soccer/500/84.png',
    'لاس پالماس': 'https://a.espncdn.com/i/teamlogos/soccer/500/98.png',
    'رایو وایکانو': 'https://a.espncdn.com/i/teamlogos/soccer/500/101.png',
    'آلاوس': 'https://a.espncdn.com/i/teamlogos/soccer/500/96.png',
    'اسپانیول': 'https://a.espncdn.com/i/teamlogos/soccer/500/88.png',
    'وایادولید': 'https://a.espncdn.com/i/teamlogos/soccer/500/95.png',
    'لگانس': 'https://a.espncdn.com/i/teamlogos/soccer/500/17534.png',

    # بوندسلیگا آلمان و اروپا (دست‌نخورده)
    'بایرن مونیخ': 'https://a.espncdn.com/i/teamlogos/soccer/500/132.png',
    'دورتموند': 'https://a.espncdn.com/i/teamlogos/soccer/500/124.png',
    'لورکوزن': 'https://a.espncdn.com/i/teamlogos/soccer/500/131.png',
    'اینتر میلان': 'https://a.espncdn.com/i/teamlogos/soccer/500/110.png',
    'آث میلان': 'https://a.espncdn.com/i/teamlogos/soccer/500/103.png',
    'یوونتوس': 'https://a.espncdn.com/i/teamlogos/soccer/500/111.png',
    'پاری‌سن‌ژرمن': 'https://a.espncdn.com/i/teamlogos/soccer/500/160.png',
}

IR_WIKI_FALLBACKS = {
    'Fajr': 'https://upload.wikimedia.org/wikipedia/fa/thumb/8/87/Fajr_Sepasi_Shiraz_FC_Logo.svg/400px-Fajr_Sepasi_Shiraz_FC_Logo.svg.png',
    'Persepolis': 'https://upload.wikimedia.org/wikipedia/fa/thumb/f/f6/Persepolis_FC_Logo.svg/400px-Persepolis_FC_Logo.svg.png',
    'Esteghlal': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Esteghlal_FC_Logo.svg/400px-Esteghlal_FC_Logo.svg.png',
    'Sepahan': 'https://upload.wikimedia.org/wikipedia/fa/thumb/1/1d/Sepahan_FC_logo.svg/400px-Sepahan_FC_logo.svg.png',
    'Tractor': 'https://upload.wikimedia.org/wikipedia/fa/thumb/8/87/Tractor_FC_Logo.svg/400px-Tractor_FC_Logo.svg.png',
    'Foolad': 'https://upload.wikimedia.org/wikipedia/fa/thumb/6/6b/Foolad_FC_Logo.svg/400px-Foolad_FC_Logo.svg.png',
    'Zob': 'https://upload.wikimedia.org/wikipedia/fa/thumb/c/c8/Zob_Ahan_FC_Logo.svg/400px-Zob_Ahan_FC_Logo.svg.png',
    'Malavan': 'https://upload.wikimedia.org/wikipedia/fa/thumb/6/6f/Malavan_FC_Logo.svg/400px-Malavan_FC_Logo.svg.png',
    'Gol': 'https://upload.wikimedia.org/wikipedia/fa/thumb/e/e0/Gol_Gohar_Sirjan_FC_Logo.svg/400px-Gol_Gohar_Sirjan_FC_Logo.svg.png',
    'Aluminium': 'https://upload.wikimedia.org/wikipedia/fa/thumb/f/f8/Aluminium_Arak_FC_Logo.svg/400px-Aluminium_Arak_FC_Logo.svg.png',
}

_orig_get = requests.get
_lordarma_tree_cache = None

class _CachedResp:
    def __init__(self, content):
        self.status_code = 200
        self.content = content
        self.ok = True

def _find_in_lordarma_repo(en_keyword):
    global _lordarma_tree_cache
    try:
        if _lordarma_tree_cache is None:
            for branch in ['main', 'master']:
                r_tree = _orig_get(f'https://api.github.com/repos/LordArma/Iran-Football-Leagues/git/trees/{branch}?recursive=1', timeout=7)
                if r_tree.status_code == 200:
                    _lordarma_tree_cache = (branch, r_tree.json().get('tree', []))
                    break
            if _lordarma_tree_cache is None:
                _lordarma_tree_cache = ('main', [])
        branch, tree = _lordarma_tree_cache
        kw_clean = en_keyword.lower().replace('%20', ' ').split()[0]
        for item in tree:
            p = item.get('path', '')
            if p.lower().endswith(('.png', '.jpg', '.webp')) and kw_clean in p.lower():
                return f'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/{branch}/{urllib.parse.quote(p)}'
    except Exception:
        pass
    return None

def _smart_logo_get(url, *args, **kwargs):
    u_str = str(url)
    if any(x in u_str for x in ["espncdn.com/i/teamlogos/", "LordArma/Iran-Football-Leagues", "api.sofascore.app"]):
        ckey = re.sub(r"[^a-zA-Z0-9_]", "_", u_str.split("//")[-1]) + ".png"
        cpath = os.path.join("logos_cache", ckey)
        if os.path.exists(cpath) and os.path.getsize(cpath) > 400:
            with open(cpath, "rb") as f:
                return _CachedResp(f.read())
        try:
            r = _orig_get(url, *args, **kwargs)
            if r.status_code == 200 and len(r.content) > 400:
                with open(cpath, "wb") as f:
                    f.write(r.content)
                return r
        except Exception:
            pass
        if "LordArma" in u_str:
            fname = urllib.parse.unquote(u_str.split("/")[-1]).replace(".png", "")
            real_git_url = _find_in_lordarma_repo(fname)
            if real_git_url:
                try:
                    r_git = _orig_get(real_git_url, timeout=8)
                    if r_git.status_code == 200 and len(r_git.content) > 400:
                        with open(cpath, "wb") as f:
                            f.write(r_git.content)
                        return r_git
                except Exception:
                    pass
            try:
                q = urllib.parse.quote(fname)
                r2 = _orig_get(f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={q}", timeout=6)
                teams = (r2.json() or {}).get("teams") or []
                if teams and teams[0].get("strBadge"):
                    r3 = _orig_get(teams[0]["strBadge"], timeout=8)
                    if r3.status_code == 200 and len(r3.content) > 400:
                        with open(cpath, "wb") as f:
                            f.write(r3.content)
                        return r3
            except Exception:
                pass
            for wk_k, wk_u in IR_WIKI_FALLBACKS.items():
                if wk_k.lower() in fname.lower():
                    try:
                        r4 = _orig_get(wk_u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
                        if r4.status_code == 200 and len(r4.content) > 400:
                            with open(cpath, "wb") as f:
                                f.write(r4.content)
                            return r4
                    except Exception:
                        pass
    return _orig_get(url, *args, **kwargs)

requests.get = _smart_logo_get

# ==========================================
# ۳. سیستم صف ضدقفل گیت‌هاب برای اینستاگرام + موتور VIP و ضدتکرار استوری
# ==========================================
import hashlib

GH_PAT_TOKEN = os.environ.get("GH_PAT_TOKEN", "").strip()
GH_USERNAME = "arpparnian-arch"
QUEUE_HASH_FILE = "insta_media_hashes.txt"

def get_active_gh_token():
    if GH_PAT_TOKEN:
        return GH_PAT_TOKEN
    if os.path.exists(SERVICE_STATE_FILE):
        try:
            d = json.load(open(SERVICE_STATE_FILE, "r", encoding="utf-8"))
            rev = d.get("gh_tok_rev", "")
            if rev:
                return rev[::-1]
        except Exception:
            pass
    return ""

def trigger_github_vip_workflow(repo_name, wf_filename="x_bot.yml"):
    tok = get_active_gh_token()
    if not tok:
        return False, "توکن تنظیم نشده"
    headers = {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        url1 = f"https://api.github.com/repos/{GH_USERNAME}/{repo_name}/dispatches"
        r1 = requests.post(url1, headers=headers, json={"event_type": "vip_publish"}, timeout=10)
        url2 = f"https://api.github.com/repos/{GH_USERNAME}/{repo_name}/actions/workflows/{wf_filename}/dispatches"
        r2 = requests.post(url2, headers=headers, json={"ref": "main"}, timeout=10)
        if r1.status_code == 204 or r2.status_code == 204:
            return True, "بیدار شد"
        return False, f"کد {r1.status_code}"
    except Exception as e:
        return False, f"خطا: {e}"

def _compute_file_md5(filepath):
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

def _master_queue_saver(task_type, paths, caption="", is_vip=False):
    os.makedirs("drafts", exist_ok=True)
    if not paths:
        return False

    # بررسی اثر انگشت فایل و کپشن برای جلوگیری ۱۰۰٪ از استوری و پست تکراری
    first_path = str(paths[0])
    media_hash = _compute_file_md5(first_path) if os.path.exists(first_path) else ""
    cap_head = caption.strip().split("\n")[0][:60] if caption else ""
    dedup_sig = f"{task_type}:{media_hash}" if media_hash else f"{task_type}:{cap_head}"

    known_hashes = set()
    if os.path.exists(QUEUE_HASH_FILE):
        try:
            with open(QUEUE_HASH_FILE, "r", encoding="utf-8") as hf:
                known_hashes = set(l.strip() for l in hf if l.strip())
        except Exception:
            pass

    if not is_vip and dedup_sig in known_hashes:
        print(f"Duplicate Insta task blocked ({task_type}): {dedup_sig}")
        return False

    queue_file = "drafts/insta_queue.json"
    q = []
    if os.path.exists(queue_file):
        try:
            with open(queue_file, "r", encoding="utf-8") as f:
                q = json.load(f)
        except Exception:
            pass

    # بررسی عدم وجود آیتم مشابه در صف فعلی
    if not is_vip:
        for existing in q:
            if existing.get("sig") == dedup_sig:
                print(f"Already in queue, skipping: {dedup_sig}")
                return False
            if cap_head and existing.get("caption", "").startswith(cap_head):
                print(f"Caption already in queue, skipping: {cap_head}")
                return False

    saved_paths = []
    for i, p in enumerate(paths):
        p_str = str(p)
        if os.path.exists(p_str):
            ext = os.path.splitext(p_str)[1] or ".jpg"
            dest = f"drafts/ready_{task_type}_{int(time.time())}_{i}{ext}"
            shutil.copy(p_str, dest)
            saved_paths.append(dest)

    new_item = {
        "type": task_type,
        "files": saved_paths,
        "caption": caption,
        "time": 9999999999.0 if is_vip else time.time(),
        "vip": is_vip,
        "sig": dedup_sig
    }

    if is_vip:
        q.insert(0, new_item)
    else:
        q.append(new_item)

    with open(queue_file, "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False, indent=2)

    if dedup_sig:
        known_hashes.add(dedup_sig)
        with open(QUEUE_HASH_FILE, "w", encoding="utf-8") as hf:
            for h_line in list(known_hashes)[-400:]:
                hf.write(h_line + "\n")

    save_memory_state(push_git=True)
    return True

class DummyMedia:
    pk = "123456789"
    id = "123456789"
    code = "ABC"
    def dict(self, *args, **kwargs):
        return {"pk": "123456789", "id": "123456789"}

class DummyInstaClient:
    def __init__(self, *args, **kwargs):
        self.user_id = 123456789
        self.delay_range = [2, 5]
        self.vip_mode = False
    def __bool__(self):
        return True
    def load_settings(self, *args, **kwargs):
        pass
    def dump_settings(self, *args, **kwargs):
        pass
    def login(self, *args, **kwargs):
        return True
    def photo_upload(self, path, caption="", *args, **kwargs):
        _master_queue_saver("photo", [path], caption, is_vip=self.vip_mode)
        return DummyMedia()
    def album_upload(self, paths, caption="", *args, **kwargs):
        _master_queue_saver("album", paths, caption, is_vip=self.vip_mode)
        return DummyMedia()
    def photo_upload_to_story(self, path, *args, **kwargs):
        _master_queue_saver("story_photo", [path], "", is_vip=self.vip_mode)
        return DummyMedia()
    def video_upload_to_story(self, path, *args, **kwargs):
        _master_queue_saver("story_video", [path], "", is_vip=self.vip_mode)
        return DummyMedia()
    def clip_upload(self, path, caption="", *args, **kwargs):
        _master_queue_saver("reel", [path], caption, is_vip=self.vip_mode)
        return DummyMedia()
    def video_upload(self, path, caption="", *args, **kwargs):
        _master_queue_saver("video", [path], caption, is_vip=self.vip_mode)
        return DummyMedia()
    def __getattr__(self, name):
        return lambda *args, **kwargs: DummyMedia()

Client = DummyInstaClient

# ==========================================
# ۴. فیدهای خبری، کلیدواژه‌ها و بانک‌های اطلاعاتی
# ==========================================
FARS_FEEDS = [
    'https://www.isna.ir/rss/tp/274',
    'https://www.irna.ir/rss/tp/1023',
    'https://www.mehrnews.com/rss/tp/649',
    'https://www.mehrnews.com/rss/tp/93',
    'https://www.isna.ir/rss/tp/414',
    'https://fars.isna.ir/rss',
    'https://www.varzesh3.ir/rss/domesticfootball',
    'https://www.irib-news.ir/fa/rss/27'
]

VIDEO_PRIORITY_FEEDS = [
    'https://www.mehrnews.com/rss/tp/6',
    'https://www.tasnimnews.com/fa/rss/feed/0/7/89/%D9%81%DB%8C%D9%84%D9%85',
    'https://www.irna.ir/rss/tp/15',
    'https://www.varzesh3.ir/rss/videos'
]

RSS_FEEDS = FARS_FEEDS + VIDEO_PRIORITY_FEEDS + [
    'https://www.mehrnews.com/rss/pl/77',
    'https://www.mehrnews.com/rss/pl/224',
    'https://www.mehrnews.com/rss',
    'https://www.irna.ir/rss',
    'https://www.isna.ir/rss',
    'https://snn.ir/fa/rss/allnews',
    'https://www.varzesh3.ir/rss/all',
    'https://www.tasnimnews.com/fa/rss/feed/0/8/0/%D9%85%D9%87%D9%85%D8%AA%D8%B1%DB%8C%D9%86-%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1'
]

FARS_TAGS = ['/tp/274', '/tp/1023', '/tp/649', '/tp/93', '/tp/414', 'fars.isna', '1262']
VIDEO_FEED_TAGS = ['/tp/6', '/7/89/', '/tp/15', 'rss/videos']

FARS_37_COUNTIES_UNAMBIGUOUS = [
    'شیراز', 'مرودشت', 'کازرون', 'جهرم', 'لارستان', 'فسا', 'داراب', 'فیروزآباد',
    'ممسنی', 'نورآباد ممسنی', 'آباده', 'لامرد', 'اقلید', 'کوار', 'نی‌ریز', 'نی ریز',
    'زرین‌دشت', 'زرین دشت', 'قیر و کارزین', 'کارزین', 'استهبان', 'خرم‌بید', 'خرم بید', 'صفاشهر',
    'گراش', 'بوانات', 'فراشبند', 'خرامه', 'زرقان', 'کوه‌چنار', 'کوه چنار', 'قائمیه',
    'سپیدان', 'اردکان فارس', 'ارسنجان', 'پاسارگاد', 'سعادت‌شهر', 'سعادت شهر',
    'سروستان', 'بختگان', 'آباده طشک', 'سرچهان', 'جویم', 'خفر', 'باب‌انار', 'باب انار', 'بیضا', 'شهر صدرا'
]

FARS_AMBIGUOUS_COUNTIES = [
    'شهرستان مهر', 'شهرستان رستم', 'شهرستان خنج', 'شهرستان اوز', 'شهرستان لار', 'شهرستان قیر',
    'شهر مهر', 'شهر خنج', 'شهر اوز', 'شهر لار', 'بخش اوز', 'بخش خنج', 'مصیری'
]

FARS_CITIES = FARS_37_COUNTIES_UNAMBIGUOUS + ['لار', 'خنج', 'اوز', 'قیر', 'مهر', 'رستم', 'صدرا']

FARS_SPECIAL_KW = [
    'استان فارس', 'استاندار فارس', 'نماینده ولی فقیه در فارس', 'پزشکی شیراز', 'دانشگاه شیراز',
    'شهرداری شیراز', 'مترو شیراز', 'شورای شهر شیراز', 'فجر سپاسی', 'فجرسپاسی', 'فجر شهید سپاسی',
    'شاهچراغ', 'حافظیه', 'سعدیه', 'تخت جمشید', 'دروازه قرآن', 'باغ ارم', 'ارگ کریمخان',
    'مسجد نصیرالملک', 'مسجد وکیل', 'بازار وکیل', 'فرماندار شیراز', 'پلیس فارس', 'انتظامی فارس',
    'دادگستری فارس', 'برق شیراز', 'برق فارس', 'آبفا شیراز', 'آبفا فارس', 'هواشناسی فارس', 'ورزش فارس', 'راهداری فارس'
]

IRAN_PLACES = [
    'تهران', 'اصفهان', 'مشهد', 'خراسان', 'تبریز', 'آذربایجان', 'اهواز', 'خوزستان', 'کرج', 'البرز',
    'قم', 'کرمانشاه', 'ارومیه', 'رشت', 'گیلان', 'زاهدان', 'سیستان', 'کرمان', 'همدان', 'اراک',
    'مرکزی', 'یزد', 'اردبیل', 'بندرعباس', 'هرمزگان', 'قزوین', 'زنجان', 'سنندج', 'کردستان', 'ساری',
    'مازندران', 'گرگان', 'گلستان', 'خرم‌آباد', 'لرستان', 'بوشهر', 'ایلام', 'بجنورد', 'بیرجند', 'شهرکرد',
    'سمنان', 'یاسوج', 'کهگیلویه', 'کیش', 'قشم', 'آبادان', 'دزفول', 'کاشان', 'سبزوار', 'نیشابور',
    'بابل', 'آمل', 'اردکان یزد', 'فیروزآباد لرستان'
]

IRAN_LEAGUE_CLUBS = [
    'پرسپولیس', 'استقلال', 'سپاهان', 'تراکتور', 'فجر سپاسی', 'فجرسپاسی', 'فجر', 'فولاد',
    'گل گهر', 'گل‌گهر', 'ملوان', 'ذوب آهن', 'ذوب‌آهن', 'آلومینیوم', 'مس رفسنجان', 'چادرملو',
    'شمس آذر', 'نساجی', 'هوادار', 'خیبر', 'پیکان', 'سایپا', 'نفت'
]

REEL_SCHEDULE_SLOTS = [
    (8, 30), (10, 0), (11, 30), (13, 0), (14, 30),
    (16, 0), (17, 30), (19, 0), (20, 30), (22, 0)
]

STOP_WORDS_FA = {
    'در', 'به', 'از', 'با', 'برای', 'تا', 'که', 'این', 'آن', 'را', 'ای', 'ها', 'های', 'هایی',
    'شد', 'شود', 'شده', 'است', 'بود', 'باشند', 'باشد', 'کرد', 'کند', 'کنند', 'کردند', 'داشت', 'دارد',
    'گفت', 'افزود', 'بیان', 'تصریح', 'اعلام', 'گزارش', 'خبر', 'اخبار', 'داد', 'دهد', 'دهند',
    'استان', 'فارس', 'شیراز', 'شهر', 'شهرستان', 'مدیرکل', 'رئیس', 'معاون', 'استاندار', 'فرماندار',
    'امروز', 'دیروز', 'امسال', 'سال', 'ماه', 'روز', 'طی', 'بر', 'روی', 'هم', 'نیز', 'اما', 'یا', 'و'
}

VIRAL_REEL_KEYWORDS = [
    'فوری', 'وایرال', 'ببینید', 'لحظه', 'عجیب', 'باورنکردنی', 'تکان‌دهنده', 'شوکه', 'تصادف',
    'آتش‌سوزی', 'انفجار', 'زلزله', 'سیل', 'طوفان', 'درگیری', 'زورگیری', 'سرقت', 'پلیس', 'نجات',
    'معجزه', 'جنجال', 'حاشیه', 'واکنش', 'طلا', 'دلار', 'سکه', 'خودرو', 'یارانه', 'کالابرگ',
    'تعطیل', 'فوتبال', 'تیم ملی', 'پرسپولیس', 'استقلال', 'گل ', 'پرتاب', 'موشک', 'رکورد',
    'دیدنی', 'جالب', 'قهرمان', 'طلایی'
]

BORING_BUREAUCRATIC_KW = [
    'نشست', 'جلسه', 'همایش', 'کارگروه', 'دیدار با', 'پیام تبریک', 'پیام تسلیت', 'سخنرانی',
    'معارفه', 'تودیع', 'یادواره', 'شورای اداری', 'شورای فرهنگ', 'نماز جمعه'
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

TEAM_EN_TO_FA = {
    'Real Madrid': 'رئال مادرید', 'Barcelona': 'بارسلونا', 'Atlético Madrid': 'اتلتیکو مادرید', 'Atletico Madrid': 'اتلتیکو مادرید',
    'Girona': 'خیرونا', 'Athletic Club': 'اتلتیک بیلبائو', 'Real Sociedad': 'رئال سوسیداد', 'Real Betis': 'رئال بتیس',
    'Villarreal': 'ویارئال', 'Valencia': 'والنسیا', 'Sevilla': 'سویا', 'Celta Vigo': 'سلتاویگو', 'Osasuna': 'اوساسونا',
    'Getafe': 'ختافه', 'Mallorca': 'مایورکا', 'Las Palmas': 'لاس پالماس', 'Rayo Vallecano': 'رایو وایکانو', 'Alavés': 'آلاوس',
    'Espanyol': 'اسپانیول', 'Valladolid': 'وایادولید', 'Leganés': 'لگانس',
    'Liverpool': 'لیورپول', 'Arsenal': 'آرسنال', 'Manchester City': 'منچسترسیتی', 'Manchester United': 'منچستریونایتد',
    'Chelsea': 'چلسی', 'Tottenham Hotspur': 'تاتنهام', 'Newcastle United': 'نیوکاسل', 'Aston Villa': 'استون ویلا',
    'Brighton & Hove Albion': 'برایتون', 'Brighton': 'برایتون', 'West Ham United': 'وستهم', 'Fulham': 'فولام',
    'Brentford': 'برنتفورد', 'Crystal Palace': 'کریستال پالاس', 'Everton': 'اورتون', 'Wolverhampton Wanderers': 'ولورهمپتون',
    'AFC Bournemouth': 'بورنموث', 'Bournemouth': 'بورنموث', 'Nottingham Forest': 'ناتینگهام فارست', 'Leicester City': 'لسترسیتی',
    'Ipswich Town': 'ایپسویچ', 'Southampton': 'ساوتهمپتون',
    'Bayern Munich': 'بایرن مونیخ', 'Borussia Dortmund': 'دورتموند', 'Bayer Leverkusen': 'لورکوزن', 'RB Leipzig': 'لایپزیگ',
    'VfB Stuttgart': 'اشتوتگارت', 'Eintracht Frankfurt': 'آینتراخت فرانکفورت', 'SC Freiburg': 'فرایبورگ', 'VfL Wolfsburg': 'ولفسبورگ',
    'TSG Hoffenheim': 'هوفنهایم', 'Werder Bremen': 'وردربرمن', 'Borussia Mönchengladbach': 'مونشن‌گلادباخ', 'Union Berlin': 'اونیون برلین',
    'FC Augsburg': 'آگزبورگ', 'Mainz 05': 'ماینتس', '1. FSV Mainz 05': 'ماینتس', 'VfL Bochum': 'بوخوم', 'Heidenheim': 'هایدنهایم',
    'St. Pauli': 'سن پائولی', 'Holstein Kiel': 'هولشتاین کیل',
    'Inter': 'اینتر میلان', 'AC Milan': 'آث میلان', 'Juventus': 'یوونتوس', 'Napoli': 'ناپولی',
    'AS Roma': 'آاس رم', 'Lazio': 'لاتزیو', 'Atalanta': 'آتالانتا', 'Paris Saint-Germain': 'پاری‌سن‌ژرمن'
}

TOURISM_DB = [
    {
        'name': 'مسجد نصیرالملک (مسجد صورتی)',
        'in_shiraz': True,
        'img': 'https://upload.wikimedia.org/wikipedia/commons/8/80/Nasir-al_molk_-1.jpg?utm_source=fa.wikipedia.org&utm_campaign=imageinfo&utm_content=original.jpg',
        'desc': 'مسجد نصیرالملک یکی از زیباترین شاهکارهای معماری دوران قاجار در شیراز است که به دلیل استفاده از شیشه‌های رنگی و کاشی‌کاری‌های هفت‌رنگ با طرح گل‌ومرغ، به مسجد صورتی شهرت دارد. رقص نورهای رنگارنگ صبحگاهی بر فرش‌های دستباف شبستان غربی و ستون‌های سنگی مارپیچ آن، فضایی رویایی خلق می‌کند.',
        'loc_desc': 'مسجد نصیرالملک در قلب بافت تاریخی شیراز (خیابان لطفعلی‌خان زند، محله گود عربان) قرار دارد.',
        'distances': ['مرودشت: ۵۰ کیلومتر (حدود ۵۰ دقیقه)', 'کازرون: ۱۴۰ کیلومتر (حدود ۲ ساعت)', 'جهرم: ۱۸۵ کیلومتر (حدود ۲ ساعت و ۱۵ دقیقه)', 'فسا: ۱۴۵ کیلومتر (حدود ۲ ساعت)']
    },
    {
        'name': 'مجموعه جهانی تخت جمشید (پرسپولیس)',
        'in_shiraz': False,
        'img': 'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b4/Persian_ccity.jpg/1920px-Persian_ccity.jpg?utm_source=fa.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail.jpg',
        'desc': 'تخت جمشید یا پارسه، پایتخت باشکوه تشریفاتی امپراتوری هخامنشیان است که به فرمان داریوش بزرگ بنا نهاده شد. کاخ آپادانا، دروازه ملل، کاخ صدستون و سنگ‌نگاره‌های بی‌نظیر اهدای هدایا توسط نمایندگان ملل باستان، شکوه تمدن و هنر معماری ایران زمین را به رخ جهانیان می‌کشد.',
        'loc_desc': 'مجموعه جهانی تخت جمشید در شمال شهرستان مرودشت و در دامنه کوه رحمت واقع شده است.',
        'distances': ['شیراز: ۶۰ کیلومتر (حدود ۵۵ دقیقه)', 'مرودشت: ۱۰ کیلومتر (حدود ۱۵ دقیقه)', 'آباده: ۲۲۰ کیلومتر (حدود ۲ ساعت و نیم)', 'پاسارگاد: ۸۰ کیلومتر (حدود ۱ ساعت)']
    },
    {
        'name': 'آرامگاه لسان‌الغیب حافظ شیرازی (حافظیه)',
        'in_shiraz': True,
        'img': 'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b9/Hafezieh_001.jpg/1920px-Hafezieh_001.jpg?utm_source=fa.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail.jpg',
        'desc': 'حافظیه، میعادگاه عاشقان شعر و ادب پارسی در شمال شهر شیراز است. گنبد مسی کلاه‌فرنگی این بنا که بر هشت ستون سنگی استوار شده، با کاشی‌های معرق فیروزه‌ای و ابیاتی از غزلیات خواجه شمس‌الدین محمد حافظ شیرازی آراسته گشته و در میان باغی پر از درختان نارنج و سرو می‌درخشد.',
        'loc_desc': 'آرامگاه حافظ در شهر شیراز، حدفاصل چهارراه ادبیات و دروازه قرآن واقع شده است.',
        'distances': ['مرودشت: ۴۵ کیلومتر (حدود ۴۵ دقیقه)', 'کازرون: ۱۴۵ کیلومتر (حدود ۲ ساعت)', 'سپیدان (اردکان): ۸۰ کیلومتر (حدود ۱ ساعت و ربع)', 'جهرم: ۱۹۰ کیلومتر (حدود ۲ ساعت و نیم)']
    },
    {
        'name': 'باغ جهانی ارم شیراز',
        'in_shiraz': True,
        'img': 'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fe/Bagh-e_Eram_.jpg/1920px-Bagh-e_Eram_.jpg?utm_source=fa.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail.jpg',
        'desc': 'باغ ارم یکی از زیباترین باغ‌های ایرانی ثبت‌شده در میراث جهانی یونسکو است. عمارت سه‌طبقه مرکزی باغ با کاشی‌کاری‌های هلالی دوره‌ی قاجار، حوض بزرگ پیش‌رو، سروهای سر به فلک کشیده (از جمله سرو ناز هزارساله) و باغ گیاه‌شناسی کم‌نظیر، آن را به بهشتی در قلب شیراز تبدیل کرده است.',
        'loc_desc': 'باغ ارم در شمال غربی شیراز، خیابان ارم و در مجاورت مجموعه دانشگاه شیراز قرار دارد.',
        'distances': ['مرودشت: ۵۰ کیلومتر (حدود ۵۰ دقیقه)', 'کازرون: ۱۳۵ کیلومتر (حدود ۱ ساعت و ۵۰ دقیقه)', 'سپیدان: ۷۵ کیلومتر (حدود ۱ ساعت)', 'فسا: ۱۵۰ کیلومتر (حدود ۲ ساعت)']
    },
    {
        'name': 'مجموعه میراث جهانی پاسارگاد',
        'in_shiraz': False,
        'img': 'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/51/Pasargad_Tomb_Cyrus3.jpg/1920px-Pasargad_Tomb_Cyrus3.jpg?utm_source=fa.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail.jpg',
        'desc': 'پاسارگاد نخستین پایتخت امپراتوری هخامنشی است که به فرمان کوروش بزرگ در دشت مرغاب ساخته شد. آرامگاه سنگی و باصلابت کوروش بزرگ، کاخ بارعام، کاخ اختصاصی و باغ شاهی پاسارگاد، نخستین نمونه مهندسی باغ ایرانی و نماد همزیستی فرهنگ‌ها در دنیای باستان به شمار می‌رود.',
        'loc_desc': 'مجموعه جهانی پاسارگاد در شهرستان پاسارگاد (سعادت‌شهر) در مسیر بزرگراه شیراز به اصفهان قرار دارد.',
        'distances': ['شیراز: ۱۳۵ کیلومتر (حدود ۱ ساعت و ۴۵ دقیقه)', 'مرودشت: ۸۵ کیلومتر (حدود ۱ ساعت)', 'آباده: ۱۴۵ کیلومتر (حدود ۱ ساعت و نیم)', 'ارسنجان: ۶۵ کیلومتر (حدود ۵۰ دقیقه)']
    },
    {
        'name': 'ارگ تاریخی کریمخانی شیراز',
        'in_shiraz': True,
        'img': 'https://upload.wikimedia.org/wikipedia/commons/1/17/Arg.karimkhan.jpg?utm_source=fa.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail_unscaled.jpg',
        'desc': 'ارگ کریمخانی در مرکز شهر شیراز، محل سکونت و فرمانروایی کریم‌خان زند (وکیل‌الرعایا) بوده است. این بنا با ترکیب معماری نظامی (برج‌های آجری دوازده‌متری و دیوارهای کنگره‌دار) و معماری مسکونی (ایوان‌های شاه‌نشین، حوض‌خانه و باغچه نارنجستان داخلی) جلوه‌ای بی‌همتا دارد.',
        'loc_desc': 'ارگ کریمخانی در مرکز شهر شیراز، میدان شهدا (شهرداری) و ابتدای خیابان زند واقع شده است.',
        'distances': ['مرودشت: ۴۸ کیلومتر (حدود ۵۰ دقیقه)', 'کازرون: ۱۴۰ کیلومتر (حدود ۲ ساعت)', 'فیروزآباد: ۱۱۵ کیلومتر (حدود ۱ ساعت و ۴۵ دقیقه)', 'سروستان: ۸۵ کیلومتر (حدود ۱ ساعت)']
    },
    {
        'name': 'آبشار دیدنی مارگون سپیدان',
        'in_shiraz': False,
        'img': 'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0b/Margoon_river.JPG/1920px-Margoon_river.JPG?utm_source=fa.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail.jpg',
        'desc': 'آبشار مارگون در شهرستان سپیدان، یکی از بزرگ‌ترین و شگفت‌انگیزترین آبشارهای چشمه‌ای جهان است. در بالای این کوه هیچ رودخانه‌ای وجود ندارد، بلکه هزاران چشمه از دل دیواره صخره‌ای به بیرون می‌جوشند و آبشاری به ارتفاع ۷۰ متر و عرض ۱۰۰ متر را در دل طبیعت سرسبز زاگرس خلق می‌کنند.',
        'loc_desc': 'آبشار مارگون در بخش همایجان شهرستان سپیدان و در نزدیکی روستای مارگون قرار دارد.',
        'distances': ['شیراز: ۱۳۰ کیلومتر (حدود ۲ ساعت)', 'سپیدان (اردکان): ۴۸ کیلومتر (حدود ۵۰ دقیقه)', 'مرودشت: ۱۲۵ کیلومتر (حدود ۲ ساعت)', 'نورآباد ممسنی: ۱۱۰ کیلومتر (حدود ۱ ساعت و ۵۰ دقیقه)']
    },
    {
        'name': 'شهر باستانی بیشاپور و تنگ چوگان',
        'in_shiraz': False,
        'img': 'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/74/Anahita_Temple_of_Bishapur_%28Kazerun%29_1.jpg/1920px-Anahita_Temple_of_Bishapur_%28Kazerun%29_1.jpg?utm_source=fa.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail.jpg',
        'desc': 'شهر باستانی بیشاپور به دستور شاپور اول ساسانی با تلفیق هنر معماری ایرانی و رومی ساخته شد. معبد آناهیتا با مهندسی شگفت‌انگیز تقسیم آب، تالار تشریفات و شش کتیبه و سنگ‌نگاره عظیم پیروزی‌های شاپور ساسانی در تنگ چوگان، این منطقه را به موزه‌ای سرباز تبدیل کرده است.',
        'loc_desc': 'شهر باستانی بیشاپور در ۲۵ کیلومتری شمال شهرستان کازرون و در ابتدای تنگ چوگان قرار دارد.',
        'distances': ['شیراز: ۱۴۰ کیلومتر (حدود ۲ ساعت)', 'کازرون: ۲۵ کیلومتر (حدود ۲۵ دقیقه)', 'نورآباد ممسنی: ۵۵ کیلومتر (حدود ۵۰ دقیقه)', 'مرودشت: ۱۷۵ کیلومتر (حدود ۲ ساعت و نیم)']
    }
]

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

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}

TEAM_LOGO_FALLBACKS = {}
TEAM_LOGO_FALLBACKS.update(NEW_TEAM_LOGOS)
# ==========================================
# ۵. مدیریت حافظه، ضدتکرار چندلایه و همگام‌سازی ایمن گیت‌هاب
# ==========================================
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

for f_init in [
    DB_FILE, TITLES_DB_FILE, INSTA_TITLES_DB_FILE, DAILY_FILE,
    NIGHT_FILE, MATCHES_FILE, TOURISM_STATE_FILE, TITLES_FILE,
    INSTA_LOG, INSTA_REEL_LOG, QUEUE_HASH_FILE
]:
    if not os.path.exists(f_init):
        with open(f_init, 'w', encoding='utf-8') as f:
            pass

def _merge_lines_with_disk(filepath, mem_iterable, max_keep=800):
    """ترکیب حافظه رم با فایل روی دیسک تا در هنگام git pull هیچ رکوردی پاک نشود"""
    combined = []
    seen = set()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    s = line.strip()
                    if s and s not in seen:
                        seen.add(s)
                        combined.append(s)
        except Exception:
            pass
    for item in mem_iterable:
        s = str(item).strip()
        if s and s not in seen:
            seen.add(s)
            combined.append(s)
    final_list = combined[-max_keep:]
    with open(filepath, 'w', encoding='utf-8') as f:
        for x in final_list:
            f.write(x + '\n')
    return final_list

def save_memory_state(push_git=False):
    global sent_links, sent_titles_list, insta_titles_list
    try:
        sent_links = set(_merge_lines_with_disk(DB_FILE, sent_links, max_keep=1200))
        sent_titles_list = _merge_lines_with_disk(TITLES_DB_FILE, sent_titles_list, max_keep=600)
        insta_titles_list = _merge_lines_with_disk(INSTA_TITLES_DB_FILE, insta_titles_list, max_keep=400)

        if push_git:
            # استفاده از -X theirs در rebase تا تغییرات جدید ربات هرگز توسط فایل قدیمی سرور بازنویسی نشود
            cmds = [
                'git config --global user.name "Bot"',
                'git config --global user.email "bot@noreply.github.com"',
                'git add -f *.txt *.json *.jpg drafts/insta_queue.json drafts/* || true',
                'git diff --staged --quiet || git commit -m "Sync memory and queue"',
                'git pull --rebase -X theirs || true',
                'git push || true'
            ]
            subprocess.run(" && ".join(cmds), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45)
            # بازخوانی و ذخیره مجدد پس از pull برای اطمینان ۱۰۰٪
            sent_links = set(_merge_lines_with_disk(DB_FILE, sent_links, max_keep=1200))
            sent_titles_list = _merge_lines_with_disk(TITLES_DB_FILE, sent_titles_list, max_keep=600)
            insta_titles_list = _merge_lines_with_disk(INSTA_TITLES_DB_FILE, insta_titles_list, max_keep=400)
    except Exception as e:
        print('Save memory error:', e)

def is_silent_hours():
    iran_now = datetime.utcnow() + timedelta(hours=3, minutes=30)
    mins = iran_now.hour * 60 + iran_now.minute
    return mins >= (22 * 60 + 45) or mins < (7 * 60 + 45)

def normalize_persian_chars(s):
    if not s:
        return ''
    s = s.replace('ي', 'ی').replace('ك', 'ک').replace('ة', 'ه').replace('ؤ', 'و').replace('إ', 'ا').replace('أ', 'ا')
    s = s.replace('\u200c', ' ').replace('‌', ' ')
    s = s.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'))
    return s

def normalize_link(u):
    u = u.strip().split('?')[0].split('#')[0].rstrip('/')
    return re.sub(r'^https?://(www\.)?', '', u.lower())

def extract_news_id_from_url(u):
    m = re.search(r'/(?:news|fa/news|content|detail)/(\d{5,12})', u)
    if m:
        return m.group(1)
    m2 = re.search(r'/(\d{6,12})(?:/|$)', u)
    return m2.group(1) if m2 else None

def clean_agency_prefix(text):
    if not text:
        return ''
    t = text.strip()
    t = re.sub(r'^\([^)]{2,35}\)\s*[-–—:]?\s*', '', t)
    t = re.sub(r'^[^.،:]{2,40}[-–—]\s*(ایرنا|مهر|تسنیم|ایسنا|فارس|صدا و سیما|پانا|باشگاه خبرنگاران|دانشجو|ورزش سه)\s*[-–—:]\s*', '', t)
    t = re.sub(r'^(ایرنا|مهر|تسنیم|ایسنا|فارس|صدا و سیما|گروه [^.،:]{2,25})\s*[-–—:]\s*', '', t)
    t = re.sub(r'^به گزارش\s+(خبرنگار\s+|گروه\s+[^،]{2,20}\s+)?(خبرگزاری\s+|پایگاه خبری\s+)?(ایرنا|مهر|تسنیم|ایسنا|فارس|صدا و سیما|دانشجو)[^،]{0,25}،\s*', '', t)
    return t.strip()

def normalize_title(t):
    t = normalize_persian_chars(clean_agency_prefix(t))
    t = re.sub(r'[^\w\s]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def extract_core_tokens(text):
    norm = normalize_title(text)
    words = [w for w in norm.split() if len(w) > 2 and w not in STOP_WORDS_FA]
    return set(words)

def are_texts_similar(new_t, old_t, ratio_thresh=0.62, token_thresh=0.58):
    if not new_t or not old_t:
        return False
    if new_t == old_t or new_t in old_t or old_t in new_t:
        return True
    if SequenceMatcher(None, new_t, old_t).ratio() >= ratio_thresh:
        return True
    tok1 = extract_core_tokens(new_t)
    tok2 = extract_core_tokens(old_t)
    if len(tok1) >= 4 and len(tok2) >= 4:
        common = tok1.intersection(tok2)
        overlap = len(common) / float(min(len(tok1), len(tok2)))
        if overlap >= token_thresh or len(common) >= 5:
            return True
    return False

def is_duplicate_news(link, clean_t, clean_s=''):
    norm_l = normalize_link(link)
    if link in sent_links or norm_l in sent_links:
        return True
    nid = extract_news_id_from_url(norm_l)
    if nid and f'id:{nid}' in sent_links:
        return True
    norm_t = normalize_title(clean_t)
    if not norm_t:
        return False
    for old_t in sent_titles_list[-180:]:
        if are_texts_similar(norm_t, old_t, ratio_thresh=0.62, token_thresh=0.58):
            return True
    return False

def is_duplicate_for_insta(clean_t, clean_s=''):
    norm_t = normalize_title(clean_t)
    if not norm_t:
        return False
    for old_t in insta_titles_list[-120:]:
        if are_texts_similar(norm_t, old_t, ratio_thresh=0.60, token_thresh=0.55):
            return True
    return False

def record_sent_news(link, clean_t, sent_to_insta=False, clean_s=''):
    norm_l = normalize_link(link)
    sent_links.add(norm_l)
    nid = extract_news_id_from_url(norm_l)
    if nid:
        sent_links.add(f'id:{nid}')
    norm_t = normalize_title(clean_t)
    if norm_t and norm_t not in sent_titles_list:
        sent_titles_list.append(norm_t)
    if sent_to_insta and norm_t and norm_t not in insta_titles_list:
        insta_titles_list.append(norm_t)

# ==========================================
# ۶. فیلترهای هوشمند اخبار شیراز، فارس و ریلز
# ==========================================
def is_strictly_fars_shiraz_news(clean_t, clean_s, feed_url=''):
    false_positives = [
        'خلیج فارس', 'خبرگزاری فارس', 'دریای فارس', 'فرش فارس', 'زبان فارسی',
        'ادبیات فارسی', 'تقویم فارسی', 'اردکان یزد', 'فیروزآباد لرستان', 'فیروزآباد کوهدشت'
    ]
    t_clean = clean_t
    s_clean = clean_s
    for fp in false_positives:
        t_clean = t_clean.replace(fp, '')
        s_clean = s_clean.replace(fp, '')
    full_clean = t_clean + ' ' + s_clean
    has_fars_in_title = any(
        fc in t_clean for fc in FARS_37_COUNTIES_UNAMBIGUOUS + FARS_AMBIGUOUS_COUNTIES + FARS_SPECIAL_KW
    )
    for other_p in IRAN_PLACES:
        if other_p in t_clean and not has_fars_in_title:
            return False
    if has_fars_in_title:
        return True
    if any(fc in full_clean for fc in FARS_37_COUNTIES_UNAMBIGUOUS + FARS_AMBIGUOUS_COUNTIES + FARS_SPECIAL_KW):
        if not any(other_p in t_clean for other_p in IRAN_PLACES):
            return True
    if any(tag in feed_url for tag in FARS_TAGS):
        if re.search(r'(?:در|استان|شهرستان|کلانشهر)\s+فارس', full_clean):
            return True
    return False

def is_eligible_for_insta_reel(clean_t, clean_s, is_fars_news):
    if is_duplicate_for_insta(clean_t):
        return False
    if is_fars_news:
        return True
    full_t = clean_t + ' ' + clean_s
    if any(b in clean_t for b in BORING_BUREAUCRATIC_KW):
        return False
    for other_p in IRAN_PLACES:
        if other_p != 'تهران' and other_p in clean_t:
            if not any(v in clean_t for v in ['تصادف', 'انفجار', 'آتش‌سوزی', 'زلزله', 'سیل', 'عجیب', 'وایرال', 'زورگیری', 'لحظه']):
                return False
    if any(vk in full_t for vk in VIRAL_REEL_KEYWORDS):
        return True
    return False

# ==========================================
# ۷. توابع تاریخ جلالی، زمان‌بندی ریلز و گزارش وضعیت
# ==========================================
def to_persian_num(s):
    return str(s).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))

def get_persian_weekday():
    iran_now = datetime.utcnow() + timedelta(hours=3, minutes=30)
    days_fa = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه', 'یکشنبه']
    return days_fa[iran_now.weekday()]

def get_iran_jalali_date():
    iran_now = datetime.utcnow() + timedelta(hours=3, minutes=30)
    gy, gm, gd = iran_now.year, iran_now.month, iran_now.day
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
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
    return to_persian_num(f'{jy:04d}/{jm:02d}/{jd:02d}'), iran_now.hour

def get_active_reel_schedule_slot():
    iran_now = datetime.utcnow() + timedelta(hours=3, minutes=30)
    today_str, _ = get_iran_jalali_date()
    now_mins = iran_now.hour * 60 + iran_now.minute
    done_slots = []
    if os.path.exists(INSTA_REEL_LOG):
        try:
            raw_l = open(INSTA_REEL_LOG, encoding='utf-8').read().strip()
            if raw_l.startswith(today_str + '|'):
                done_slots = [x for x in raw_l.split('|')[1].split(',') if x]
        except Exception:
            pass
    if len(done_slots) >= 12:
        return None
    for sh, sm in REEL_SCHEDULE_SLOTS:
        slot_id = f'{sh:02d}:{sm:02d}'
        slot_mins = sh * 60 + sm
        if slot_mins <= now_mins <= (slot_mins + 80):
            if slot_id not in done_slots:
                return slot_id
    return None

def mark_reel_slot_completed(slot_id):
    if not slot_id:
        return
    today_str, _ = get_iran_jalali_date()
    done_slots = []
    if os.path.exists(INSTA_REEL_LOG):
        try:
            raw_l = open(INSTA_REEL_LOG, encoding='utf-8').read().strip()
            if raw_l.startswith(today_str + '|'):
                done_slots = [x for x in raw_l.split('|')[1].split(',') if x]
        except Exception:
            pass
    if slot_id not in done_slots:
        done_slots.append(slot_id)
    with open(INSTA_REEL_LOG, 'w', encoding='utf-8') as f:
        f.write(today_str + '|' + ','.join(done_slots))

def build_admin_schedule_report():
    iran_now = datetime.utcnow() + timedelta(hours=3, minutes=30)
    today_str, h_now = get_iran_jalali_date()
    m_now = iran_now.minute
    wk_fa = get_persian_weekday()
    time_fa = to_persian_num(f'{h_now:02d}:{m_now:02d}')
    post_mode = 'پست کاروسل ۲ اسلایدی (۴:۵) + استوری نظرسنجی' if (h_now % 2 == 0) else 'پست تک‌اسلایدی (۴:۵) + استوری نظرسنجی'
    cur_tasks = [
        '• پایش قطره‌چکانی خبرگزاری‌ها (حداکثر ۱ خبر در هر ۶ دقیقه در تلگرام)',
        '• رصد زنده ۶۰ ثانیه‌ای لیگ برتر ایران (انتشار خودکار گل و نتایج در استوری)',
        f'• قالب نوبت پست اینستاگرام در ساعت {to_persian_num(h_now)}: <b>{post_mode}</b> (ویژه شیراز و ۳۷ شهرستان فارس)'
    ]
    if is_silent_hours():
        cur_tasks.append('• 🔕 <b>حالت سکوت شبانه فعال است</b> (ارسال بی‌صدای پیام‌ها در تلگرام تا ۰۷:۴۵ صبح)')
    if h_now == 8:
        cur_tasks.append('• 🌅 <b>وظیفه ویژه ساعت ۸:</b> انتشار بسته صبحگاهی (اوقات شرعی، هواشناسی و نرخ طلا و ارز)')
    if 7 <= h_now <= 13:
        cur_tasks.append('• ⚽️ <b>وظیفه ویژه صبح:</b> طراحی و انتشار استوری سه‌بعدی «بازی‌های امروز»')
    if iran_now.weekday() == 3 and (16 <= h_now <= 19):
        cur_tasks.append('• 🏛 <b>وظیفه ویژه پنجشنبه:</b> انتشار آلبوم ۴ اسلایدی «پنجشنبه‌های گردشگری»')
    if h_now == 21:
        cur_tasks.append('• 🎙 <b>وظیفه ویژه ساعت ۲۱:</b> تولید پادکست صوتی خلاصه اخبار شیراز + استوری شبانه')
    active_slot = get_active_reel_schedule_slot()
    if active_slot:
        cur_tasks.append(f'• 🎬 <b>نوبت فعال Reels در این ساعت:</b> ربات در حال شکار ویدیو برای اسلات ساعت <b>{to_persian_num(active_slot)}</b> است')
    daily_ok = (open(DAILY_FILE, encoding='utf-8').read().strip() == today_str) if os.path.exists(DAILY_FILE) else False
    matches_ok = (open(MATCHES_FILE, encoding='utf-8').read().strip() == today_str) if os.path.exists(MATCHES_FILE) else False
    night_ok = (open(NIGHT_FILE, encoding='utf-8').read().strip() == today_str) if os.path.exists(NIGHT_FILE) else False
    tour_ok = False
    if os.path.exists(TOURISM_STATE_FILE):
        tour_ok = open(TOURISM_STATE_FILE, encoding='utf-8').read().strip().startswith(today_str)
    done_reels = []
    if os.path.exists(INSTA_REEL_LOG):
        raw_rl = open(INSTA_REEL_LOG, encoding='utf-8').read().strip()
        if raw_rl.startswith(today_str + '|'):
            done_reels = [x for x in raw_rl.split('|')[1].split(',') if x]
    reel_lines = []
    now_mins = h_now * 60 + m_now
    for sh, sm in REEL_SCHEDULE_SLOTS:
        sid = f'{sh:02d}:{sm:02d}'
        s_mins = sh * 60 + sm
        if sid in done_reels:
            st_icon = '✅ منتشر شد'
        elif s_mins <= now_mins <= s_mins + 80:
            st_icon = '🎯 در نوبتِ این ساعت'
        elif now_mins > s_mins + 80:
            st_icon = '➖ عبور از بازه'
        else:
            st_icon = '⏳ در انتظار فرارسیدن ساعت'
        reel_lines.append(f'  ▫️ ساعت {to_persian_num(sid)} ⬅️ {st_icon}')
    last_post_str = 'هنوز پستی در این سشن ثبت نشده'
    if os.path.exists(INSTA_LOG):
        try:
            ts_p = int(open(INSTA_LOG).read().strip())
            mins_ago = max(0, int((time.time() - ts_p) // 60))
            last_post_str = f'{to_persian_num(mins_ago)} دقیقه پیش'
        except Exception:
            pass
    tasks_joined = '\n'.join(cur_tasks)
    reels_joined = '\n'.join(reel_lines)
    st_daily = '✅ انجام شد' if daily_ok else '⏳ در انتظار ساعت ۰۸:۰۰'
    st_matches = '✅ منتشر شد' if matches_ok else '⏳ در نوبت صبح'
    st_night = '✅ منتشر شد' if night_ok else '⏳ در انتظار ساعت ۲۱:۰۰'
    st_tour = ('✅ منتشر شد' if tour_ok else '⏳ در نوبت پنجشنبه ۱۶ تا ۱۹') if iran_now.weekday() == 3 else '📅 مخصوص روزهای پنجشنبه'
    rep = (
        f'📋 <b>گزارش برنامه زمان‌بندی و وضعیت لحظه‌ای ربات</b>\n'
        f'🕰 <b>زمان فعلی ایران:</b> {wk_fa} {today_str} | ساعت {time_fa}\n\n'
        f'🎯 <b>وظایف محول‌شده به ربات در این ساعت ({to_persian_num(h_now)}:۰۰):</b>\n{tasks_joined}\n\n'
        f'📊 <b>وضعیت انجام برنامه‌های ثابت امروز:</b>\n'
        f'• بسته صبحگاهی تلگرام (۰۸:۰۰): {st_daily}\n'
        f'• استوری سه‌بعدی بازی‌های امروز: {st_matches}\n'
        f'• پادکست و استوری شبانه (۲۱:۰۰): {st_night}\n'
        f'• آلبوم ۴ اسلایدی گردشگری: {st_tour}\n'
        f'• آخرین پست تصویری اینستاگرام: {last_post_str}\n'
        f'• خبرهای یکتای ثبت‌شده در ضدتکرار: {to_persian_num(len(sent_titles_list))} خبر\n\n'
        f'🎬 <b>جدول ۱۰ نوبته ریلزهای امروز ({to_persian_num(len(done_reels))} از ۱۰):</b>\n{reels_joined}\n\n'
        f'🛑 <b>{CHANNEL_SIGN}</b>'
    )
    return rep

# ==========================================
# ۸. مدیریت فونت فارسی و استخراج لید کامل خبر
# ==========================================
def ensure_persian_font():
    if not os.path.exists(FONT_FILE):
        try:
            r = requests.get('https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Bold.ttf', timeout=10)
            if r.status_code == 200:
                with open(FONT_FILE, 'wb') as f:
                    f.write(r.content)
        except Exception:
            pass

def load_font(size=44):
    ensure_persian_font()
    font_paths = [
        FONT_FILE,
        '/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()

def fetch_full_lead_from_page(page_url, fallback_summary=''):
    s = clean_agency_prefix(fallback_summary)
    s = re.sub(r'\.\.\.+|…', '', s).strip()
    if len(s) >= 85 and any(p in s for p in ['.', '!', '؟']):
        return s
    if page_url:
        try:
            r = requests.get(page_url, headers=HEADERS, timeout=7, verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            selectors = [
                'p.introtext', 'div.lead', 'p.lead', 'h3.lead',
                'div.item-summary', 'p.summary', 'div.subtitle',
                'meta[name="description"]', 'meta[property="og:description"]'
            ]
            for sel in selectors:
                el = soup.select_one(sel)
                if el:
                    txt = el.get('content', '').strip() if el.name == 'meta' else el.get_text().strip()
                    txt = clean_agency_prefix(re.sub(r'\s+', ' ', txt))
                    txt = re.sub(r'\.\.\.+|…', '', txt).strip()
                    if len(txt) > len(s) and len(txt) >= 55:
                        s = txt
                        break
            if len(s) < 65:
                for p in soup.find_all('p'):
                    pt = clean_agency_prefix(re.sub(r'\s+', ' ', p.get_text()).strip())
                    if len(pt) >= 75 and not any(bad in pt for bad in ['کلیه حقوق', 'کپی رایت', 'تلگرام', 'اینستاگرام']):
                        s = pt
                        break
        except Exception:
            pass
    return s

def extract_complete_lead(raw_summary, title_fallback, min_chars=65, max_chars=220):
    t = clean_agency_prefix(raw_summary or '')
    t = re.sub(r'\.\.\.+|…', '', t).strip()
    t = re.sub(r'\s+', ' ', t)
    if not t or len(t) < 30:
        base_t = clean_agency_prefix(title_fallback).rstrip('.!؟،: ')
        return f'بر اساس گزارش‌های منتشرشده، {base_t} و جزئیات تکمیلی این خبر اعلام شد.'
    sentences = [s.strip() for s in re.split(r'(?<=[\.\!\؟])\s+', t) if s.strip()]
    if sentences:
        accum = ''
        for s in sentences:
            cand = (accum + ' ' + s).strip() if accum else s
            if len(cand) <= max_chars:
                accum = cand
                if len(accum) >= min_chars:
                    break
            else:
                if not accum:
                    accum = s
                break
        if accum and len(accum) <= max_chars + 35:
            if accum[-1] not in ['.', '!', '؟', '»']:
                accum += '.'
            return accum
    clauses = [c.strip() for c in re.split(r'[،؛]', t) if c.strip()]
    accum_c = ''
    for c in clauses:
        cand = (accum_c + '، ' + c).strip('، ') if accum_c else c
        if len(cand) <= max_chars - 12:
            accum_c = cand
        else:
            break
    res = accum_c if len(accum_c) >= 40 else t[:max_chars].rsplit(' ', 1)[0]
    res = res.rstrip('،؛:- ')
    verbs = (
        'است', 'شد', 'بود', 'دارد', 'کرد', 'شود', 'اند', 'گردد', 'گردید',
        'یافت', 'رسید', 'ماند', 'داد', 'گرفت', 'کند', 'کنند', 'شمار می‌رود'
    )
    if not any(res.endswith(v) for v in verbs) and not res.endswith('.'):
        res += ' اعلام شد.'
    elif res[-1] not in ['.', '!', '؟', '»']:
        res += '.'
    return res

def fit_wrapped_text(text, base_font_size, min_font_size, base_width, max_lines):
    if not text:
        return [], load_font(base_font_size), base_font_size
    clean_t = re.sub(r'\s+', ' ', text).strip()
    for sz in range(base_font_size, min_font_size - 1, -2):
        char_w = int(base_width * (base_font_size / float(sz)))
        lines_w = textwrap.wrap(clean_t, width=char_w)
        if len(lines_w) <= max_lines:
            return lines_w, load_font(sz), sz
    for extra_sz in range(min_font_size - 2, 17, -2):
        char_w = int(base_width * (base_font_size / float(extra_sz)))
        lines_w = textwrap.wrap(clean_t, width=char_w)
        if len(lines_w) <= max_lines + 1:
            return lines_w, load_font(extra_sz), extra_sz
    char_w = int(base_width * (base_font_size / float(18)))
    return textwrap.wrap(clean_t, width=char_w), load_font(18), 18
    # ==========================================
# ۹. طراحی آلبوم ۴ اسلایدی «پنجشنبه‌های گردشگری»
# ==========================================
def create_heritage_bg(W, H):
    c = Image.new('RGBA', (W, H), (54, 34, 18, 255))
    d = ImageDraw.Draw(c)
    for y in range(0, H, 4):
        v = int(12 * abs((y / float(H)) - 0.5))
        d.line([(0, y), (W, y)], fill=(58 - v, 38 - v, 22 - v, 255), width=4)
    d.rectangle([26, 26, W - 26, H - 26], outline=(218, 175, 72, 255), width=4)
    d.rectangle([38, 38, W - 38, H - 38], outline=(242, 205, 110, 195), width=2)
    return c

def generate_thursday_tourism_4slides(item):
    slides = []
    try:
        ensure_persian_font()
        W, H = 1080, 1350
        img_bytes = None
        try:
            r = requests.get(item['img'], headers=HEADERS, timeout=10, verify=False)
            if r.status_code == 200 and len(r.content) > 2000:
                img_bytes = r.content
        except Exception:
            pass
        if not img_bytes and os.path.exists(LAST_IMG_FILE):
            with open(LAST_IMG_FILE, 'rb') as lf:
                img_bytes = lf.read()
        s1 = create_heritage_bg(W, H)
        if img_bytes:
            bg_b = Image.open(io.BytesIO(img_bytes)).convert('RGBA').resize((W, H), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(22))
            ov_dark = Image.new('RGBA', (W, H), (42, 26, 12, 185))
            s1 = Image.alpha_composite(bg_b, ov_dark)
        d1 = ImageDraw.Draw(s1)
        d1.rectangle([26, 26, W - 26, H - 26], outline=(218, 175, 72, 255), width=4)
        d1.rectangle([38, 38, W - 38, H - 38], outline=(242, 205, 110, 195), width=2)
        f_3d_1 = load_font(88)
        f_3d_2 = load_font(96)
        t1, t2 = 'پنجشنبه‌های', 'گردشگری'
        b1 = d1.textbbox((0, 0), t1, font=f_3d_1)
        b2 = d1.textbbox((0, 0), t2, font=f_3d_2)
        x1 = (W - (b1[2] - b1[0])) / 2
        x2 = (W - (b2[2] - b2[0])) / 2
        for off in range(10, 0, -2):
            d1.text((x1 + off, 55 + off), t1, font=f_3d_1, fill=(28, 14, 5, 240))
            d1.text((x2 + off, 165 + off), t2, font=f_3d_2, fill=(28, 14, 5, 240))
        d1.text((x1, 55), t1, font=f_3d_1, fill=(255, 248, 225, 255))
        d1.text((x2, 165), t2, font=f_3d_2, fill=(242, 202, 100, 255))
        ax, ay, aw, ah = 135, 310, W - 270, 680
        d1.rounded_rectangle([ax - 12, ay - 12, ax + aw + 12, ay + ah + 12], radius=160, fill=(38, 24, 12, 255), outline=(218, 175, 72, 255), width=5)
        if img_bytes:
            im_c = Image.open(io.BytesIO(img_bytes)).convert('RGB')
            iw, ih = im_c.size
            sc = max(aw / iw, ah / ih)
            nw, nh = int(iw * sc), int(ih * sc)
            im_cr = im_c.resize((nw, nh), Image.Resampling.LANCZOS).crop(((nw - aw) // 2, (nh - ah) // 2, (nw - aw) // 2 + aw, (nh - ah) // 2 + ah))
            mask = Image.new('L', (aw, ah), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, aw, ah], radius=150, fill=255)
            s1.paste(im_cr, (ax, ay), mask)
        d1.rounded_rectangle([90, 1035, W - 90, 1205], radius=24, fill=(48, 30, 16, 245), outline=(218, 175, 72, 255), width=4)
        sub_lines, f_sub1, sz_s1 = fit_wrapped_text(f"این هفته: {item['name']}", base_font_size=42, min_font_size=30, base_width=28, max_lines=2)
        y_s1 = 1065 if len(sub_lines) > 1 else 1092
        for l in sub_lines:
            bb = d1.textbbox((0, 0), l, font=f_sub1)
            d1.text(((W - (bb[2] - bb[0])) / 2, y_s1), l, font=f_sub1, fill=(255, 248, 225, 255))
            y_s1 += int(sz_s1 * 1.45)
        d1.rounded_rectangle([310, 1248, W - 310, 1308], radius=20, fill=(218, 175, 72, 255))
        f_id = load_font(28)
        bb_id = d1.textbbox((0, 0), '@ShirazLastNews', font=f_id)
        d1.text(((W - (bb_id[2] - bb_id[0])) / 2, 1260), '@ShirazLastNews', font=f_id, fill=(32, 18, 8, 255))
        p1 = 'tourism_slide1.jpg'
        s1.convert('RGB').save(p1, format='JPEG', quality=95)
        slides.append(p1)

        s2 = create_heritage_bg(W, H)
        d2 = ImageDraw.Draw(s2)
        f_h2 = load_font(44)
        h2_txt = f"🏛 درباره {item['name'].split('(')[0].strip()}"
        bb_h2 = d2.textbbox((0, 0), h2_txt, font=f_h2)
        d2.text(((W - (bb_h2[2] - bb_h2[0])) / 2, 95), h2_txt, font=f_h2, fill=(242, 202, 100, 255))
        d2.rounded_rectangle([75, 200, W - 75, 1140], radius=34, fill=(248, 241, 225, 255), outline=(195, 148, 52, 255), width=5)
        d2.rounded_rectangle([92, 217, W - 92, 1123], radius=26, outline=(218, 175, 72, 180), width=2)
        desc_lines, f_desc, sz_d = fit_wrapped_text(item['desc'], base_font_size=36, min_font_size=26, base_width=32, max_lines=9)
        y2 = 280
        for dl in desc_lines:
            bb = d2.textbbox((0, 0), dl, font=f_desc)
            d2.text(((W - (bb[2] - bb[0])) / 2, y2), dl, font=f_desc, fill=(42, 26, 14, 255))
            y2 += int(sz_d * 1.65)
        d2.rounded_rectangle([340, 1168, W - 340, 1222], radius=18, fill=(155, 22, 28, 255))
        f_br = load_font(26)
        br_t = 'آخرین خبرهای شیراز'
        bb_br = d2.textbbox((0, 0), br_t, font=f_br)
        d2.text(((W - (bb_br[2] - bb_br[0])) / 2, 1178), br_t, font=f_br, fill=(255, 255, 255, 255))
        d2.rounded_rectangle([310, 1248, W - 310, 1308], radius=20, fill=(218, 175, 72, 255))
        d2.text(((W - (bb_id[2] - bb_id[0])) / 2, 1260), '@ShirazLastNews', font=f_id, fill=(32, 18, 8, 255))
        p2 = 'tourism_slide2.jpg'
        s2.convert('RGB').save(p2, format='JPEG', quality=95)
        slides.append(p2)

        s3 = create_heritage_bg(W, H)
        d3 = ImageDraw.Draw(s3)
        h3_txt = '📍 موقعیت و فاصله از شهرهای مهم فارس'
        bb_h3 = d3.textbbox((0, 0), h3_txt, font=f_h2)
        d3.text(((W - (bb_h3[2] - bb_h3[0])) / 2, 95), h3_txt, font=f_h2, fill=(242, 202, 100, 255))
        d3.rounded_rectangle([75, 200, W - 75, 1140], radius=34, fill=(248, 241, 225, 255), outline=(195, 148, 52, 255), width=5)
        loc_lines, f_loc, sz_l = fit_wrapped_text(item['loc_desc'], base_font_size=34, min_font_size=26, base_width=34, max_lines=3)
        y3 = 260
        for ll in loc_lines:
            bb = d3.textbbox((0, 0), ll, font=f_loc)
            d3.text(((W - (bb[2] - bb[0])) / 2, y3), ll, font=f_loc, fill=(42, 26, 14, 255))
            y3 += int(sz_l * 1.55)
        d3.line([(140, y3 + 20), (W - 140, y3 + 20)], fill=(195, 148, 52, 200), width=3)
        y3 += 55
        f_dh = load_font(34)
        dh_t = '🚗 فاصله زمانی و مسافتی تا این بنای تاریخی:'
        bb_dh = d3.textbbox((0, 0), dh_t, font=f_dh)
        d3.text((W - 125 - (bb_dh[2] - bb_dh[0]), y3), dh_t, font=f_dh, fill=(145, 22, 28, 255))
        y3 += 75
        f_dist = load_font(33)
        for dst_item in item['distances']:
            if item.get('in_shiraz') and dst_item.startswith('شیراز'):
                continue
            d_line = f'• {dst_item}'
            bb = d3.textbbox((0, 0), d_line, font=f_dist)
            d3.text((W - 135 - (bb[2] - bb[0]), y3), d_line, font=f_dist, fill=(38, 24, 12, 255))
            y3 += 78
        draw_luxury_brand_badge(d3, W // 2, 1065, scale=0.82)
        d3.rounded_rectangle([310, 1248, W - 310, 1308], radius=20, fill=(218, 175, 72, 255))
        d3.text(((W - (bb_id[2] - bb_id[0])) / 2, 1260), '@ShirazLastNews', font=f_id, fill=(32, 18, 8, 255))
        p3 = 'tourism_slide3.jpg'
        s3.convert('RGB').save(p3, format='JPEG', quality=95)
        slides.append(p3)

        s4 = create_heritage_bg(W, H)
        d4 = ImageDraw.Draw(s4)
        cx, cy, cr = W // 2, 640, 445
        d4.ellipse([cx - cr - 14, cy - cr - 14, cx + cr + 14, cy + cr + 14], fill=(218, 175, 72, 255))
        d4.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(12, 22, 42, 255), outline=(245, 210, 110, 255), width=5)
        f_c1 = load_font(46)
        t_c1 = '📢 با ما، فارس را زیباتر ببینید!'
        bb = d4.textbbox((0, 0), t_c1, font=f_c1)
        d4.text(((W - (bb[2] - bb[0])) / 2, 340), t_c1, font=f_c1, fill=(242, 202, 100, 255))
        cta_body = 'همشهری عزیز، برای کشف زیباترین جاذبه‌های گردشگری، تاریخی و تفریحی استان فارس و دریافت فوری‌ترین اخبار روزانه شیراز، همراه ما باشید.'
        c_lines, f_cb, sz_cb = fit_wrapped_text(cta_body, base_font_size=34, min_font_size=28, base_width=28, max_lines=4)
        yc = 440
        for cl in c_lines:
            bb = d4.textbbox((0, 0), cl, font=f_cb)
            d4.text(((W - (bb[2] - bb[0])) / 2, yc), cl, font=f_cb, fill=(255, 255, 255, 255))
            yc += int(sz_cb * 1.55)
        f_fl = load_font(28)
        fl_t = '🔴 پیج اینستاگرام و کانال تلگرام ما را دنبال کنید:'
        bb = d4.textbbox((0, 0), fl_t, font=f_fl)
        d4.text(((W - (bb[2] - bb[0])) / 2, 710), fl_t, font=f_fl, fill=(242, 202, 100, 255))
        f_big_id = load_font(54)
        bb = d4.textbbox((0, 0), '@ShirazLastNews', font=f_big_id)
        d4.text(((W - (bb[2] - bb[0])) / 2, 775), '@ShirazLastNews', font=f_big_id, fill=(255, 255, 255, 255))
        f_sh = load_font(27)
        sh_t = '👈 این پست را برای دوستانت بفرست تا با هم به شیرازگردی بریم!'
        bb = d4.textbbox((0, 0), sh_t, font=f_sh)
        d4.text(((W - (bb[2] - bb[0])) / 2, 885), sh_t, font=f_sh, fill=(242, 202, 100, 255))
        d4.rounded_rectangle([310, 1248, W - 310, 1308], radius=20, fill=(218, 175, 72, 255))
        d4.text(((W - (bb_id[2] - bb_id[0])) / 2, 1260), '@ShirazLastNews', font=f_id, fill=(32, 18, 8, 255))
        p4 = 'tourism_slide4.jpg'
        s4.convert('RGB').save(p4, format='JPEG', quality=95)
        slides.append(p4)
    except Exception as e:
        print('Tourism 4-slides error:', e)
    return slides

def check_thursday_tourism_post(insta_cl):
    iran_now = datetime.utcnow() + timedelta(hours=3, minutes=30)
    if iran_now.weekday() != 3:
        return
    today_str, hour_now = get_iran_jalali_date()
    if not (16 <= hour_now <= 19):
        return
    last_date, last_idx = '', -1
    if os.path.exists(TOURISM_STATE_FILE):
        raw_st = open(TOURISM_STATE_FILE, encoding='utf-8').read().strip()
        if '|' in raw_st:
            p = raw_st.split('|')
            last_date = p[0]
            try:
                last_idx = int(p[1])
            except Exception:
                last_idx = -1
    if last_date == today_str:
        return
    next_idx = (last_idx + 1) % len(TOURISM_DB)
    item = TOURISM_DB[next_idx]
    slides = generate_thursday_tourism_4slides(item)
    if len(slides) < 4:
        return
    dist_text = '\n'.join([f'✅ {d}' for d in item['distances'] if not (item.get('in_shiraz') and d.startswith('شیراز'))])
    tg_cap = (
        f"⭕️ <b>پنجشنبه‌های گردشگری | این هفته: {item['name']}</b>\n\n"
        f"✅ {item['desc']}\n\n"
        f"📍 <b>موقعیت:</b> {item['loc_desc']}\n\n"
        f"🚗 <b>فاصله از شهرهای مهم فارس:</b>\n{dist_text}\n\n"
        f"🛑 <b>{CHANNEL_SIGN}</b>"
    )
    try:
        media_group = []
        for i, sp in enumerate(slides):
            with open(sp, 'rb') as f:
                img_data = f.read()
            if i == 0:
                media_group.append(InputMediaPhoto(img_data, caption=tg_cap, parse_mode='HTML'))
            else:
                media_group.append(InputMediaPhoto(img_data))
        bot.send_media_group(TARGET_CHAT, media_group, disable_notification=is_silent_hours())
    except Exception as e:
        print('Telegram tourism album error:', e)
    if insta_cl:
        try:
            insta_cap = (
                f"⭕️ پنجشنبه‌های شیرازگردی | این هفته: {item['name']}\n\n"
                f"✅ ورق بزنید 👈 تا به امروز چند بار از این مکان تماشایی دیدن کرده‌اید؟ بهترین خاطره‌تان را در کامنت‌ها بنویسید👇\n\n"
                f"✅ {item['desc']}\n\n"
                f"📍 {item['loc_desc']}\n\n"
                f"🚗 فاصله‌ها:\n{dist_text}\n\n"
                f"✅ برای کشف جاذبه‌های استان فارس و دریافت فوری‌ترین خبرهای شیراز، پیج ما را دنبال کنید:\n"
                f"🛑 @{INSTA_USER.replace('@', '')}\n\n"
                f"#شیراز #شیرازگردی #فارس #گردشگری #ایرانگردی #تخت_جمشید #حافظیه #نصیرالملک #اکسپلور #وایرال #shiraz #iran #explore"
            )
            insta_cl.album_upload(slides, caption=insta_cap)
            upload_story_with_native_poll(insta_cl, slides[0])
        except Exception as e:
            print('Instagram tourism album error:', e)
    with open(TOURISM_STATE_FILE, 'w', encoding='utf-8') as f:
        f.write(f'{today_str}|{next_idx}')

# ==========================================
# ۱۰. اسکرپینگ و طراحی استوری‌های سه‌بعدی ورزشی و فوتبال زنده
# ==========================================
def match_target_league(league_title):
    t = league_title.strip()
    if any(x in t for x in ['لیگ برتر ایران', 'خلیج فارس', 'برتر حرفه ای', 'فجر', 'آزادگان', 'جام حذفی']):
        return 'لیگ برتر ایران'
    if 'لالیگا' in t or ('اسپانیا' in t and 'لیگ' in t):
        return 'لالیگا اسپانیا'
    if ('لیگ برتر انگلیس' in t) or ('جزیره' in t) or ('انگلیس' in t and 'برتر' in t):
        return 'لیگ برتر انگلیس'
    if 'بوندسلیگا' in t or 'بوندس‌لیگا' in t or ('آلمان' in t and 'لیگ' in t):
        return 'بوندسلیگا آلمان'
    if 'سری آ' in t or ('ایتالیا' in t and 'لیگ' in t):
        return 'سری آ ایتالیا'
    if 'قهرمانان اروپا' in t or 'نخبه' in t or 'آسیا' in t:
        return 'لیگ قهرمانان'
    return None

def tr_team_fa(en_name):
    clean_en = en_name.strip()
    if not re.search(r'[A-Za-z]', clean_en):
        return clean_en[:15]
    if clean_en in TEAM_EN_TO_FA:
        return TEAM_EN_TO_FA[clean_en]
    for k, v in TEAM_EN_TO_FA.items():
        if k.lower() in clean_en.lower() or clean_en.lower() in k.lower():
            return v
    return 'تیم منتخب'

def scrape_football360_today_matches():
    matches = []
    seen = set()
    try:
        for f_url in ['https://football360.ir/results', 'https://football360.ir/api/cms/v2/matches/today', 'https://api.football360.ir/api/v1/matches/live']:
            try:
                r = requests.get(f_url, headers=HEADERS, timeout=9, verify=False)
                if r.status_code != 200:
                    continue
                if 'application/json' in r.headers.get('Content-Type', ''):
                    d = r.json()
                    items = d if isinstance(d, list) else d.get('data', d.get('matches', d.get('competitions', [])))
                    for it in items:
                        lg_raw = str(it.get('competition', {}).get('title', it.get('title', 'لیگ برتر ایران')))
                        lg = match_target_league(lg_raw) or 'لیگ برتر ایران'
                        m_list = it.get('matches', [it]) if isinstance(it, dict) else []
                        for m in m_list:
                            h_obj = m.get('home_team', m.get('home', m.get('host', {})))
                            a_obj = m.get('away_team', m.get('away', m.get('guest', {})))
                            h_n = tr_team_fa(str(h_obj.get('title', h_obj.get('name', '')) if isinstance(h_obj, dict) else h_obj))
                            a_n = tr_team_fa(str(a_obj.get('title', a_obj.get('name', '')) if isinstance(a_obj, dict) else a_obj))
                            h_l = h_obj.get('logo', h_obj.get('image', '')) if isinstance(h_obj, dict) else ''
                            a_l = a_obj.get('logo', a_obj.get('image', '')) if isinstance(a_obj, dict) else ''
                            tm = to_persian_num(str(m.get('time', m.get('start_time', '۱۹:۰۰')))[:5])
                            if h_n and a_n and h_n != 'تیم منتخب' and f'{h_n}_{a_n}' not in seen:
                                seen.add(f'{h_n}_{a_n}')
                                matches.append({'league': lg, 'home': h_n, 'away': a_n, 'time': tm, 'home_logo': h_l, 'away_logo': a_l})
                else:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    nxt = soup.find('script', id='__NEXT_DATA__')
                    if nxt and nxt.string:
                        txt_j = nxt.string
                        pairs = re.findall(r'"home[^"]*"\s*:\s*\{[^}]*"title"\s*:\s*"([^"]+)"[^}]*\}\s*,\s*"away[^"]*"\s*:\s*\{[^}]*"title"\s*:\s*"([^"]+)"', txt_j)
                        for h_raw, a_raw in pairs[:6]:
                            h_n, a_n = tr_team_fa(h_raw), tr_team_fa(a_raw)
                            if h_n and a_n and f'{h_n}_{a_n}' not in seen:
                                seen.add(f'{h_n}_{a_n}')
                                matches.append({'league': 'مسابقات مهم روز', 'home': h_n, 'away': a_n, 'time': '۲۰:۰۰', 'home_logo': '', 'away_logo': ''})
            except Exception:
                pass
    except Exception as e:
        print('Football360 scrape error:', e)
    return matches[:4]

def fetch_espn_matches_for_date(date_yyyymmdd):
    found = []
    leagues = [
        ('eng.1', 'لیگ برتر انگلیس'),
        ('esp.1', 'لالیگا اسپانیا'),
        ('ger.1', 'بوندسلیگا آلمان'),
        ('ita.1', 'سری آ ایتالیا')
    ]
    for code, fa_lg in leagues:
        try:
            url = f'https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={date_yyyymmdd}'
            d = requests.get(url, headers=HEADERS, timeout=8).json()
            for ev in d.get('events', []):
                comps = ev.get('competitions', [])
                if not comps:
                    continue
                competitors = comps[0].get('competitors', [])
                if len(competitors) < 2:
                    continue
                home_c = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
                away_c = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])
                h_name = tr_team_fa(home_c.get('team', {}).get('displayName', ''))
                a_name = tr_team_fa(away_c.get('team', {}).get('displayName', ''))
                if h_name == 'تیم منتخب' or a_name == 'تیم منتخب':
                    continue
                h_logo = home_c.get('team', {}).get('logo', '')
                a_logo = away_c.get('team', {}).get('logo', '')
                raw_dt = ev.get('date', '')
                tm_fa = '۲۱:۰۰'
                if 'T' in raw_dt:
                    try:
                        dt_utc = datetime.strptime(raw_dt[:16], '%Y-%m-%dT%H:%M')
                        dt_ir = dt_utc + timedelta(hours=3, minutes=30)
                        tm_fa = to_persian_num(dt_ir.strftime('%H:%M'))
                    except Exception:
                        pass
                found.append({'league': fa_lg, 'home': h_name, 'away': a_name, 'time': tm_fa, 'home_logo': h_logo, 'away_logo': a_logo})
        except Exception as e:
            print('ESPN API error:', e)
    return found

def scrape_varzesh3_today_matches():
    matches = []
    seen_pairs = set()
    for f360_m in scrape_football360_today_matches():
        pk = f"{f360_m['home']}_{f360_m['away']}"
        if pk not in seen_pairs:
            seen_pairs.add(pk)
            matches.append(f360_m)
    try:
        for v_url in ['https://www.varzesh3.com/livescore', 'https://web-api.varzesh3.com/v1.0/livescore/today']:
            r = requests.get(v_url, headers=HEADERS, timeout=10, verify=False)
            if r.status_code != 200:
                continue
            if 'application/json' in r.headers.get('Content-Type', ''):
                data = r.json()
                groups_list = data if isinstance(data, list) else data.get('leagues', data.get('data', []))
                for grp in groups_list:
                    lg_name = match_target_league(str(grp.get('title', grp.get('leagueName', ''))))
                    if not lg_name:
                        continue
                    for m in grp.get('matches', grp.get('games', [])):
                        t1 = tr_team_fa(str(m.get('host', m.get('home', ''))).strip())
                        t2 = tr_team_fa(str(m.get('guest', m.get('away', ''))).strip())
                        tm = to_persian_num(str(m.get('time', m.get('startTime', '۱۸:۰۰'))))
                        if t1 and t2 and t1 != 'تیم منتخب' and t2 != 'تیم منتخب' and f'{t1}_{t2}' not in seen_pairs:
                            seen_pairs.add(f'{t1}_{t2}')
                            matches.append({'league': lg_name, 'home': t1, 'away': t2, 'time': tm, 'home_logo': m.get('hostLogo', ''), 'away_logo': m.get('guestLogo', '')})
            else:
                soup = BeautifulSoup(r.text, 'html.parser')
                blocks = soup.select('.livescore-league, .league-box, .match-group, .competition-box, section, .widget')
                for b in blocks:
                    h_el = b.select_one('.league-title, .header-title, .title, h2, h3, .competition-title')
                    if not h_el:
                        continue
                    lg_name = match_target_league(h_el.get_text())
                    if not lg_name:
                        continue
                    rows = b.select('.match-row, .match-item, .game-row, tr, .live-match')
                    for row in rows:
                        t_els = row.select('.team-name, .team, .host, .guest, .home-team, .away-team, td.team')
                        if len(t_els) >= 2:
                            t1 = tr_team_fa(re.sub(r'\s+', ' ', t_els[0].get_text()).strip())
                            t2 = tr_team_fa(re.sub(r'\s+', ' ', t_els[1].get_text()).strip())
                            if not t1 or not t2 or t1 == t2 or t1 == 'تیم منتخب' or f'{t1}_{t2}' in seen_pairs:
                                continue
                            seen_pairs.add(f'{t1}_{t2}')
                            tm_el = row.select_one('.match-time, .time, .start-time, .status, td.time')
                            tm_txt = re.sub(r'\s+', ' ', tm_el.get_text()).strip() if tm_el else ''
                            m_time = re.search(r'\d{1,2}:\d{2}', tm_txt)
                            final_time = to_persian_num(m_time.group(0)) if m_time else '۱۹:۰۰'
                            logos = []
                            for img in row.find_all('img'):
                                src = img.get('data-src') or img.get('src') or ''
                                if src and not any(x in src.lower() for x in ['pixel', 'blank', 'icon']):
                                    if src.startswith('//'):
                                        src = 'https:' + src
                                    elif src.startswith('/'):
                                        src = 'https://www.varzesh3.com' + src
                                    logos.append(src)
                            matches.append({
                                'league': lg_name, 'home': t1, 'away': t2, 'time': final_time,
                                'home_logo': logos[0] if len(logos) >= 1 else '',
                                'away_logo': logos[1] if len(logos) >= 2 else ''
                            })
    except Exception as e:
        print('Varzesh3 scrape error:', e)
    iran_now = datetime.utcnow() + timedelta(hours=3, minutes=30)
    for day_offset in [0, 1, 2]:
        if len(matches) >= 4:
            break
        d_str = (iran_now + timedelta(days=day_offset)).strftime('%Y%m%d')
        espn_m = fetch_espn_matches_for_date(d_str)
        for em in espn_m:
            pk = f"{em['home']}_{em['away']}"
            if pk not in seen_pairs:
                seen_pairs.add(pk)
                matches.append(em)
    if len(matches) < 4:
        fallback_top = [
            {'league': 'لیگ برتر ایران', 'home': 'پرسپولیس', 'away': 'فجر سپاسی', 'time': '۱۷:۳۰', 'home_logo': '', 'away_logo': ''},
            {'league': 'لیگ برتر ایران', 'home': 'سپاهان', 'away': 'استقلال', 'time': '۱۹:۰۰', 'home_logo': '', 'away_logo': ''},
            {'league': 'لالیگا اسپانیا', 'home': 'بارسلونا', 'away': 'رئال مادرید', 'time': '۲۲:۳۰', 'home_logo': '', 'away_logo': ''},
            {'league': 'لیگ برتر انگلیس', 'home': 'لیورپول', 'away': 'آرسنال', 'time': '۲۱:۰۰', 'home_logo': '', 'away_logo': ''}
        ]
        for fm in fallback_top:
            if len(matches) >= 4:
                break
            pk = f"{fm['home']}_{fm['away']}"
            if pk not in seen_pairs:
                seen_pairs.add(pk)
                matches.append(fm)
    return matches[:4]

def fetch_live_iran_league_matches():
    live_list = []
    seen = set()
    try:
        for f_url in ['https://api.football360.ir/api/v1/matches/live', 'https://football360.ir/api/cms/v2/matches/today', 'https://web-api.varzesh3.com/v1.0/livescore/today']:
            try:
                r = requests.get(f_url, headers=HEADERS, timeout=8, verify=False)
                if r.status_code != 200 or 'application/json' not in r.headers.get('Content-Type', ''):
                    continue
                d = r.json()
                items = d if isinstance(d, list) else d.get('data', d.get('leagues', d.get('matches', [])))
                for grp in items:
                    lg_raw = str(grp.get('title', grp.get('leagueName', grp.get('competition', {}).get('title', ''))))
                    m_arr = grp.get('matches', grp.get('games', [grp])) if isinstance(grp, dict) else []
                    for m in m_arr:
                        if not isinstance(m, dict):
                            continue
                        h_obj = m.get('home_team', m.get('home', m.get('host', {})))
                        a_obj = m.get('away_team', m.get('away', m.get('guest', {})))
                        h_n = str(h_obj.get('title', h_obj.get('name', '')) if isinstance(h_obj, dict) else h_obj).strip()
                        a_n = str(a_obj.get('title', a_obj.get('name', '')) if isinstance(a_obj, dict) else a_obj).strip()
                        if not h_n or not a_n:
                            continue
                        is_iran_lg = ('ایران' in lg_raw or 'خلیج فارس' in lg_raw or 'حذفی' in lg_raw or any(cl in (h_n + ' ' + a_n) for cl in IRAN_LEAGUE_CLUBS))
                        if not is_iran_lg:
                            continue
                        h_sc = m.get('home_score', m.get('hostScore', m.get('home_goals', None)))
                        a_sc = m.get('away_score', m.get('guestScore', m.get('away_goals', None)))
                        if h_sc is None and isinstance(h_obj, dict):
                            h_sc = h_obj.get('score', 0)
                        if a_sc is None and isinstance(a_obj, dict):
                            a_sc = a_obj.get('score', 0)
                        try:
                            h_sc = int(str(h_sc).translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')))
                        except Exception:
                            h_sc = 0
                        try:
                            a_sc = int(str(a_sc).translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')))
                        except Exception:
                            a_sc = 0
                        st_raw = str(m.get('status', m.get('state', m.get('time', m.get('minute', ''))))).strip()
                        h_logo = h_obj.get('logo', m.get('hostLogo', '')) if isinstance(h_obj, dict) else str(m.get('hostLogo', ''))
                        a_logo = a_obj.get('logo', m.get('guestLogo', '')) if isinstance(a_obj, dict) else str(m.get('guestLogo', ''))
                        pk = f'{h_n}_{a_n}'
                        if pk not in seen:
                            seen.add(pk)
                            live_list.append({'home': h_n, 'away': a_n, 'h_score': h_sc, 'a_score': a_sc, 'status': st_raw, 'home_logo': h_logo, 'away_logo': a_logo})
            except Exception:
                pass
        r_v3 = requests.get('https://www.varzesh3.com/livescore', headers=HEADERS, timeout=9, verify=False)
        if r_v3.status_code == 200:
            soup = BeautifulSoup(r_v3.text, 'html.parser')
            blocks = soup.select('.livescore-league, .league-box, .match-group, .competition-box, section')
            for b in blocks:
                h_el = b.select_one('.league-title, .header-title, .title, h2, h3, .competition-title')
                lg_t = h_el.get_text() if h_el else ''
                rows = b.select('.match-row, .match-item, .game-row, tr, .live-match')
                for row in rows:
                    t_els = row.select('.team-name, .team, .host, .guest, .home-team, .away-team, td.team')
                    if len(t_els) < 2:
                        continue
                    h_n = re.sub(r'\s+', ' ', t_els[0].get_text()).strip()
                    a_n = re.sub(r'\s+', ' ', t_els[1].get_text()).strip()
                    if not ('ایران' in lg_t or 'خلیج فارس' in lg_t or any(cl in (h_n + ' ' + a_n) for cl in IRAN_LEAGUE_CLUBS)):
                        continue
                    pk = f'{h_n}_{a_n}'
                    if pk in seen:
                        continue
                    sc_el = row.select_one('.score, .match-score, .result, td.score')
                    sc_txt = sc_el.get_text().strip() if sc_el else ''
                    sc_nums = re.findall(r'[0-9۰-۹]+', sc_txt)
                    if len(sc_nums) >= 2:
                        h_sc = int(sc_nums[0].translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')))
                        a_sc = int(sc_nums[1].translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')))
                    else:
                        h_sc, a_sc = 0, 0
                    tm_el = row.select_one('.match-time, .time, .start-time, .status, td.time')
                    st_raw = re.sub(r'\s+', ' ', tm_el.get_text()).strip() if tm_el else ''
                    seen.add(pk)
                    live_list.append({'home': h_n, 'away': a_n, 'h_score': h_sc, 'a_score': a_sc, 'status': st_raw, 'home_logo': '', 'away_logo': ''})
    except Exception as e:
        print('Live Iran league scrape error:', e)
    return live_list

def fetch_team_badge_img(team_name, logo_url, size=92):
    url_to_try = logo_url
    if not url_to_try:
        for k, v in TEAM_LOGO_FALLBACKS.items():
            if k in team_name:
                url_to_try = v
                break
    if url_to_try:
        try:
            r = requests.get(url_to_try, headers=HEADERS, timeout=6, verify=False)
            if r.status_code == 200 and len(r.content) > 300:
                im = Image.open(io.BytesIO(r.content)).convert('RGBA')
                im.thumbnail((size - 14, size - 14), Image.Resampling.LANCZOS)
                bg = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                d = ImageDraw.Draw(bg)
                d.ellipse([0, 0, size - 1, size - 1], fill=(14, 24, 44, 255), outline=(235, 195, 85, 255), width=4)
                d.ellipse([5, 5, size - 6, size - 6], fill=(255, 255, 255, 245))
                bg.alpha_composite(im, ((size - im.width) // 2, (size - im.height) // 2))
                return bg
        except Exception:
            pass
    bg = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(bg)
    d.ellipse([0, 0, size - 1, size - 1], fill=(18, 32, 58, 255), outline=(235, 195, 85, 255), width=4)
    f_in = load_font(int(size * 0.32))
    short_w = re.sub(r'[A-Za-z]', '', team_name).strip().split()[0][:5] if team_name else 'تیم'
    bb = d.textbbox((0, 0), short_w, font=f_in)
    d.text(((size - (bb[2] - bb[0])) / 2, (size - (bb[3] - bb[1])) / 2 - 4), short_w, font=f_in, fill=(245, 210, 105, 255))
    return bg

def get_stadium_atmosphere_bg(W, H):
    if os.path.exists(STADIUM_BG_CACHE):
        try:
            return Image.open(STADIUM_BG_CACHE).convert('RGBA').resize((W, H), Image.Resampling.LANCZOS)
        except Exception:
            pass
    for u_st in ['https://images.unsplash.com/photo-1518091043644-c1d4457512c6?w=1080&q=80', 'https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1080&q=80']:
        try:
            r = requests.get(u_st, timeout=8)
            if r.status_code == 200 and len(r.content) > 5000:
                with open(STADIUM_BG_CACHE, 'wb') as f:
                    f.write(r.content)
                im = Image.open(io.BytesIO(r.content)).convert('RGBA')
                iw, ih = im.size
                sc = max(W / iw, H / ih)
                nw, nh = int(iw * sc), int(ih * sc)
                return im.resize((nw, nh), Image.Resampling.LANCZOS).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        except Exception:
            pass
    canvas = Image.new('RGBA', (W, H), (8, 18, 32, 255))
    d = ImageDraw.Draw(canvas)
    for y in range(H):
        c_r = int(8 + 12 * (y / float(H)))
        c_g = int(18 + 38 * (y / float(H)))
        c_b = int(32 + 20 * (y / float(H)))
        d.line([(0, y), (W, y)], fill=(c_r, c_g, c_b, 255))
    return canvas

def make_gold_metallic_box(w, h, radius=20):
    box = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    grad = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(h):
        ratio = abs((y / float(max(1, h - 1))) - 0.35)
        r = max(165, min(255, int(248 - 70 * ratio)))
        g = max(125, min(230, int(212 - 75 * ratio)))
        b = max(35, min(145, int(118 - 65 * ratio)))
        gd.line([(0, y), (w, y)], fill=(r, g, b, 255))
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    box.paste(grad, (0, 0), mask)
    bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, outline=(255, 238, 170, 255), width=3)
    bd.rounded_rectangle([3, 3, w - 4, h - 4], radius=max(4, radius - 3), outline=(140, 95, 20, 200), width=2)
    return box

def create_3d_live_match_story(match_data, banner_text='گزارش زنده و لحظه‌ای لیگ برتر ایران'):
    try:
        ensure_persian_font()
        W, H = 1080, 1920
        bg = get_stadium_atmosphere_bg(W, H)
        dark_ov = Image.new('RGBA', (W, H), (4, 8, 18, 195))
        canvas = Image.alpha_composite(bg, dark_ov)
        lasers = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lasers)
        cyan_beams = [(-40, 260, 480, 1920), (85, 0, 420, 1920), (-60, 620, 640, 1650), (0, 1280, 520, 680)]
        for x1, y1, x2, y2 in cyan_beams:
            ld.line([(x1, y1), (x2, y2)], fill=(0, 235, 255, 115), width=14)
            ld.line([(x1, y1), (x2, y2)], fill=(185, 252, 255, 215), width=4)
        red_beams = [(W + 40, 260, W - 480, 1920), (W - 85, 0, W - 420, 1920), (W + 60, 620, W - 640, 1650), (W, 1280, W - 520, 680)]
        for x1, y1, x2, y2 in red_beams:
            ld.line([(x1, y1), (x2, y2)], fill=(255, 28, 65, 120), width=14)
            ld.line([(x1, y1), (x2, y2)], fill=(255, 180, 195, 215), width=4)
        ld.ellipse([-120, 520, 260, 820], fill=(200, 245, 255, 140))
        ld.ellipse([W - 260, 520, W + 120, 820], fill=(255, 220, 225, 140))
        flames = [(x_f, random.randint(1335, 1415), random.randint(36, 75)) for x_f in range(135, W - 135, 38)]
        for fx, fy, fr in flames:
            ld.ellipse([fx - fr, fy - fr, fx + fr, fy + fr + 45], fill=(255, 125, 15, 145))
            ld.ellipse([fx - fr // 2, fy - fr // 2 + 10, fx + fr // 2, fy + fr], fill=(255, 225, 85, 195))
        canvas = Image.alpha_composite(canvas, lasers.filter(ImageFilter.GaussianBlur(8)))
        sharp_l = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sld = ImageDraw.Draw(sharp_l)
        for x1, y1, x2, y2 in cyan_beams:
            sld.line([(x1, y1), (x2, y2)], fill=(160, 250, 255, 190), width=3)
        for x1, y1, x2, y2 in red_beams:
            sld.line([(x1, y1), (x2, y2)], fill=(255, 130, 150, 190), width=3)
        random.seed(99)
        for _ in range(130):
            sx = random.randint(15, W - 15)
            sy = random.randint(140, H - 180)
            sr = random.randint(2, 5)
            sld.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 215, 95, random.randint(140, 250)))
        canvas = Image.alpha_composite(canvas, sharp_l)
        draw = ImageDraw.Draw(canvas)
        draw_luxury_brand_badge(draw, W - 130, 65, scale=1.22)
        pill_w, pill_h = 460, 88
        pill_x, pill_y = (W - pill_w) // 2, 198
        draw.rounded_rectangle([pill_x - 5, pill_y - 5, pill_x + pill_w + 5, pill_y + pill_h + 5], radius=45, fill=(255, 45, 55, 165))
        draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=44, fill=(185, 18, 28, 245), outline=(255, 195, 110, 255), width=3)
        f_pill = load_font(42)
        p_txt = 'زنده | تب داغ فوتبال '
        bb_p = draw.textbbox((0, 0), p_txt, font=f_pill)
        draw.text(((W - (bb_p[2] - bb_p[0])) / 2, pill_y + 15), p_txt, font=f_pill, fill=(255, 255, 255, 255))
        f_3d = load_font(96)
        hdr_txt = 'گزارش زنده و لحظه‌ای'
        bb_h = draw.textbbox((0, 0), hdr_txt, font=f_3d)
        xh = (W - (bb_h[2] - bb_h[0])) / 2
        yh = 395
        for d_off in range(16, 0, -1):
            c_sh = (45, 22, 5, 255) if d_off > 8 else (212, 162, 42, 255)
            draw.text((xh + d_off * 0.6, yh + d_off), hdr_txt, font=f_3d, fill=c_sh)
        draw.text((xh, yh), hdr_txt, font=f_3d, fill=(215, 28, 38, 255), stroke_width=4, stroke_fill=(255, 225, 120, 255))
        sb_x1, sb_y1, sb_x2, sb_y2 = 85, 650, W - 85, 1185
        draw.rounded_rectangle([sb_x1 - 10, sb_y1 - 10, sb_x2 + 10, sb_y2 + 10], radius=46, outline=(0, 235, 255, 195), width=5)
        draw.rounded_rectangle([sb_x1 - 4, sb_y1 - 4, sb_x2 + 4, sb_y2 + 4], radius=42, outline=(245, 208, 98, 245), width=4)
        sb_glass = Image.new('RGBA', (sb_x2 - sb_x1, sb_y2 - sb_y1), (10, 20, 36, 232))
        sbg_d = ImageDraw.Draw(sb_glass)
        sbg_d.rounded_rectangle([14, 14, (sb_x2 - sb_x1) - 15, (sb_y2 - sb_y1) - 15], radius=32, outline=(0, 225, 255, 160), width=2)
        sb_mask = Image.new('L', (sb_x2 - sb_x1, sb_y2 - sb_y1), 0)
        ImageDraw.Draw(sb_mask).rounded_rectangle([0, 0, sb_x2 - sb_x1 - 1, sb_y2 - sb_y1 - 1], radius=40, fill=255)
        canvas.paste(sb_glass, (sb_x1, sb_y1), sb_mask)
        draw = ImageDraw.Draw(canvas)
        home_clean = re.sub(r'[A-Za-z]', '', match_data.get('home', 'فجر سپاسی')).strip() or 'فجر سپاسی'
        away_clean = re.sub(r'[A-Za-z]', '', match_data.get('away', 'پرسپولیس')).strip() or 'پرسپولیس'
        logo_sz = 175
        h_badge = fetch_team_badge_img(home_clean, match_data.get('home_logo', ''), size=logo_sz)
        a_badge = fetch_team_badge_img(away_clean, match_data.get('away_logo', ''), size=logo_sz)
        h_cx = sb_x2 - 195
        a_cx = sb_x1 + 195
        logo_y = sb_y1 + 85
        canvas.alpha_composite(h_badge, (h_cx - logo_sz // 2, logo_y))
        canvas.alpha_composite(a_badge, (a_cx - logo_sz // 2, logo_y))
        draw = ImageDraw.Draw(canvas)
        f_tm_name = load_font(44 if max(len(home_clean), len(away_clean)) <= 11 else 36)
        bb_hn = draw.textbbox((0, 0), home_clean, font=f_tm_name)
        bb_an = draw.textbbox((0, 0), away_clean, font=f_tm_name)
        draw.text((h_cx - (bb_hn[2] - bb_hn[0]) / 2, logo_y + logo_sz + 32), home_clean, font=f_tm_name, fill=(255, 255, 255, 255))
        draw.text((a_cx - (bb_an[2] - bb_an[0]) / 2, logo_y + logo_sz + 32), away_clean, font=f_tm_name, fill=(255, 255, 255, 255))
        h_sc_fa = to_persian_num(match_data.get('h_score', 0))
        a_sc_fa = to_persian_num(match_data.get('a_score', 0))
        score_str = f'{a_sc_fa} - {h_sc_fa}'
        f_sc = load_font(135)
        bb_sc = draw.textbbox((0, 0), score_str, font=f_sc)
        sc_x = (W - (bb_sc[2] - bb_sc[0])) / 2
        sc_y = sb_y1 + 135
        for off in range(12, 0, -1):
            draw.text((sc_x + off, sc_y + off), score_str, font=f_sc, fill=(95, 65, 12, 240))
        draw.text((sc_x, sc_y), score_str, font=f_sc, fill=(252, 222, 115, 255), stroke_width=3, stroke_fill=(255, 250, 220, 255))
        st_label = to_persian_num(str(match_data.get('status', 'در جریان')))
        if st_label and st_label not in ('', 'None'):
            f_st = load_font(32)
            bb_st = draw.textbbox((0, 0), st_label, font=f_st)
            draw.rounded_rectangle([(W - (bb_st[2] - bb_st[0])) / 2 - 24, sb_y1 + 45, (W + (bb_st[2] - bb_st[0])) / 2 + 24, sb_y1 + 98], radius=18, fill=(200, 25, 35, 235), outline=(245, 208, 98, 255), width=2)
            draw.text(((W - (bb_st[2] - bb_st[0])) / 2, sb_y1 + 52), st_label, font=f_st, fill=(255, 255, 255, 255))
        bn_x1, bn_y1, bn_x2, bn_y2 = 75, 1415, W - 75, 1595
        pts_outer = [(bn_x1 + 28, bn_y1), (bn_x2, bn_y1), (bn_x2 - 28, bn_y2), (bn_x1, bn_y2)]
        pts_inner = [(bn_x1 + 34, bn_y1 + 8), (bn_x2 - 8, bn_y1 + 8), (bn_x2 - 34, bn_y2 - 8), (bn_x1 + 8, bn_y2 - 8)]
        draw.polygon(pts_outer, fill=(235, 190, 75, 255))
        draw.polygon(pts_inner, fill=(32, 22, 10, 248))
        b_lines, f_bn, sz_bn = fit_wrapped_text(banner_text, base_font_size=46, min_font_size=30, base_width=28, max_lines=2)
        y_bn = bn_y1 + (58 if len(b_lines) == 1 else 32)
        for bl in b_lines:
            bb_b = draw.textbbox((0, 0), bl, font=f_bn)
            draw.text(((W - (bb_b[2] - bb_b[0])) / 2, y_bn), bl, font=f_bn, fill=(255, 255, 255, 255))
            y_bn += int(sz_bn * 1.45)
        foot_h = 125
        foot_box = make_gold_metallic_box(W + 40, foot_h + 20, radius=10)
        canvas.alpha_composite(foot_box, (-20, H - foot_h))
        draw = ImageDraw.Draw(canvas)
        f_foot = load_font(52)
        foot_txt = 'آخرین خبرهای شیراز'
        bb_f = draw.textbbox((0, 0), foot_txt, font=f_foot)
        draw.text(((W - (bb_f[2] - bb_f[0])) / 2, H - foot_h + 24), foot_txt, font=f_foot, fill=(10, 16, 28, 255))
        out = io.BytesIO()
        canvas.convert('RGB').save(out, format='JPEG', quality=95)
        img_b = out.getvalue()
        with open(LAST_SPORT_STORY_FILE, 'wb') as sf:
            sf.write(img_b)
        with open(LAST_SPORT_META_FILE, 'w', encoding='utf-8') as mf:
            json.dump({
                'home': home_clean, 'away': away_clean,
                'h_score': match_data.get('h_score', 0), 'a_score': match_data.get('a_score', 0),
                'banner': banner_text, 'time': int(time.time())
            }, mf, ensure_ascii=False)
        return img_b
    except Exception as e:
        print('3D Live story error:', e)
        return None

def check_live_iran_league_stories(insta_cl):
    today_str, _ = get_iran_jalali_date()
    l_state = {'date': today_str, 'matches': {}}
    if os.path.exists(LIVE_IRAN_STATE_FILE):
        try:
            loaded = json.load(open(LIVE_IRAN_STATE_FILE, encoding='utf-8'))
            if loaded.get('date') == today_str:
                l_state = loaded
        except Exception:
            pass
    live_matches = fetch_live_iran_league_matches()
    if not live_matches:
        return
    state_changed = False
    for m in live_matches:
        mk = f"{m['home']}_{m['away']}"
        st_txt = str(m.get('status', '')).strip()
        h_sc, a_sc = int(m.get('h_score', 0)), int(m.get('a_score', 0))
        is_future = bool(re.search(r'^\d{1,2}:\d{2}$', normalize_persian_chars(st_txt)))
        if is_future and h_sc == 0 and a_sc == 0:
            continue
        prev = l_state['matches'].get(mk)
        event_banner = None
        is_ht = any(w in st_txt for w in ['نیمه اول', 'بین دو نیمه', 'HT'])
        is_ft = any(w in st_txt for w in ['پایان', 'نهایی', 'FT']) and not is_ht
        if not prev:
            l_state['matches'][mk] = {'h_score': h_sc, 'a_score': a_sc, 'ht_sent': is_ht, 'ft_sent': is_ft}
            state_changed = True
            if (h_sc + a_sc) > 0:
                event_banner = f"انفجار در ورزشگاه! ثبت گل در دیدار {m['home']} و {m['away']}"
            elif is_ft:
                event_banner = f"سوت پایان مسابقه | {m['home']} {to_persian_num(h_sc)} - {to_persian_num(a_sc)} {m['away']}"
        else:
            old_h, old_a = int(prev.get('h_score', 0)), int(prev.get('a_score', 0))
            if h_sc > old_h or a_sc > old_a:
                scorer = m['home'] if h_sc > old_h else m['away']
                min_part = f' در دقیقه {to_persian_num(st_txt)}' if re.search(r'[0-9۰-۹]', st_txt) else ''
                event_banner = f'انفجار در ورزشگاه! ثبت گل برای {scorer}{min_part}'
                prev['h_score'], prev['a_score'] = h_sc, a_sc
                state_changed = True
            elif is_ht and not prev.get('ht_sent'):
                event_banner = f"پایان نیمه اول مسابقه | {m['home']} {to_persian_num(h_sc)} - {to_persian_num(a_sc)} {m['away']}"
                prev['ht_sent'] = True
                state_changed = True
            elif is_ft and not prev.get('ft_sent'):
                event_banner = f"سوت پایان بازی! نتیجه نهایی: {m['home']} {to_persian_num(h_sc)} - {to_persian_num(a_sc)} {m['away']}"
                prev['ft_sent'] = True
                state_changed = True
        if event_banner:
            st_bytes = create_3d_live_match_story(m, event_banner)
            if st_bytes:
                if insta_cl:
                    post_to_instagram(insta_cl, st_bytes, '', is_story=True)
                if ADMIN_ID:
                    try:
                        s_io = io.BytesIO(st_bytes)
                        s_io.name = 'live_match_story.jpg'
                        bot.send_photo(ADMIN_ID, s_io, caption=f'🔴 <b>استوری زنده لیگ برتر ایران ساخته و در استوری اینستاگرام منتشر شد:</b>\n⚽️ {event_banner}', parse_mode='HTML')
                    except Exception:
                        pass
    if state_changed:
        with open(LIVE_IRAN_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(l_state, f, ensure_ascii=False)
        save_memory_state(push_git=True)

def send_latest_sport_story_to_telegram(cid, reply_kb):
    today_str, _ = get_iran_jalali_date()
    live_m = fetch_live_iran_league_matches()
    if live_m:
        top_m = next((x for x in live_m if 'فجر' in (x['home'] + x['away'])), live_m[0])
        st_t = str(top_m.get('status', '')).strip()
        bn_t = (
            f"گزارش لحظه‌ای: {top_m['home']} {to_persian_num(top_m['h_score'])} - {to_persian_num(top_m['a_score'])} {top_m['away']}"
            if (top_m['h_score'] + top_m['a_score'] > 0 or not re.search(r':', st_t))
            else f"دیدار حساس امروز ساعت {to_persian_num(st_t)}"
        )
        st_b = create_3d_live_match_story(top_m, bn_t)
        if st_b:
            s_io = io.BytesIO(st_b)
            s_io.name = 'latest_live_sport_story.jpg'
            lines_m = [f"⚽️ {x['home']} {to_persian_num(x['h_score'])} - {to_persian_num(x['a_score'])} {x['away']} ({to_persian_num(x.get('status', ''))})" for x in live_m[:6]]
            cap_s = f'🔴 <b>آخرین استوری زنده ورزش و لیگ برتر ایران ({today_str})</b>\n\n' + '\n'.join(lines_m) + f'\n\n🛑 <b>{CHANNEL_SIGN}</b>'
            bot.send_photo(cid, s_io, caption=cap_s, parse_mode='HTML', reply_markup=reply_kb)
            return
    if os.path.exists(LAST_SPORT_STORY_FILE):
        with open(LAST_SPORT_STORY_FILE, 'rb') as sf:
            bot.send_photo(cid, sf, caption=f'🔴 <b>آخرین استوری زنده لیگ برتر ایران ({today_str})</b>\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=reply_kb)
        return
    matches = scrape_varzesh3_today_matches()
    if matches:
        m0 = matches[0]
        sample_m = {
            'home': m0['home'], 'away': m0['away'], 'h_score': 0, 'a_score': 0,
            'status': m0['time'], 'home_logo': m0.get('home_logo', ''), 'away_logo': m0.get('away_logo', '')
        }
        st_b = create_3d_live_match_story(sample_m, f"دیدار حساس امروز | شروع بازی ساعت {m0['time']}")
        if st_b:
            s_io = io.BytesIO(st_b)
            s_io.name = 'sport_story.jpg'
            bot.send_photo(cid, s_io, caption=f'⚽️ <b>آخرین استوری ورزشی و برنامه بازی‌های امروز ({today_str})</b>\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=reply_kb)
        if os.path.exists(DAILY_MATCHES_STORY_CACHE):
            with open(DAILY_MATCHES_STORY_CACHE, 'rb') as df:
                bot.send_photo(cid, df, caption=f'📅 <b>استوری جدول کامل بازی‌های امروز ({today_str})</b>\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=reply_kb)

def create_daily_matches_infographic_story(matches_list, today_jalali):
    if not matches_list:
        return None
    try:
        ensure_persian_font()
        W, H = 1080, 1920
        bg = get_stadium_atmosphere_bg(W, H)
        dark_ov = Image.new('RGBA', (W, H), (6, 12, 24, 185))
        canvas = Image.alpha_composite(bg, dark_ov)
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow)
        g_draw.ellipse([-80, 220, 320, 480], fill=(255, 245, 210, 125))
        g_draw.ellipse([W - 320, 220, W + 80, 480], fill=(255, 245, 210, 125))
        g_draw.ellipse([180, 80, W - 180, 440], fill=(0, 195, 205, 65))
        random.seed(77)
        for _ in range(85):
            px = random.randint(25, W - 25)
            py = random.randint(450, H - 140)
            pr = random.randint(3, 9)
            g_draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(255, 215, 95, random.randint(90, 210)))
        canvas = Image.alpha_composite(canvas, glow.filter(ImageFilter.GaussianBlur(18)))
        sparks = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sp_d = ImageDraw.Draw(sparks)
        for _ in range(110):
            sx = random.randint(20, W - 20)
            sy = random.randint(60, H - 130)
            sr = random.randint(1, 4)
            sp_d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 235, 150, random.randint(130, 245)))
        canvas = Image.alpha_composite(canvas, sparks)
        draw = ImageDraw.Draw(canvas)
        draw_luxury_brand_badge(draw, W - 130, 75, scale=1.22)
        f_3d = load_font(118)
        w_part1 = 'بازی‌های'
        w_part2 = 'امروز'
        bb1 = draw.textbbox((0, 0), w_part1, font=f_3d)
        bb2 = draw.textbbox((0, 0), w_part2, font=f_3d)
        w1, w2 = bb1[2] - bb1[0], bb2[2] - bb2[0]
        x_p1 = 445
        x_p2 = x_p1 - w2 - 28
        y_hdr = 105
        for depth in range(14, 0, -1):
            c_d = (12, 42, 48, 255) if depth > 6 else (22, 85, 92, 255)
            draw.text((x_p1 + depth, y_hdr + depth), w_part1, font=f_3d, fill=c_d)
            c_d2 = (55, 35, 8, 255) if depth > 6 else (125, 85, 18, 255)
            draw.text((x_p2 + depth, y_hdr + depth), w_part2, font=f_3d, fill=c_d2)
        draw.text((x_p1, y_hdr), w_part1, font=f_3d, fill=(64, 224, 208, 255), stroke_width=3, stroke_fill=(245, 215, 120, 255))
        draw.text((x_p2, y_hdr), w_part2, font=f_3d, fill=(248, 208, 92, 255), stroke_width=3, stroke_fill=(255, 245, 200, 255))
        pill_x, pill_y, pill_w, pill_h = 240, 295, W - 480, 92
        draw.rounded_rectangle([pill_x - 4, pill_y - 4, pill_x + pill_w + 4, pill_y + pill_h + 4], radius=46, fill=(245, 208, 98, 235))
        draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=44, fill=(38, 48, 58, 240), outline=(255, 235, 165, 255), width=3)
        f_date = load_font(44)
        wk_fa = get_persian_weekday()
        dt_str = f'{wk_fa} {today_jalali}'
        bb_dt = draw.textbbox((0, 0), dt_str, font=f_date)
        draw.text(((W - (bb_dt[2] - bb_dt[0])) / 2, pill_y + 16), dt_str, font=f_date, fill=(255, 255, 255, 255))
        y_card = 455
        card_h = 265
        card_gap = 52
        for m in matches_list[:4]:
            c_x1, c_x2 = 85, W - 155
            draw.rounded_rectangle([c_x1 - 3, y_card - 3, c_x2 + 3, y_card + card_h + 3], radius=34, outline=(120, 185, 225, 200), width=3)
            card_glass = Image.new('RGBA', (c_x2 - c_x1, card_h), (12, 26, 48, 215))
            cg_d = ImageDraw.Draw(card_glass)
            cg_d.rounded_rectangle([0, 0, c_x2 - c_x1 - 1, card_h - 1], radius=32, outline=(218, 175, 72, 220), width=3)
            c_mask = Image.new('L', (c_x2 - c_x1, card_h), 0)
            ImageDraw.Draw(c_mask).rounded_rectangle([0, 0, c_x2 - c_x1 - 1, card_h - 1], radius=32, fill=255)
            canvas.paste(card_glass, (c_x1, y_card), c_mask)
            draw = ImageDraw.Draw(canvas)
            f_lg = load_font(34)
            lg_fa = re.sub(r'[A-Za-z]', '', m['league']).strip() or 'مسابقات مهم روز'
            bb_lg = draw.textbbox((0, 0), lg_fa, font=f_lg)
            draw.text((c_x1 + ((c_x2 - c_x1) - (bb_lg[2] - bb_lg[0])) / 2, y_card + 16), lg_fa, font=f_lg, fill=(242, 202, 100, 255))
            bar_y = y_card + 82
            bar_h = 135
            r_bar_w = 235
            r_bar_x = c_x2 - 22 - r_bar_w
            l_bar_w = 235
            l_bar_x = c_x1 + 22
            g_box_r = make_gold_metallic_box(r_bar_w, bar_h, radius=22)
            g_box_l = make_gold_metallic_box(l_bar_w, bar_h, radius=22)
            canvas.alpha_composite(g_box_r, (r_bar_x, bar_y))
            canvas.alpha_composite(g_box_l, (l_bar_x, bar_y))
            tm_box_w, tm_box_h = 165, bar_h
            tm_box_x = c_x2 + 12
            g_box_tm = make_gold_metallic_box(tm_box_w, tm_box_h, radius=22)
            canvas.alpha_composite(g_box_tm, (tm_box_x, bar_y))
            draw = ImageDraw.Draw(canvas)
            f_tm = load_font(48)
            tm_fa = to_persian_num(re.sub(r'[^0-9۰-۹:]', '', m['time']) or '۲۰:۰۰')
            bb_t = draw.textbbox((0, 0), tm_fa, font=f_tm)
            draw.text((tm_box_x + (tm_box_w - (bb_t[2] - bb_t[0])) / 2, bar_y + (bar_h - (bb_t[3] - bb_t[1])) / 2 - 8), tm_fa, font=f_tm, fill=(10, 16, 28, 255))
            home_clean = re.sub(r'[A-Za-z]', '', m['home']).strip() or 'میزبان'
            away_clean = re.sub(r'[A-Za-z]', '', m['away']).strip() or 'میهمان'
            f_hr = load_font(36 if len(home_clean) <= 10 else 29)
            bb_hr = draw.textbbox((0, 0), home_clean, font=f_hr)
            draw.text((r_bar_x + (r_bar_w - (bb_hr[2] - bb_hr[0])) / 2, bar_y + (bar_h - (bb_hr[3] - bb_hr[1])) / 2 - 6), home_clean, font=f_hr, fill=(10, 16, 28, 255))
            f_aw = load_font(36 if len(away_clean) <= 10 else 29)
            bb_aw = draw.textbbox((0, 0), away_clean, font=f_aw)
            draw.text((l_bar_x + (l_bar_w - (bb_aw[2] - bb_aw[0])) / 2, bar_y + (bar_h - (bb_aw[3] - bb_aw[1])) / 2 - 6), away_clean, font=f_aw, fill=(10, 16, 28, 255))
            logo_sz = 112
            mid_x = (l_bar_x + l_bar_w + r_bar_x) // 2
            draw.line([(mid_x, bar_y + 15), (mid_x, bar_y + bar_h - 15)], fill=(218, 175, 72, 160), width=2)
            h_badge = fetch_team_badge_img(home_clean, m.get('home_logo', ''), size=logo_sz)
            a_badge = fetch_team_badge_img(away_clean, m.get('away_logo', ''), size=logo_sz)
            canvas.alpha_composite(h_badge, (mid_x + 14, bar_y + (bar_h - logo_sz) // 2))
            canvas.alpha_composite(a_badge, (mid_x - 14 - logo_sz, bar_y + (bar_h - logo_sz) // 2))
            draw = ImageDraw.Draw(canvas)
            y_card += card_h + card_gap
        foot_h = 125
        foot_box = make_gold_metallic_box(W + 40, foot_h + 20, radius=10)
        canvas.alpha_composite(foot_box, (-20, H - foot_h))
        draw = ImageDraw.Draw(canvas)
        f_foot = load_font(52)
        foot_txt = 'آخرین خبرهای شیراز'
        bb_f = draw.textbbox((0, 0), foot_txt, font=f_foot)
        draw.text(((W - (bb_f[2] - bb_f[0])) / 2, H - foot_h + 24), foot_txt, font=f_foot, fill=(10, 16, 28, 255))
        out = io.BytesIO()
        canvas.convert('RGB').save(out, format='JPEG', quality=95)
        img_b = out.getvalue()
        with open(DAILY_MATCHES_STORY_CACHE, 'wb') as df:
            df.write(img_b)
        return img_b
    except Exception as e:
        print('Matches 3D infographic error:', e)
        return None

def check_daily_matches_story(insta_cl):
    today_str, hour_now = get_iran_jalali_date()
    if not (7 <= hour_now <= 13):
        return
    last_m_date = open(MATCHES_FILE, encoding='utf-8').read().strip() if os.path.exists(MATCHES_FILE) else ''
    if last_m_date == today_str:
        return
    matches = scrape_varzesh3_today_matches()
    if not matches:
        return
    story_bytes = create_daily_matches_infographic_story(matches, today_str)
    if story_bytes:
        posted_ok = False
        if insta_cl:
            posted_ok = post_to_instagram(insta_cl, story_bytes, '', is_story=True)
        if ADMIN_ID:
            try:
                s_io = io.BytesIO(story_bytes)
                s_io.name = 'matches_story.jpg'
                bot.send_photo(ADMIN_ID, s_io, caption=f'⚽️ استوری سه‌بعدی «بازی‌های امروز» ({today_str}) آماده و ارسال شد.')
            except Exception:
                pass
        if posted_ok or not insta_cl:
            with open(MATCHES_FILE, 'w', encoding='utf-8') as f:
                f.write(today_str)
            save_memory_state(push_git=True)
            print('Successfully published 3D Daily Matches Infographic to Instagram Story!')
    # ==========================================
# ۱۱. سرویس‌های شهروندی (آب‌وهوا، اوقات شرعی، طلا و ارز) و پنل ادمین
# ==========================================
def get_source_name(url):
    u = url.lower()
    if 'irna.ir' in u:
        return 'خبرگزاری ایرنا'
    if 'mehrnews.com' in u:
        return 'خبرگزاری مهر'
    if 'tasnimnews.com' in u:
        return 'خبرگزاری تسنیم'
    if 'isna.ir' in u:
        return 'خبرگزاری ایسنا'
    if 'farsnews' in u:
        return 'خبرگزاری فارس'
    if 'irib-news' in u or 'iribnews' in u:
        return 'خبرگزاری صدا و سیما'
    if 'snn.ir' in u:
        return 'خبرگزاری دانشجو'
    if 'varzesh3.com' in u:
        return 'ورزش سه'
    return 'تحریریه آخرین خبرهای شیراز'

def get_shiraz_weather():
    try:
        url = 'https://api.open-meteo.com/v1/forecast?latitude=29.5918&longitude=52.5837&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=auto'
        d = requests.get(url, timeout=6).json()
        return f"✅ دمای فعلی شیراز: {d['current_weather']['temperature']}°C (بیشینه: {d['daily']['temperature_2m_max'][0]}° | کمینه: {d['daily']['temperature_2m_min'][0]}°)"
    except Exception:
        return '✅ وضعیت هوای شیراز: صاف تا کمی ابری'

def get_shiraz_prayer_times():
    try:
        url = 'https://api.aladhan.com/v1/timingsByCity?city=Shiraz&country=Iran&method=7'
        t = requests.get(url, timeout=6).json()['data']['timings']
        return f"✅ اذان صبح: {t['Fajr']} | طلوع: {t['Sunrise']}\n✅ اذان ظهر: {t['Dhuhr']} | اذان مغرب: {t['Maghrib']}"
    except Exception:
        return '✅ التماس دعا به افق زیبای شیراز'

def get_market_prices():
    prices = {}
    try:
        r = requests.get('https://www.tgju.org/', headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, 'html.parser')
        items = {'price_dollar_rl': 'دلار آزاد', 'price_eur': 'یورو', 'geram18': 'طلای ۱۸ عیار', 'sekee': 'سکه امامی'}
        for slug, title in items.items():
            el = soup.find('tr', {'data-market-row': slug})
            if el and el.find('td', class_='nf'):
                prices[title] = el.find('td', class_='nf').get_text().strip() + ' ریال'
    except Exception:
        pass
    return '\n'.join([f'✅ {k}: {v}' for k, v in prices.items()]) if prices else '✅ همراه با آخرین نوسانات بازار در طول روز'

def parse_admin_news_caption(raw_caption):
    if not raw_caption:
        return '', ''
    lines_c = [l.strip() for l in raw_caption.strip().split('\n') if l.strip()]
    if not lines_c:
        return '', ''
    title = re.sub(r'^(تیتر|عنوان)\s*[:：-]\s*', '', lines_c[0]).strip()
    lead = ' '.join(lines_c[1:]).strip() if len(lines_c) > 1 else title
    lead = re.sub(r'^(لید|متن|توضیحات)\s*[:：-]\s*', '', lead).strip()
    return title, lead

def process_bot_service(insta_cl=None, current_iran_hour=12):
    s_data = {'last_update_id': 0, 'admin_id': ADMIN_ID, 'files': {}, 'file_counter': 0, 'drafts': {}, 'draft_counter': 0}
    if os.path.exists(SERVICE_STATE_FILE):
        try:
            with open(SERVICE_STATE_FILE, 'r', encoding='utf-8') as f:
                s_data.update(json.load(f))
        except Exception:
            pass
    if 'drafts' not in s_data:
        s_data['drafts'] = {}
    if 'draft_counter' not in s_data:
        s_data['draft_counter'] = 0

    def is_member(uid):
        try:
            st = bot.get_chat_member(TARGET_CHAT, uid).status
            return st in ['member', 'administrator', 'creator']
        except Exception:
            return True

    def lock_kb(payload='menu'):
        mk = InlineKeyboardMarkup()
        mk.add(InlineKeyboardButton('📢 ۱. عضویت در آخرین خبرهای شیراز', url=CHANNEL_LINK))
        mk.add(InlineKeyboardButton('✅ ۲. عضو شدم (دریافت فایل و خدمات)', callback_data=f'verify|{payload}'))
        return mk

    def main_kb(is_admin=False):
        mk = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        mk.add(KeyboardButton('💰 نرخ لحظه‌ای طلا و ارز'), KeyboardButton('🌤 آب‌وهوا و اوقات شرعی شیراز'))
        mk.add(KeyboardButton('⚽️ آخرین استوری ورزش و لیگ برتر'), KeyboardButton('📸 ارسال سوژه و ارتباط با ما'))
        if is_admin:
            mk.add(KeyboardButton('📋 برنامه این ساعت و وضعیت ربات'), KeyboardButton('🔥 تست استوری زنده فوتبال'))
            mk.add(KeyboardButton('⚡ مدیریت صف و انتشار فوری VIP'))
        return mk

    def draft_confirm_kb(dkey):
        mk = InlineKeyboardMarkup(row_width=1)
        mk.add(InlineKeyboardButton('⚡ ۰) انتشار فوری VIP (تلگرام + صدر صف اینستا + X)', callback_data=f'pubdraft_vip|{dkey}'))
        mk.add(InlineKeyboardButton('📢 ۱) انتشار در کانال و استوری', callback_data=f'pubdraft_ch_st|{dkey}'))
        mk.add(InlineKeyboardButton('📱 ۲) انتشار در استوری', callback_data=f'pubdraft_st|{dkey}'))
        mk.add(InlineKeyboardButton('🚀 ۳) انتشار در پست، استوری و کانال تلگرام', callback_data=f'pubdraft_all|{dkey}'))
        mk.add(InlineKeyboardButton('❌ لغو و حذف پیش‌نمایش', callback_data=f'canceldraft|{dkey}'))
        return mk

    def build_vip_queue_panel():
        queue_file = "drafts/insta_queue.json"
        q = []
        if os.path.exists(queue_file):
            try:
                with open(queue_file, "r", encoding="utf-8") as f:
                    q = json.load(f)
            except Exception:
                pass
        iran_now = datetime.utcnow() + timedelta(hours=3, minutes=30)
        h_ir = iran_now.hour
        if (13 <= h_ir <= 15) or (20 <= h_ir <= 23):
            p_status = "🔥 <b>ساعت طلایی (Prime Time) فعال است</b> (اولویت حداکثری انتشار)"
        elif 1 <= h_ir < 7:
            p_status = "💤 <b>ساعت استراحت شبانه</b> (نگهداری پست‌ها برای صبح)"
        else:
            p_status = "✅ <b>ساعت عادی انتشار روزانه</b>"

        has_tok = "✅ متصل" if get_active_gh_token() else "⚠️ تنظیم نشده (بفرستید: توکن: ghp_...)"
        txt_q = (
            f"⚡ <b>پنل فرماندهی انتشار فوری (VIP) و ساعت طلایی</b>\n\n"
            f"🕒 وضعیت الگوریتم: {p_status}\n"
            f"🔑 وضعیت توکن گیت‌هاب: <b>{has_tok}</b>\n"
            f"📦 تعداد آیتم‌های منتظر در صف اینستاگرام: <b>{to_persian_num(len(q))} مورد</b>\n\n"
        )
        if q:
            txt_q += "📋 <b>۳ آیتم اول صف انتظار فعلی:</b>\n"
            for idx, item in enumerate(q[:3], 1):
                t_type = item.get("type", "post")
                is_v = "⚡ [VIP]" if item.get("vip") else ""
                cap_short = (item.get("caption") or "بدون کپشن (استوری)").split("\n")[0][:40]
                txt_q += f"{to_persian_num(idx)}. <code>{t_type}</code> {is_v} | {html.escape(cap_short)}...\n"
        mk_v = InlineKeyboardMarkup(row_width=1)
        mk_v.add(InlineKeyboardButton("🚀 اجرای فوری ربات X و اینستاگرام (همین ثانیه)", callback_data="vip_action|trigger_now"))
        if len(q) > 1:
            mk_v.add(InlineKeyboardButton("🔝 انتقال آخرین خبر صف به صدر اولویت (VIP)", callback_data="vip_action|promote_last"))
        if len(q) > 10:
            mk_v.add(InlineKeyboardButton("🧹 پاکسازی صف قدیمی (حفظ VIPها و ۱۰ خبر آخر)", callback_data="vip_action|clean_old"))
        return txt_q, mk_v

    def send_file_by_key(cid, fkey, is_adm=False):
        f_info = s_data['files'].get(fkey)
        if not f_info:
            bot.send_message(cid, '⭕️ <b>فایل مورد نظر یافت نشد</b>\n\n✅ ممکن است لینک منقضی شده باشد.\n\n🛑 ' + CHANNEL_SIGN, parse_mode='HTML', reply_markup=main_kb(is_adm))
            return
        ft, fid = f_info['type'], f_info['file_id']
        cap = f"⭕️ <b>{f_info.get('caption', 'فایل اختصاصی آخرین خبرهای شیراز')}</b>\n\n🛑 <b>{CHANNEL_SIGN}</b>"
        if ft == 'video':
            bot.send_video(cid, fid, caption=cap, parse_mode='HTML', reply_markup=main_kb(is_adm))
        elif ft == 'document':
            bot.send_document(cid, fid, caption=cap, parse_mode='HTML', reply_markup=main_kb(is_adm))
        elif ft == 'photo':
            bot.send_photo(cid, fid, caption=cap, parse_mode='HTML', reply_markup=main_kb(is_adm))
        elif ft == 'audio':
            bot.send_audio(cid, fid, caption=cap, parse_mode='HTML', reply_markup=main_kb(is_adm))

    try:
        updates = bot.get_updates(offset=s_data['last_update_id'] + 1, timeout=3)
        for u in updates:
            s_data['last_update_id'] = u.update_id
            if u.callback_query:
                cq = u.callback_query
                uid, cid = cq.from_user.id, cq.message.chat.id
                is_adm_cb = (str(cid) == str(s_data.get('admin_id')) or str(cid) == str(ADMIN_ID))
                if cq.data.startswith('verify|'):
                    payload = cq.data.split('|', 1)[1]
                    if is_member(uid):
                        bot.answer_callback_query(cq.id, '✅ عضویت شما تایید شد!')
                        if payload.startswith('file_'):
                            send_file_by_key(cid, payload, is_adm_cb)
                        else:
                            bot.send_message(cid, f'⭕️ <b>عضویت شما تایید شد</b>\n\n✅ همشهری عزیز، از دکمه‌های پایین صفحه خدمت مورد نظر خود را انتخاب کنید:\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=main_kb(is_adm_cb))
                    else:
                        bot.answer_callback_query(cq.id, '❌ هنوز عضو کانال نشده‌اید! ابتدا دکمه اول را بزنید.', show_alert=True)
                elif cq.data.startswith('vip_action|'):
                    sub_act = cq.data.split('|', 1)[1]
                    if sub_act == 'trigger_now':
                        ok_x, msg_x = trigger_github_vip_workflow("shiraz-x-publisher", "x_bot.yml")
                        ok_ig, msg_ig = trigger_github_vip_workflow("shiraz-insta-publisher", "main.yml")
                        bot.answer_callback_query(cq.id, '⚡ فرمان بیدارباش فوری ارسال شد!')
                        bot.send_message(
                            cid,
                            f"⚡ <b>فرمان اجرای فوری (Zero-Delay) صادر شد:</b>\n\n"
                            f"🐦 ربات شبکه X: {'✅ بیدار شد (در حال پست)' if ok_x else f'⚠️ {msg_x}'}\n"
                            f"📸 ربات اینستاگرام: {'✅ بیدار شد (در حال آپلود)' if ok_ig else '✅ در صدر صف اولویت اول قرار گرفت'}",
                            parse_mode='HTML', reply_markup=main_kb(is_adm_cb)
                        )
                    elif sub_act == 'promote_last':
                        queue_file = "drafts/insta_queue.json"
                        if os.path.exists(queue_file):
                            try:
                                q = json.load(open(queue_file, "r", encoding="utf-8"))
                                if len(q) > 1:
                                    last_it = q.pop()
                                    last_it["vip"] = True
                                    last_it["time"] = 9999999999.0
                                    q.insert(0, last_it)
                                    json.dump(q, open(queue_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                                    save_memory_state(push_git=True)
                                    bot.answer_callback_query(cq.id, '🔝 خبر به صدر صف اولویت منتقل شد!')
                                    bot.send_message(cid, "✅ <b>آخرین خبر با موفقیت به صدر صف اولویت (VIP) اینستاگرام منتقل شد!</b>", parse_mode='HTML')
                            except Exception:
                                pass
                    elif sub_act == 'clean_old':
                        queue_file = "drafts/insta_queue.json"
                        if os.path.exists(queue_file):
                            try:
                                q = json.load(open(queue_file, "r", encoding="utf-8"))
                                vip_items = [x for x in q if x.get("vip")]
                                normal_items = [x for x in q if not x.get("vip")][-10:]
                                new_q = vip_items + normal_items
                                json.dump(new_q, open(queue_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                                save_memory_state(push_git=True)
                                bot.answer_callback_query(cq.id, '🧹 صف قدیمی پاکسازی شد!')
                                bot.send_message(cid, f"✅ <b>پاکسازی صف انجام شد!</b>\nاکنون فقط <b>{to_persian_num(len(new_q))} مورد</b> (خبرهای VIP و ۱۰ خبر آخر) در صف قرار دارند.", parse_mode='HTML')
                            except Exception:
                                pass
                elif cq.data.startswith('publivestory|'):
                    if not os.path.exists(LAST_SPORT_STORY_FILE):
                        bot.answer_callback_query(cq.id, '⚠️ فایل استوری یافت نشد.', show_alert=True)
                        continue
                    bot.answer_callback_query(cq.id, '🚀 در حال انتشار در استوری اینستاگرام...')
                    st_bytes = open(LAST_SPORT_STORY_FILE, 'rb').read()
                    if insta_cl and post_to_instagram(insta_cl, st_bytes, '', is_story=True):
                        bot.send_message(cid, '✅ <b>استوری سه‌بعدی زنده با موفقیت در استوری اینستاگرام منتشر شد!</b>', parse_mode='HTML', reply_markup=main_kb(is_adm_cb))
                    else:
                        bot.send_message(cid, '⚠️ خطا در ارسال به اینستاگرام (لاگین اینستاگرام را بررسی کنید).', parse_mode='HTML', reply_markup=main_kb(is_adm_cb))
                elif cq.data.startswith('canceldraft|'):
                    dkey = cq.data.split('|', 1)[1]
                    s_data['drafts'].pop(dkey, None)
                    bot.answer_callback_query(cq.id, '❌ پیش‌نمایش لغو و حذف شد.')
                    bot.send_message(cid, '❌ پیش‌نمایش خبر اختصاصی لغو شد. می‌توانید نسخه جدید را ارسال کنید.', reply_markup=main_kb(is_adm_cb))
                elif cq.data.startswith(('pubdraft_vip|', 'pubdraft_ch_st|', 'pubdraft_st|', 'pubdraft_all|', 'pubdraft|')):
                    act, dkey = cq.data.split('|', 1)
                    dr = s_data['drafts'].get(dkey)
                    if not dr:
                        bot.answer_callback_query(cq.id, '⚠️ این پیش‌نمایش قبلاً منتشر یا حذف شده است.', show_alert=True)
                        continue
                    is_vip_req = (act == 'pubdraft_vip')
                    do_channel = act in ('pubdraft_vip', 'pubdraft_ch_st', 'pubdraft_all', 'pubdraft')
                    do_story = True
                    do_post = act in ('pubdraft_vip', 'pubdraft_all', 'pubdraft')
                    bot.answer_callback_query(cq.id, '⚡ در حال انتشار فوری VIP...' if is_vip_req else '🚀 در حال انتشار طبق گزینه انتخابی شما...')
                    if insta_cl:
                        insta_cl.vip_mode = is_vip_req
                    src_exclusive = 'اختصاصی آخرین خبرهای شیراز'
                    tg_cap = format_caption(dr['title'], dr['lead'], True, 'exclusive', is_video=(dr['type'] == 'video'))
                    insta_cap = format_insta_caption(dr['title'], dr['lead'], True, 'exclusive', is_even_hour=(current_iran_hour % 2 == 0), is_video=(dr['type'] == 'video'))
                    record_sent_news(f'exclusive_{dkey}', dr['title'], sent_to_insta=True)
                    save_memory_state(push_git=True)
                    if dr['type'] == 'photo':
                        raw_p = dr.get('raw_path', '')
                        if os.path.exists(raw_p):
                            raw_bytes = open(raw_p, 'rb').read()
                            if do_channel:
                                framed_b = clean_and_apply_frame(raw_bytes, dr['title'])
                                send_news_post(TARGET_CHAT, framed_b, tg_cap, news_link=None, video_path=None)
                            if insta_cl:
                                if do_post:
                                    post_to_instagram(insta_cl, raw_bytes, insta_cap, is_story=False, title=dr['title'], summary=dr['lead'], source_name=src_exclusive, hour_now=current_iran_hour)
                                if do_story:
                                    st_b = create_premium_news_story(raw_bytes, dr['title'], dr['lead'], src_exclusive)
                                    if st_b:
                                        post_to_instagram(insta_cl, st_b, '', is_story=True)
                            if is_vip_req:
                                trigger_github_vip_workflow("shiraz-x-publisher", "x_bot.yml")
                                trigger_github_vip_workflow("shiraz-insta-publisher", "main.yml")
                            msg_done = '⚡ <b>خبر ویژه (VIP) در تلگرام منتشر شد، در صدر صف اینستاگرام قرار گرفت و فرمان انتشار فوری X صادر گردید!</b>' if is_vip_req else '✅ <b>خبر تصویری اختصاصی با موفقیت منتشر شد!</b>'
                            bot.send_message(cid, msg_done, parse_mode='HTML', reply_markup=main_kb(is_adm_cb))
                    elif dr['type'] == 'video':
                        tg_vp = dr.get('tg_vid_path', '')
                        reel_vp = dr.get('reel_vid_path', '')
                        vw_d, vh_d = dr.get('vw', 1080), dr.get('vh', 1920)
                        if do_channel and os.path.exists(tg_vp):
                            send_news_post(TARGET_CHAT, None, tg_cap, news_link=None, video_path=tg_vp, vid_w=vw_d, vid_h=vh_d)
                        if insta_cl and os.path.exists(reel_vp):
                            if do_post:
                                post_video_to_insta(insta_cl, reel_vp, insta_cap, also_story=do_story)
                            elif do_story:
                                post_video_story_only_to_insta(insta_cl, reel_vp)
                        if is_vip_req:
                            trigger_github_vip_workflow("shiraz-x-publisher", "x_bot.yml")
                            trigger_github_vip_workflow("shiraz-insta-publisher", "main.yml")
                        msg_done = '⚡ <b>ویدیوی ویژه (VIP) در تلگرام منتشر شد، در صدر صف ریلز قرار گرفت و فرمان انتشار فوری صادر گردید!</b>' if is_vip_req else '✅ <b>ویدیوی اختصاصی با موفقیت منتشر شد!</b>'
                        bot.send_message(cid, msg_done, parse_mode='HTML', reply_markup=main_kb(is_adm_cb))
                    if insta_cl:
                        insta_cl.vip_mode = False
                    s_data['drafts'].pop(dkey, None)

            elif u.message and u.message.chat.type == 'private':
                m = u.message
                cid, uid = m.chat.id, m.from_user.id
                txt = (m.text or '').strip()
                is_admin_user = (str(cid) == str(s_data.get('admin_id')) or str(cid) == str(ADMIN_ID))
                if is_admin_user and (txt.startswith('توکن:') or txt.startswith('/token')):
                    raw_tok = txt.replace('توکن:', '').replace('/token', '').strip()
                    if raw_tok:
                        s_data['gh_tok_rev'] = raw_tok[::-1]
                        with open(SERVICE_STATE_FILE, 'w', encoding='utf-8') as f:
                            json.dump(s_data, f, ensure_ascii=False)
                        save_memory_state(push_git=True)
                        bot.send_message(cid, '✅ <b>توکن گیت‌هاب با موفقیت به صورت امن در حافظه ربات ثبت شد!</b>\nاکنون دکمه اجرای فوری VIP را تست کنید.', parse_mode='HTML', reply_markup=main_kb(True))
                    continue
                if txt in ['/admin', 'ادمین']:
                    s_data['admin_id'] = str(cid)
                    bot.send_message(
                        cid,
                        f'⭕️ <b>پنل تحریریه اختصاصی ادمین فعال است</b>\n\n'
                        f'✅ <b>۱. ارسال خبر اختصاصی (با دکمه VIP):</b>\n'
                        f'یک عکس یا ویدیو بفرستید و در کپشن خط اول تیتر و خط دوم لید را بنویسید.\n\n'
                        f'✅ <b>۲. فرماندهی صف و انتشار فوری VIP:</b>\n'
                        f'دکمه <b>«⚡ مدیریت صف و انتشار فوری VIP»</b> یا دستور /vip را بزنید.\n\n'
                        f'🛑 <b>{CHANNEL_SIGN}</b>',
                        parse_mode='HTML',
                        reply_markup=main_kb(True)
                    )
                    continue
                if is_admin_user and (txt in ['/vip', 'vip', '⚡ مدیریت صف و انتشار فوری VIP'] or 'انتشار فوری' in txt):
                    v_txt, v_kb = build_vip_queue_panel()
                    bot.send_message(cid, v_txt, parse_mode='HTML', reply_markup=v_kb)
                    continue
                if is_admin_user and (txt in ['/barname', '/schedule', '/plan', 'برنامه', 'وضعیت'] or 'برنامه این ساعت' in txt):
                    bot.send_message(cid, build_admin_schedule_report(), parse_mode='HTML', reply_markup=main_kb(True))
                    continue
                if is_admin_user and (txt in ['/livetest', 'تست استوری زنده', '🔥 تست استوری زنده فوتبال'] or txt.startswith(('زنده:', 'تست زنده:'))):
                    h_team, a_team, h_sc, a_sc, st_min, bn_custom = 'فجر سپاسی', 'پرسپولیس', 2, 1, 'دقیقه ۷۸', 'انفجار در ورزشگاه! ثبت گل دوم در دقیقه ۷۸'
                    if ':' in txt and '|' in txt:
                        raw_p = txt.split(':', 1)[1].strip()
                        parts_l = [p.strip() for p in raw_p.split('|') if p.strip()]
                        if len(parts_l) >= 3:
                            h_team, a_team = parts_l[0], parts_l[1]
                            sc_part = normalize_persian_chars(parts_l[2])
                            nums_s = re.findall(r'\d+', sc_part)
                            if len(nums_s) >= 2:
                                h_sc, a_sc = int(nums_s[0]), int(nums_s[1])
                            if len(parts_l) == 4:
                                bn_custom = parts_l[3]
                            elif len(parts_l) >= 5:
                                st_min, bn_custom = parts_l[3], parts_l[4]
                            else:
                                bn_custom = f'گزارش لحظه‌ای | {h_team} {to_persian_num(h_sc)} - {to_persian_num(a_sc)} {a_team}'
                    sample_data = {'home': h_team, 'away': a_team, 'h_score': h_sc, 'a_score': a_sc, 'status': st_min, 'home_logo': '', 'away_logo': ''}
                    st_b = create_3d_live_match_story(sample_data, bn_custom)
                    if st_b:
                        mk_lv = InlineKeyboardMarkup(row_width=1)
                        mk_lv.add(InlineKeyboardButton('📱 انتشار همین استوری در اینستاگرام', callback_data='publivestory|last'))
                        s_io = io.BytesIO(st_b)
                        s_io.name = 'live_test_story.jpg'
                        guide_txt = (
                            '🔥 <b>پیش‌نمایش استوری سه‌بعدی زنده آماده شد!</b>\n\n'
                            '👇 در صورت تایید، دکمه زیر را بزنید تا در استوری پیج منتشر شود:'
                        )
                        bot.send_photo(cid, s_io, caption=guide_txt, parse_mode='HTML', reply_markup=mk_lv)
                    continue
                if is_admin_user and (m.photo or m.video):
                    cap_raw = (m.caption or '').strip()
                    if cap_raw and not cap_raw.startswith(('قفل', 'فایل', 'lock')):
                        title_ex, lead_ex = parse_admin_news_caption(cap_raw)
                        s_data['draft_counter'] += 1
                        dkey = f"draft_{s_data['draft_counter']}"
                        src_exclusive = 'اختصاصی آخرین خبرهای شیراز'
                        if m.photo:
                            f_info = bot.get_file(m.photo[-1].file_id)
                            raw_b = bot.download_file(f_info.file_path)
                            raw_p = f'drafts/{dkey}_raw.jpg'
                            with open(raw_p, 'wb') as df:
                                df.write(raw_b)
                            framed_b = clean_and_apply_frame(raw_b, title_ex)
                            st_b = create_premium_news_story(raw_b, title_ex, lead_ex, src_exclusive)
                            post_p = create_approved_post_slide1(raw_b, title_ex, lead_ex, src_exclusive, is_carousel=False)
                            s_data['drafts'][dkey] = {'type': 'photo', 'title': title_ex, 'lead': lead_ex, 'raw_path': raw_p}
                            prev_cap = format_caption(title_ex, lead_ex, True, 'exclusive', is_video=False) + '\n\n👇 <b>محل انتشار این خبر را انتخاب کنید (گزینه ۰ برای انتشار فوری VIP):</b>'
                            p_io = io.BytesIO(framed_b)
                            p_io.name = 'preview_tg.jpg'
                            bot.send_photo(cid, p_io, caption=prev_cap, parse_mode='HTML', reply_markup=draft_confirm_kb(dkey))
                            if post_p and os.path.exists(post_p):
                                with open(post_p, 'rb') as pf:
                                    bot.send_photo(cid, pf, caption='📸 پیش‌نمایش قالب پست اینستاگرام (۴:۵)')
                            if st_b:
                                s_io = io.BytesIO(st_b)
                                s_io.name = 'preview_story.jpg'
                                bot.send_photo(cid, s_io, caption='📱 پیش‌نمایش قالب استوری اینستاگرام (۹:۱۶)')
                            continue
                        elif m.video:
                            bot.send_message(cid, '⏳ در حال اعمال واترمارک، تنظیم دقیق نسبت تصویر ۹:۱۶ و بهینه‌سازی حجم ویدیو...')
                            f_info = bot.get_file(m.video.file_id)
                            vid_b = bot.download_file(f_info.file_path)
                            in_vp = f'drafts/{dkey}_in.mp4'
                            with open(in_vp, 'wb') as vf:
                                vf.write(vid_b)
                            tg_vp, reel_vp, out_vw, out_vh = process_local_video_file(in_vp, title_ex, src_exclusive, out_prefix=f'drafts/{dkey}')
                            if tg_vp and os.path.exists(tg_vp):
                                s_data['drafts'][dkey] = {
                                    'type': 'video', 'title': title_ex, 'lead': lead_ex,
                                    'tg_vid_path': tg_vp, 'reel_vid_path': reel_vp or tg_vp,
                                    'vw': out_vw, 'vh': out_vh
                                }
                                sz_mb = round(os.path.getsize(reel_vp or tg_vp) / (1024.0 * 1024.0), 1)
                                prev_cap = format_caption(title_ex, lead_ex, True, 'exclusive', is_video=True) + f'\n\n📦 حجم بهینه‌شده: {to_persian_num(sz_mb)} مگابایت\n👇 <b>محل انتشار این ویدیو را انتخاب کنید:</b>'
                                with open(reel_vp or tg_vp, 'rb') as vf:
                                    bot.send_video(cid, vf, caption=prev_cap, parse_mode='HTML', width=1080, height=1920, supports_streaming=True, reply_markup=draft_confirm_kb(dkey))
                                continue
                if is_admin_user and (m.video or m.document or m.photo or m.audio):
                    s_data['file_counter'] += 1
                    fkey = f"file_{s_data['file_counter']}"
                    ft = 'video' if m.video else ('document' if m.document else ('photo' if m.photo else 'audio'))
                    fid = m.video.file_id if m.video else (m.document.file_id if m.document else (m.photo[-1].file_id if m.photo else m.audio.file_id))
                    clean_c = re.sub(r'^(قفل|فایل|lock)\s*[:：-]?\s*', '', m.caption or '').strip()
                    s_data['files'][fkey] = {'type': ft, 'file_id': fid, 'caption': clean_c or 'فایل اختصاصی آخرین خبرهای شیراز'}
                    link = f'https://t.me/{BOT_USERNAME.replace("@", "")}?start={fkey}'
                    bot.send_message(cid, f'⭕️ <b>لینک قفل‌دار آماده شد</b>\n\n✅ لینک زیر را در کانال یا استوری قرار دهید:\n{link}\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=main_kb(True))
                    continue
                if txt.startswith('/start'):
                    parts = txt.split()
                    payload = parts[1] if len(parts) > 1 else 'menu'
                    if not is_member(uid):
                        bot.send_message(cid, f'⭕️ <b>قفل عضویت در کانال</b>\n\n✅ همشهری عزیز، برای دریافت این فایل و استفاده از خدمات هوشمند شیراز، ابتدا از دکمه زیر عضو کانال شوید و سپس دکمه «عضو شدم» را بزنید:\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=lock_kb(payload))
                    else:
                        if payload.startswith('file_'):
                            send_file_by_key(cid, payload, is_admin_user)
                        else:
                            bot.send_message(cid, f'⭕️ <b>سامانه هوشمند آخرین خبرهای شیراز</b>\n\n✅ به ربات خدمات شهروندی، نرخ طلا و ارز و ارتباط مردمی خوش آمدید. از منوی زیر انتخاب کنید:\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=main_kb(is_admin_user))
                    continue
                if not is_member(uid):
                    bot.send_message(cid, f'⭕️ <b>نیاز به عضویت در کانال</b>\n\n✅ ابتدا عضو کانال شوید:\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=lock_kb('menu'))
                    continue
                if any(k in txt for k in ['/gold', 'طلا', 'ارز', 'دلار', 'سکه']):
                    bot.send_message(cid, f'⭕️ <b>نرخ لحظه‌ای طلا، سکه و ارز</b>\n\n{get_market_prices()}\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=main_kb(is_admin_user))
                elif any(k in txt for k in ['/weather', 'هوا', 'اذان', 'شرعی']):
                    bot.send_message(cid, f'⭕️ <b>وضعیت آب‌وهوا و اوقات شرعی شیراز</b>\n\n{get_shiraz_weather()}\n{get_shiraz_prayer_times()}\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=main_kb(is_admin_user))
                elif any(k in txt for k in ['/sport', '/fajr', 'استوری ورزش', 'لیگ برتر', 'فجر', 'ورزش', 'فوتبال']):
                    send_latest_sport_story_to_telegram(cid, main_kb(is_admin_user))
                elif 'سوژه' in txt or 'ارتباط' in txt:
                    bot.send_message(cid, f'⭕️ <b>ارسال سوژه خبری</b>\n\n✅ لطفاً عکس، ویدیو یا پیام خود را همین‌جا بفرستید تا مستقیماً به دست تحریریه برسد:\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML')
                else:
                    if s_data.get('admin_id') and str(cid) != str(s_data['admin_id']):
                        bot.forward_message(s_data['admin_id'], cid, m.message_id)
                    bot.send_message(cid, f'⭕️ <b>دریافت شد</b>\n\n✅ پیام و سوژه شما با موفقیت برای تحریریه ارسال گردید.\n\n🛑 <b>{CHANNEL_SIGN}</b>', parse_mode='HTML', reply_markup=main_kb(is_admin_user))
    except Exception as e:
        print('Bot service error:', e)
    with open(SERVICE_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(s_data, f, ensure_ascii=False)

# ==========================================
# ۱۲. موتور گرافیکی قالب‌های پست، کاروسل و استوری خبری
# ==========================================
def get_transparent_frame():
    if not os.path.exists(FRAME_FILE):
        return None
    frame = Image.open(FRAME_FILE).convert('RGBA')
    datas = frame.getdata()
    new_data = []
    for item in datas:
        r, g, b, a = item
        if abs(r - g) < 12 and abs(g - b) < 12 and r < 145:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append(item)
    frame.putdata(new_data)
    return frame

def draw_luxury_brand_badge(draw, x_center, y_top, scale=1.0):
    r = int(68 * scale)
    draw.ellipse([x_center - r - 4, y_top - 4, x_center + r + 4, y_top + 2 * r + 4], fill=(242, 202, 100, 255))
    draw.ellipse([x_center - r, y_top, x_center + r, y_top + 2 * r], fill=(165, 22, 28, 255), outline=(235, 190, 60, 255), width=max(2, int(4 * scale)))
    f_lg = load_font(int(30 * scale))
    f_sm = load_font(int(21 * scale))
    t1, t2 = 'آخرین', 'خبرهای شیراز'
    b1 = draw.textbbox((0, 0), t1, font=f_lg)
    b2 = draw.textbbox((0, 0), t2, font=f_sm)
    draw.text((x_center - (b1[2] - b1[0]) / 2, y_top + int(28 * scale)), t1, font=f_lg, fill=(255, 255, 255, 255))
    draw.text((x_center - (b2[2] - b2[0]) / 2, y_top + int(76 * scale)), t2, font=f_sm, fill=(245, 210, 100, 255))

def draw_post_corner_badge(draw, x_center, y_top, scale=1.0):
    r = int(68 * scale)
    draw.ellipse([x_center - r, y_top, x_center + r, y_top + 2 * r], fill=(235, 195, 85, 255), outline=(175, 25, 30, 255), width=max(3, int(6 * scale)))
    f_b = load_font(int(25 * scale))
    lines_b = ['آخرین', 'خبرهای', 'شیراز']
    yb = y_top + int(18 * scale)
    for lb in lines_b:
        bb = draw.textbbox((0, 0), lb, font=f_b)
        draw.text((x_center - (bb[2] - bb[0]) / 2, yb), lb, font=f_b, fill=(135, 15, 20, 255))
        yb += int(34 * scale)

def clean_and_apply_frame(bg_bytes, title=''):
    try:
        frame = get_transparent_frame()
        if not frame:
            return bg_bytes
        bg = Image.open(io.BytesIO(bg_bytes)).convert('RGBA')
        W, H = frame.size
        bg_resized = bg.resize((W, H), Image.Resampling.LANCZOS)
        combined = Image.alpha_composite(bg_resized, frame)
        out = io.BytesIO()
        combined.convert('RGB').save(out, format='JPEG', quality=93)
        return out.getvalue()
    except Exception as e:
        print('Frame error:', e)
        return bg_bytes

def add_bokeh_background(W, H):
    canvas = Image.new('RGBA', (W, H), (10, 16, 30, 255))
    bokeh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bokeh)
    random.seed(42)
    for _ in range(42):
        bx = random.randint(30, W - 30)
        by = random.randint(int(H * 0.42), H - 90)
        br = random.randint(15, 62)
        b_draw.ellipse([bx - br, by - br, bx + br, by + br], fill=(218, 165, 32, random.randint(18, 52)))
    for _ in range(90):
        dx = random.randint(20, W - 20)
        dy = random.randint(int(H * 0.38), H - 70)
        dr = random.randint(2, 5)
        b_draw.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=(255, 225, 130, random.randint(85, 205)))
    return Image.alpha_composite(canvas, bokeh.filter(ImageFilter.GaussianBlur(10)))

def create_premium_news_story(bg_bytes, title, summary='', source_name='خبرگزاری رسمی'):
    try:
        ensure_persian_font()
        W, H = 1080, 1920
        canvas = add_bokeh_background(W, H)
        draw = ImageDraw.Draw(canvas)
        draw_luxury_brand_badge(draw, 495, 38, scale=1.08)
        draw.ellipse([622, 92, 666, 136], fill=(215, 35, 40, 255))
        f_top = load_font(54)
        draw.text((685, 76), 'خبر فوری', font=f_top, fill=(242, 202, 100, 255))
        img_box_x, img_box_y, img_box_w, img_box_h = 75, 225, W - 150, 595
        draw.rounded_rectangle([img_box_x - 12, img_box_y - 12, img_box_x + img_box_w + 12, img_box_y + img_box_h + 12], radius=34, fill=(10, 16, 30, 255), outline=(218, 165, 32, 235), width=3)
        draw.rounded_rectangle([img_box_x - 4, img_box_y - 4, img_box_x + img_box_w + 4, img_box_y + img_box_h + 4], radius=26, outline=(245, 205, 95, 255), width=2)
        bg = Image.open(io.BytesIO(bg_bytes)).convert('RGB')
        bw, bh = bg.size
        scale = max(img_box_w / bw, img_box_h / bh)
        nw, nh = int(bw * scale), int(bh * scale)
        bg_res = bg.resize((nw, nh), Image.Resampling.LANCZOS)
        bg_crop = bg_res.crop(((nw - img_box_w) // 2, (nh - img_box_h) // 2, (nw - img_box_w) // 2 + img_box_w, (nh - img_box_h) // 2 + img_box_h))
        mask = Image.new('L', (img_box_w, img_box_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, img_box_w, img_box_h], radius=22, fill=255)
        canvas.paste(bg_crop, (img_box_x, img_box_y), mask)
        t_lines, f_title, sz_title = fit_wrapped_text(title, base_font_size=46, min_font_size=30, base_width=26, max_lines=3)
        y_t = 865
        for line in t_lines:
            bb = draw.textbbox((0, 0), line, font=f_title)
            tw = bb[2] - bb[0]
            draw.text(((W - tw) / 2 + 2, y_t + 3), line, font=f_title, fill=(0, 0, 0, 215))
            draw.text(((W - tw) / 2, y_t), line, font=f_title, fill=(242, 202, 100, 255))
            y_t += int(sz_title * 1.52)
        y_t += 16
        clean_s = extract_complete_lead(summary, title, min_chars=80, max_chars=230)
        s_lines, f_sum, sz_sum = fit_wrapped_text(clean_s, base_font_size=34, min_font_size=24, base_width=36, max_lines=5)
        for sline in s_lines:
            bb = draw.textbbox((0, 0), sline, font=f_sum)
            tw = bb[2] - bb[0]
            draw.text(((W - tw) / 2 + 2, y_t + 2), sline, font=f_sum, fill=(0, 0, 0, 205))
            draw.text(((W - tw) / 2, y_t), sline, font=f_sum, fill=(255, 255, 255, 255))
            y_t += int(sz_sum * 1.55)
        draw.rectangle([0, 1810, W, 1920], fill=(222, 182, 78, 255))
        f_bar = load_font(34)
        bar_txt = f'@ShirazLastNews | منبع: {source_name}'
        bb_bar = draw.textbbox((0, 0), bar_txt, font=f_bar)
        draw.text(((W - (bb_bar[2] - bb_bar[0])) / 2, 1842), bar_txt, font=f_bar, fill=(10, 16, 30, 255))
        out = io.BytesIO()
        canvas.convert('RGB').save(out, format='JPEG', quality=95)
        return out.getvalue()
    except Exception as e:
        print('Story design error:', e)
        return None

def create_approved_post_slide1(raw_img_bytes, title, summary, source_name, is_carousel=False):
    try:
        ensure_persian_font()
        W, H = 1080, 1350
        canvas = Image.new('RGBA', (W, H), (244, 245, 248, 255))
        bg = Image.open(io.BytesIO(raw_img_bytes)).convert('RGB')
        iw, ih = bg.size
        top_h = 855
        sc = max(W / iw, top_h / ih)
        nw, nh = int(iw * sc), int(ih * sc)
        bg_crop = bg.resize((nw, nh), Image.Resampling.LANCZOS).crop(((nw - W) // 2, (nh - top_h) // 2, (nw - W) // 2 + W, (nh - top_h) // 2 + top_h))
        canvas.paste(bg_crop, (0, 0))
        grad = Image.new('RGBA', (W, 240), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(grad)
        for y in range(240):
            alpha = int(235 * (y / 240.0))
            g_draw.line([(0, y), (W, y)], fill=(12, 22, 42, alpha))
        canvas.alpha_composite(grad, (0, top_h - 220))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, top_h, W, 1020], fill=(12, 22, 42, 255))
        draw_post_corner_badge(draw, W - 115, 30, scale=1.0)
        draw.rounded_rectangle([54, 738, W - 54, 1246], radius=36, fill=(210, 214, 222, 255))
        draw.rounded_rectangle([50, 730, W - 50, 1238], radius=36, fill=(255, 255, 255, 255), outline=(228, 232, 238, 255), width=2)
        draw.rounded_rectangle([W - 88, 768, W - 74, 1202], radius=6, fill=(190, 22, 30, 255))
        t_lines, f_title, sz_title = fit_wrapped_text(title, base_font_size=42, min_font_size=28, base_width=28, max_lines=3)
        y_t = 762
        for l in t_lines:
            bb = draw.textbbox((0, 0), l, font=f_title)
            tw = bb[2] - bb[0]
            draw.text((W - 108 - tw, y_t), l, font=f_title, fill=(12, 24, 48, 255))
            y_t += int(sz_title * 1.44)
        y_t += 10
        clean_s = extract_complete_lead(summary, title, min_chars=70, max_chars=185)
        s_lines, f_sub, sz_sub = fit_wrapped_text(clean_s, base_font_size=30, min_font_size=22, base_width=39, max_lines=3)
        for sl in s_lines:
            bb = draw.textbbox((0, 0), sl, font=f_sub)
            tw = bb[2] - bb[0]
            draw.text((W - 108 - tw, y_t), sl, font=f_sub, fill=(60, 70, 85, 255))
            y_t += int(sz_sub * 1.46)
        if is_carousel:
            draw.rounded_rectangle([75, 1172, 325, 1222], radius=16, fill=(190, 22, 30, 255))
            f_sw = load_font(22)
            draw.text((97, 1181), '👈 ورق بزنید (مشروح)', font=f_sw, fill=(255, 255, 255, 255))
        draw.rounded_rectangle([230, 1266, W - 230, 1334], radius=26, fill=(20, 26, 36, 255))
        f_pill = load_font(28)
        p_txt = '@ShirazLastNews | آخرین خبرهای شیراز'
        bb_p = draw.textbbox((0, 0), p_txt, font=f_pill)
        draw.text(((W - (bb_p[2] - bb_p[0])) / 2, 1280), p_txt, font=f_pill, fill=(242, 202, 100, 255))
        out_p = 'approved_post_slide1.jpg'
        canvas.convert('RGB').save(out_p, format='JPEG', quality=95)
        return out_p
    except Exception as e:
        print('Approved post slide1 error:', e)
        return None

def create_approved_carousel_slides(raw_img_bytes, title, summary, source_name):
    slides = []
    s1 = create_approved_post_slide1(raw_img_bytes, title, summary, source_name, is_carousel=True)
    if s1:
        slides.append(s1)
    try:
        W, H = 1080, 1350
        c2 = Image.new('RGBA', (W, H), (244, 245, 248, 255))
        d2 = ImageDraw.Draw(c2)
        d2.rectangle([0, 0, W, 240], fill=(12, 22, 42, 255))
        draw_post_corner_badge(d2, W - 115, 30, scale=0.9)
        f_h2 = load_font(40)
        d2.text((80, 85), '📝 مشروح و جزئیات کامل خبر', font=f_h2, fill=(242, 202, 100, 255))
        d2.rounded_rectangle([55, 200, W - 55, 1235], radius=36, fill=(255, 255, 255, 255), outline=(220, 225, 235, 255), width=3)
        d2.rounded_rectangle([W - 92, 245, W - 78, 1190], radius=6, fill=(190, 22, 30, 255))
        t_lines, f_t2, sz_t2 = fit_wrapped_text(title, base_font_size=38, min_font_size=28, base_width=30, max_lines=3)
        y2 = 245
        for tl in t_lines:
            bb = d2.textbbox((0, 0), tl, font=f_t2)
            d2.text((W - 115 - (bb[2] - bb[0]), y2), tl, font=f_t2, fill=(12, 24, 48, 255))
            y2 += int(sz_t2 * 1.48)
        d2.line([(115, y2 + 15), (W - 115, y2 + 15)], fill=(220, 225, 235, 255), width=2)
        y2 += 40
        clean_full_s = extract_complete_lead(summary, title, min_chars=140, max_chars=480)
        b_lines, f_b2, sz_b2 = fit_wrapped_text(clean_full_s, base_font_size=33, min_font_size=24, base_width=36, max_lines=10)
        for bl in b_lines:
            bb = d2.textbbox((0, 0), bl, font=f_b2)
            d2.text((W - 115 - (bb[2] - bb[0]), y2), bl, font=f_b2, fill=(55, 65, 80, 255))
            y2 += int(sz_b2 * 1.55)
        f_src = load_font(27)
        src_t = f'📌 منبع خبر: {source_name}'
        bb_s = d2.textbbox((0, 0), src_t, font=f_src)
        d2.text((W - 115 - (bb_s[2] - bb_s[0]), 1165), src_t, font=f_src, fill=(190, 22, 30, 255))
        d2.rounded_rectangle([230, 1266, W - 230, 1334], radius=26, fill=(20, 26, 36, 255))
        f_pill = load_font(28)
        p_txt = '@ShirazLastNews | آخرین خبرهای شیراز'
        bb_p = d2.textbbox((0, 0), p_txt, font=f_pill)
        draw_x = (W - (bb_p[2] - bb_p[0])) / 2
        d2.text((draw_x, 1280), p_txt, font=f_pill, fill=(242, 202, 100, 255))
        s2_path = 'approved_post_slide2.jpg'
        c2.convert('RGB').save(s2_path, format='JPEG', quality=95)
        slides.append(s2_path)
    except Exception as e:
        print('Approved slide2 error:', e)
    return slides
    # ==========================================
# ۱۳. پردازشگر ویدیو (FFmpeg) برای تلگرام و ریلز
# ==========================================
def create_9_16_video_overlay(W, H, subtitle_text='', source_name='رسانه آخرین خبرهای شیراز'):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ov)
    sc = W / 1080.0
    draw.rounded_rectangle([int(35 * sc), int(40 * sc), int(490 * sc), int(115 * sc)], radius=int(22 * sc), fill=(10, 16, 30, 215), outline=(218, 165, 32, 240), width=max(2, int(3 * sc)))
    draw.ellipse([int(435 * sc), int(62 * sc), int(465 * sc), int(92 * sc)], fill=(215, 30, 40, 255))
    f_top = load_font(int(30 * sc))
    draw.text((int(60 * sc), int(53 * sc)), 'آخرین خبرهای شیراز', font=f_top, fill=(245, 205, 95, 255))
    draw_luxury_brand_badge(draw, W - int(105 * sc), int(25 * sc), scale=0.85 * sc)
    if subtitle_text:
        box_top = H - int(420 * sc)
        box_bot = H - int(155 * sc)
        draw.rounded_rectangle([int(40 * sc), box_top, W - int(40 * sc), box_bot], radius=int(26 * sc), fill=(10, 16, 30, 230), outline=(218, 165, 32, 245), width=max(2, int(3 * sc)))
        draw.rounded_rectangle([W - int(310 * sc), box_top - int(28 * sc), W - int(75 * sc), box_top + int(26 * sc)], radius=int(12 * sc), fill=(200, 25, 35, 255))
        f_b = load_font(int(26 * sc))
        draw.text((W - int(285 * sc), box_top - int(22 * sc)), '🎬 گزارش ویدیویی', font=f_b, fill=(255, 255, 255, 255))
        sub_lines, f_sub, sz_sub = fit_wrapped_text(subtitle_text, base_font_size=int(36 * sc), min_font_size=int(26 * sc), base_width=30, max_lines=3)
        y_s = box_top + int(42 * sc)
        for sl in sub_lines:
            bb = draw.textbbox((0, 0), sl, font=f_sub)
            draw.text(((W - (bb[2] - bb[0])) / 2, y_s), sl, font=f_sub, fill=(255, 255, 255, 255))
            y_s += int(sz_sub * 1.5)
    bar_top = H - int(115 * sc)
    draw.rectangle([0, bar_top, W, bar_top + int(62 * sc)], fill=(218, 175, 70, 250))
    f_bar = load_font(int(28 * sc))
    b_txt = f'@ShirazLastNews  |  📢 منبع: {source_name}'
    bb_bar = draw.textbbox((0, 0), b_txt, font=f_bar)
    draw.text(((W - (bb_bar[2] - bb_bar[0])) / 2, bar_top + int(10 * sc)), b_txt, font=f_bar, fill=(10, 16, 30, 255))
    return ov

def get_video_url(entry, page_url):
    for k_list in ['links', 'enclosures', 'media_content']:
        if k_list in entry:
            for item in entry.get(k_list, []):
                u = item.get('href') or item.get('url') or ''
                if 'video' in item.get('type', '').lower() or '.mp4' in u.lower():
                    return u.split('?')[0] if '.mp4' in u.lower() else u
    if page_url:
        try:
            r = requests.get(page_url, headers=HEADERS, timeout=9, verify=False)
            html_txt = html.unescape(r.text).replace('\\/', '/')
            matches = re.findall(r'https?://[^"\'\s<>()\\]+\.mp4(?:\?[^"\'\s<>()\\]*)?', html_txt, re.IGNORECASE)
            for m in matches:
                if not any(bad in m.lower() for bad in ['ad_', '/ads/', 'banner', 'teaser', 'logo']):
                    return m
            rel_matches = re.findall(r'["\'](/[^"\'\s<>()\\]+\.mp4(?:\?[^"\'\s<>()\\]*)?)["\']', html_txt, re.IGNORECASE)
            if rel_matches:
                base = '/'.join(page_url.split('/')[:3])
                return base + rel_matches[0]
            soup = BeautifulSoup(html_txt, 'html.parser')
            for attr in ['data-src', 'data-video', 'data-file', 'data-mp4', 'src', 'content']:
                for tag in soup.find_all(attrs={attr: True}):
                    val = tag.get(attr, '')
                    if '.mp4' in val.lower():
                        if val.startswith('//'):
                            return 'https:' + val
                        if val.startswith('/'):
                            return '/'.join(page_url.split('/')[:3]) + val
                        if val.startswith('http'):
                            return val
        except Exception:
            pass
    return None

def get_video_dimensions(vid_path):
    probe_jpg = '_probe_orient.jpg'
    try:
        if os.path.exists(probe_jpg):
            os.remove(probe_jpg)
        subprocess.run(['ffmpeg', '-y', '-i', vid_path, '-vframes', '1', '-q:v', '5', probe_jpg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
        if os.path.exists(probe_jpg):
            im = Image.open(probe_jpg)
            w, h = im.size
            im.close()
            if w > 0 and h > 0:
                return w, h
    except Exception:
        pass
    try:
        cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:stream_tags=rotate:stream_side_data=rotation', '-of', 'json', vid_path]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(res.stdout)
        st = data['streams'][0]
        w, h = int(st['width']), int(st['height'])
        rot = int(st.get('tags', {}).get('rotate', 0))
        if not rot and 'side_data_list' in st:
            for sd in st['side_data_list']:
                if 'rotation' in sd:
                    rot = abs(int(sd['rotation']))
                    break
        if abs(rot) in (90, 270):
            return h, w
        return w, h
    except Exception:
        return 1080, 1920

# ==========================================
# موتور هوش مصنوعی سردبیر + طراحی بنر قلاب ۳ ثانیه اول (استایل کاغذ سوخته دوطبقه)
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
_AI_VIRAL_CACHE = {}

def build_fallback_hook_lines(title_text):
    """ساخت خودکار قلاب ۲ سطری با جمله کامل فارسی در صورت عدم دسترسی به API"""
    clean_t = clean_agency_prefix(title_text or "خبر مهم شیراز")
    clean_t = re.sub(r'[.!؟،؛:«»"\']+', ' ', clean_t)
    words = [w.strip() for w in clean_t.split() if w.strip()]
    if len(words) < 3:
        return "خبر فوری برای شیراز", "جزییات را حتما ببینید!"
    if len(words) <= 6:
        mid = max(2, len(words) // 2)
        l1 = " ".join(words[:mid])
        l2 = " ".join(words[mid:])
        if not l2.endswith(("!", "؟")):
            l2 += "!"
        return l1, l2
    # انتخاب ۴ تا ۶ کلمه اول + بستن جمله با عبارت کامل و جذاب
    l1 = " ".join(words[:3])
    l2_words = words[3:6]
    verbs = ("شد", "می‌شود", "است", "رسید", "کرد", "دارد", "بود", "گشت")
    if any(l2_words[-1].endswith(v) for v in verbs):
        l2 = " ".join(l2_words) + "!"
    else:
        l2 = " ".join(words[3:5]) + " را ببینید!"
    return l1, l2

def get_ai_viral_hook_and_caption(title, summary):
    """دریافت JSON استاندارد شامل hook و caption از هوش مصنوعی همراه با کش داخلی"""
    cache_key = (title or "")[:50]
    if cache_key in _AI_VIRAL_CACHE:
        return _AI_VIRAL_CACHE[cache_key]

    news_text = f"تیتر: {title}\nمتن خبر: {summary}".strip()
    if not GEMINI_API_KEY or len(news_text) < 15:
        l1, l2 = build_fallback_hook_lines(title)
        return (l1, l2, None)

    prompt = f"""تو یک سردبیر حرفه‌ای اخبار و متخصص وایرال کردن محتوا در اینستاگرام هستی.
متن خبری که در ادامه می‌آید را بخوان و خروجی را فقط و فقط به شکل یک آبجکت JSON معتبر برگردان. هیچ متن، توضیح یا فرمت مارک‌داون قبل و بعد از خروجی قرار نده.

ساختار JSON باید دقیقاً شامل این کلیدها باشد:
1. "hook_line1": سطر اول قلاب (۲ تا ۳ کلمه، بیانگر موضوع اصلی خبر، بدون نقطه‌چین و کاملاً صحیح از نظر دستور زبان فارسی).
2. "hook_line2": سطر دوم قلاب (۲ تا ۳ کلمه، ادامه و فعل کامل و هیجانی جمله که حتماً با ! یا ؟! تمام شود تا جمله کامل گردد).
3. "caption": متن کامل و جذاب برای کپشن اینستاگرام (۳ تا ۴ پاراگراف کوتاه و روان با جملات کامل و یک سوال تعاملی در انتها). در پایان کپشن آیدی @shirazlastnews و ۵ هشتگ مرتبط (حتماً شامل #شیراز و #آخرین_خبرهای_شیراز) قرار بده.

متن خبر:
{news_text}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.65, "responseMimeType": "application/json"}
    }
    try:
        r = requests.post(url, json=payload, timeout=12)
        if r.status_code == 200:
            raw_out = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            m = re.search(r"\{.*\}", raw_out, re.DOTALL)
            data = json.loads(m.group(0) if m else raw_out)
            h1 = str(data.get("hook_line1", "")).strip().replace("...", "")
            h2 = str(data.get("hook_line2", "")).strip().replace("...", "")
            cap = str(data.get("caption", "")).strip()
            if h1 and h2:
                if not h2.endswith(("!", "؟")):
                    h2 += "!"
                res = (h1, h2, cap if len(cap) > 40 else None)
                _AI_VIRAL_CACHE[cache_key] = res
                return res
    except Exception as e:
        print("AI JSON Hook fallback to local:", e)

    l1, l2 = build_fallback_hook_lines(title)
    res = (l1, l2, None)
    _AI_VIRAL_CACHE[cache_key] = res
    return res

def _make_torn_polygon(x1, y1, x2, y2, seed_val=10, step=14, jitter=9):
    """ساخت مختصات لبه‌های مضرس و پاره‌شده کاغذ"""
    rng = random.Random(seed_val)
    pts = []
    for x in range(x1, x2, step):
        pts.append((x, y1 + rng.randint(-jitter, jitter)))
    for y in range(y1, y2, step):
        pts.append((x2 + rng.randint(-jitter, jitter), y))
    for x in range(x2, x1, -step):
        pts.append((x, y2 + rng.randint(-jitter, jitter)))
    for y in range(y2, y1, -step):
        pts.append((x1 + rng.randint(-jitter, jitter), y))
    return pts

def create_3s_hook_overlay(W, H, title_text, summary_text=""):
    """
    طراحی لایه شفاف (RGBA) بنر دوطبقه کاغذ سوخته برای ۳ ثانیه اول ویدیو:
    - نوار اول: کاغذ کرم با لبه سوخته و فونت مشکی ضخیم
    - نوار دوم: کاغذ قرمز با لبه سوخته و فونت زرد با دورخط مشکی
    """
    ensure_persian_font()
    line1, line2, _ = get_ai_viral_hook_and_caption(title_text, summary_text)
    sc = W / 1080.0
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # فونت درشت و تنظیم خودکار اندازه برای جا شدن کامل در کادر
    _, f1, sz1 = fit_wrapped_text(line1, base_font_size=int(64 * sc), min_font_size=int(42 * sc), base_width=22, max_lines=1)
    _, f2, sz2 = fit_wrapped_text(line2, base_font_size=int(68 * sc), min_font_size=int(44 * sc), base_width=22, max_lines=1)

    tmp_d = ImageDraw.Draw(ov)
    b1 = tmp_d.textbbox((0, 0), line1, font=f1)
    b2 = tmp_d.textbbox((0, 0), line2, font=f2)
    w1, h1 = (b1[2] - b1[0]), (b1[3] - b1[1])
    w2, h2 = (b2[2] - b2[0]), (b2[3] - b2[1])

    pad_x = int(70 * sc)
    box_w1 = min(W - int(90 * sc), max(w1 + pad_x * 2, int(560 * sc)))
    box_w2 = min(W - int(80 * sc), max(w2 + pad_x * 2, int(600 * sc)))
    box_h1 = int(142 * sc)
    box_h2 = int(152 * sc)

    cx = W // 2
    top_y1 = int(H * 0.25) if H >= W else int(H * 0.22)
    top_y2 = top_y1 + box_h1 - int(12 * sc)

    # لایه سایه نرم زیر کاغذها
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh_d = ImageDraw.Draw(shadow)

    x1_l, x1_r = cx - box_w1 // 2, cx + box_w1 // 2
    x2_l, x2_r = cx - box_w2 // 2, cx + box_w2 // 2

    poly1_outer = _make_torn_polygon(x1_l - int(10*sc), top_y1 - int(8*sc), x1_r + int(10*sc), top_y1 + box_h1 + int(8*sc), seed_val=101, step=max(6, int(12*sc)), jitter=max(4, int(8*sc)))
    poly1_inner = _make_torn_polygon(x1_l, top_y1, x1_r, top_y1 + box_h1, seed_val=102, step=max(6, int(12*sc)), jitter=max(3, int(6*sc)))

    poly2_outer = _make_torn_polygon(x2_l - int(10*sc), top_y2 - int(8*sc), x2_r + int(10*sc), top_y2 + box_h2 + int(8*sc), seed_val=202, step=max(6, int(12*sc)), jitter=max(4, int(8*sc)))
    poly2_inner = _make_torn_polygon(x2_l, top_y2, x2_r, top_y2 + box_h2, seed_val=203, step=max(6, int(12*sc)), jitter=max(3, int(6*sc)))

    sh_d.polygon([(x + int(8*sc), y + int(12*sc)) for x, y in poly1_outer], fill=(0, 0, 0, 185))
    sh_d.polygon([(x + int(8*sc), y + int(12*sc)) for x, y in poly2_outer], fill=(0, 0, 0, 195))
    ov = Image.alpha_composite(ov, shadow.filter(ImageFilter.GaussianBlur(max(3, int(8 * sc)))))
    draw = ImageDraw.Draw(ov)

    # ۱. رسم نوار بالایی (لبه سوخته قهوه‌ای تیره + کاغذ کرم روشن)
    draw.polygon(poly1_outer, fill=(58, 32, 14, 250))
    draw.polygon(poly1_inner, fill=(242, 222, 186, 255), outline=(120, 72, 32, 255))

    # ۲. رسم نوار پایینی (لبه سوخته زرشکی/مشکی + کاغذ قرمز تند)
    draw.polygon(poly2_outer, fill=(45, 10, 10, 252))
    draw.polygon(poly2_inner, fill=(192, 18, 24, 255), outline=(95, 12, 14, 255))

    # نوشتن متن سطر اول (مشکی ضخیم با سایه ظریف سفید روی کاغذ کرم)
    tx1 = cx - w1 // 2
    ty1 = top_y1 + (box_h1 - h1) // 2 - int(12 * sc)
    draw.text((tx1, ty1), line1, font=f1, fill=(18, 12, 8, 255), stroke_width=max(1, int(2 * sc)), stroke_fill=(255, 248, 230, 255))

    # نوشتن متن سطر دوم (زرد درخشان با دورخط ضخیم مشکی روی کاغذ قرمز)
    tx2 = cx - w2 // 2
    ty2 = top_y2 + (box_h2 - h2) // 2 - int(12 * sc)
    draw.text((tx2, ty2), line2, font=f2, fill=(255, 230, 25, 255), stroke_width=max(3, int(6 * sc)), stroke_fill=(10, 10, 10, 255))

    return ov

def find_watermark_file():
    for wm_name in ['watermark.mp4', 'Watermark.mp4', 'WATERMARK.MP4', 'watermark.mov']:
        if os.path.exists(wm_name) and os.path.getsize(wm_name) > 1000:
            return wm_name
    return None

def process_local_video_file(raw_vid, subtitle_text='', source_name='رسانه‌های خبری', out_prefix='vid'):
    try:
        tg_vid = f'{out_prefix}_tg.mp4'
        reel_vid = f'{out_prefix}_reel.mp4'
        vw, vh = get_video_dimensions(raw_vid)
        is_vertical = (vh >= vw)
        wm_file = find_watermark_file()

        # ساخت بنر قلاب ۳ ثانیه اول (کاغذ سوخته دوطبقه)
        hook_9_16 = create_3s_hook_overlay(1080, 1920, subtitle_text, subtitle_text)
        hook_9_16.save('ov_hook_9_16.png', format='PNG')

        if is_vertical:
            ov_tg = create_9_16_video_overlay(1080, 1920, subtitle_text, source_name)
            ov_tg.save('ov_tg_9_16.png', format='PNG')

            flt_base_9_16 = (
                '[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:4,eq=brightness=-0.22,setsar=1[bg];'
                '[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,setsar=1[fg];'
                '[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[base];'
                '[base][1:v]overlay=0:0,setsar=1[with_frame];'
                "[with_frame][2:v]overlay=0:0:enable='between(t,0,3)',setsar=1"
            )

            done_vertical = False
            if wm_file:
                try:
                    flt_wm_9_16 = (
                        f'{flt_base_9_16},fps=30,setpts=PTS-STARTPTS,format=gbrp,setsar=1[main_rgb];'
                        '[3:v]fps=30,scale=1080:1920:force_original_aspect_ratio=decrease,'
                        'pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,'
                        'tpad=start_duration=3:start_mode=add:color=black:stop=-1:stop_mode=add:color=black,'
                        'setpts=PTS-STARTPTS,format=gbrp,setsar=1[wm_rgb];'
                        '[main_rgb][wm_rgb]blend=all_mode=lighten:all_opacity=0.78:shortest=1,format=yuv420p,setsar=1'
                    )
                    cmd_tg_wm = [
                        'ffmpeg', '-y', '-i', raw_vid, '-i', 'ov_tg_9_16.png', '-i', 'ov_hook_9_16.png', '-i', wm_file,
                        '-filter_complex', flt_wm_9_16,
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '26', '-maxrate', '1900k', '-bufsize', '3800k',
                        '-profile:v', 'high', '-level', '4.1', '-r', '30', '-c:a', 'aac', '-b:a', '96k',
                        '-ar', '44100', '-ac', '2', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                        '-metadata:s:v:0', 'rotate=0', '-t', '58', tg_vid
                    ]
                    subprocess.run(cmd_tg_wm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=125, check=True)
                    done_vertical = True
                except Exception as e_wm:
                    print('Watermark+Hook 9:16 fallback to Hook-only:', e_wm)

            if not done_vertical:
                cmd_tg = [
                    'ffmpeg', '-y', '-i', raw_vid, '-i', 'ov_tg_9_16.png', '-i', 'ov_hook_9_16.png',
                    '-filter_complex', flt_base_9_16,
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '26', '-maxrate', '1900k', '-bufsize', '3800k',
                    '-profile:v', 'high', '-level', '4.1', '-r', '30', '-c:a', 'aac', '-b:a', '96k',
                    '-ar', '44100', '-ac', '2', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                    '-metadata:s:v:0', 'rotate=0', '-t', '58', tg_vid
                ]
                subprocess.run(cmd_tg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=115, check=True)

            return tg_vid, tg_vid, 1080, 1920

        else:
            out_w, out_h = 1280, 720
            hook_16_9 = create_3s_hook_overlay(1280, 720, subtitle_text, subtitle_text)
            hook_16_9.save('ov_hook_16_9.png', format='PNG')
            frame = get_transparent_frame()
            if frame:
                frame.save('ov_tg_16_9.png', format='PNG')
                flt_base_16_9 = (
                    '[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=#0a101e,setsar=1[base];'
                    '[1:v]scale=1280:720,setsar=1[wm];'
                    '[base][wm]overlay=0:0,setsar=1[with_frame];'
                    "[with_frame][2:v]overlay=0:0:enable='between(t,0,3)',setsar=1"
                )
                done_16_9 = False
                if wm_file:
                    try:
                        flt_wm_16_9 = (
                            f'{flt_base_16_9},fps=30,setpts=PTS-STARTPTS,format=gbrp,setsar=1[main_rgb];'
                            '[3:v]fps=30,scale=1280:720:force_original_aspect_ratio=decrease,'
                            'pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black,'
                            'tpad=start_duration=3:start_mode=add:color=black:stop=-1:stop_mode=add:color=black,'
                            'setpts=PTS-STARTPTS,format=gbrp,setsar=1[wm_rgb];'
                            '[main_rgb][wm_rgb]blend=all_mode=lighten:all_opacity=0.78:shortest=1,format=yuv420p,setsar=1'
                        )
                        cmd_tg16_wm = [
                            'ffmpeg', '-y', '-i', raw_vid, '-i', 'ov_tg_16_9.png', '-i', 'ov_hook_16_9.png', '-i', wm_file,
                            '-filter_complex', flt_wm_16_9,
                            '-c:v', 'libx264', '-preset', 'fast', '-crf', '26', '-maxrate', '1700k', '-bufsize', '3400k',
                            '-profile:v', 'high', '-c:a', 'aac', '-b:a', '96k', '-pix_fmt', 'yuv420p',
                            '-movflags', '+faststart', '-metadata:s:v:0', 'rotate=0', '-t', '58', tg_vid
                        ]
                        subprocess.run(cmd_tg16_wm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120, check=True)
                        done_16_9 = True
                    except Exception as e_wm16:
                        print('Watermark+Hook 16:9 fallback:', e_wm16)

                if not done_16_9:
                    cmd_tg16 = [
                        'ffmpeg', '-y', '-i', raw_vid, '-i', 'ov_tg_16_9.png', '-i', 'ov_hook_16_9.png',
                        '-filter_complex', flt_base_16_9,
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '26', '-maxrate', '1700k', '-bufsize', '3400k',
                        '-profile:v', 'high', '-c:a', 'aac', '-b:a', '96k', '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart', '-metadata:s:v:0', 'rotate=0', '-t', '58', tg_vid
                    ]
                    subprocess.run(cmd_tg16, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=110, check=True)
            else:
                tg_vid = raw_vid
                out_w, out_h = vw, vh

            ov_reel = create_9_16_video_overlay(1080, 1920, subtitle_text, source_name)
            ov_reel.save('ov_reel_9_16.png', format='PNG')
            flt_base_reel = (
                '[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.25,setsar=1[bg];'
                '[0:v]scale=1020:-2:force_original_aspect_ratio=decrease,setsar=1[fg];'
                '[bg][fg]overlay=(W-w)/2:(H-h)/2-80,setsar=1[comp];'
                '[comp][1:v]overlay=0:0,setsar=1[with_frame];'
                "[with_frame][2:v]overlay=0:0:enable='between(t,0,3)',setsar=1"
            )

            done_reel = False
            if wm_file:
                try:
                    flt_wm_reel = (
                        f'{flt_base_reel},fps=30,setpts=PTS-STARTPTS,format=gbrp,setsar=1[main_rgb];'
                        '[3:v]fps=30,scale=1080:1920:force_original_aspect_ratio=decrease,'
                        'pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,'
                        'tpad=start_duration=3:start_mode=add:color=black:stop=-1:stop_mode=add:color=black,'
                        'setpts=PTS-STARTPTS,format=gbrp,setsar=1[wm_rgb];'
                        '[main_rgb][wm_rgb]blend=all_mode=lighten:all_opacity=0.78:shortest=1,format=yuv420p,setsar=1'
                    )
                    cmd_reel_wm = [
                        'ffmpeg', '-y', '-i', raw_vid, '-i', 'ov_reel_9_16.png', '-i', 'ov_hook_9_16.png', '-i', wm_file,
                        '-filter_complex', flt_wm_reel,
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '26', '-maxrate', '1900k', '-bufsize', '3800k',
                        '-profile:v', 'high', '-level', '4.1', '-r', '30', '-c:a', 'aac', '-b:a', '96k',
                        '-ar', '44100', '-ac', '2', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                        '-metadata:s:v:0', 'rotate=0', '-t', '58', reel_vid
                    ]
                    subprocess.run(cmd_reel_wm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=125, check=True)
                    done_reel = True
                except Exception as e_wmr:
                    print('Watermark+Hook reel fallback:', e_wmr)

            if not done_reel:
                cmd_reel = [
                    'ffmpeg', '-y', '-i', raw_vid, '-i', 'ov_reel_9_16.png', '-i', 'ov_hook_9_16.png',
                    '-filter_complex', flt_base_reel,
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '26', '-maxrate', '1900k', '-bufsize', '3800k',
                    '-profile:v', 'high', '-level', '4.1', '-r', '30', '-c:a', 'aac', '-b:a', '96k',
                    '-ar', '44100', '-ac', '2', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                    '-metadata:s:v:0', 'rotate=0', '-t', '58', reel_vid
                ]
                subprocess.run(cmd_reel, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=115, check=True)

            return (tg_vid if os.path.exists(tg_vid) else raw_vid), (reel_vid if os.path.exists(reel_vid) else tg_vid), out_w, out_h
    except Exception as e:
        print('Local video process error:', e)
        return None, None, 1080, 1920

def process_video_for_telegram_and_reels(vid_url, subtitle_text='', source_name='رسانه‌های خبری'):
    try:
        r = requests.get(vid_url, headers=HEADERS, stream=True, timeout=25, verify=False)
        if r.status_code != 200:
            return None, None, 1080, 1920
        raw_vid = 'raw_video.mp4'
        size = 0
        with open(raw_vid, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 512):
                if chunk:
                    f.write(chunk)
                    size += len(chunk)
                    if size > 45 * 1024 * 1024:
                        return None, None, 1080, 1920
        if size < 35000:
            return None, None, 1080, 1920
        return process_local_video_file(raw_vid, subtitle_text, source_name, out_prefix='news_vid')
    except Exception as e:
        print('Video download error:', e)
        return None, None, 1080, 1920

def get_raw_image(entry, url):
    img_url = None
    if 'media_content' in entry and len(entry.media_content) > 0:
        img_url = entry.media_content[0].get('url')
    if not img_url and 'links' in entry:
        for l in entry.links:
            if 'image' in l.get('type', ''):
                img_url = l.get('href')
                break
    if not img_url and url:
        try:
            r = requests.get(url, headers=HEADERS, timeout=6, verify=False)
            og = BeautifulSoup(r.text, 'html.parser').find('meta', property='og:image')
            if og and og.get('content'):
                img_url = og['content']
        except Exception:
            pass
    if img_url:
        try:
            r = requests.get(img_url, headers=HEADERS, timeout=8, verify=False)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(LAST_IMG_FILE, 'wb') as cf:
                    cf.write(r.content)
                return r.content
        except Exception:
            pass
    try:
        r = requests.get('https://picsum.photos/800/500', timeout=6)
        if r.status_code == 200:
            with open(LAST_IMG_FILE, 'wb') as cf:
                cf.write(r.content)
            return r.content
    except Exception:
        pass
    return None

# ==========================================
# ۱۴. ارسال به تلگرام و اینستاگرام، پادکست شبانه (بدون استوری) و خبرخوان ضدتکرار
# ==========================================
def send_news_post(chat_id, img_bytes, caption, news_link=None, video_path=None, vid_w=None, vid_h=None):
    try:
        kb = make_buttons(news_link)
        silent = is_silent_hours()
        if video_path and os.path.exists(video_path):
            with open(video_path, 'rb') as vf:
                bot.send_video(chat_id, vf, caption=caption, parse_mode='HTML', width=vid_w, height=vid_h, supports_streaming=True, reply_markup=kb, disable_notification=silent)
        elif img_bytes:
            photo_file = io.BytesIO(img_bytes)
            photo_file.name = 'news.jpg'
            bot.send_photo(chat_id, photo_file, caption=caption, parse_mode='HTML', reply_markup=kb, disable_notification=silent)
        else:
            bot.send_message(chat_id, caption, parse_mode='HTML', reply_markup=kb, disable_notification=silent)
        return True
    except Exception as e:
        print('Send error:', e)
        return False

def get_insta_client():
    return DummyInstaClient()

def can_post_to_insta(is_video=False):
    iran_now = datetime.utcnow() + timedelta(hours=3, minutes=30)
    h_ir = iran_now.hour
    if 1 <= h_ir < 7:
        return False
    if is_video:
        return get_active_reel_schedule_slot() is not None
    now_ts = int(time.time())
    if not os.path.exists(INSTA_LOG):
        return True
    try:
        txt = open(INSTA_LOG).read().strip()
        if not txt:
            return True
        cooldown = 1200 if ((13 <= h_ir <= 15) or (20 <= h_ir <= 23)) else 1800
        return (now_ts - int(txt)) >= cooldown
    except Exception:
        return True

def build_smart_hashtags(full_txt, is_fars_feed):
    tags = []
    for c in FARS_37_COUNTIES_UNAMBIGUOUS:
        if c in full_txt:
            tags.append('#' + c.replace(' ', '_').replace('‌', '_'))
    if tags or is_fars_feed:
        if '#شیراز' not in tags and 'شیراز' in full_txt:
            tags.insert(0, '#شیراز')
        tags.append('#استان_فارس')
    else:
        for p in IRAN_PLACES:
            if p in full_txt:
                tags.append('#' + p.replace(' ', '_'))
        if not tags:
            tags.append('#ایران')
    if any(k in full_txt for k in SPORT_KW):
        tags.append('#ورزشی')
    if 'فجر' in full_txt:
        tags.append('#فجر_سپاسی')
    if any(k in full_txt for k in ['اقتصاد', 'تورم', 'طلا', 'دلار', 'بانک', 'یارانه', 'معیشت']):
        tags.append('#اقتصادی')
    if any(k in full_txt for k in ['سیاسی', 'مجلس', 'دولت', 'رئیس جمهور', 'وزیر']):
        tags.append('#سیاسی')
    if any(k in full_txt for k in ALERT_KW):
        tags.append('#فوری')
    seen = []
    for t in tags:
        if t not in seen:
            seen.append(t)
    return ' '.join(seen[:5])

def build_viral_insta_hashtags(full_txt, is_fars_feed):
    topic_tags = build_smart_hashtags(full_txt, is_fars_feed)
    shiraz_tags = '#شیراز #شیرازی #اخبار_شیراز #فارس #شهر_راز #shiraz'
    viral_pool = random.choice(TRENDING_UNRELATED_TAGS)
    all_t = (topic_tags + ' ' + shiraz_tags + ' ' + viral_pool).split()
    seen = []
    for t in all_t:
        if t not in seen:
            seen.append(t)
    return ' '.join(seen[:18])

def format_insta_caption(title, summary, is_fars_feed, source_url, is_even_hour=True, is_video=False):
    clean_title = clean_agency_prefix(title)
    s = extract_complete_lead(summary, clean_title, min_chars=90, max_chars=600)
    source_name = 'اختصاصی آخرین خبرهای شیراز' if source_url == 'exclusive' else get_source_name(source_url)
    all_tags = build_viral_insta_hashtags(clean_title + ' ' + s, is_fars_feed)
    if is_video:
        cta_top = '✅ تا آخر ببینید! نظر شما درباره این ویدیو چیست؟ حتماً کامنت بگذارید👇'
    elif is_even_hour:
        cta_top = '✅ ورق بزنید 👈 نظر شما همشهریان عزیز درباره این خبر چیست؟ در کامنت‌ها بنویسید👇'
    else:
        cta_top = '✅ نظر شما همشهریان عزیز درباره این خبر چیست؟ در کامنت‌ها بنویسید👇'
    cta_bot = f'✅ برای دریافت فوری‌ترین خبرهای شیراز و فارس، پیج ما را دنبال کنید:\n🛑 @{INSTA_USER.replace("@", "")}'
    return f'⭕️ {clean_title}\n\n{cta_top}\n\n✅ {s}\n\n✅ منبع خبر: {source_name}\n\n{cta_bot}\n\n{all_tags}'

def upload_story_with_native_poll(cl, story_jpg_path):
    cl = cl or DummyInstaClient()
    if HAS_STORY_POLL:
        try:
            poll_sticker = StoryPoll(
                x=0.5, y=0.80, width=0.66, height=0.14,
                question='نظر شما چیست؟',
                tallies=[StoryTallie(text='عالیه 👍', count=0), StoryTallie(text='انتقاد دارم 👎', count=0)]
            )
            cl.photo_upload_to_story(story_jpg_path, polls=[poll_sticker])
            return True
        except Exception as e_p:
            print('Native poll fallback to standard story:', e_p)
    cl.photo_upload_to_story(story_jpg_path)
    return True

def post_to_instagram(cl, raw_img_bytes, insta_caption, is_story=False, title='', summary='', source_name='', hour_now=12):
    cl = cl or DummyInstaClient()
    if not raw_img_bytes:
        return False
    try:
        if is_story:
            tmp_jpg = 'temp_insta_story.jpg'
            with open(tmp_jpg, 'wb') as f:
                f.write(raw_img_bytes)
            return upload_story_with_native_poll(cl, tmp_jpg)
        is_even = (hour_now % 2 == 0)
        if is_even:
            slides = create_approved_carousel_slides(raw_img_bytes, title, summary, source_name)
            if len(slides) >= 2:
                try:
                    cl.album_upload(slides, caption=insta_caption)
                    with open(INSTA_LOG, 'w') as f:
                        f.write(str(int(time.time())))
                    return True
                except Exception as e_alb:
                    print('Album fallback:', e_alb)
        single_path = create_approved_post_slide1(raw_img_bytes, title, summary, source_name, is_carousel=False)
        if single_path:
            cl.photo_upload(single_path, caption=insta_caption)
            with open(INSTA_LOG, 'w') as f:
                f.write(str(int(time.time())))
            return True
    except Exception as e:
        print('Instagram Post/Story Error:', e)
        return False

def post_video_story_only_to_insta(cl, video_path):
    cl = cl or DummyInstaClient()
    if not os.path.exists(video_path):
        return False
    try:
        thumb_jpg = 'reel_thumb_st.jpg'
        subprocess.run(['ffmpeg', '-y', '-i', video_path, '-ss', '00:00:01', '-vframes', '1', thumb_jpg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cl.video_upload_to_story(video_path, thumbnail=thumb_jpg if os.path.exists(thumb_jpg) else None)
        return True
    except Exception as e:
        print('Instagram Video Story Only Error:', e)
        return False

def post_video_to_insta(cl, video_path, insta_caption, also_story=True, slot_id=None):
    cl = cl or DummyInstaClient()
    if not os.path.exists(video_path):
        return False
    try:
        thumb_jpg = 'reel_thumb.jpg'
        subprocess.run(['ffmpeg', '-y', '-i', video_path, '-ss', '00:00:01', '-vframes', '1', thumb_jpg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            cl.clip_upload(video_path, caption=insta_caption, thumbnail=thumb_jpg if os.path.exists(thumb_jpg) else None)
        except Exception:
            cl.video_upload(video_path, caption=insta_caption, thumbnail=thumb_jpg if os.path.exists(thumb_jpg) else None)
        if slot_id:
            mark_reel_slot_completed(slot_id)
        if also_story:
            try:
                cl.video_upload_to_story(video_path, thumbnail=thumb_jpg if os.path.exists(thumb_jpg) else None)
            except Exception:
                pass
        return True
    except Exception as e:
        print('Instagram Video Error:', e)
        return False

def check_daily_morning_post():
    today_str, hour_now = get_iran_jalali_date()
    last_date = open(DAILY_FILE, encoding='utf-8').read().strip() if os.path.exists(DAILY_FILE) else ''
    if hour_now == 8 and last_date != today_str:
        with open(DAILY_FILE, 'w', encoding='utf-8') as f:
            f.write(today_str)
        msg = (
            f'⭕️ <b>صبح بخیر شیراز! تقویم و گزارش روزانه ({today_str})</b>\n\n'
            f'✅ <b>اوقات شرعی به افق شیراز:</b>\n{get_shiraz_prayer_times()}\n\n'
            f'✅ <b>وضعیت آب‌وهوا:</b>\n{get_shiraz_weather()}\n\n'
            f'✅ <b>نبض بازار طلا و ارز:</b>\n{get_market_prices()}\n\n'
            f'🛑 <b>{CHANNEL_SIGN}</b>'
        )
        bot.send_message(TARGET_CHAT, msg, parse_mode='HTML', reply_markup=make_buttons(), disable_notification=is_silent_hours())
        save_memory_state(push_git=True)

# ۱. لغو کامل استوری اول صبح بازی‌های امروز طبق درخواست شما
def check_daily_matches_story(insta_cl):
    return

# ۲. ارسال فقط پادکست صوتی در ساعت ۲۱ (لغو کامل استوری شبانه بعد از پادکست)
def send_night_podcast_and_story(latest_raw_img, latest_title, insta_cl=None):
    today_str, hour_now = get_iran_jalali_date()
    last_night = open(NIGHT_FILE, encoding='utf-8').read().strip() if os.path.exists(NIGHT_FILE) else ''
    if hour_now == 21 and last_night != today_str and os.path.exists(TITLES_FILE):
        with open(NIGHT_FILE, 'w', encoding='utf-8') as f:
            f.write(today_str)
        save_memory_state(push_git=True)
        titles = [l.strip() for l in open(TITLES_FILE, encoding='utf-8') if l.strip()][-5:]
        if titles:
            try:
                speech_text = (
                    'شنوندگان عزیز، سلام و وقت بخیر. خلاصه مهم‌ترین خبرهای امروز در رسانه آخرین خبرهای شیراز: '
                    + ' . خبر بعدی: '.join(titles)
                    + ' . برای دریافت اخبار لحظه‌ای، همراه کانال آخرین خبرهای شیراز باشید.'
                )
                mp3_path = 'ShirazLastNews_Podcast.mp3'
                subprocess.run(['edge-tts', '--voice', 'fa-IR-FaridNeural', '--text', speech_text, '--write-media', mp3_path], check=True)
                with open(mp3_path, 'rb') as af:
                    thumb_io = None
                    if os.path.exists(FRAME_FILE):
                        t_img = Image.open(FRAME_FILE).convert('RGB').resize((300, 300))
                        thumb_io = io.BytesIO()
                        t_img.save(thumb_io, format='JPEG')
                        thumb_io.seek(0)
                        thumb_io.name = 'thumb.jpg'
                    cap_pod = f'⭕️ <b>پادکست صوتی | خلاصه مهم‌ترین خبرهای شیراز و فارس ({today_str})</b>\n\n✅ با صدای گوینده هوشمند اختصاصی\n\n🛑 <b>{CHANNEL_SIGN}</b>'
                    bot.send_audio(TARGET_CHAT, af, caption=cap_pod, parse_mode='HTML', title='پادکست آخرین خبرهای شیراز', performer='@ShirazLastNews', thumb=thumb_io, reply_markup=make_buttons(), disable_notification=is_silent_hours())
            except Exception as e:
                print('Podcast error:', e)

# ۳. ضدتکرار استوری زنده فوتبال (یکسان‌سازی نام تیم‌ها برای جلوگیری از استوری تکراری)
def _canonical_iran_team(name):
    s = normalize_persian_chars(name)
    for w in ['شهید', 'تهران', 'اصفهان', 'شیراز', 'تبریز', 'خوزستان', 'مازندران', 'اراک', 'سیرجان', 'قزوین', 'اردکان', 'خرم آباد', 'بندرانزلی', 'رفسنجان']:
        s = s.replace(w, '')
    s = re.sub(r'\s+', '', s).strip()
    if 'فجر' in s:
        return 'فجرسپاسی'
    return s

def check_live_iran_league_stories(insta_cl):
    today_str, _ = get_iran_jalali_date()
    l_state = {'date': today_str, 'matches': {}}
    if os.path.exists(LIVE_IRAN_STATE_FILE):
        try:
            loaded = json.load(open(LIVE_IRAN_STATE_FILE, encoding='utf-8'))
            if loaded.get('date') == today_str:
                l_state = loaded
        except Exception:
            pass
    live_matches = fetch_live_iran_league_matches()
    if not live_matches:
        return
    state_changed = False
    for m in live_matches:
        c_home = _canonical_iran_team(m['home'])
        c_away = _canonical_iran_team(m['away'])
        mk = f"{c_home}_{c_away}"
        st_txt = str(m.get('status', '')).strip()
        h_sc, a_sc = int(m.get('h_score', 0)), int(m.get('a_score', 0))
        is_future = bool(re.search(r'^\d{1,2}:\d{2}$', normalize_persian_chars(st_txt)))
        if is_future and h_sc == 0 and a_sc == 0:
            continue
        prev = l_state['matches'].get(mk)
        event_banner = None
        is_ht = any(w in st_txt for w in ['نیمه اول', 'بین دو نیمه', 'HT'])
        is_ft = any(w in st_txt for w in ['پایان', 'نهایی', 'FT']) and not is_ht
        if not prev:
            l_state['matches'][mk] = {'h_score': h_sc, 'a_score': a_sc, 'ht_sent': is_ht, 'ft_sent': is_ft}
            state_changed = True
            if (h_sc + a_sc) > 0 and not is_ft:
                event_banner = f"انفجار در ورزشگاه! ثبت گل در دیدار {m['home']} و {m['away']}"
        else:
            old_h, old_a = int(prev.get('h_score', 0)), int(prev.get('a_score', 0))
            if (h_sc + a_sc) > (old_h + old_a) and (h_sc > old_h or a_sc > old_a):
                scorer = m['home'] if h_sc > old_h else m['away']
                min_part = f' در دقیقه {to_persian_num(st_txt)}' if re.search(r'[0-9۰-۹]', st_txt) else ''
                event_banner = f'انفجار در ورزشگاه! ثبت گل برای {scorer}{min_part}'
                prev['h_score'], prev['a_score'] = h_sc, a_sc
                state_changed = True
            elif is_ht and not prev.get('ht_sent'):
                event_banner = f"پایان نیمه اول مسابقه | {m['home']} {to_persian_num(h_sc)} - {to_persian_num(a_sc)} {m['away']}"
                prev['ht_sent'] = True
                state_changed = True
            elif is_ft and not prev.get('ft_sent'):
                event_banner = f"سوت پایان بازی! نتیجه نهایی: {m['home']} {to_persian_num(h_sc)} - {to_persian_num(a_sc)} {m['away']}"
                prev['ft_sent'] = True
                state_changed = True
        if event_banner:
            st_bytes = create_3d_live_match_story(m, event_banner)
            if st_bytes:
                if insta_cl:
                    post_to_instagram(insta_cl, st_bytes, '', is_story=True)
                if ADMIN_ID:
                    try:
                        s_io = io.BytesIO(st_bytes)
                        s_io.name = 'live_match_story.jpg'
                        bot.send_photo(ADMIN_ID, s_io, caption=f'🔴 <b>استوری زنده لیگ برتر ایران منتشر شد:</b>\n⚽️ {event_banner}', parse_mode='HTML')
                    except Exception:
                        pass
    if state_changed:
        with open(LIVE_IRAN_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(l_state, f, ensure_ascii=False)
        save_memory_state(push_git=True)

def clean_html(raw_html):
    if not raw_html:
        return ''
    return re.sub(r'\s+', ' ', BeautifulSoup(raw_html, 'html.parser').get_text()).strip()

def format_caption(title, summary, is_fars_feed, source_url, is_video=False):
    clean_title = clean_agency_prefix(title)
    s = extract_complete_lead(summary, clean_title, min_chars=80, max_chars=520)
    full_txt = clean_title + ' ' + s
    safe_title = html.escape(clean_title)
    safe_s = html.escape(s)
    tags = build_smart_hashtags(full_txt, is_fars_feed)
    source_name = 'اختصاصی آخرین خبرهای شیراز' if source_url == 'exclusive' else get_source_name(source_url)
    return f'⭕️ <b>{safe_title}</b>\n\n✅ {safe_s}\n\n✅ <b>منبع خبر:</b> {source_name}\n#️⃣ {tags}\n🛑 <b>{CHANNEL_SIGN}</b>'

def make_buttons(news_link=None):
    markup = InlineKeyboardMarkup()
    if news_link:
        markup.add(InlineKeyboardButton('🔗 مشاهده متن کامل خبر', url=news_link))
    clean_bot = BOT_USERNAME.replace('@', '').strip()
    citizen_url = f'https://t.me/{clean_bot}' if clean_bot else CHANNEL_LINK
    markup.add(InlineKeyboardButton('💰 نرخ طلا و ارز | 🌤 هواشناسی | 📸 ارسال سوژه', url=citizen_url))
    markup.add(InlineKeyboardButton('📢 عضویت در آخرین خبرهای شیراز', url=CHANNEL_LINK))
    return markup

def fetch_and_send_single_drip_news(insta_cl, current_iran_hour):
    global first_run
    active_reel_slot = get_active_reel_schedule_slot()
    ordered_feeds = (
        VIDEO_PRIORITY_FEEDS + FARS_FEEDS + [f for f in RSS_FEEDS if f not in VIDEO_PRIORITY_FEEDS and f not in FARS_FEEDS]
    ) if active_reel_slot else RSS_FEEDS
    for u in ordered_feeds:
        try:
            resp = requests.get(u, headers=HEADERS, timeout=8, verify=False)
            feed = feedparser.parse(resp.content)
            is_vid_feed = any(vt in u for vt in VIDEO_FEED_TAGS)
            for entry in feed.entries[:6]:
                link = entry.get('link', '').strip()
                if not link:
                    continue
                title = clean_html(entry.get('title', ''))
                clean_t = clean_agency_prefix(title)
                raw_rss_sum = clean_html(entry.get('summary', entry.get('description', '')))
                if is_duplicate_news(link, clean_t, raw_rss_sum):
                    continue
                clean_s = fetch_full_lead_from_page(link, raw_rss_sum)
                if is_duplicate_news(link, clean_t, clean_s):
                    continue
                full_txt = clean_t + ' ' + clean_s
                is_shiraz_fars_news = is_strictly_fars_shiraz_news(clean_t, clean_s, u)
                has_kw = any(k in full_txt for k in KEYWORDS)
                if is_shiraz_fars_news or has_kw or is_vid_feed:
                    if first_run:
                        record_sent_news(link, clean_t, sent_to_insta=is_shiraz_fars_news, clean_s=clean_s)
                        continue
                    src_name = get_source_name(link or u)
                    vid_url = get_video_url(entry, link)
                    tg_vid_path, reel_vid_path, v_w, v_h = (
                        process_video_for_telegram_and_reels(vid_url, clean_t, src_name)
                        if vid_url else (None, None, None, None)
                    )
                    if is_vid_feed and not tg_vid_path and not is_shiraz_fars_news:
                        record_sent_news(link, clean_t, sent_to_insta=False, clean_s=clean_s)
                        continue
                    raw_img = get_raw_image(entry, link)
                    framed_img = clean_and_apply_frame(raw_img, clean_t) if (raw_img and not tg_vid_path) else None
                    cap = format_caption(title, clean_s, is_shiraz_fars_news, link or u, is_video=bool(tg_vid_path))
                    record_sent_news(link, clean_t, sent_to_insta=False, clean_s=clean_s)
                    if send_news_post(TARGET_CHAT, framed_img, cap, link, video_path=tg_vid_path, vid_w=v_w, vid_h=v_h):
                        if is_shiraz_fars_news:
                            with open(TITLES_FILE, 'a', encoding='utf-8') as tf:
                                tf.write(clean_t + '\n')
                        if not is_duplicate_for_insta(clean_t, clean_s):
                            is_even_h = (current_iran_hour % 2 == 0)
                            slot_now = get_active_reel_schedule_slot()
                            if reel_vid_path and slot_now and is_eligible_for_insta_reel(clean_t, clean_s, is_shiraz_fars_news):
                                record_sent_news(link, clean_t, sent_to_insta=True, clean_s=clean_s)
                                insta_cap = format_insta_caption(title, clean_s, is_shiraz_fars_news, link or u, is_even_hour=is_even_h, is_video=True)
                                post_video_to_insta(insta_cl, reel_vid_path, insta_cap, also_story=True, slot_id=slot_now)
                            elif raw_img and not reel_vid_path and is_shiraz_fars_news:
                                record_sent_news(link, clean_t, sent_to_insta=True, clean_s=clean_s)
                                # ۱. استوری ۹:۱۶ برای تمام خبرهای جدید شیراز و فارس ساخته و در صف قرار می‌گیرد
                                iran_now = datetime.utcnow() + timedelta(hours=3, minutes=30)
                                if not (1 <= iran_now.hour < 7):
                                    story_b = create_premium_news_story(raw_img, clean_t, clean_s, src_name)
                                    if story_b:
                                        post_to_instagram(insta_cl, story_b, '', is_story=True)
                                # ۲. پست ۴:۵ طبق فاصله زمانی استاندارد (۲۰ تا ۳۰ دقیقه) منتشر می‌شود
                                if can_post_to_insta(is_video=False):
                                    insta_cap = format_insta_caption(title, clean_s, True, link or u, is_even_hour=is_even_h, is_video=False)
                                    post_to_instagram(insta_cl, raw_img, insta_cap, is_story=False, title=clean_t, summary=clean_s, source_name=src_name, hour_now=current_iran_hour)
                        save_memory_state(push_git=True)
                        return 1, raw_img if is_shiraz_fars_news else None, clean_t if is_shiraz_fars_news else None
        except Exception as e:
            print('Feed loop error:', e)
    if first_run:
        first_run = False
        save_memory_state(push_git=True)
    return 0, None, None

# ==========================================
# ۱۵. حلقه اصلی اجرای ۵۰ دقیقه‌ای ربات (Main Loop)
# ==========================================
insta_cl = get_insta_client()
SESSION_DURATION_SECONDS = 50 * 60
DRIP_INTERVAL_SECONDS = 360
LIVE_MATCH_CHECK_INTERVAL = 60

start_run_ts = time.time()
last_rss_check_ts = 0
last_live_match_ts = 0
total_sent_session = 0
last_raw_img = None
last_title = None

print('Starting Continuous 50-Minute Drip-Feed + Live Iran League Runner...')
while (time.time() - start_run_ts) < SESSION_DURATION_SECONDS:
    _, current_iran_hour = get_iran_jalali_date()
    process_bot_service(insta_cl=insta_cl, current_iran_hour=current_iran_hour)
    now_t = time.time()
    if (now_t - last_live_match_ts) >= LIVE_MATCH_CHECK_INTERVAL:
        last_live_match_ts = now_t
        check_live_iran_league_stories(insta_cl)
    if (now_t - last_rss_check_ts) >= DRIP_INTERVAL_SECONDS:
        last_rss_check_ts = now_t
        check_daily_morning_post()
        check_thursday_tourism_post(insta_cl)
        cnt, r_img, r_title = fetch_and_send_single_drip_news(insta_cl, current_iran_hour)
        total_sent_session += cnt
        if r_img:
            last_raw_img = r_img
        if r_title:
            last_title = r_title
        send_night_podcast_and_story(last_raw_img, last_title, insta_cl)
    time.sleep(5)

save_memory_state(push_git=True)
print(f'Session finished cleanly! Total drip-fed news items: {total_sent_session}')
