# =======================================================================
# 👑 JSM AI - V40.1 FINAL MASTER - JAM SAEED MUTHA - 5 KEYS ACTIVE
# =======================================================================

import streamlit as st
import requests, os, re, asyncio, datetime, sqlite3
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mp
import edge_tts
import numpy as np
from contextlib import closing
from itertools import cycle

ADMIN_PASSWORD = os.environ.get("ADMIN_KEY", "jsm_master_saeed_786")
BRAND_NAME = "JSM AI"
BRAND_FULL = "JAM SAEED MUTHA"

# ✅ تیری 5 Pexels Keys - آٹو روٹیشن
PEXELS_KEYS = [
    "ROKJvfYuuSkc7QVVL6VjCgYFyB8UQZCLLCctD2SfTJcIrDGo5Ex3JMX6",
    "zniYyavhaI66VGwuV2kUIpRm7vG3Y0rddDLuzrlTvmPqQ26kdG0vcyy0",
    "f6IKxrHR8MHj1geD62crLTfDTQX0s7ewFkw3hEI4d4CenRTZXCkpCWD9",
    "1j6kFq1GRB4291F1s1RMGhlglX3d3u78OaTpiDKmtISAjJkKPb9vVTkL",
    "tpkypogswv07n84dh0iaHI9tamu43GEcvZokA3Xi3JSTUT0NV32A6gG9",
]
PEXELS_KEYS = [k.strip() for k in PEXELS_KEYS if k.strip()]
KEY_CYCLE = cycle(PEXELS_KEYS)

DB_FILE = "jsm_ai_database.db"

