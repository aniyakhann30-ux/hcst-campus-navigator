"""HCST Smart Campus Guide - Streamlit app (single file).
All faculty data is synthetic. Marker coordinates are approximate until verified in Admin.
"""
import math
import re
import sqlite3
import difflib
import hashlib
import hmac
import html
import secrets as pysecrets
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus

import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium

# ------------------------------------------------------------------ CONFIG
COLLEGE = "Hindustan College of Science and Technology"
COLLEGE_QUERY = "Hindustan College of Science and Technology, Farah, Mathura"
# Approximate centre (Farah). Replace by right-clicking the campus in Google Maps and copying coordinates.
C_LAT, C_LNG = 27.3212, 77.7609
DB_PATH = "hcst_campus.db"
DEMO_NOTE = "Demo data - not an actual HCST faculty or contact."

st.set_page_config(page_title="HCST Smart Campus Guide", page_icon="🎓", layout="wide")
st.markdown(
    """<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');
html, body, .stApp, [class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:radial-gradient(1100px 480px at 90% -8%, rgba(27,153,139,.12), transparent 60%),
       radial-gradient(900px 420px at -10% 8%, rgba(201,162,39,.12), transparent 60%), #FAF7F2;}
.block-container{padding-top:1.4rem;max-width:1200px;animation:fadeUp .5s ease both;}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@keyframes flow{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(255,255,255,.7)}70%{box-shadow:0 0 0 9px rgba(255,255,255,0)}100%{box-shadow:0 0 0 0 rgba(255,255,255,0)}}
h1,h2,h3{font-family:'Playfair Display',serif !important;color:#0B1F3A;letter-spacing:.2px;}

/* hero */
.hero{background:linear-gradient(120deg,#0B1F3A,#13335C,#1B998B,#13335C);background-size:300% 300%;animation:flow 16s ease infinite;
      padding:2rem 2.2rem;border-radius:22px;margin-bottom:1rem;position:relative;overflow:hidden;box-shadow:0 14px 34px rgba(11,31,58,.25);}
.hero:after{content:"";position:absolute;right:-60px;top:-60px;width:220px;height:220px;border-radius:50%;
            background:radial-gradient(circle,rgba(201,162,39,.55),transparent 70%);}
.hero h1,.hero h2{color:#fff !important;margin:.35rem 0 0 0;}
.hero h1{font-size:2.2rem;}
.hero h2{font-size:1.25rem;font-weight:600;opacity:.92;}
.hero p{margin:.5rem 0 0 0;color:#E6EEF8 !important;}
.chip{display:inline-flex;align-items:center;gap:.45rem;background:rgba(255,255,255,.14);color:#fff;padding:.25rem .7rem;border-radius:999px;font-size:.8rem;backdrop-filter:blur(4px);}
.live{width:8px;height:8px;border-radius:50%;background:#7CFFB2;animation:pulse 2s infinite;display:inline-block;}
.ticker{background:#fff;border:1px solid #eadfc4;border-left:5px solid #C9A227;padding:.65rem 1rem;border-radius:12px;margin-bottom:1rem;color:#1c2733;}
.demo{font-size:.8rem;color:#8a5a00;background:#fff4d6;padding:.2rem .55rem;border-radius:8px;display:inline-block;}

/* stat cards */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:.4rem 0 1rem 0;}
.stat{background:#fff;border:1px solid #eadfc4;border-radius:16px;padding:1rem;text-align:center;transition:transform .25s, box-shadow .25s;}
.stat:hover{transform:translateY(-4px);box-shadow:0 12px 26px rgba(11,31,58,.14);}
.stat b{display:block;font-family:'Playfair Display',serif;font-size:1.9rem;color:#0B1F3A;}
.stat span{color:#5b6b7c;font-size:.85rem;}
@media(max-width:720px){.stats{grid-template-columns:repeat(2,1fr);} .hero h1{font-size:1.6rem;}}

/* cards (st.container border=True) */
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px !important;background:#fff;border:1px solid #eadfc4 !important;
    box-shadow:0 2px 10px rgba(11,31,58,.05);transition:transform .25s ease, box-shadow .25s ease;}
[data-testid="stVerticalBlockBorderWrapper"]:hover{transform:translateY(-3px);box-shadow:0 14px 30px rgba(11,31,58,.13);}

/* buttons */
.stButton>button,.stLinkButton a,.stFormSubmitButton>button,.stDownloadButton>button{border-radius:999px !important;border:1px solid #C9A227 !important;
    background:#fff;color:#0B1F3A !important;font-weight:600;transition:all .25s ease;}
.stButton>button:hover,.stLinkButton a:hover,.stFormSubmitButton>button:hover{background:linear-gradient(135deg,#C9A227,#E8CF7A);transform:translateY(-2px);box-shadow:0 8px 18px rgba(201,162,39,.35);}
button[kind="primary"],.stFormSubmitButton>button[kind="primary"],.stFormSubmitButton>button[kind="primaryFormSubmit"]{background:linear-gradient(135deg,#0B1F3A,#1B998B) !important;color:#fff !important;border:none !important;}
button[kind="primary"]:hover,.stFormSubmitButton>button[kind="primaryFormSubmit"]:hover{filter:brightness(1.12);box-shadow:0 8px 20px rgba(27,153,139,.4);}

/* inputs */
.stTextInput input,.stTextArea textarea,.stDateInput input,.stNumberInput input{border-radius:12px !important;}
div[data-baseweb="select"]>div{border-radius:12px !important;}
.stTextInput input:focus,.stTextArea textarea:focus{box-shadow:0 0 0 2px rgba(27,153,139,.35) !important;}

/* tabs */
.stTabs [data-baseweb="tab"]{font-weight:600;border-radius:10px 10px 0 0;transition:background .2s;}
.stTabs [data-baseweb="tab"]:hover{background:rgba(201,162,39,.12);}
.stTabs [data-baseweb="tab-highlight"]{background:#C9A227 !important;}

/* sidebar */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0B1F3A 0%,#13335C 100%);}
[data-testid="stSidebar"] *{color:#E8EEF7 !important;}
[data-testid="stSidebar"] .brand{font-family:'Playfair Display',serif;font-size:1.25rem;line-height:1.2;padding:.3rem .2rem 1rem .2rem;}
[data-testid="stSidebar"] .brand span{font-family:'Inter',sans-serif;font-size:.78rem;opacity:.75;}
[data-testid="stSidebar"] .userchip{background:rgba(255,255,255,.1);padding:.55rem .8rem;border-radius:12px;margin-bottom:.8rem;font-size:.9rem;}
[data-testid="stSidebar"] div[role="radiogroup"] label{padding:.45rem .7rem;border-radius:10px;margin:2px 0;transition:all .2s ease;cursor:pointer;}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:rgba(255,255,255,.12);transform:translateX(5px);}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){background:rgba(201,162,39,.28);border-left:3px solid #C9A227;}
[data-testid="stSidebar"] .stButton>button{background:transparent !important;border:1px solid rgba(255,255,255,.55) !important;color:#fff !important;}
[data-testid="stSidebar"] .stButton>button:hover{background:rgba(201,162,39,.35) !important;}
.stAlert{border-radius:14px;}
</style>""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ DATABASE
@st.cache_resource
def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def qdf(sql, params=()):
    return pd.read_sql_query(sql, conn(), params=params)


def run(sql, params=()):
    c = conn()
    cur = c.execute(sql, params)
    c.commit()
    return cur.lastrowid


def m2deg(dx, dy):
    lat = C_LAT + dy / 111000.0
    lng = C_LNG + dx / (111000.0 * math.cos(math.radians(C_LAT)))
    return round(lat, 6), round(lng, 6)


T = "Sample: 9:00 AM - 5:00 PM (to be verified)"
# name, category, building, floor, dx(m), dy(m), description, timings, keywords
LOC_SEED = [
    ("Main Gate", "Entry", "Entrance", "Ground", 0, -220, "Main entrance of the campus. Starting point for most visitor journeys.", "Open daily (to be verified)", "entrance gate security start"),
    ("Reception", "Academic & Administrative", "Administrative Block", "Ground", 10, -170, "Front desk for visitors and general enquiries.", T, "front desk enquiry help visitor"),
    ("Admission Cell", "Academic & Administrative", "Administrative Block", "Ground", -30, -140, "Admission enquiries, counselling and application guidance.", T, "admission admissions enquiry counselling new student apply"),
    ("Document Verification Office", "Academic & Administrative", "Administrative Block", "Ground", -45, -125, "Verification of admission documents.", T, "document verification certificate documents admission"),
    ("Fee Office", "Academic & Administrative", "Administrative Block", "Ground", -60, -110, "Fee payment and fee-related enquiries.", T, "fee fees payment accounts cash admission fee"),
    ("Director's Office", "Academic & Administrative", "Administrative Block", "First", 40, -90, "Office of the Director.", T, "director principal head"),
    ("Dean of Academics", "Academic & Administrative", "Administrative Block", "First", 60, -80, "Dean of Academics office - academic policy and enquiries.", T, "dean academics academic enquiry"),
    ("Examination Cell", "Academic & Administrative", "Administrative Block", "Ground", 80, -60, "Examinations, results and related queries.", T, "exam examination results marksheet"),
    ("Training & Placement (T&P) Department", "Academic & Administrative", "Placement Block", "Ground", 100, -20, "Placement drives, internships and recruiter coordination.", T, "tnp t&p training placement placements job recruiter internship drive"),
    ("PDP Department", "Academic & Administrative", "Placement Block", "Ground", 120, -5, "Personality Development Programme - soft skills and career readiness.", T, "pdp personality development soft skills communication"),
    ("Computer Science Department", "Academic & Administrative", "Academic Block A", "Second", -40, -20, "Department of Computer Science and Engineering.", T, "computer science cse department it programming"),
    ("Computer Labs", "Academic & Administrative", "Academic Block A", "Ground", -60, 0, "Computer laboratories used by CS and other departments.", "Sample: during lab schedule", "computer lab labs laboratory"),
    ("Civil Engineering Department", "Academic & Administrative", "Academic Block B", "First", -120, 40, "Department of Civil Engineering.", T, "civil engineering department"),
    ("Seminar Hall", "Academic & Administrative", "Academic Block A", "First", 30, 10, "Seminars, guest lectures and workshops.", "As per event schedule", "seminar hall lecture workshop"),
    ("Library", "Campus Facility", "Library Building", "Ground", -10, 60, "Books, journals, reading room and digital resources.", "Sample: 8:30 AM - 6:00 PM (to be verified)", "library books reading study journals"),
    ("Cafeteria", "Campus Facility", "Cafeteria Block", "Ground", 60, 100, "Food, snacks and beverages.", "Sample: 8:00 AM - 6:00 PM (to be verified)", "cafeteria canteen food mess snacks tea coffee"),
    ("Auditorium", "Campus Facility", "Auditorium Building", "Ground", 150, 60, "Large events, orientation programmes and cultural functions.", "As per event schedule", "auditorium hall events orientation function"),
    ("Sports Ground", "Campus Facility", "Open Ground", "Ground", 0, 200, "Grounds and sports facilities.", "Sample: 6:00 AM - 7:00 PM (to be verified)", "sports ground playground cricket football game"),
    ("Medical Room", "Campus Facility", "Administrative Block", "Ground", -80, -60, "First aid and basic medical assistance.", "Sample: 9:00 AM - 5:00 PM (to be verified)", "medical doctor first aid health clinic"),
    ("Parking", "Campus Facility", "Parking Area", "Ground", -110, -170, "Vehicle parking for students, staff and visitors.", "Open daily (to be verified)", "parking vehicle bike car"),
    ("Transport Office", "Campus Facility", "Parking Area", "Ground", -130, -150, "College bus and transport enquiries.", T, "transport bus office route"),
    ("Drinking Water Point", "Campus Facility", "Near Library", "Ground", 20, 40, "Drinking water point.", "Open daily (to be verified)", "drinking water ro"),
    ("Washrooms", "Campus Facility", "Near Library", "Ground", 45, 45, "Washrooms.", "Open daily (to be verified)", "washroom toilet restroom"),
    ("Hostel Office", "Hostel", "Hostel Area", "Ground", -160, 110, "Hostel admissions, rooms and rules enquiries.", T, "hostel office warden accommodation room"),
    ("Boys' Hostel", "Hostel", "Hostel Area", "Ground", -200, 140, "Residence for male students.", "-", "boys boy hostel male residence"),
    ("Girls' Hostel", "Hostel", "Hostel Area", "Ground", 200, 150, "Residence for female students.", "-", "girls girl ladies women hostel female residence"),
]

FAC_SEED = [
    # name, designation, department, cabin, timings, responsibilities, role_loc
    ("Dr. Aarav Sharma", "Professor & HOD", "Computer Science", "CS-201", "Mon-Fri 11:00-13:00", "Department administration, curriculum, project allocation", "Computer Science Department"),
    ("Dr. Meera Kapoor", "Associate Professor", "Data Science", "CS-205", "Mon-Thu 14:00-16:00", "Data science electives, research mentoring", "Computer Science Department"),
    ("Prof. Rohan Verma", "Assistant Professor", "Computer Science", "CS-210", "Tue-Fri 10:00-12:00", "Lab coordination, student mentoring", "Computer Labs"),
    ("Dr. Nisha Rao", "Professor", "Civil Engineering", "CE-110", "Mon-Fri 12:00-14:00", "Structural engineering, department HOD", "Civil Engineering Department"),
    ("Dr. Kabir Malhotra", "Dean of Academics", "Administration", "ADM-12", "Mon-Fri 10:30-12:30", "Academic policies, academic enquiries, time-tables", "Dean of Academics"),
    ("Dr. Ishita Menon", "Director", "Administration", "ADM-01", "By appointment", "Institute administration and strategy", "Director's Office"),
    ("Mr. Aditya Bose", "Admission In-charge", "Admission Cell", "ADM-05", "Mon-Sat 10:00-16:00", "Admission enquiries, counselling, process guidance", "Admission Cell"),
    ("Ms. Tanvi Joshi", "Placement Coordinator", "Training & Placement", "TNP-02", "Mon-Fri 10:00-16:00", "Placement drives, recruiter coordination, internships", "Training & Placement (T&P) Department"),
    ("Dr. Sameer Khanna", "Controller of Examinations", "Examination Cell", "ADM-08", "Mon-Fri 11:00-15:00", "Examination schedules and results", "Examination Cell"),
    ("Ms. Pooja Nair", "PDP Faculty", "PDP", "TNP-05", "Mon-Fri 11:00-15:00", "Soft skills, communication and aptitude training", "PDP Department"),
]


def init_db():
    c = conn()
    c.executescript(
        """
    CREATE TABLE IF NOT EXISTS locations(id INTEGER PRIMARY KEY, name TEXT UNIQUE, category TEXT, building TEXT,
        floor TEXT, lat REAL, lng REAL, description TEXT, timings TEXT, keywords TEXT, verified INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS faculty(id INTEGER PRIMARY KEY, name TEXT, designation TEXT, department TEXT, cabin TEXT,
        timings TEXT, responsibilities TEXT, location_name TEXT, email TEXT, phone TEXT);
    CREATE TABLE IF NOT EXISTS appointments(id INTEGER PRIMARY KEY, name TEXT, phone TEXT, email TEXT, faculty_id INTEGER,
        purpose TEXT, details TEXT, appt_date TEXT, appt_time TEXT, status TEXT DEFAULT 'Pending', created TEXT);
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, phone TEXT, role TEXT,
        salt TEXT, pw_hash TEXT, created TEXT);
    CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, title TEXT, category TEXT, event_date TEXT, event_time TEXT,
        location_name TEXT, description TEXT);
    CREATE TABLE IF NOT EXISTS lost_found(id INTEGER PRIMARY KEY, kind TEXT, item TEXT, description TEXT, where_text TEXT,
        reporter TEXT, contact TEXT, status TEXT DEFAULT 'Open', claimant TEXT, claim_note TEXT, created TEXT);
    """
    )
    for tbl in ("appointments", "lost_found"):
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({tbl})")]
        if "user_id" not in cols:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN user_id INTEGER")
    c.commit()
    if c.execute("SELECT COUNT(*) FROM locations").fetchone()[0] == 0:
        for n, cat, b, fl, dx, dy, d, t, k in LOC_SEED:
            lat, lng = m2deg(dx, dy)
            c.execute("INSERT INTO locations(name,category,building,floor,lat,lng,description,timings,keywords,verified) VALUES(?,?,?,?,?,?,?,?,?,0)",
                      (n, cat, b, fl, lat, lng, d, t, k))
    if c.execute("SELECT COUNT(*) FROM faculty").fetchone()[0] == 0:
        for n, des, dep, cab, tim, resp, loc in FAC_SEED:
            slug = re.sub(r"[^a-z]", "", n.lower())
            c.execute("INSERT INTO faculty(name,designation,department,cabin,timings,responsibilities,location_name,email,phone) VALUES(?,?,?,?,?,?,?,?,?)",
                      (n, des, dep, cab, tim, resp, loc, f"{slug}@demo.example", "+91-00000-00000 (demo)"))
    if c.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
        t0 = date.today()
        ev = [
            ("Orientation Programme for New Students", "Orientation", t0 + timedelta(days=3), "10:00", "Auditorium", "Welcome session for newly admitted students and parents."),
            ("Campus Placement Drive (Demo Company)", "Placement", t0 + timedelta(days=7), "09:30", "Training & Placement (T&P) Department", "Sample placement drive; registration at T&P."),
            ("Guest Lecture: Careers in AI", "Seminar", t0 + timedelta(days=10), "14:00", "Seminar Hall", "Sample seminar on emerging technologies."),
            ("Inter-Department Sports Meet", "Sports", t0 + timedelta(days=15), "08:00", "Sports Ground", "Cricket, football and athletics."),
            ("Annual Cultural Evening", "Cultural", t0 + timedelta(days=25), "17:00", "Auditorium", "Music, dance and drama performances."),
            ("Notice: Fee Payment Window", "Notice", t0 + timedelta(days=5), "-", "Fee Office", "Sample notice - verify actual dates with the Fee Office."),
        ]
        for e in ev:
            c.execute("INSERT INTO events(title,category,event_date,event_time,location_name,description) VALUES(?,?,?,?,?,?)",
                      (e[0], e[1], e[2].isoformat(), e[3], e[4], e[5]))
    c.commit()


init_db()


# ------------------------------------------------------------------ AUTH
REQUIRE_LOGIN_FOR_ACTIONS = True  # set False to let anyone book / report without an account
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_pw(pw, salt=None):
    salt = salt or pysecrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(salt), 150_000).hex()
    return salt, h


def current_user():
    return st.session_state.get("user")


def login_required(msg):
    if current_user() or not REQUIRE_LOGIN_FOR_ACTIONS:
        return True
    st.warning(msg)
    st.button("🔑 Login / Sign up", on_click=lambda: st.session_state.update(page="Account"), type="primary", key="need_login_" + str(abs(hash(msg))))
    return False


# ------------------------------------------------------------------ HELPERS
def locations():
    return qdf("SELECT * FROM locations ORDER BY name")


def loc_by_name(name):
    r = qdf("SELECT * FROM locations WHERE name=?", (name,))
    return r.iloc[0] if len(r) else None


def haversine(a, b, c, d):
    R = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    dphi, dl = p2 - p1, math.radians(d - b)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def compass(a, b, c, d):
    y = math.sin(math.radians(d - b)) * math.cos(math.radians(c))
    x = math.cos(math.radians(a)) * math.sin(math.radians(c)) - math.sin(math.radians(a)) * math.cos(math.radians(c)) * math.cos(math.radians(d - b))
    br = (math.degrees(math.atan2(y, x)) + 360) % 360
    return ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"][int((br + 22.5) // 45) % 8]


def gmaps_dir(dest, origin=None, waypoints=None):
    u = f"https://www.google.com/maps/dir/?api=1&destination={dest['lat']},{dest['lng']}&travelmode=walking"
    if origin is not None:
        u += f"&origin={origin['lat']},{origin['lng']}"
    if waypoints:
        u += "&waypoints=" + "|".join(f"{w['lat']},{w['lng']}" for w in waypoints)
    return u


def gmaps_place(loc):
    return f"https://www.google.com/maps/search/?api=1&query={loc['lat']},{loc['lng']}"


COLORS = {"Entry": "green", "Academic & Administrative": "blue", "Campus Facility": "orange", "Hostel": "purple"}


def make_map(df, highlight=None, start=None, path=None, height=480):
    if len(df):
        centre = [df["lat"].mean(), df["lng"].mean()]
    else:
        centre = [C_LAT, C_LNG]
    m = folium.Map(location=centre, zoom_start=17, max_zoom=19, control_scale=True, tiles=None)
    folium.TileLayer("OpenStreetMap", name="Street map").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri", name="Satellite", max_zoom=19).add_to(m)
    for _, r in df.iterrows():
        is_h = highlight is not None and r["name"] == highlight["name"]
        v = "verified position" if r["verified"] else "approximate position"
        folium.Marker(
            [r["lat"], r["lng"]],
            tooltip=r["name"],
            popup=folium.Popup(f"<b>{r['name']}</b><br>{r['building']} · {r['floor']} floor<br><i>{v}</i>", max_width=250),
            icon=folium.Icon(color="red" if is_h else COLORS.get(r["category"], "gray"), icon="star" if is_h else "info-sign"),
        ).add_to(m)
    if start is not None:
        folium.Marker([start["lat"], start["lng"]], tooltip="Start: " + start["name"], icon=folium.Icon(color="green", icon="play")).add_to(m)
    if path:
        folium.PolyLine(path, color="#e63946", weight=4, dash_array="8", tooltip="Indicative route").add_to(m)
    folium.LayerControl().add_to(m)
    st_folium(m, height=height, use_container_width=True, returned_objects=[])


def nearby(loc, n=4):
    df = locations()
    df = df[df["name"] != loc["name"]].copy()
    df["dist"] = df.apply(lambda r: haversine(loc["lat"], loc["lng"], r["lat"], r["lng"]), axis=1)
    return df.sort_values("dist").head(n)


def goto(page):
    st.session_state["page"] = page


def book_with(fid):
    st.session_state["prefill_fid"] = int(fid)
    st.session_state["page"] = "Book Appointment"


# ------------------------------------------------------------------ DESTINATION PANEL
def destination_panel(dest, key):
    locs = locations()
    names = list(locs["name"])
    c1, c2 = st.columns([1, 1])
    with c1:
        start_opts = ["My current location (use Google Maps GPS)"] + names
        default = start_opts.index("Main Gate")
        start_name = st.selectbox("Starting point", start_opts, index=default, key=f"start_{key}")
    start = None if start_name.startswith("My current") else loc_by_name(start_name)

    left, right = st.columns([1, 1.4])
    with left:
        st.subheader(dest["name"])
        st.write(dest["description"])
        st.markdown(f"**Building:** {dest['building']}  \n**Floor:** {dest['floor']}  \n**Timings:** {dest['timings']}")
        if not dest["verified"]:
            st.caption("📍 Marker position is approximate and pending verification.")
        fac = qdf("SELECT * FROM faculty WHERE location_name=?", (dest["name"],))
        if len(fac):
            st.markdown("**People / contacts here** " + '<span class="demo">demo data</span>', unsafe_allow_html=True)
            for _, f in fac.iterrows():
                st.write(f"• {f['name']} - {f['designation']} (Cabin {f['cabin']})")
        st.link_button("🧭 Open directions in Google Maps", gmaps_dir(dest, start), use_container_width=True)
        if start is not None and start["name"] != dest["name"]:
            d = haversine(start["lat"], start["lng"], dest["lat"], dest["lng"])
            st.info(f"From **{start['name']}**, head **{compass(start['lat'], start['lng'], dest['lat'], dest['lng'])}** for roughly "
                    f"**{int(d)} m** (straight line). Then go to **{dest['building']}**, **{dest['floor']} floor**.")
        st.markdown("**Nearby facilities**")
        for _, r in nearby(dest).iterrows():
            st.write(f"• {r['name']} - ~{int(r['dist'])} m")
    with right:
        path = [[start["lat"], start["lng"]], [dest["lat"], dest["lng"]]] if start is not None else None
        make_map(locs, highlight=dest, start=start, path=path)
        st.caption("Red dashed line is an indicative straight-line guide, not a verified footpath.")


# ------------------------------------------------------------------ ROUTES
ROUTES = {
    "New admission visitor": ["Main Gate", "Admission Cell", "Document Verification Office", "Fee Office", "Hostel Office"],
    "Placement enquiry": ["Main Gate", "Reception", "Training & Placement (T&P) Department"],
    "Academic enquiry": ["Main Gate", "Reception", "Computer Science Department", "Dean of Academics"],
    "Parent visit": ["Main Gate", "Reception", "Computer Science Department"],
    "Hostel enquiry": ["Main Gate", "Hostel Office", "Boys' Hostel", "Girls' Hostel"],
    "Main Gate → Director's Office": ["Main Gate", "Reception", "Director's Office"],
    "Main Gate → T&P Department": ["Main Gate", "Training & Placement (T&P) Department"],
    "Main Gate → Computer Science Department": ["Main Gate", "Computer Science Department"],
    "Main Gate → Cafeteria": ["Main Gate", "Cafeteria"],
    "Main Gate → Girls' Hostel": ["Main Gate", "Girls' Hostel"],
    "Main Gate → Auditorium": ["Main Gate", "Auditorium"],
}
VISITOR_JOURNEYS = {
    "New admission": ("Admission Cell → Document Verification → Fee Office", "New admission visitor"),
    "Placement enquiry": ("T&P Department → Placement Coordinator", "Placement enquiry"),
    "Academic enquiry": ("Relevant Department → Dean's Office", "Academic enquiry"),
    "Parent visit": ("Reception → Concerned Department", "Parent visit"),
    "Hostel enquiry": ("Hostel Office → Hostel Location", "Hostel enquiry"),
}


def render_route(route_name):
    stops = [loc_by_name(n) for n in ROUTES[route_name]]
    stops = [s for s in stops if s is not None]
    if len(stops) < 2:
        st.warning("Route stops not found.")
        return
    left, right = st.columns([1, 1.4])
    with left:
        total = 0
        for i, s in enumerate(stops):
            leg = ""
            if i > 0:
                dd = haversine(stops[i - 1]["lat"], stops[i - 1]["lng"], s["lat"], s["lng"])
                total += dd
                leg = f" · ~{int(dd)} m {compass(stops[i-1]['lat'], stops[i-1]['lng'], s['lat'], s['lng'])} from previous"
            st.markdown(f"**{i+1}. {s['name']}**{leg}  \n{s['description']}  \n_{s['building']} · {s['floor']} floor_")
        st.caption(f"Approx. total straight-line distance: {int(total)} m")
        st.link_button("🧭 Open full route in Google Maps", gmaps_dir(stops[-1], stops[0], stops[1:-1]), use_container_width=True)
    with right:
        make_map(pd.DataFrame(stops), highlight=stops[-1], start=stops[0], path=[[s["lat"], s["lng"]] for s in stops])


# ------------------------------------------------------------------ CHAT ASSISTANT
STOP = set("where is the a an to how can i do does what who which of for in on at me my find reach get go tell about please are there it be and or "
           "location locate office handles handle handled need want should".split())


def tokens(text):
    return {t for t in re.findall(r"[a-z0-9&]+", text.lower()) if t not in STOP}


def best_location(q):
    qt = tokens(q)
    if not qt:
        return None, 0
    best, bs = None, 0
    for _, r in locations().iterrows():
        kt = tokens(r["name"] + " " + r["keywords"])
        score = len(qt & kt)
        for t in qt - kt:
            if len(t) > 3 and difflib.get_close_matches(t, list(kt), n=1, cutoff=0.82):
                score += 0.6
        if r["name"].lower() in q.lower():
            score += 3
        if score > bs:
            best, bs = r, score
    return (best, bs) if bs >= 1 else (None, 0)


def answer(q):
    ql = q.lower()
    if re.search(r"appointment|meeting|meet |book", ql):
        return "You can request a meeting from the **Book Appointment** page: choose the person, purpose, date and time. You will get a reference ID to track or cancel the request. The admin approves or rejects it.", None
    if re.search(r"hello|hi$|hey|namaste", ql):
        return "Hello! Ask me about any office, department, hostel, library, cafeteria and more.", None
    if re.search(r"faculty|professor|dr\.|who handles|who is|incharge|in-charge|coordinator", ql):
        qt = tokens(q)
        fdf = qdf("SELECT * FROM faculty")
        sc = []
        for _, f in fdf.iterrows():
            ft = tokens(" ".join([f["name"], f["designation"], f["department"], f["responsibilities"]]))
            sc.append((len(qt & ft), f))
        sc.sort(key=lambda x: -x[0])
        if sc and sc[0][0] >= 1:
            f = sc[0][1]
            loc = loc_by_name(f["location_name"])
            return (f"**{f['name']}** ({f['designation']}, {f['department']}) - Cabin {f['cabin']}, timings {f['timings']}. "
                    f"Handles: {f['responsibilities']}. _{DEMO_NOTE}_"), loc
    loc, _ = best_location(q)
    if loc is not None:
        extra = f" Timings: {loc['timings']}." if loc["timings"] not in ("-", "") else ""
        return (f"**{loc['name']}** is in **{loc['building']}**, {loc['floor']} floor. {loc['description']}{extra}"), loc
    return ("Sorry, I couldn't match that to a campus location. Try names like *Admission Cell*, *Library*, *Girls' hostel* or *Computer Science*.", None)


# ------------------------------------------------------------------ PAGES
def page_home():
    u = current_user()
    hr = (datetime.utcnow() + timedelta(hours=5, minutes=30)).hour
    greet = "Good morning" if hr < 12 else "Good afternoon" if hr < 17 else "Good evening"
    who = f", {html.escape(u['name'].split()[0])}" if u else ""
    st.markdown(
        f"""<div class="hero"><span class="chip"><span class="live"></span> Smart Campus · Farah, Mathura</span>
        <h1>{greet}{who} 👋</h1><h2>Welcome to HCST</h2>
        <p>Find your destination anywhere on campus. Where do you want to go?</p></div>""",
        unsafe_allow_html=True)
    nx = qdf("SELECT * FROM events WHERE event_date>=? ORDER BY event_date LIMIT 1", (date.today().isoformat(),))
    if len(nx):
        e = nx.iloc[0]
        st.markdown(f'<div class="ticker">📣 <b>Next up:</b> {html.escape(e["title"])} · {e["event_date"]} · 📍 {html.escape(e["location_name"])}</div>',
                    unsafe_allow_html=True)
    locs = locations()
    q = st.text_input("🔍 Search offices, departments, hostels, facilities", placeholder="e.g. admission, library, girls hostel, T&P")
    if q:
        qt = tokens(q)
        hits = []
        for _, r in locs.iterrows():
            kt = tokens(r["name"] + " " + r["keywords"] + " " + r["category"])
            s = len(qt & kt) + (2 if q.lower() in r["name"].lower() else 0)
            for t in qt - kt:
                if len(t) > 3 and difflib.get_close_matches(t, list(kt), n=1, cutoff=0.82):
                    s += 0.5
            if s > 0:
                hits.append((s, r["id"], r["name"]))
        hits.sort(key=lambda x: -x[0])
        if hits:
            choice = st.radio("Matches", [h[2] for h in hits[:6]], horizontal=True)
            st.session_state["dest"] = int(locs[locs["name"] == choice]["id"].iloc[0])
        else:
            st.warning("No match found. Try another keyword.")
    st.markdown("**Popular destinations**")
    pop = ["Admission Cell", "Training & Placement (T&P) Department", "PDP Department", "Dean of Academics", "Director's Office",
           "Computer Science Department", "Boys' Hostel", "Girls' Hostel", "Cafeteria", "Sports Ground", "Library"]
    cols = st.columns(4)
    for i, n in enumerate(pop):
        r = locs[locs["name"] == n]
        if len(r) and cols[i % 4].button(n.replace(" (T&P)", ""), key=f"pop_{i}", use_container_width=True):
            st.session_state["dest"] = int(r["id"].iloc[0])
    st.divider()
    did = st.session_state.get("dest")
    if did:
        r = locs[locs["id"] == did]
        if len(r):
            destination_panel(r.iloc[0], "home")
    else:
        nloc = len(locs)
        nfac = int(qdf("SELECT COUNT(*) AS n FROM faculty").iloc[0]["n"])
        nev = int(qdf("SELECT COUNT(*) AS n FROM events WHERE event_date>=?", (date.today().isoformat(),)).iloc[0]["n"])
        st.markdown(
            f"""<div class="stats"><div class="stat"><b>{nloc}</b><span>Campus locations</span></div>
            <div class="stat"><b>{nfac}</b><span>Faculty & staff (demo)</span></div>
            <div class="stat"><b>{nev}</b><span>Upcoming events</span></div>
            <div class="stat"><b>{len(ROUTES)}</b><span>Guided routes</span></div></div>""",
            unsafe_allow_html=True)
        qa = st.columns(4)
        for col, (label, pg) in zip(qa, [("🧭 Visitor help", "Visitor Help Centre"), ("📅 Book a meeting", "Book Appointment"),
                                          ("💬 Ask HCST", "Ask HCST"), ("🛣️ Smart routes", "Smart Routes")]):
            col.button(label, key="qa_" + pg, on_click=goto, args=(pg,), use_container_width=True)
        st.subheader("📍 HCST on Google Maps")
        components.html(
            f'<iframe src="https://www.google.com/maps?q={quote_plus(COLLEGE_QUERY)}&output=embed" width="100%" height="420" '
            f'style="border:0;border-radius:12px" loading="lazy"></iframe>', height=430)
        st.link_button("Open HCST in Google Maps", "https://www.google.com/maps/search/?api=1&query=" + quote_plus(COLLEGE_QUERY))


def page_navigate():
    st.header("🗺️ Campus Map & Navigation")
    locs = locations()
    cats = ["All"] + sorted(locs["category"].unique())
    c1, c2 = st.columns(2)
    cat = c1.selectbox("Category", cats)
    sub = locs if cat == "All" else locs[locs["category"] == cat]
    dest_name = c2.selectbox("Destination", sub["name"])
    dest = sub[sub["name"] == dest_name].iloc[0]
    destination_panel(dest, "nav")
    with st.expander("All locations (table)"):
        st.dataframe(locs[["name", "category", "building", "floor", "timings", "verified"]], use_container_width=True, hide_index=True)


def page_faculty():
    st.header("👩‍🏫 Faculty & Department Connect")
    st.markdown(f'<span class="demo">All faculty names, photographs, contact details and availability are fictional demonstration data.</span>',
                unsafe_allow_html=True)
    fdf = qdf("SELECT * FROM faculty ORDER BY department, name")
    dept = st.selectbox("Department / Office", ["All"] + sorted(fdf["department"].unique()))
    if dept != "All":
        fdf = fdf[fdf["department"] == dept]
    cols = st.columns(2)
    for i, (_, f) in enumerate(fdf.iterrows()):
        with cols[i % 2].container(border=True):
            st.markdown(f"### 👤 {f['name']}")
            st.caption(f"Sample Faculty · {f['department']}")
            st.write(f"**Designation:** {f['designation']}  \n**Cabin:** {f['cabin']}  \n**Office timings (sample):** {f['timings']}  \n"
                     f"**Responsibilities:** {f['responsibilities']}")
            st.write(f"📧 {f['email']}  \n📞 {f['phone']}")
            b1, b2 = st.columns(2)
            b1.button("Request appointment", key=f"ap_{f['id']}", on_click=book_with, args=(f["id"],), use_container_width=True)
            loc = loc_by_name(f["location_name"])
            if loc is not None:
                b2.link_button("Navigate", gmaps_dir(loc), use_container_width=True)


def slots_for(fid, d):
    base = ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]
    taken = qdf("SELECT appt_time FROM appointments WHERE faculty_id=? AND appt_date=? AND status IN ('Pending','Approved')", (int(fid), d.isoformat()))
    return [s for s in base if s not in set(taken["appt_time"])]


def my_appointments_ui(u, prefix):
    mine = qdf("SELECT a.*, f.name AS fname FROM appointments a JOIN faculty f ON f.id=a.faculty_id WHERE a.user_id=? ORDER BY a.id DESC",
               (int(u["id"]),))
    if not len(mine):
        st.info("You have no meeting requests yet.")
        return
    for _, a in mine.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            badge = {"Pending": "🟡", "Approved": "🟢", "Rejected": "🔴", "Cancelled": "⚪"}.get(a["status"], "⚪")
            c1.markdown(f"**APT-{int(a['id']):05d}** · {a['fname']}  \n📅 {a['appt_date']} {a['appt_time']} · {a['purpose']}  \n{badge} **{a['status']}**")
            if a["status"] in ("Pending", "Approved") and c2.button("Cancel", key=f"{prefix}_c_{int(a['id'])}"):
                run("UPDATE appointments SET status='Cancelled' WHERE id=?", (int(a["id"]),))
                st.toast("Request cancelled", icon="✅")
                st.rerun()


def page_appointment():
    st.header("📅 Meeting & Appointment Booking")
    st.caption("Sample booking interface. " + DEMO_NOTE)
    if not login_required("Please log in or sign up to request a meeting. Browsing the rest of the site needs no account."):
        return
    u = current_user()
    fdf = qdf("SELECT * FROM faculty ORDER BY name")
    labels = {int(r["id"]): f"{r['name']} - {r['designation']}" for _, r in fdf.iterrows()}
    ids = list(labels)
    pre = st.session_state.get("prefill_fid")
    idx = ids.index(pre) if pre in ids else 0
    tab1, tab2 = st.tabs(["Request a meeting", "My requests / track by ID"])
    with tab1:
        fid = st.selectbox("Who would you like to meet?", ids, index=idx, format_func=lambda i: labels[i])
        c1, c2 = st.columns(2)
        purpose = c1.selectbox("Purpose of meeting", ["Admission enquiry", "Academic enquiry", "Placement enquiry", "Hostel enquiry", "Fee enquiry", "Other"])
        d = c2.date_input("Preferred date", min_value=date.today() + timedelta(days=1), value=date.today() + timedelta(days=1))
        if d.weekday() == 6:
            st.warning("Sundays are not available (sample rule). Choose another date.")
            slots = []
        else:
            slots = slots_for(fid, d)
        t = st.selectbox("Preferred time (available sample slots)", slots if slots else ["No slots available"])
        with st.form("appt_form", clear_on_submit=True):
            name = st.text_input("Your name *", value=u["name"])
            phone = st.text_input("Phone *", value=u.get("phone") or "")
            email = st.text_input("Email", value=u["email"])
            details = st.text_area("Additional details")
            ok = st.form_submit_button("Submit meeting request", type="primary")
        if ok:
            if not name.strip() or not phone.strip():
                st.error("Name and phone are required.")
            elif not slots:
                st.error("Please pick a date with an available slot.")
            elif not re.fullmatch(r"[0-9+\-\s]{7,15}", phone.strip()):
                st.error("Enter a valid phone number.")
            else:
                aid = run("INSERT INTO appointments(name,phone,email,faculty_id,purpose,details,appt_date,appt_time,created,user_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
                          (name.strip(), phone.strip(), email.strip(), int(fid), purpose, details.strip(), d.isoformat(), t,
                           datetime.now().isoformat(timespec="seconds"), int(u["id"])))
                st.success(f"Request submitted! Your reference ID is **APT-{aid:05d}**. Status: Pending approval.")
                st.toast("Meeting request sent", icon="📅")
    with tab2:
        st.markdown("#### Your requests")
        my_appointments_ui(u, "appt")
        with st.expander("Track a request by reference ID"):
            ref = st.text_input("Reference ID (e.g. APT-00001)")
            ph = st.text_input("Phone used while booking")
            if st.button("Check status"):
                m = re.search(r"(\d+)", ref)
                if m:
                    r = qdf("SELECT a.*, f.name AS fname FROM appointments a JOIN faculty f ON f.id=a.faculty_id WHERE a.id=? AND a.phone=?", (int(m.group(1)), ph.strip()))
                    if len(r):
                        a = r.iloc[0]
                        st.info(f"**APT-{int(a['id']):05d}** · {a['fname']} · {a['appt_date']} {a['appt_time']} · {a['purpose']}  \nStatus: **{a['status']}**")
                    else:
                        st.error("No matching request found.")


def page_account():
    st.header("👤 My Account")
    u = current_user()
    if u:
        with st.container(border=True):
            st.markdown(f"### {html.escape(u['name'])}")
            st.write(f"📧 {u['email']}  \n📞 {u.get('phone') or '-'}  \n🏷️ {u['role']}")
            if st.button("Logout", key="logout_main"):
                st.session_state["user"] = None
                st.toast("Logged out", icon="👋")
                st.rerun()
        t1, t2, t3 = st.tabs(["My meeting requests", "My lost & found reports", "Change password"])
        with t1:
            my_appointments_ui(u, "acct")
        with t2:
            df = qdf("SELECT id,kind,item,description,status,created FROM lost_found WHERE user_id=? ORDER BY id DESC", (int(u["id"]),))
            if len(df):
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("You have not submitted any reports.")
        with t3:
            with st.form("chpw", clear_on_submit=True):
                old = st.text_input("Current password", type="password")
                new = st.text_input("New password (min 8 characters)", type="password")
                ok = st.form_submit_button("Update password", type="primary")
            if ok:
                row = qdf("SELECT * FROM users WHERE id=?", (int(u["id"]),)).iloc[0]
                if not hmac.compare_digest(hash_pw(old, row["salt"])[1], row["pw_hash"]):
                    st.error("Current password is incorrect.")
                elif len(new) < 8:
                    st.error("New password must be at least 8 characters.")
                else:
                    salt, h = hash_pw(new)
                    run("UPDATE users SET salt=?, pw_hash=? WHERE id=?", (salt, h, int(u["id"])))
                    st.success("Password updated.")
        return

    st.write("Create an account to book meetings and report lost & found items. Browsing the campus guide needs no account.")
    tl, ts = st.tabs(["Login", "Sign up"])
    with tl:
        with st.form("login_form"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            ok = st.form_submit_button("Login", type="primary")
        if ok:
            if st.session_state.get("fails", 0) >= 5:
                st.error("Too many failed attempts. Please refresh the page and try again later.")
            else:
                r = qdf("SELECT * FROM users WHERE email=?", (email.strip().lower(),))
                if len(r) and hmac.compare_digest(hash_pw(pw, r.iloc[0]["salt"])[1], r.iloc[0]["pw_hash"]):
                    x = r.iloc[0]
                    st.session_state["user"] = {"id": int(x["id"]), "name": x["name"], "email": x["email"], "phone": x["phone"], "role": x["role"]}
                    st.session_state["fails"] = 0
                    st.toast(f"Welcome back, {x['name'].split()[0]}!", icon="👋")
                    st.rerun()
                else:
                    st.session_state["fails"] = st.session_state.get("fails", 0) + 1
                    st.error("Incorrect email or password.")
    with ts:
        with st.form("signup_form", clear_on_submit=False):
            name = st.text_input("Full name *")
            c1, c2 = st.columns(2)
            email = c1.text_input("Email *", key="su_email")
            phone = c2.text_input("Phone")
            role = st.selectbox("I am a…", ["New student / candidate", "Current student", "Parent", "Visitor", "Alumni"])
            p1 = st.text_input("Password * (min 8 characters)", type="password", key="su_p1")
            p2 = st.text_input("Confirm password *", type="password", key="su_p2")
            ok = st.form_submit_button("Create account", type="primary")
        if ok:
            em = email.strip().lower()
            if not name.strip() or not em:
                st.error("Name and email are required.")
            elif not EMAIL_RE.match(em):
                st.error("Enter a valid email address.")
            elif phone.strip() and not re.fullmatch(r"[0-9+\-\s]{7,15}", phone.strip()):
                st.error("Enter a valid phone number.")
            elif len(p1) < 8:
                st.error("Password must be at least 8 characters.")
            elif p1 != p2:
                st.error("Passwords do not match.")
            else:
                salt, h = hash_pw(p1)
                try:
                    uid = run("INSERT INTO users(name,email,phone,role,salt,pw_hash,created) VALUES(?,?,?,?,?,?,?)",
                              (name.strip(), em, phone.strip(), role, salt, h, datetime.now().isoformat(timespec="seconds")))
                    st.session_state["user"] = {"id": int(uid), "name": name.strip(), "email": em, "phone": phone.strip(), "role": role}
                    st.toast("Account created. Welcome to HCST!", icon="🎉")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("An account with this email already exists. Please log in.")


def page_visitor():
    st.header("🧭 Visitor Help Centre")
    st.write("Not sure where to begin? Choose your purpose to get a guided journey. Journeys use the campus locations in our directory.")
    st.table(pd.DataFrame([(k, v[0]) for k, v in VISITOR_JOURNEYS.items()], columns=["Visitor purpose", "Suggested journey"]))
    p = st.selectbox("I am here for…", list(VISITOR_JOURNEYS))
    render_route(VISITOR_JOURNEYS[p][1])
    with st.expander("Common questions"):
        st.markdown("- **Where to begin admission?** Admission Cell.\n- **Document verification?** Document Verification Office.\n"
                    "- **Pay admission fees?** Fee Office.\n- **Hostel facilities?** Hostel Office.\n- **Submit forms?** Admission Cell / Reception.")


def page_chat():
    st.header("💬 Ask HCST - Campus Chat Assistant")
    st.caption("Answers come from the campus database (keyword matching, no external AI). Try: *Where is the Admission Cell?*")
    if "chat" not in st.session_state:
        st.session_state["chat"] = [("assistant", "Hi! I'm the HCST campus assistant. Ask me where something is or who handles what.", None)]
    for role, txt, loc in st.session_state["chat"]:
        with st.chat_message(role):
            st.markdown(txt)
            if loc is not None:
                st.link_button("🧭 Directions", gmaps_dir(loc), key=f"d_{id(txt)}_{loc['name']}")
    q = st.chat_input("Ask a question about the campus…")
    if q:
        st.session_state["chat"].append(("user", q, None))
        a, loc = answer(q)
        st.session_state["chat"].append(("assistant", a, loc))
        st.rerun()
    st.markdown("**Sample questions**")
    for s in ["Where is the Admission Cell?", "Where is the girls' hostel?", "Who handles placement-related queries?",
              "Where can I find the Dean of Academics?", "How can I request a meeting with a faculty member?"]:
        if st.button(s, key="sq_" + s):
            a, loc = answer(s)
            st.session_state["chat"] += [("user", s, None), ("assistant", a, loc)]
            st.rerun()


def page_facilities():
    st.header("🏫 Campus Facilities")
    locs = locations()
    f = locs[locs["category"].isin(["Campus Facility", "Hostel"])]
    for _, r in f.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{r['name']}** - {r['building']} ({r['floor']} floor)  \n{r['description']}  \n⏰ {r['timings']}")
            c2.link_button("Directions", gmaps_dir(r), use_container_width=True)


def page_events():
    st.header("📢 Events & Notices")
    st.caption("Sample events for demonstration.")
    ev = qdf("SELECT * FROM events ORDER BY event_date")
    cat = st.multiselect("Filter", sorted(ev["category"].unique()))
    if cat:
        ev = ev[ev["category"].isin(cat)]
    for _, e in ev.iterrows():
        with st.container(border=True):
            st.markdown(f"**{e['title']}** · _{e['category']}_  \n📅 {e['event_date']} {e['event_time']} · 📍 {e['location_name']}  \n{e['description']}")
            loc = loc_by_name(e["location_name"])
            if loc is not None:
                st.link_button("Navigate to Event", gmaps_dir(loc), key=f"ev_{e['id']}")


def page_lost():
    st.header("🎒 Lost & Found")
    u = current_user()
    tab1, tab2, tab3 = st.tabs(["Report", "Browse items", "Claim an item"])
    with tab1:
        if login_required("Please log in or sign up to submit a lost / found report."):
            with st.form("lf", clear_on_submit=True):
                kind = st.radio("I want to report a…", ["Lost item", "Found item"], horizontal=True)
                item = st.selectbox("Item type", ["ID card", "Book", "Water bottle", "Bag", "Other"])
                desc = st.text_area("Description *")
                where = st.text_input("Where (lost / found)?")
                who = st.text_input("Your name *", value=u["name"] if u else "")
                contact = st.text_input("Contact (phone/email) *", value=(u.get("phone") or u["email"]) if u else "")
                ok = st.form_submit_button("Submit report", type="primary")
            if ok:
                if not (desc.strip() and who.strip() and contact.strip()):
                    st.error("Please fill all required fields.")
                else:
                    run("INSERT INTO lost_found(kind,item,description,where_text,reporter,contact,created,user_id) VALUES(?,?,?,?,?,?,?,?)",
                        (kind, item, desc.strip(), where.strip(), who.strip(), contact.strip(), datetime.now().isoformat(timespec="seconds"),
                         int(u["id"]) if u else None))
                    st.success("Report submitted. The admin will coordinate.")
                    st.toast("Report submitted", icon="🎒")
    with tab2:
        df = qdf("SELECT id,kind,item,description,where_text,status,created FROM lost_found ORDER BY id DESC")
        if len(df):
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No reports yet.")
    with tab3:
        if login_required("Please log in or sign up to claim an item."):
            open_df = qdf("SELECT id,item,description FROM lost_found WHERE status='Open' AND kind='Found item'")
            if not len(open_df):
                st.info("No found items available to claim.")
            else:
                sel = st.selectbox("Found item", open_df["id"], format_func=lambda i: f"#{i} · {open_df[open_df['id']==i]['item'].iloc[0]} - {open_df[open_df['id']==i]['description'].iloc[0][:50]}")
                cl = st.text_input("Your name", value=u["name"] if u else "", key="cl_n")
                note = st.text_area("Proof / details to verify ownership", key="cl_d")
                if st.button("Submit claim", type="primary"):
                    if cl.strip() and note.strip():
                        run("UPDATE lost_found SET status='Claim pending', claimant=?, claim_note=? WHERE id=?", (cl.strip(), note.strip(), int(sel)))
                        st.success("Claim submitted. Admin will verify and coordinate return.")
                    else:
                        st.error("Name and details are required.")


def page_routes():
    st.header("🛣️ Smart Campus Routes")
    st.write("Predefined journeys with step-by-step stops, indicative distances and a Google Maps link.")
    r = st.selectbox("Choose a route", list(ROUTES))
    render_route(r)


def admin_password():
    try:
        return st.secrets.get("ADMIN_PASSWORD", "admin123")
    except Exception:
        return "admin123"


def page_admin():
    st.header("🔐 Admin")
    if not st.session_state.get("admin"):
        pw = st.text_input("Admin password", type="password")
        if st.button("Login"):
            if pw == admin_password():
                st.session_state["admin"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        return
    if st.button("Logout"):
        st.session_state["admin"] = False
        st.rerun()
    t1, t2, t3, t4, t5 = st.tabs(["Appointments", "Lost & Found", "Locations", "Events", "Users"])
    with t1:
        df = qdf("SELECT a.id,a.name,a.phone,f.name AS meet,a.purpose,a.appt_date,a.appt_time,a.status FROM appointments a JOIN faculty f ON f.id=a.faculty_id ORDER BY a.id DESC")
        st.dataframe(df, use_container_width=True, hide_index=True)
        if len(df):
            c1, c2, c3 = st.columns(3)
            aid = c1.selectbox("Request ID", df["id"], key="adm_aid")
            ns = c2.selectbox("Set status", ["Approved", "Rejected", "Pending", "Cancelled"])
            if c3.button("Update status"):
                run("UPDATE appointments SET status=? WHERE id=?", (ns, int(aid)))
                st.rerun()
    with t2:
        df = qdf("SELECT * FROM lost_found ORDER BY id DESC")
        st.dataframe(df, use_container_width=True, hide_index=True)
        if len(df):
            c1, c2, c3 = st.columns(3)
            lid = c1.selectbox("Item ID", df["id"], key="adm_lid")
            ns = c2.selectbox("Set status", ["Open", "Claim pending", "Returned", "Closed"], key="adm_ls")
            if c3.button("Update item"):
                run("UPDATE lost_found SET status=? WHERE id=?", (ns, int(lid)))
                st.rerun()
    with t3:
        st.caption("Edit coordinates by right-clicking the exact spot in Google Maps and copying 'lat, lng'. Tick 'verified' once checked. "
                   "Note: edits live in the app database; on Streamlit Cloud this resets on reboot - also update LOC_SEED in app.py to keep them permanently.")
        df = qdf("SELECT id,name,category,building,floor,lat,lng,timings,verified FROM locations ORDER BY name")
        df["verified"] = df["verified"].astype(bool)
        ed = st.data_editor(df, use_container_width=True, hide_index=True, disabled=["id"], key="loc_ed")
        if st.button("Save location changes"):
            for _, r in ed.iterrows():
                run("UPDATE locations SET name=?,category=?,building=?,floor=?,lat=?,lng=?,timings=?,verified=? WHERE id=?",
                    (r["name"], r["category"], r["building"], r["floor"], float(r["lat"]), float(r["lng"]), r["timings"], int(bool(r["verified"])), int(r["id"])))
            st.success("Saved.")
        with st.form("newloc", clear_on_submit=True):
            st.markdown("**Add a new location**")
            n = st.text_input("Name")
            cat = st.selectbox("Category", ["Academic & Administrative", "Campus Facility", "Hostel", "Entry"])
            b = st.text_input("Building")
            fl = st.text_input("Floor", "Ground")
            la = st.number_input("Latitude", value=C_LAT, format="%.6f")
            lo = st.number_input("Longitude", value=C_LNG, format="%.6f")
            ds = st.text_area("Description")
            kw = st.text_input("Search keywords")
            if st.form_submit_button("Add") and n.strip():
                try:
                    run("INSERT INTO locations(name,category,building,floor,lat,lng,description,timings,keywords,verified) VALUES(?,?,?,?,?,?,?,?,?,0)",
                        (n.strip(), cat, b, fl, la, lo, ds, "To be verified", kw))
                    st.success("Added.")
                except sqlite3.IntegrityError:
                    st.error("A location with this name exists.")
    with t4:
        with st.form("newev", clear_on_submit=True):
            title = st.text_input("Title")
            cat = st.selectbox("Category", ["Placement", "Seminar", "Cultural", "Sports", "Notice", "Orientation"])
            d = st.date_input("Date")
            tm = st.text_input("Time", "10:00")
            ln = st.selectbox("Location", list(locations()["name"]))
            ds = st.text_area("Description")
            if st.form_submit_button("Add event") and title.strip():
                run("INSERT INTO events(title,category,event_date,event_time,location_name,description) VALUES(?,?,?,?,?,?)",
                    (title.strip(), cat, d.isoformat(), tm, ln, ds))
                st.success("Event added.")
        ev = qdf("SELECT * FROM events ORDER BY event_date")
        st.dataframe(ev, use_container_width=True, hide_index=True)
        if len(ev):
            eid = st.selectbox("Delete event ID", ev["id"])
            if st.button("Delete event"):
                run("DELETE FROM events WHERE id=?", (int(eid),))
                st.rerun()


    with t5:
        us = qdf("SELECT id,name,email,phone,role,created FROM users ORDER BY id DESC")
        st.dataframe(us, use_container_width=True, hide_index=True)
        if len(us):
            c1, c2 = st.columns(2)
            uid = c1.selectbox("User ID", us["id"], key="adm_uid")
            tmp = c2.text_input("Temporary new password (min 8 chars)", key="adm_tmp")
            b1, b2 = st.columns(2)
            if b1.button("Reset password"):
                if len(tmp) >= 8:
                    salt, h = hash_pw(tmp)
                    run("UPDATE users SET salt=?, pw_hash=? WHERE id=?", (salt, h, int(uid)))
                    st.success("Password reset. Share the temporary password with the user.")
                else:
                    st.error("Use at least 8 characters.")
            if b2.button("Delete user"):
                run("DELETE FROM users WHERE id=?", (int(uid),))
                st.rerun()


# ------------------------------------------------------------------ ROUTER
PAGES = {
    "Home": page_home,
    "Campus Map & Navigate": page_navigate,
    "Smart Routes": page_routes,
    "Visitor Help Centre": page_visitor,
    "Ask HCST": page_chat,
    "Account": page_account,
    "Faculty Directory": page_faculty,
    "Book Appointment": page_appointment,
    "Facilities": page_facilities,
    "Events & Notices": page_events,
    "Lost & Found": page_lost,
    "Admin": page_admin,
}
ICONS = {"Home": "🏠", "Campus Map & Navigate": "🗺️", "Smart Routes": "🛣️", "Visitor Help Centre": "🧭", "Ask HCST": "💬",
         "Account": "👤", "Faculty Directory": "👩‍🏫", "Book Appointment": "📅", "Facilities": "🏫", "Events & Notices": "📢",
         "Lost & Found": "🎒", "Admin": "🔐"}
st.sidebar.markdown('<div class="brand">🎓 HCST<br><span>Smart Campus Guide</span></div>', unsafe_allow_html=True)
_u = current_user()
if _u:
    st.sidebar.markdown(f'<div class="userchip">👋 Hi, <b>{html.escape(_u["name"].split()[0])}</b><br><span style="opacity:.7">{html.escape(_u["role"])}</span></div>',
                        unsafe_allow_html=True)
    if st.sidebar.button("Logout", key="logout_side"):
        st.session_state["user"] = None
        st.rerun()
else:
    st.sidebar.button("🔑 Login / Sign up", key="login_side", on_click=goto, args=("Account",), use_container_width=True)
if "page" not in st.session_state:
    st.session_state["page"] = "Home"
st.sidebar.radio("Go to", list(PAGES), key="page", format_func=lambda k: f"{ICONS.get(k, '•')}  {k}")
st.sidebar.caption("Faculty names and contacts are synthetic demo data. Marker positions are approximate until verified.")
PAGES[st.session_state["page"]]()