def init_db():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (email TEXT PRIMARY KEY, credits INTEGER, plan TEXT,
                      free_videos_today INTEGER, last_free_date TEXT,
                      expiry_date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS ips (ip TEXT PRIMARY KEY, email TEXT)''')
        c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?)",
                  ("saeed@jsm.com", 500000, "Master Owner", 0, "", "2099-12-31"))
        conn.commit()

def get_user(email):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        c = conn.cursor()
        c.execute("SELECT credits, plan, free_videos_today, last_free_date, expiry_date FROM users WHERE email=?", (email,))
        row = c.fetchone()
        if row:
            return {"credits": row[0], "plan": row[1], "free_videos_today": row[2],
                    "last_free_date": row[3], "expiry_date": row[4]}
        return None

def update_user(email, credits, plan, free_videos_today, last_free_date, expiry_date):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?)",
                  (email, credits, plan, free_videos_today, last_free_date, expiry_date))
        conn.commit()

def reset_daily_free_if_needed(email):
    user = get_user(email)
    today = str(datetime.date.today())
    if user and user["last_free_date"]!= today:
        update_user(email, user["credits"], user["plan"], 0, today, user["expiry_date"])

def is_package_active(user):
    if user["plan"] == "Free Trial": return True
    if not user["expiry_date"]: return False
    expiry = datetime.datetime.strptime(user["expiry_date"], "%Y-%m-%d").date()
    return datetime.date.today() <= expiry

init_db()

st.set_page_config(page_title="JSM AI - Golden Studio", page_icon="👑", layout="wide")
st.markdown("""
    <style>
   @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;900&display=swap');
   html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
.main { background: radial-gradient(circle at top, #1a1a1a 0%, #0d1117 100%); color: #ffffff; }
.stButton>button {
        background: linear-gradient(90deg, #FFD700 0%, #FFA500 50%, #FFD700 100%);
        color: #000; font-weight: 700; font-size: 16px; border-radius: 12px; width: 100%;
        border: 2px solid #FFD700; box-shadow: 0 0 25px rgba(255, 215, 0, 0.6);
    }
.stButton>button:hover { background: #FFD700; transform: scale(1.05); }
.golden-card {
        background: linear-gradient(145deg, #1a1a1a, #2d2d2d);
        border: 2px solid #FFD700; border-radius: 18px; padding: 25px;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.5); margin: 15px 0;
    }
.metric-gold { color: #FFD700; font-size: 32px; font-weight: 700; text-shadow: 0 0 10px #FFD700; }
.brand-title {
        background: linear-gradient(90deg, #FFD700, #FFA500, #FFD700);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 56px; font-weight: 900; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"<h1 class='brand-title'>👑 {BRAND_NAME}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #FFA500; font-size: 18px;'>Premium AI Video Studio by {BRAND_FULL}</p>", unsafe_allow_html=True)
st.write("---")

if 'active_email' not in st.session_state: st.session_state['active_email'] = None

st.sidebar.markdown("<h2 style='color: #FFD700;'>🔐 JSM Control</h2>", unsafe_allow_html=True)
with st.sidebar.expander("👑 Admin Login"):
    adm_pass = st.text_input("Admin Key:", type="password")
    if adm_pass == ADMIN_PASSWORD:
        st.success("Authorized!")
        st.write(f"**Active API Keys: {len(PEXELS_KEYS)}**")
        t_email = st.text_input("User Gmail:").strip().lower()
        t_credits = st.number_input("Assign Words:", min_value=0, value=50000, step=5000)
        package_days = st.number_input("Package Days:", min_value=1, value=30, step=1)
        if st.button("⚡ Activate Package"):
            if t_email and "@" in t_email:
                expiry = datetime.date.today() + datetime.timedelta(days=package_days)
                update_user(t_email, t_credits, "Premium Creator", 0, "", str(expiry))
                st.success(f"Activated! Expiry: {expiry}")
                st.rerun()

if not st.session_state['active_email']:
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("""
            <div class='golden-card'>
                <h3 style='color: #FFD700;'>🚀 Start Free Trial</h3>
                <p>ہر 24 گھنٹے میں <b style='color: #FFD700;'>2 ویڈیو بالکل فری</b> بناؤ!</p>
            </div>
        """, unsafe_allow_html=True)
        input_email = st.text_input("📧 اپنی Gmail درج کریں:").strip().lower()
        if st.button("🎁 فری میں شروع کریں"):
            if input_email and "@" in input_email:
                if not get_user(input_email):
                    update_user(input_email, 0, "Free Trial", 0, str(datetime.date.today()), "")
                reset_daily_free_if_needed(input_email)
                st.session_state['active_email'] = input_email
                st.rerun()
            else: st.error("❌ درست Gmail لکھیں")
    with col_r:
        st.markdown(f"""
            <div class='golden-card'>
                <h4 style='color: #FFD700;'>💎 JSM STARTER PACK - 3,500 Rs</h4>
                <p>✔️ <b style='color: #FFD700;'>50,000 الفاظ</b> = 33 ویڈیو 10 منٹ والی</p>
                <p>✔️ <b style='color: #FFD700;'>30 دن کی Validity</b> - جس دن لو گے اس دن سے</p>
                <p>✔️ <b style='color: #FFD700;'>روز 2 فری</b> = 60 ویڈیو ایکسٹرا</p>
                <p>📢 <b>Managed by {BRAND_FULL}</b></p>
            </div>
        """, unsafe_allow_html=True)
else:
    current_user = st.session_state['active_email']
    reset_daily_free_if_needed(current_user)
    user_data = get_user(current_user)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='golden-card'><p>👤 یوزر</p><p class='metric-gold'>{current_user.split('@')[0]}</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='golden-card'><p>🎁 کریڈٹ</p><p class='metric-gold'>{user_data['credits']}</p></div>", unsafe_allow_html=True)
    with col3:
        free_left = 2 - user_data['free_videos_today']
        st.markdown(f"<div class='golden-card'><p>🆓 آج فری</p><p class='metric-gold'>{free_left} / 2</p></div>", unsafe_allow_html=True)
    with col4:
        exp_text = user_data['expiry_date'] if user_data['plan']!= "Free Trial" else "Lifetime"
        st.markdown(f"<div class='golden-card'><p>📅 Expiry</p><p class='metric-gold'>{exp_text}</p></div>", unsafe_allow_html=True)

    if st.sidebar.button("🚪 لاگ آؤٹ"):
        st.session_state['active_email'] = None
        st.rerun()

    package_active = is_package_active(user_data)
    is_free_user = user_data["plan"] == "Free Trial"
    can_use_free = is_free_user and user_data['free_videos_today'] < 2
    has_paid_credits = user_data["credits"] > 0 and package_active

    if not can_use_free and not has_paid_credits:
        if user_data["plan"]!= "Free Trial" and not package_active:
            st.markdown(f"""
                <div class='golden-card'>
                    <h3 style='color: #FFD700;'>🚨 پیکج Expire ہو گیا</h3>
                    <p>آپکا پیکج {user_data['expiry_date']} کو ختم ہو گیا تھا</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class='golden-card'>
                    <h3 style='color: #FFD700;'>🚨 آج کی فری لمٹ ختم</h3>
                    <p>کل پھر 2 فری ویڈیو ملیں گی</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        raw_input = st.text_area("📝 اپنا اسکرپٹ یہاں پیسٹ کریں:", height=150)
        word_count = len(raw_input.split())

        if word_count > 0:
            if can_use_free:
                st.info(f"🆓 یہ ویڈیو فری بنے گی! آج کی {user_data['free_videos_today']+1}/2 فری ویڈیو")
                if word_count > 150: st.warning("⚠️ فری میں 150 الفاظ = 1 منٹ کی لمٹ۔")
            else:
                st.write(f"📊 اسکرپٹ: **{word_count} الفاظ** | کٹیں گے: **{word_count} کریڈٹ**")

        col_set1, col_set2 = st.columns(2)
        with col_set1:
            video_ratio = st.radio("🎬 سائز:", ["Long Video (16:9)", "Shorts / Reels (9:16)"])
            quality = st.selectbox("🎥 کوالٹی:", ["SD 360p - تیز + سستی ⚡", "HD 720p - پریمیم"], disabled=is_free_user)
        with col_set2:
            t1 = st.text_input("✍️ تھمب نیل لائن 1:", value="VIRAL VIDEO")
            t2 = st.text_input("✍️ تھمب نیل لائن 2:", value=f"BY {BRAND_NAME}")

        if is_free_user or quality.startswith("SD"):
            W, H = (640, 360) if video_ratio == "Long Video (16:9)" else (360, 640)
        else:
            W, H = (1280, 720) if video_ratio == "Long Video (16:9)" else (720, 1280)

        def generate_thumb(txt1, txt2):
            img = Image.new('RGB', (1280, 720), color=(15, 20, 35))
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, 60, 720], fill=(255, 215, 0))
            try: font = ImageFont.truetype("DejaVuSans.ttf", 90)
            except: font = ImageFont.load_default(size=90)
            d.text((120, 220), txt1, font=font, fill=(255, 255, 255))
            d.text((120, 370), txt2, font=font, fill=(255, 215, 0))
            img.save("jsm_thumbnail.png")

        def fetch_video(query, idx):
            if not PEXELS_KEYS:
                fn = f"bg_fallback_{idx}.mp4"
                mp.ColorClip(size=(W, H), color=(15,30,55), duration=5).write_videofile(fn, fps=24, verbose=False, logger=None)
                return fn
            for key_idx in range(len(PEXELS_KEYS)):
                api_key = next(KEY_CYCLE)
                headers = {"Authorization": api_key}
                url = f"https://api.pexels.com/videos/search?query={query}&orientation={'landscape' if W>H else 'portrait'}&per_page=3"
                try:
                    r = requests.get(url, headers=headers, timeout=12)
                    if r.status_code == 429: continue
                    videos = r.json().get("videos", [])
                    if not videos: continue
                    v_link = videos[idx % len(videos)]["video_files"][0]["link"]
                    fn = f"bg_{idx}.mp4"
                    with open(fn, 'wb') as f: f.write(requests.get(v_link, timeout=20).content)
                    return fn
                except: continue
            fn = f"bg_fallback_{idx}.mp4"
            mp.ColorClip(size=(W, H), color=(15,30,55), duration=5).write_videofile(fn, fps=24, verbose=False, logger=None)
            return fn

        if st.button("🚀 ویڈیو بناؤ - بسم اللہ"):
            if word_count == 0: st.error("پہلے اسکرپٹ لکھیں۔")
            elif can_use_free and word_count > 150: st.error("🆓 فری میں 150 الفاظ سے زیادہ نہیں۔")
            elif not can_use_free and word_count > user_data["credits"]: st.error(f"🚨 بیلنس کم!")
            elif not package_active and not can_use_free: st.error("🚨 پیکج Expire ہو گیا!")
            else:
                success = False
                try:
                    with st.spinner(f"⚡ {BRAND_NAME} انجن چل رہا ہے... {len(PEXELS_KEYS)} Keys ایکٹو..."):
                        generate_thumb(t1, t2)
                        communicate = edge_tts.Communicate(raw_input, "en-US-AndrewNeural", rate="-3%")
                        asyncio.run(communicate.save("voice.mp3"))
                        audio_clip = mp.AudioFileClip("voice.mp3")
                        sentences = [s.strip() for s in re.split(r'\.\s*', raw_input) if len(s.strip()) > 8]
                        if not sentences: st.error("جملے نہیں ملے۔"); st.stop()
                        clips = []
                        progress = st.progress(0)
                        for i, sentence in enumerate(sentences):
                            v_path = fetch_video("golden luxury technology", i)
                            try:
                                raw_c = mp.VideoFileClip(v_path).resize((W, H)).without_audio()
                                raw_c = raw_c.subclip(0, min(raw_c.duration, 6))
                            except:
                                raw_c = mp.ColorClip(size=(W, H), color=(15,30,55), duration=5)
                            clips.append(raw_c)
                            progress.progress((i + 1) / len(sentences))
                        final_video = mp.concatenate_videoclips(clips, method="compose").set_audio(audio_clip)
                        final_video.write_videofile("JSM_OUTPUT.mp4", fps=24, codec="libx264", audio_codec="aac", preset='ultrafast', verbose=False, logger=None)
                        success = True
                except Exception as e: st.error(f"ایرر: {str(e)}")

                if success:
                    if can_use_free:
                        update_user(current_user, user_data["credits"], user_data["plan"],
                                   user_data['free_videos_today'] + 1, user_data['last_free_date'], user_data['expiry_date'])
                        st.success("✅ فری ویڈیو تیار!")
                    else:
                        update_user(current_user, user_data["credits"] - word_count, user_data["plan"],
                                   user_data['free_videos_today'], user_data['last_free_date'], user_data['expiry_date'])
                        st.success(f"✅ پریمیم ویڈیو تیار! {word_count} کریڈٹ کٹ گئے")
                    st.balloons()
                    st.rerun()

        if os.path.exists("JSM_OUTPUT.mp4"):
            st.write("---")
            st.markdown(f"<h3 style='color: #FFD700;'>👑 آپکی {BRAND_NAME} ویڈیو تیار ہے!</h3>", unsafe_allow_html=True)
            col_vid, col_meta = st.columns([2,1])
            with col_vid:
                st.video("JSM_OUTPUT.mp4")
                st.download_button("📥 ویڈیو ڈاؤن لوڈ کریں", open("JSM_OUTPUT.mp4", "rb"), "JSM_AI_Video.mp4")
            with col_meta:
                if os.path.exists("jsm_thumbnail.png"):
                    st.image("jsm_thumbnail.png", use_container_width=True)
                    st.download_button("📥 تھمب نیل ڈاؤن لوڈ", open("jsm_thumbnail.png", "rb"), "JSM_AI_Thumbnail.png")
