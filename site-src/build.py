#!/usr/bin/env python3
"""Victor Tai personal site generator.
Edit CONFIG, run `python3 build.py`. Outputs:
  ../victortai-site/   deployable static site (EN at /, ZH at /zh/)
  ../preview/index.html  single-file preview (all pages, hash-routed)
"""
import base64
import json, os, shutil, html
from urllib.parse import quote
import hashlib
ASSET_V=hashlib.md5(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'site.css'),'rb').read()+open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'calc.js'),'rb').read()).hexdigest()[:8]

# ---------- CONFIG: replace the TODO values, then rebuild ----------
CONFIG = dict(
    domain="https://victortai.my",   # TODO confirm after buying the domain
    ren="REN 26739",
    zh_name="戴燊通",
    photo="assets/victor.jpg",          # from Drive "_profile_Victor_Tai.jpg" (19 Nov 2026)
    phone_display="+6017-775 7229",
    wa="https://wa.me/60177757229",
    ig="https://www.instagram.com/victor_lin_dao/",
    socials=[   # (name, handle shown, url or None if still needed)
        ("Facebook", "Victor Tai", "https://www.facebook.com/share/1Xb4AGVCfv/"),
        ("Facebook Page", "Victor 淋岛", "https://www.facebook.com/200843523787654"),
        ("Instagram", "@victor_lin_dao", "https://www.instagram.com/victor_lin_dao/"),
        ("TikTok", "@victortai92", "https://www.tiktok.com/@victortai92"),
        ("YouTube", "@VictorLinDao92", "https://www.youtube.com/@VictorLinDao92"),
        ("Xiaohongshu", "小红书", "https://xhslink.cn/m/2DWDDkfRTQM"),
        ("Douyin", "抖音", "https://www.douyin.com/user/MS4wLjABAAAAfKpoUUaOoF7L4MM144zqRURAXpMu5CcbGpF7_7wQWyM"),
    ],
    # featured videos: Facebook reel id (personal profile), title, note. Cover image: assets/v/fb-<id>.jpg
    videos=[
        ("1872628807039008", "Rental income tax: 6 costs landlords can deduct", "606K views"),
        ("1824036028830003", "Two US moves in one week: is Johor's data centre boom in trouble?", "151K views"),
        ("1727335951849033", "RTS opens in 2027: RM9 billion of spending heads to JB", "398K views"),
        ("1121776210641222", "Ten years ago I audited factories in Pasir Gudang. Now I sell them", ""),
        ("29161843470163428", "A landlord lost RM45K waiting for a better rent", ""),
        ("1169916672199384", "Shop or factory not renting? Try this", ""),
        ("1082917634795487", "The JB industrial area nobody wanted is now selling", ""),
        ("1863496624679278", "90,000 sqft warehouse for rent in Pasir Gudang", ""),
    ],
    updated="2026-11-22",
    fb_followers="17K",   # Facebook personal profile followers, synced from facebook.com/singthong.victortai
    stats_date="22 Nov 2026",
    listings=[   # Victor's own C&I listings from the Listing Hub (19 Nov 2026). Add Hub-selected ones here.
        dict(kind="ind", deal="For sale or rent", area="Ulu Tiram", title="Corner cluster factory, Taman Perindustrian Tropika",
             size="Land approx. 10,000 sqft · Built-up approx. 6,300 sqft · Medium industrial · 100 A · Freehold",
             price="RM3.98M · or RM18,000/mo"),
        dict(kind="ind", deal="For sale or rent", area="Desa Cemerlang", title="Semi-D factory, adjoining unit available",
             size="Land approx. 9,000 sqft · Built-up approx. 5,000 sqft · Light industrial · Freehold",
             price="RM3.38M · or RM16,800/mo"),
        dict(kind="ind", deal="For sale, tenanted", area="Eco Business Park 1", title="Renovated cluster factory, Phase 2",
             size="Land 9,000 sqft · Built-up 5,259 sqft · Light industrial · 150 A · Tenant paying RM12,000/mo",
             price="RM3.3M"),
        dict(kind="com", deal="For rent", area="Southkey", title="Ground floor shop, Mosaic Block F",
             size="1,690 sqft · Basement parking · Partly furnished", price="RM8,800/mo"),
        dict(kind="com", deal="For rent", area="Taman Molek", title="3-storey shoplot, Jalan Molek 3/20",
             size="26' × 95' · Ground floor RM5,800 · First floor RM2,500", price="From RM2,500/mo"),
        dict(kind="com", deal="For rent", area="Southkey", title="Office, Mosaic Block F, Level 2",
             size="1,690 sqft · Lift · Basement parking · Fully furnished", price="RM3,900/mo"),
    ],
    reviews=[],    # (quote, "Name, business") from real clients only.
    entity="Victor Tai (Tai Sing Thong, REN 26739) is a Johor Bahru real estate negotiator and Associate Leader at The Roof Realty (TRR), focusing on commercial and industrial property: shoplots, factories and warehouses. A former external auditor at Big 4 firm Ernst &amp; Young (EY), he explains property through numbers (rent, tax, loan and yield) and matches businesses to the space they actually need. He has been a TRR Multi Million Agent every year since 2023. He is founder of The Worthy Group, which produces over RM10 million in sales commission a year. He shares JB property content on Facebook, Instagram, Xiaohongshu, TikTok, Douyin and YouTube.",
)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site")
PREV = os.path.join(HERE, "..", "preview")

MEDIA = {}   # output rel path -> (source path, max width)
def media(c, src, rel, width, q=78):
    """Image URL: data: URI in the single-file preview, a resized file on the real site."""
    if c.preview:
        from PIL import Image; import io
        im = Image.open(src).convert("RGB"); im.thumbnail((width, width * 2))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=min(q, 70), optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    MEDIA[rel] = (src, width, q)
    return "/" + rel

def unit_photos(u):
    """Photos for a unit: site-src/photos/<hub id>/ (exported from the Listing Hub). Order from listings.json, else file name."""
    for hid_ in u.get("hub_ids") or [u["id"]]:
        d = os.path.join(HERE, "photos", hid_)
        if os.path.isdir(d):
            files = [f for f in sorted(os.listdir(d)) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
            order = [f for f in (u.get("photos") or []) if f in files]
            files = order + [f for f in files if f not in order]
            if files: return [(os.path.join(d, f), f"media/units/{u['slug']}/{i+1}.jpg") for i, f in enumerate(files)]
    return []

def todo(label):
    return f'<mark class="todo">{label}</mark>'

def REN(lang):
    return CONFIG["ren"] or todo("REN 号码" if lang == "zh" else "REN number")

def ZHNAME(lang):
    return CONFIG["zh_name"] or todo("中文名" if lang == "zh" else "Chinese name")

LANGS = ["en"]   # English only. Add "zh" to bring back the Chinese pages at /zh/.
PAGES = ["home", "space", "tool", "about", "join"]
PATHS = {"home": "/", "space": "/find-factory-warehouse-johor-bahru/", "tool": "/tools/vacancy-cost/",
         "about": "/about/", "join": "/join/"}

def wa(msg):
    return CONFIG["wa"] + "?text=" + quote(msg)

def hid(page):
    return page.replace(":", "-")

def real_url(lang, page):
    return ("/zh" if lang == "zh" else "") + PATHS[page]

class Ctx:
    def __init__(self, lang, preview):
        self.lang, self.preview = lang, preview
    def url(self, page, lang=None):
        lang = lang or self.lang
        return f"#{lang}-{hid(page)}" if self.preview else real_url(lang, page)
    def t(self, en, zh):
        return zh if self.lang == "zh" else en

# ---------- shared chrome ----------
def header(c, page):
    nav = [("units", "Units"), ("space", "Find space"), ("tool", "For landlords"), ("about", "About"), ("join", "Join the team")]
    navwa = f'<a class="navbtn" href="{wa("Hi Victor, I found you through your website.")}">Ask VT</a>'
    cur = ' aria-current="page"'
    links = "".join(
        f'<a href="{c.url(p)}"{cur if p == page else ""}>{label}</a>' for p, label in nav)
    other = "en" if c.lang == "zh" else "zh"
    return f'''<header class="top">
  <a class="brand" href="{c.url("home")}">Victor Tai</a>
  <nav aria-label="{c.t("Main", "主导航")}">{links}</nav>
  {navwa}
  {f'<a class="lang" href="{c.url(page, other)}">{"English" if other == "en" else "中文"}</a>' if len(LANGS) > 1 else ""}
</header>'''

def footer(c):
    return f'''<footer class="foot">
  <p><strong>Victor Tai (Tai Sing Thong)</strong> · {REN(c.lang)} · The Roof Realty · Johor Bahru, Malaysia</p>
  <p>WhatsApp <a href="{CONFIG["wa"]}" rel="me">{CONFIG["phone_display"]}</a></p>
  <p class="socials">{" · ".join(f'<a href="{u}" rel="me">{n}</a>' for n, h, u in CONFIG["socials"] if u)}</p>
  <p class="small">{c.t("Figures on this site are for general reference. Confirm tax and loan matters with your tax agent and banker.",
                         "本站数字仅供参考。税务和贷款细节请向你的 tax agent 和银行确认。")} {c.t("Last updated", "最后更新")} {CONFIG["updated"]}.</p>
</footer>
<a class="wa-float" href="{wa("Hi Victor, I found you through your website.")}">WhatsApp Victor</a>'''

def reads(c):
    items = "".join(f'<li><a href="/guides/{s}/"><strong>{html.escape(t)}</strong><span>{html.escape(d.split(", by Victor")[0])}</span></a></li>'
                    for s, t, d, dt, fn in sorted(GUIDES, key=lambda g: g[3], reverse=True))
    return f'''<section id="read">
  <p class="eyebrow">Read</p>
  <h2>Notes for owners.</h2>
  <p class="rsub">The ideas from my videos, written out properly.</p>
  <ul class="reads">{items}</ul>
</section>'''

def cta(c, text_en, text_zh, msg="Hi Victor, I found you through your website."):
    return f'''<p class="cta"><a class="btn" href="{wa(msg)}">{c.t(text_en, text_zh)}</a>
  <span class="num">{CONFIG["phone_display"]}</span></p>'''

def portrait(c):
    if CONFIG["photo"]:
        if c.preview:
            import base64
            src = "data:image/jpeg;base64," + base64.b64encode(open(os.path.join(HERE, CONFIG["photo"]), "rb").read()).decode()
        else:
            src = "/" + CONFIG["photo"]
        return f'<img class="portrait" src="{src}" alt="Victor Tai (Tai Sing Thong)" width="320" height="400">'
    return f'<div class="portrait ph">{todo(c.t("Portrait photo", "正式照片"))}</div>'

# ---------- pages ----------
AREAS_COM = [
    ("JB City / Southkey", "City centre", "Close to the Causeway and the city centre"),
    ("Mount Austin / Tebrau", "Northeast JB", "Busy shop rows near Tebrau"),
    ("Taman Molek / Johor Jaya", "East JB", "Established shopping streets in east JB"),
    ("Permas Jaya", "East JB", "East of the city, facing Singapore"),
    ("Eco Botanic / Medini", "Iskandar Puteri", "The growing west side of JB"),
    ("Skudai / Tun Aminah", "West JB", "Mature neighbourhoods along the Skudai Highway"),
]
AREAS_IND = [
    ("Tampoi / Tebrau", "JB city", "Close to Johor Bahru city centre"),
    ("Senai / Kulai", "Airport side", "Near Senai International Airport"),
    ("Pasir Gudang / Tanjung Langsat", "Port side", "Near Johor Port"),
    ("Iskandar Puteri / Gelang Patah", "Second Link", "Near the Second Link to Tuas, Singapore"),
    ("Tanjung Pelepas", "Port side", "Near the Port of Tanjung Pelepas"),
    ("Ulu Tiram / Desa Cemerlang", "East JB", "East of the city along Jalan Kota Tinggi"),
]
HOW_I_WORK = [
    ("“Professional advice.”", "Owners tell me my audit and banking background shows. When I give a view on price or rent, it comes with the numbers behind it."),
    ("“Young, hungry, proactive.”", "They say I move fast, follow up without being chased, and keep going until the deal is done."),
    ("“He gets what we need.”", "Clients tell me I take time to understand what the space has to do for their business before I show them anything."),
    ("“He showed me my blind spots.”", "Owners say I point out what they had not thought about, before it becomes expensive."),
    ("“Sharp with numbers.”", "They value that I read the market and work out rent, yield and vacancy cost instead of guessing."),
]

SERVICES = [
    ("Factory and warehouse rental", "Units shortlisted by power supply, floor loading, height and lorry access, with the full move-in cost laid out."),
    ("Buying factories and industrial land", "Price, loan, zoning and yield worked out before you commit."),
    ("Shoplots and offices", "Frontage, foot traffic, parking and what similar units nearby pay in rent."),
    ("Landlords: rent out or sell", "Pricing against nearby deals, and the numbers on accepting an offer or waiting."),
]

def listing_card(l):
    return (f'<article class="lcard" data-kind="{l["kind"]}"><div class="ltag">{l["deal"]} · {l["area"]}</div><h3>{l["title"]}</h3>'
            f'<p class="lspec">{l["size"]}</p><p class="lprice">{l["price"]}</p>'
            f'<a class="textlink" href="{wa("Hi Victor, I saw this on your website: " + l["title"] + ". Is it still available?")}">Ask about this unit ›</a></article>')

def home(c):
    stats = [("RM10M+", "sales commission a year", "The Worthy Group, founded by Victor"),
             ("Since 2023", "TRR Multi Million Agent", "every year"),
             ("Big 4", "former external auditor", "Ernst &amp; Young (EY)"),
             ("6", "platforms", "Facebook, Instagram, XHS, TikTok, Douyin, YouTube")]
    stats_html = "".join(f'<div class="stat"><b>{n}</b><span>{a}</span><small>{b}</small></div>' for n, a, b in stats)
    def tiles(rows, what):
        return "".join(
            f'<a class="area" href="{wa(f"Hi Victor, I found you through your website. I am looking for {what} in {n}.")}">'
            f'<span class="eyebrow">{tag}</span><h3>{n}</h3><p>{d}</p><span class="go">See units here ›</span></a>'
            for n, tag, d in rows)
    areas_com = tiles(AREAS_COM, "a shop or office")
    areas_ind = tiles(AREAS_IND, "a factory or warehouse")
    listings = f'''<section id="listings">
  <h2>Latest units.</h2>
  <div class="seg" role="group" aria-label="Filter units"><button type="button" data-f="all" aria-pressed="true">All</button><button type="button" data-f="com" aria-pressed="false">Commercial</button><button type="button" data-f="ind" aria-pressed="false">Industrial</button></div>
  <div class="lgrid">{"".join(unit_card(c, u) for u in UNITS[:9])}</div>
  <p class="cta"><a class="textlink" href="{c.url("units")}">See all {len(UNITS)} units ›</a></p>
</section>'''
    area_links = [(sl, a) for sl, a in sorted(AREAS.items(), key=lambda x: -len(x[1]["units"])) if area_key(sl)]
    by_area = ""
    if len(area_links) >= 3:   # appears on its own once there are 3+ area pages
        tiles_html = "".join(f'<a class="area" href="{c.url(area_key(sl))}"><span class="eyebrow">{len(a["units"])} units</span><h3>{a["name"]}</h3><span class="go">See units ›</span></a>' for sl, a in area_links[:6])
        by_area = f'<section><h2>Browse by area.</h2><div class="areas">{tiles_html}</div></section>'
    follow = "".join(
        f'<a class="soc" href="{u}" rel="me"><b>{n}</b><span>{h}</span></a>' if u else
        (f'<span class="soc"><b>{n}</b><span>{todo("link needed")}</span></span>' if c.preview else "")
        for n, h, u in CONFIG["socials"])
    vids = "".join(
        f'<a class="vcard" href="https://www.facebook.com/reel/{vid}/"{"" if c.preview else f" data-fb={chr(34)}{vid}{chr(34)}"}>'
        f'<div class="vframe"><img src="{media(c, os.path.join(HERE, "assets", "v", f"fb-{vid}.jpg"), f"media/v/fb-{vid}.jpg", 360)}" alt="" loading="lazy"><i class="play" aria-hidden="true"></i></div>'
        f'<span>{t}</span><small>Facebook{" · " + note if note else ""}</small></a>'
        for vid, t, note in CONFIG["videos"])
    if not vids and c.preview:
        vids = f'<div class="vcard ph">{todo("Featured videos go here")}<span>3 to 6 of your best videos, e.g. the rental tax video and the tenant interviews. Send the links.</span></div>'
    videos = f'''<section id="watch">
  <h2>Watch and follow.</h2>
  <p class="lead center2">Property in Johor Bahru, explained with real numbers. In Mandarin, with #Victor淋岛.</p>
  {f'<div class="vgrid">{vids}</div>' if vids else ""}
  <div class="socgrid">{follow}</div>
</section>'''
    svc_html = "".join(f"<article><h3>{h}</h3><p>{p}</p></article>" for h, p in SERVICES)
    how_html = "".join(f"<article><h3>{h}</h3><p>{p}</p></article>" for h, p in HOW_I_WORK)
    if CONFIG["reviews"]:
        rev = "".join(f'<figure class="review"><blockquote>{q}</blockquote><figcaption>{who}</figcaption></figure>' for q, who in CONFIG["reviews"])
        reviews = f'<section><h2>What clients say.</h2><div class="reviews">{rev}</div></section>'
    elif c.preview:
        reviews = f'<section><h2>What clients say.</h2><div class="reviews"><figure class="review"><blockquote>{todo("Real client reviews go here")}</blockquote><figcaption>2 to 4 reviews in the client\'s own words, with their business type. Hidden until Victor provides them.</figcaption></figure></div></section>'
    else:
        reviews = ""
    return f'''<section class="hero solo herome">
  <div class="hm-text">
    <p class="eyebrow">Victor Tai · Property agent and creator · Johor Bahru</p>
    <h1>Shops, offices, factories and warehouses in Johor Bahru.</h1>
    <p class="lead">Commercial and industrial property to rent or buy, worked out in numbers by a former Big 4 auditor, and put on video in front of thousands of followers.</p>
    <p class="cta"><a class="btn" href="{c.url("units")}">Browse units</a><a class="textlink" href="{wa("Hi Victor, I found you through your website.")}">WhatsApp Victor ›</a></p>
    <p class="trust">{REN(c.lang)} · The Roof Realty</p>
  </div>
  <figure class="hm-photo"><img src="{media(c, os.path.join(HERE, "assets", "victor-hero.jpg"), "media/victor-hero.jpg", 800, 84)}" alt="Victor Tai, commercial and industrial property agent in Johor Bahru" fetchpriority="high"></figure>
</section>
{listings}
<section class="dark">
  <p class="eyebrow light">Not just another listing</p>
  <h2>An agent with an audience.</h2>
  <p class="lead center">Most agents post a listing and wait. I put property on video, in front of business owners, landlords and investors who already follow my numbers on six platforms.</p>
  <div class="cstats">
    <div><b>600K</b><span>views on one video, on rental tax deductions</span></div>
    <div><b>300K+</b><span>Facebook views in 28 days</span></div>
    <div><b>{CONFIG["fb_followers"]}</b><span>Facebook followers</span></div>
    <div><b>6</b><span>platforms, in Mandarin and English</span></div>
  </div>
  <p class="cta"><a class="btn" href="{wa("Hi Victor, I found you through your website. I would like to list my unit with you.")}">List your unit with Victor</a></p>
  <p class="note light">Facebook figures from Victor's profile and Creator Dashboard, updated {CONFIG["stats_date"]}.</p>
</section>
{videos}
{reads(c)}
{by_area}
<section>
  <div class="stats">{stats_html}</div>
</section>
<section>
  <h2>How I can help.</h2>
  <div class="cols two">{svc_html}</div>
  <p class="cta"><a class="textlink" href="{c.url("space")}">Send your requirement ›</a><a class="textlink" href="{c.url("tool")}">Landlord calculator ›</a></p>
</section>
{reviews}
<section>
  <div class="split">
    <div class="portrait"><img src="{media(c, os.path.join(HERE, "assets", "victor-stage.jpg"), "media/victor-stage.jpg", 800, 84)}" alt="Victor Tai speaking on stage at a sales training" loading="lazy"></div>
    <div>
      <p class="eyebrow">About Victor</p>
      <h2 class="left">The person behind the numbers.</h2>
      <p>{CONFIG["entity"]}</p>
      <p><a class="textlink" href="{c.url("about")}">More about Victor ›</a></p>
    </div>
  </div>
</section>
<section class="dark">
  <h2>Let's talk.</h2>
  <p class="lead center">Tell me the space you need, or the unit you want to let. I reply on WhatsApp.</p>
  <p class="cta"><a class="btn" href="{wa("Hi Victor, I found you through your website.")}">WhatsApp Victor</a><span class="phone">{CONFIG["phone_display"]}</span></p>
</section>'''

def space(c):
    checks = [
        ("Power supply", "List the machines and their load first. A unit with too little supply means an upgrade application, and that costs both money and weeks."),
        ("Floor loading", "Racking, heavy machines and stacked pallets all put weight on the slab. Ask what the floor was designed to carry."),
        ("Clear height", "Height decides how many racking levels fit and whether an overhead crane is possible."),
        ("Loading and access", "Check the loading bay, the door size, and whether a 40-foot container can turn into the compound."),
        ("Zoning and licence", "The industrial category of the land has to match your activity. Confirm with the local council before signing."),
        ("Location", "Measure the drive to your customers, suppliers, workers, the ports and the two road links to Singapore."),
    ]
    checks_html = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in checks)
    opt = lambda xs: "".join(f"<option>{x}</option>" for x in xs)
    return f'''<section class="hero solo">
  <div>
    <p class="eyebrow">For business owners</p>
    <h1>Find a shop, office, factory or warehouse in Johor Bahru that fits how your business runs</h1>
    <p class="lead">A cheap unit that cannot power your machines or take your lorries is an expensive mistake. Tell me what the operation needs and I will shortlist units that fit, with the full cost of each laid out side by side.</p>
    <p class="trust">Victor Tai (Tai Sing Thong) · {REN(c.lang)} · The Roof Realty</p>
  </div>
</section>
<section class="brief">
  <form class="panel" id="brief-form" autocomplete="off">
    <div class="grp">Your requirement</div>
    <div class="row wide"><label for="brief-type">Property type</label>
      <select id="brief-type">{opt(["Shoplot", "Office", "Factory", "Warehouse", "Industrial land", "Commercial land"])}</select></div>
    <div class="row wide"><label for="brief-deal">Rent or buy</label>
      <select id="brief-deal">{opt(["Rent", "Buy", "Either"])}</select></div>
    <div class="row wide"><label for="brief-area">Preferred area</label>
      <input id="brief-area" type="text" placeholder="e.g. Tampoi, Senai, Pasir Gudang"></div>
    <div class="row wide"><label for="brief-size">Size needed</label>
      <input id="brief-size" type="text" placeholder="e.g. 10,000 sq ft built-up"></div>
    <div class="row wide"><label for="brief-note">Business and special needs <span class="opt">optional</span></label>
      <input id="brief-note" type="text" placeholder="e.g. food processing, 200A, container access"></div>
    <a class="btn block" id="brief-send" href="{wa("Hi Victor, I found you through your website. I am looking for a commercial or industrial property in Johor Bahru.")}">Send on WhatsApp</a>
    <p class="hint">Opens WhatsApp with your requirement written out. Nothing is stored on this site. Or message {CONFIG["phone_display"]} directly.</p>
  </form>
  <div class="results">
    <h2 class="plain">What happens next</h2>
    <ol class="steps">
      <li>You send the requirement. Four lines are enough to start.</li>
      <li>I reply with units that fit, and for each one the rent or price, deposits and the likely set-up cost.</li>
      <li>We view the short list together, then negotiate terms on the one that works.</li>
    </ol>
  </div>
</section>
<section>
  <h2>Six things to check before you sign for a factory or warehouse</h2>
  <dl class="ledger">{checks_html}</dl>
</section>
<section>
  <h2>Compare the full cost, not only the rent</h2>
  <p>Two units with the same monthly rent can cost very different amounts to occupy. Before choosing, add up the rent, the security and utility deposits, stamp duty on the tenancy, renovation and power upgrades, and the cost of reinstating the unit when you leave. I put these in one table for every unit on your short list.</p>
  <p class="byline">By Victor Tai (Tai Sing Thong), {REN(c.lang)}, The Roof Realty · Updated {CONFIG["updated"]}</p>
</section>'''

def about(c):
    return f'''<section class="hero">
  <div>
    <p class="eyebrow">{c.t("About", "关于")}</p>
    <h1>{c.t("An accountant's way of looking at shoplots and factories", "用会计的方法看店铺和厂房")}</h1>
    <p class="lead">{c.t(
      "I am Victor Tai (Tai Sing Thong), a real estate negotiator and Associate Leader at The Roof Realty in Johor Bahru. Before property I was an external auditor at Big 4 firm Ernst &amp; Young (EY), which is why every conversation with me starts with a calculation.",
      "我是 Victor Tai（Tai Sing Thong），新山 The Roof Realty 的房地产中介。我念会计，进这行之前在 EY 做 auditor，所以跟我谈产业，都是从一条算式开始。")}</p>
  </div>
  {portrait(c)}
</section>
<section>
  <h2>{c.t("Background", "背景")}</h2>
  <dl class="ledger">
    <div><dt>{c.t("Full name", "全名")}</dt><dd>Victor Tai (Tai Sing Thong) · {ZHNAME(c.lang)}</dd></div>
    <div><dt>{c.t("Registration", "注册号码")}</dt><dd>{REN(c.lang)}</dd></div>
    <div><dt>Agency</dt><dd>The Roof Realty (TRR), Associate Leader</dd></div>
    <div><dt>Education</dt><dd>Degree in accounting</dd></div>
    <div><dt>Before property</dt><dd>External auditor, Ernst &amp; Young (EY), a Big 4 firm</dd></div>
    <div><dt>Track record</dt><dd>TRR Multi Million Agent (MMA) every year since 2023</dd></div>
    <div><dt>The Worthy Group</dt><dd>Founder. A TRR sales team producing over RM10 million in sales commission a year</dd></div>
    <div><dt>Content</dt><dd>JB property content on Facebook, Instagram, Xiaohongshu, TikTok, Douyin and YouTube</dd></div>
  </dl>
</section>
<section>
  <h2>{c.t("What I focus on", "我专注什么")}</h2>
  <p>{c.t(
    "My work is moving toward commercial and industrial property in Johor Bahru: shoplots, factories and warehouses. A factory is chosen by what the business needs to run, so I start with the operation and work back to the building.",
    "我的重心正在转向新山的商业和工业产业：店铺、厂房、货仓。厂房是按生意运作的需要来选的，所以我先了解你的生意，再回头找建筑。")}</p>
  <p>{c.t(
    "Completed commercial and industrial deals will be added to this site as short case notes: property type, area, size and the problem solved, without client names.",
    "每完成一单商业或工业成交，我会在这个网站加一条 case：类型、区域、面积、解决了什么问题，不写客户名字。")}</p>
</section>
<section>
  <h2>#Victor淋岛</h2>
  <p>{c.t(
    "I publish videos in Mandarin on Facebook, Instagram, Xiaohongshu, TikTok, Douyin and YouTube under the tag #Victor淋岛. Two things run through them: street interviews where shop tenants and landlords speak for themselves, and number topics such as tax, loans and rent versus buy. A video on which rental expenses are tax-deductible reached about 500,000 views.",
    "我用 #Victor淋岛 发中文视频，有两条主线：让店家租客和业主自己讲话的街访，还有税、贷款、租还是买这类数字题。讲出租开销扣税的那一支，大约有 50 万 views。")}</p>
  <p><a href="{CONFIG["ig"]}" rel="me">Instagram @victor_lin_dao</a></p>
</section>
<section>
  <h2>{c.t("Contact", "联络")}</h2>
  {cta(c, "WhatsApp Victor", "WhatsApp 联络 Victor")}
</section>'''

def join(c):
    systems = [
        (c.t("Shared Listing Hub", "共享 Listing Hub"),
         c.t("One team database of listings and buyer requirements, with matching between the two. A new agent starts with inventory to work on.",
             "全队共用的 listing 和买家需求资料库，两边自动配对。新人一进来就有货可以做。")),
        (c.t("Team dashboard", "团队 Dashboard"),
         c.t("Activity and results are tracked in one place, so coaching is based on your numbers.",
             "活动量和成绩都在同一个地方追踪，辅导是看你的数字来做的。")),
        (c.t("Commercial and industrial learning route", "C&amp;I 学习路线"),
         c.t("We learn shoplots, factories and warehouses together and turn what we learn into training material.",
             "店铺、厂房、货仓我们一起学，学到的整理成 training material。")),
        (c.t("AI in daily work", "把 AI 用在日常工作"),
         c.t("Internal workshops on using AI for listings, follow-up and content.",
             "内部工作坊教你用 AI 做 listing、follow-up 和内容。")),
    ]
    sys_html = "".join(f"<article><h3>{h}</h3><p>{p}</p></article>" for h, p in systems)
    fit = [c.t("You want to be measured by numbers and coached on them.", "愿意被数字衡量，也愿意按数字被辅导。"),
           c.t("You are ready to follow a system before inventing your own.", "愿意先跟系统做，再发展自己的做法。"),
           c.t("You want to learn commercial and industrial, beyond residential.", "除了住宅，也想学商业和工业。")]
    nofit = [c.t("You are looking for a fixed monthly salary. Agency work is commission-based.", "想要固定月薪。中介是 commission 制。"),
             c.t("You prefer to work without reporting or accountability.", "不想汇报，不想被问责。"),
             c.t("You expect leads to be handed over without doing your own prospecting.", "只等公司派 lead，自己不开发客源。")]
    li = lambda xs: "".join(f"<li>{x}</li>" for x in xs)
    return f'''<section class="hero solo">
  <div>
    <p class="eyebrow">{c.t("Join The Worthy Group", "加入 The Worthy Group")}</p>
    <h1>{c.t("A property sales team in Johor Bahru that runs on systems", "新山一个靠系统做事的房地产销售团队")}</h1>
    <p class="lead">{c.t(
      "The Worthy Group (TWG) is a sales team within The Roof Realty in Johor Bahru, founded by Victor Tai (Tai Sing Thong), and produces over RM10 million in sales commission a year. What sets it apart is how well the team's systems support each agent.",
      "The Worthy Group（TWG）是新山 The Roof Realty 旗下的销售团队，由 Victor Tai（Tai Sing Thong）联合创办。我们不比人数，比的是系统能给每个 agent 多少支持。")}</p>
  </div>
</section>
<section>
  <h2>{c.t("What the team gives you", "团队给你什么")}</h2>
  <div class="cols two">{sys_html}</div>
</section>
<section>
  <h2>{c.t("High support, high accountability", "高支持，高问责")}</h2>
  <p>{c.t("The structure is simple: Victor works with leaders, leaders work with agents. Support and accountability come together. You get help, and you are asked about your numbers.",
          "结构很简单：Victor 带 leaders，leaders 带 agents。支持和问责是一起来的：有人帮你，也有人问你的数字。")}</p>
  <div class="pair">
    <article class="card good"><h3>{c.t("This suits you if", "适合你，如果")}</h3><ul>{li(fit)}</ul></article>
    <article class="card bad"><h3>{c.t("This does not suit you if", "不适合你，如果")}</h3><ul>{li(nofit)}</ul></article>
  </div>
</section>
<section>
  <h2>{c.t("How to apply", "怎么申请")}</h2>
  <ol class="steps">
    <li>{c.t("WhatsApp Victor with a short introduction: what you do now and why property.", "WhatsApp Victor，简单介绍自己：现在做什么，为什么想做房地产。")}</li>
    <li>{c.t("We meet for a coffee chat. You ask anything, and we both decide if it fits.", "约出来喝杯咖啡聊。你有什么都可以问，双方看适不适合。")}</li>
    <li>{c.t("New to the industry? Registration as a Real Estate Negotiator (REN) is done through the agency.", "新人入行？Real Estate Negotiator（REN）的注册是通过公司办理的。")}</li>
  </ol>
  {cta(c, "WhatsApp Victor about joining", "WhatsApp Victor 了解加入")}
</section>'''

def tool(c):
    p = c.lang
    f = lambda i, label, val, pre="", suf="": (
        f'<div class="row"><label for="{p}-{i}">{label}</label><div class="field">'
        f'{f"<span>{pre}</span>" if pre else ""}<input id="{p}-{i}" inputmode="decimal" value="{val}">'
        f'{f"<span>{suf}</span>" if suf else ""}</div></div>')
    mth = c.t("mth", "月")
    mk = [(1, c.t("Hot", "热门"), c.t("1 month vacant", "空 1 个月"), c.t("Tenants competing", "很多人抢着租")),
          (3, c.t("Moderate", "一般"), c.t("3 months vacant", "空 3 个月"), c.t("A few other units", "还有几间可选")),
          (6, c.t("Weak", "差"), c.t("6 months vacant", "空 6 个月"), c.t("Many units competing", "很多单位竞争")),
          (12, c.t("Very weak", "极差"), c.t("12 months vacant", "空 12 个月"), c.t("Almost no tenants", "几乎没人租"))]
    mk_html = "".join(
        f'<label><input type="radio" name="{p}-mkt" id="{p}-m{m}" value="{m}"{" checked" if m == 3 else ""}>'
        f'<span class="t">{t}</span><span class="m">{d}</span><span class="d">{e}</span><span class="badge" id="{p}-b{m}"></span></label>'
        for m, t, d, e in mk)
    return f'''<section class="hero solo">
  <div>
    <p class="eyebrow">{c.t("Tool for landlords", "业主工具")}</p>
    <h1>{c.t("Should you accept this tenant offer?", "这个 Tenant Offer，接还是不接？")}</h1>
    <p class="lead">{c.t(
      "Waiting for a higher rent costs you the months the unit sits empty. This calculator compares taking the offer now with waiting for your expected rent over the same period. The figures shown are samples. Replace them with your own unit.",
      "等更高的租金，代价是空置的那几个月。这个计算器用同样的时间长度，比较现在接 offer 和等期望租金，哪个净收入更高。里面是示例数字，换成你自己的单位。")}</p>
  </div>
</section>
<section class="calc" data-calc="{p}">
  <form class="panel" id="{p}-form" autocomplete="off">
    <div class="grp">{c.t("Rental", "租金")}</div>
    {f("offer", c.t("Tenant offer", "租客出价"), 1900, "RM")}
    {f("expect", c.t("Expected rental", "期望租金"), 2200, "RM")}
    {f("freeO", c.t("Free renovation period requested", "租客要求的免租装修期"), 0.5, "", mth)}
    <div class="grp">{c.t("Market for your expected rent", "期望租金的行情")}</div>
    <p class="hint">{c.t("At your expected rent, how long until it gets rented?", "按期望租金，现在要空多久才租得出？")}</p>
    <div class="mkt">{mk_html}</div>
    <div class="grp">{c.t("Costs", "成本")}</div>
    {f("inst", c.t("Monthly instalment", "每月供期"), 2100, "RM")}
    <div class="hint" id="{p}-intHint"></div>
    {f("fee", c.t("Agent fee (months of rent)", "中介费（几个月租金）"), 1, "", mth)}
    {f("sst", c.t("Service tax on agent fee", "中介费的 SST"), 8, "", "%")}
    {f("term", c.t("Tenancy term", "租约"), 12, "", mth)}
  </form>
  <div class="results">
    <div class="verdict" id="{p}-verdict"><div class="big" id="{p}-vBig"></div><p id="{p}-vSub"></p></div>
    <div class="panel">
      <div class="cost"><span>{c.t("Instalment you pay while vacant", "再空下去，你自己掏的供期")}</span><b class="neg" id="{p}-cCash"></b></div>
      <div class="cost"><span>{c.t("Of which interest (money lost for good)", "其中利息（真正烧掉的钱）")}</span><b class="neg" id="{p}-cInt"></b></div>
    </div>
    <div class="panel"><div class="scroll"><table id="{p}-tbl"></table></div><p class="note" id="{p}-tNote"></p></div>
    <button type="button" id="{p}-copyBtn"></button>
    <textarea id="{p}-copyOut" readonly aria-hidden="true" tabindex="-1"></textarea>
  </div>
</section>
<section>
  <h2>{c.t("How the comparison works", "这个比较怎么算")}</h2>
  <p>{c.t(
    "Both options are measured over the same window: the waiting time plus one tenancy term. If you accept, the tenant moves in now and is assumed to renew at the same rent. If you wait, the unit earns nothing until the tenant at your expected rent arrives. Agent fee and service tax are deducted on both sides. Your instalment is paid either way, so it is left out of the comparison and shown separately. Interest is estimated at 70% of the instalment.",
    "两边用同样的时间长度来比：等待的时间加一个租约期。接 offer，租客现在就入住，假设到期后用同样租金续租。等的话，期望租金的租客出现之前，单位没有收入。两边都扣中介费和 SST。供期两边都要付，所以不放进比较，另外列出来。利息以供期的 70% 估算。")}</p>
  <p>{c.t("New to this? Read the guide first:", "")} <a href="/guides/vacancy-cost-shop-factory-johor-bahru/">How much does an empty shop or factory really cost in Johor Bahru?</a></p>
  <p class="byline">{c.t("By", "作者")} Victor Tai (Tai Sing Thong), {REN(c.lang)}, The Roof Realty · {c.t("Updated", "更新")} {CONFIG["updated"]}</p>
</section>
<section>
  <h2>Want a second pair of eyes on your numbers?</h2>
  <p>Send me the unit, the offer and your asking rent. I will check the calculation against what similar units nearby are fetching.</p>
  {cta(c, "Send Victor your unit", "", "Hi Victor, I used the vacancy cost calculator on your website. Can you check my numbers? My unit is at: ")}
</section>'''

BUILDERS = dict(home=home, space=space, about=about, join=join, tool=tool)
META = {
    ("en", "home"): ("Shops, Offices, Factories & Warehouses in Johor Bahru | Victor Tai (REN 26739)",
                     "Victor Tai (Tai Sing Thong, REN 26739), Associate Leader at The Roof Realty in Johor Bahru, focusing on shoplots, factories and warehouses. Former EY external auditor."),
    ("zh", "home"): ("Victor Tai（Tai Sing Thong）｜新山店铺、厂房、货仓房地产中介",
                     "Victor Tai（Tai Sing Thong），新山 The Roof Realty 房地产中介，专注店铺、厂房和货仓，用租金、税、贷款、回报这些数字讲房地产。"),
    ("en", "space"): ("Find a Factory, Warehouse or Shoplot in Johor Bahru | Victor Tai",
                      "Looking for a factory, warehouse or shoplot to rent or buy in Johor Bahru? Send your requirement to Victor Tai (Tai Sing Thong) of The Roof Realty, plus six things to check before you sign."),
    ("en", "about"): ("About Victor Tai (Tai Sing Thong) | The Roof Realty, Johor Bahru",
                      "Victor Tai (Tai Sing Thong), REN 26739: former EY external auditor, TRR Associate Leader, Multi Million Agent every year since 2023, founder of The Worthy Group."),
    ("zh", "about"): ("关于 Victor Tai（Tai Sing Thong）｜新山 The Roof Realty",
                      "Victor Tai（Tai Sing Thong）的背景：会计系毕业，前 EY auditor，TRR Multi Million Agent 2025，The Worthy Group 联合创办人。"),
    ("en", "join"): ("Join The Worthy Group | Property Agent Team in Johor Bahru",
                     "The Worthy Group, founded by Victor Tai, is a TRR sales team in Johor Bahru producing over RM10 million in sales commission a year, built on a shared Listing Hub, a team dashboard and a C&I learning route."),
    ("zh", "join"): ("加入 The Worthy Group｜新山房地产中介团队",
                     "The Worthy Group 是新山 The Roof Realty 旗下的销售团队：共享 Listing Hub、团队 dashboard、C&I 学习路线，高支持高问责。"),
    ("en", "tool"): ("Vacancy Cost Calculator: Accept the Tenant Offer or Wait? | Victor Tai",
                     "Free calculator for landlords in Malaysia: compare accepting a tenant's offer now with waiting for your expected rent, after vacancy, agent fee and service tax."),
    ("zh", "tool"): ("空置成本计算器：Tenant Offer 接还是不接？｜Victor Tai",
                     "给业主的免费计算器：比较现在接租客的 offer 和等期望租金，扣掉空置、中介费和 SST 后哪个净收入更高。"),
}


# ---------- unit, area and index pages from data/listings.json ----------
import units as U
UNITS = U.load()
AREA_NOTES = {
    "eco-business-park-1": "Eco Business Park 1 sits between Dato Onn and Kempas, with gated cluster, semi-D and detached factories, mostly light and medium industrial.",
    "southkey": "Southkey is a mixed commercial hub around Mid Valley Southkey, close to Johor Bahru city centre.",
    "desa-cemerlang": "Desa Cemerlang is an established industrial and commercial area in east Johor Bahru, along the route to Ulu Tiram.",
    "ulu-tiram": "Ulu Tiram lies east of Johor Bahru along Jalan Kota Tinggi, with industrial estates of larger land plots.",
    "taman-molek": "Taman Molek is a mature commercial and residential neighbourhood in east Johor Bahru.",
}
AREAS = {}
for u in UNITS:
    AREAS.setdefault(u["area_slug"], {"name": u["area"], "units": []})["units"].append(u)
AREA_PAGE_MIN = 2   # an area gets its own page once it has this many units

def area_key(slug):
    return "a:" + slug if len(AREAS[slug]["units"]) >= AREA_PAGE_MIN else None

def unit_card(c, u):
    ph = unit_photos(u)
    pic = (f'<div class="lpic"><img src="{media(c, ph[0][0], ph[0][1].replace(".jpg", "-card.jpg"), 720)}" alt="{u["category"]}, {u["estate"]}" loading="lazy"></div>' if ph
           else f'<div class="lpic none"><span>{"Factory" if u["kind"] == "ind" else "Shop · Office"}</span><small>Photos on request</small></div>')
    return (f'<a class="lcard" data-kind="{u["kind"]}" href="{c.url("u:" + u["slug"])}">{pic}<div class="ltag">{u["deal"].capitalize()} · {u["area"]}</div>'
            f'<h3>{u["category"]}, {u["estate"]}</h3><p class="lspec">{u["spec_line"]}</p><p class="lprice">{u["price_text"]}</p>'
            f'<span class="textlink">View unit ›</span></a>')

def unit_page(c, u):
    ask = wa(f'Hi Victor, I saw this unit on your website: {u["title"]} ({u["estate"]}). Is it still available?')
    rows = [("Deal", u["deal"].capitalize())]
    if u.get("sale"): rows.append(("Selling price", U.money(u["sale"])))
    if u.get("rent"): rows.append(("Monthly rent", u.get("rent_note") or f'{U.money(u["rent"])} per month'))
    if u.get("psf"): rows.append(("Rent per sqft", f'About RM{u["psf"]:.2f} psf on built-up (asking)'))
    if u.get("land_sqft"): rows.append(("Land", f'{u["land_sqft"]:,} sqft (approx.)'))
    elif u.get("land_text"): rows.append(("Land", u["land_text"]))
    if u.get("builtup_sqft"): rows.append(("Built-up", f'{u["builtup_sqft"]:,} sqft (approx.)'))
    for k, lab in (("industry", "Industrial category"), ("power", "Power supply"), ("tenure", "Tenure"), ("available", "Availability")):
        if u.get(k): rows.append((lab, u[k]))
    loc = u["estate"] if u["area"].lower() in u["estate"].lower() else f'{u["estate"]}, {u["area"]}'
    rows.append(("Location", f'{loc}, Johor Bahru, Johor'))
    ledger = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)
    ph = unit_photos(u)
    gallery = (f'<div class="gal"><div class="gstrip">' + "".join(
        f'<figure><img src="{media(c, src, rel, 1600)}" alt="{u["category"]}, {u["estate"]}, photo {i+1}" loading="{"eager" if i == 0 else "lazy"}"></figure>'
        for i, (src, rel) in enumerate(ph)) + f'</div><p class="gcount">{len(ph)} photo{"s" if len(ph) > 1 else ""} · swipe ›</p></div>') if ph else ""
    feats = "".join(f"<li>{f}</li>" for f in u.get("features", []))
    ak = area_key(u["area_slug"])
    others = [x for x in (AREAS[u["area_slug"]]["units"] if ak else UNITS) if x is not u][:3]
    more_t = f'More in {u["area"]}.' if ak else "Other units."
    more = f'<section><h2>{more_t}</h2><div class="lgrid">{"".join(unit_card(c, x) for x in others)}</div><p class="cta"><a class="textlink" href="{c.url(ak or "units")}">See all ›</a></p></section>' if others else ""
    return f'''<section class="hero solo">
  <p class="eyebrow">{u["area"]} · {u["kind"] == "ind" and "Industrial" or "Commercial"}</p>
  <h1>{u["category"]} {u["deal"]} in {u["area"]}, Johor Bahru</h1>
  <p class="lead">{u["estate"]}. {u["price_text"]}.</p>
  <p class="cta"><a class="btn" href="{ask}">Ask about this unit</a><a class="textlink" href="{c.url("units")}">All units ›</a></p>
  {gallery}
</section>
<section>
  <h2>Unit details.</h2>
  <dl class="ledger">{ledger}</dl>
  {f'<ul class="feats">{feats}</ul>' if feats else ""}
  <p class="byline">Listed by Victor Tai (Tai Sing Thong), {REN(c.lang)}, The Roof Realty · Listed {u["listed"]} · Ref {u["id"][-6:]}. Prices are asking prices and may change.</p>
</section>
{more}'''

def area_page(c, slug):
    a = AREAS[slug]; us = a["units"]
    psf = sorted(x["psf"] for x in us if x.get("psf"))
    psf_line = (f'<p>Asking rent of the units listed here: RM{psf[0]:.2f} to RM{psf[-1]:.2f} per sqft of built-up, per month.</p>' if len(psf) > 1
                else (f'<p>Asking rent of the unit listed here: about RM{psf[0]:.2f} per sqft of built-up, per month.</p>' if psf else ""))
    note = AREA_NOTES.get(slug, "")
    return f'''<section class="hero solo">
  <p class="eyebrow">Area guide</p>
  <h1>Property for sale and rent in {a["name"]}, Johor Bahru</h1>
  <p class="lead">{len(us)} unit{"s" if len(us) > 1 else ""} listed by Victor Tai in {a["name"]}. {note}</p>
</section>
<section>
  <div class="lgrid">{"".join(unit_card(c, x) for x in us)}</div>
  {psf_line}
  <p class="cta"><a class="textlink" href="{c.url("space")}">Not the right unit? Send your requirement ›</a></p>
</section>'''

def units_index(c):
    chips = "".join(f'<li><a href="{c.url(area_key(sl))}">{a["name"]} · {len(a["units"])}</a></li>' for sl, a in sorted(AREAS.items()) if area_key(sl))
    return f'''<section class="hero solo">
  <p class="eyebrow">Victor Tai · Johor Bahru</p>
  <h1>Shops, offices and factories for sale and rent.</h1>
  <p class="lead">{len(UNITS)} commercial and industrial units, updated from Victor's listings. Prices are asking prices.</p>
</section>
<section>
  <div class="seg" role="group" aria-label="Filter units"><button type="button" data-f="all" aria-pressed="true">All</button><button type="button" data-f="com" aria-pressed="false">Commercial</button><button type="button" data-f="ind" aria-pressed="false">Industrial</button></div>
  <div class="lgrid">{"".join(unit_card(c, u) for u in UNITS)}</div>
  {f'<h3 class="sub">By area</h3><ul class="chips">{chips}</ul>' if chips else ""}
</section>'''

PAGES.insert(1, "units"); PATHS["units"] = "/units/"; BUILDERS["units"] = units_index
META[("en", "units")] = ("Commercial & Industrial Property for Sale and Rent in Johor Bahru | Victor Tai",
                         f"{len(UNITS)} shops, offices, factories and warehouses for sale and rent in Johor Bahru, listed by Victor Tai (REN 26739), The Roof Realty.")
EXTRA_LD = {}
for u in UNITS:
    k = "u:" + u["slug"]; PAGES.append(k); PATHS[k] = f'/units/{u["slug"]}/'
    BUILDERS[k] = (lambda uu: (lambda c: unit_page(c, uu)))(u)
    META[("en", k)] = (f'{u["category"]} {u["deal"].capitalize()}, {u["area"]}, Johor Bahru · {u["price_text"]} | Victor Tai',
                       f'{u["category"]} {u["deal"]} at {u["estate"]}, {u["area"]}, Johor Bahru. {u["spec_line"]}. {u["price_text"]}. Contact Victor Tai, REN 26739.')
    offers = []
    if u.get("sale"): offers.append({"@type": "Offer", "price": u["sale"], "priceCurrency": "MYR", "businessFunction": "http://purl.org/goodrelations/v1#Sell"})
    if u.get("rent"): offers.append({"@type": "Offer", "price": u["rent"], "priceCurrency": "MYR", "businessFunction": "http://purl.org/goodrelations/v1#LeaseOut"})
    EXTRA_LD[k] = {"@context": "https://schema.org", "@type": "RealEstateListing", "name": META[("en", k)][0].split(" | ")[0],
                   "url": CONFIG["domain"] + PATHS[k], "datePosted": u["listed"], "offers": offers,
                   "contentLocation": {"@type": "Place", "name": f'{u["estate"]}, {u["area"]}, Johor Bahru'},
                   "author": {"@id": CONFIG["domain"] + "/#victor-tai"}}
    if unit_photos(u): EXTRA_LD[k]["image"] = [CONFIG["domain"] + "/" + rel for _, rel in unit_photos(u)]
for sl in AREAS:
    k = area_key(sl)
    if not k: continue
    PAGES.append(k); PATHS[k] = f"/area/{sl}/"
    BUILDERS[k] = (lambda ss: (lambda c: area_page(c, ss)))(sl)
    META[("en", k)] = (f'Property for Sale and Rent in {AREAS[sl]["name"]}, Johor Bahru | Victor Tai',
                       f'Commercial and industrial units for sale and rent in {AREAS[sl]["name"]}, Johor Bahru, with asking prices, listed by Victor Tai, REN 26739.')

# ---------- guides (question-led articles) ----------
GUIDES = []   # (slug, title, description, published, builder)

def guide_vacancy(c):
    by = f'Victor Tai (Tai Sing Thong), {REN(c.lang)}, The Roof Realty · Updated {CONFIG["updated"]}'
    ex = [("Tenant's offer", "RM5,000 a month"), ("Rent you hope for", "RM5,500 a month"),
          ("Difference", "RM500 a month"), ("Lease", "3 years (36 months)"),
          ("Extra income over the lease", "RM500 × 36 = RM18,000"),
          ("Break-even waiting time", "RM18,000 ÷ RM5,500 ≈ 3.3 months")]
    ledger = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in ex)
    return f'''<section class="hero solo">
  <p class="eyebrow">Guide for landlords</p>
  <h1>How much does an empty shop or factory really cost in Johor Bahru?</h1>
  <p class="lead">Every month a shop or factory sits empty, you lose the full month's rent plus your holding costs. If you turn down a tenant to wait for RM500 more a month on a 3-year lease, you only come out ahead if the better tenant arrives within about three months.</p>
  <p class="byline">By {by}</p>
</section>
<section>
  <h2>The mistake most landlords make.</h2>
  <p>Landlords compare two rents: the offer in hand and the rent they hope to get. They forget the third number, which is time.</p>
  <p>An empty unit earns nothing, but the costs keep running: loan interest, quit rent, assessment, service charges for stratified units, insurance and basic maintenance. An empty factory also starts to deteriorate.</p>
</section>
<section>
  <h2>A simple way to calculate it.</h2>
  <p><strong>Break-even waiting time (months) = (rent you hope for − rent offered) × lease months ÷ rent you hope for.</strong></p>
  <p>Example, a terrace factory:</p>
  <dl class="ledger">{ledger}</dl>
  <p>If the RM5,500 tenant takes longer than about 3.3 months to appear, accepting RM5,000 today would have earned you more. That is before holding costs, which make the real break-even shorter still.</p>
  <p class="note">These figures illustrate the method. They are not market rents. Use your own numbers.</p>
</section>
<section>
  <h2>What changes the answer.</h2>
  <ul class="steps">
    <li><strong>Lease length.</strong> A longer lease makes a higher rent worth more, so you can afford to wait a little longer. A one-year lease rarely justifies waiting.</li>
    <li><strong>How fast your type of unit rents out.</strong> A ground-floor shop on a busy road may rent in weeks. A large detached factory in a quieter industrial area can take many months. Ask an agent who handles that area what recent vacancy times have been.</li>
    <li><strong>Free renovation period.</strong> Commercial and industrial tenants often ask for one to three months rent-free to fit out. Count it as a cost in the comparison.</li>
    <li><strong>Tenant quality.</strong> A tenant who pays on time for three years is worth more than one who pays RM300 more and leaves after a year.</li>
  </ul>
</section>
<section>
  <h2>When holding out makes sense.</h2>
  <ol class="steps">
    <li>Your asking rent is supported by recent deals for similar units nearby, not just by listings.</li>
    <li>The unit type is in short supply in that area.</li>
    <li>You can carry the holding costs without strain.</li>
  </ol>
  <p>If none of these is true, the offer in hand is usually the better deal.</p>
</section>
<section>
  <h2>Run your own numbers.</h2>
  <p>The free <a href="{c.url("tool")}">vacancy cost calculator</a> runs this comparison for you, including free renovation months, agent fee and service tax.</p>
  {cta(c, "Send Victor your unit and the offer", "", "Hi Victor, I read your guide on vacancy cost. I have a tenant offer for my unit and want a second opinion. My unit is at: ")}
</section>'''

GUIDES.append(("vacancy-cost-shop-factory-johor-bahru",
               "How Much Does an Empty Shop or Factory Really Cost in Johor Bahru?",
               "Holding out for higher rent can cost a JB landlord more than it earns. A simple formula for when to accept a tenant's offer, by Victor Tai (REN 26739).",
               "2026-11-19", guide_vacancy))

def guide_datacentre(c):
    by = f'Victor Tai (Tai Sing Thong), {REN(c.lang)}, The Roof Realty · Published 22 Nov 2026'
    return f'''<section class="hero solo">
  <p class="eyebrow">Market note for landowners</p>
  <h1>Two US moves in one week. What do they mean for Johor industrial land?</h1>
  <p class="lead">In the week of 16 November 2026 the United States tightened exports of advanced AI chips to Malaysia, and President Trump spoke about taxing US companies that build data centres abroad. Johor's data centre boom is not over, but not every piece of industrial land is affected the same way. It depends on which of three kinds of land you hold.</p>
  <p class="byline">By {by}</p>
</section>
<section>
  <h2>The two moves.</h2>
  <ol class="steps">
    <li><strong>Chip export licences.</strong> On 16 November the US Commerce Department's Bureau of Industry and Security announced that shipping certain advanced AI chips to Malaysia, Singapore, Indonesia, Thailand and Brazil now needs a US export licence. The rule took effect on 19 November. Chips going to companies headquartered in the US are exempt if reporting conditions are met.</li>
    <li><strong>A tax on data centres abroad.</strong> At a White House press conference on 20 November, as reported by AP, CNBC and NBC, President Trump said he wants a large tax on American companies that build data centres outside the US. This is a statement, not a law yet.</li>
  </ol>
  <p>Johor's data centre customers come mainly from two groups: US technology companies, and Chinese companies. The first move hits buyers linked to China. The second, if it happens, hits US buyers. That is why the market noticed.</p>
</section>
<section>
  <h2>Why the US is doing this.</h2>
  <p>AI capacity is now treated like oil: whoever has the most computing power leads. The US wants to keep that lead at home. It also wants to stop its most advanced chips reaching Chinese companies through third countries. Chinese firms were among the first to build data centre capacity in Malaysia, so Malaysia sits squarely in that picture.</p>
</section>
<section>
  <h2>Three kinds of industrial land, three different outcomes.</h2>
  <ul class="steps">
    <li><strong>1. Data centre grade land.</strong> Large sites with the power and water supply data centres need. Impact is the most direct. Expect buyers to wait and see, and deals to take longer.</li>
    <li><strong>2. Land priced like data centre land, without the infrastructure.</strong> This is where the pressure is greatest. Data centre grade land has traded at very roughly 40% to 70% above ordinary industrial land in Johor. If even the best sites see buyers pause, sites that do not yet meet the requirements fall further down the queue. The buyers left are factory and warehouse operators, and they pay ordinary industrial prices.</li>
    <li><strong>3. Ordinary factories and smaller industrial lots.</strong> The buyers and tenants here are manufacturers and logistics firms, not data centre operators. Impact is the smallest.</li>
  </ul>
  <p class="note">The 40% to 70% range compares two different sources (JLL's 2025 average for Johor industrial land and The Star's July 2026 report on data centre grade land), so treat it as approximate.</p>
</section>
<section>
  <h2>What I would think about as an owner.</h2>
  <ul class="steps">
    <li>Be honest about which of the three kinds your land is. Power capacity and land size decide that, not the asking price on a listing site.</li>
    <li>If your asking price assumes a data centre buyer, ask what the land is worth to a factory or warehouse user, because that is who is buying today.</li>
    <li>If you own an ordinary factory or warehouse, the main drivers of your rent and value have not changed: location, power, ceiling height, loading access and title.</li>
  </ul>
  <p>My view: data centres in Johor will not disappear, but the market may stay cool for a while. With US policy, nobody can be sure.</p>
  <p class="note">This is my personal view, not a forecast or a guarantee.</p>
</section>
<section>
  <h2>Watch the video.</h2>
  <p>I explain this in Mandarin in <a href="https://www.facebook.com/reel/1824036028830003/">a short video on Facebook</a>.</p>
  {cta(c, "Ask Victor about your land", "", "Hi Victor, I read your note on data centres and Johor industrial land. My land is at: ")}
</section>'''

GUIDES.append(("us-data-centre-moves-johor-industrial-land",
               "Two US Moves in One Week: What They Mean for Johor Industrial Land",
               "US chip export licences for Malaysia and talk of a tax on overseas data centres: which kinds of Johor industrial land are affected, by Victor Tai (REN 26739).",
               "2026-11-22", guide_datacentre))

for slug, gtitle, gdesc, gdate, gfn in GUIDES:
    k = "g:" + slug; PAGES.append(k); PATHS[k] = f"/guides/{slug}/"; BUILDERS[k] = gfn
    META[("en", k)] = (f"{gtitle} | Victor Tai", gdesc)
    EXTRA_LD[k] = {"@context": "https://schema.org", "@type": "Article", "headline": gtitle, "description": gdesc,
                   "url": CONFIG["domain"] + PATHS[k], "datePublished": gdate, "dateModified": CONFIG["updated"],
                   "inLanguage": "en", "author": {"@id": CONFIG["domain"] + "/#victor-tai", "@type": "Person", "name": "Victor Tai"}}

def person_ld():
    names = ["Tai Sing Thong"] + ([CONFIG["zh_name"]] if CONFIG["zh_name"] else [])
    d = {"@context": "https://schema.org", "@type": "Person", "@id": CONFIG["domain"] + "/#victor-tai",
         "name": "Victor Tai", "alternateName": names, "url": CONFIG["domain"] + "/",
         "jobTitle": "Real Estate Negotiator and Associate Leader",
         "description": CONFIG["entity"].replace("&amp;", "&"),
         "worksFor": {"@type": "RealEstateAgent", "name": "The Roof Realty",
                      "address": {"@type": "PostalAddress", "addressLocality": "Johor Bahru", "addressRegion": "Johor", "addressCountry": "MY"}},
         "memberOf": [{"@type": "Organization", "name": "The Worthy Group", "url": CONFIG["domain"] + "/join/"}],
         "alumniOf": {"@type": "Organization", "name": "Ernst & Young (EY)"},
         "award": "TRR Multi Million Agent, every year since 2023",
         "telephone": "+60177757229",
         "address": {"@type": "PostalAddress", "addressLocality": "Johor Bahru", "addressRegion": "Johor", "addressCountry": "MY"},
         "knowsAbout": ["Commercial property in Johor Bahru", "Industrial property in Johor Bahru", "Shoplots", "Factories", "Warehouses"],
         "knowsLanguage": ["zh", "en"], "sameAs": [u for n, h, u in CONFIG["socials"] if u]}
    if CONFIG["ren"]:
        d["identifier"] = CONFIG["ren"]
    if CONFIG["photo"]:
        d["image"] = CONFIG["domain"] + "/" + CONFIG["photo"]
    return d

def org_ld():
    return {"@context": "https://schema.org", "@type": "Organization", "name": "The Worthy Group", "alternateName": "TWG",
            "url": CONFIG["domain"] + "/join/", "description": "A property sales team within The Roof Realty, Johor Bahru, producing over RM10 million in sales commission a year.",
            "founder": {"@id": CONFIG["domain"] + "/#victor-tai"},
            "parentOrganization": {"@type": "RealEstateAgent", "name": "The Roof Realty"},
            "address": {"@type": "PostalAddress", "addressLocality": "Johor Bahru", "addressRegion": "Johor", "addressCountry": "MY"}}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap">')

def real_page(lang, page):
    c = Ctx(lang, False)
    title, desc = META[(lang, page)]
    canon = CONFIG["domain"] + real_url(lang, page)
    alts = "" if len(LANGS) < 2 else "".join(f'<link rel="alternate" hreflang="{hl}" href="{CONFIG["domain"] + real_url(l, page)}">'
                   for hl, l in (("en", "en"), ("zh-Hans", "zh"), ("x-default", "en")))
    lds = [person_ld()] if page in ("home", "about") else ([EXTRA_LD[page]] if page in EXTRA_LD else [])
    if page == "join":
        lds = [org_ld(), person_ld()]
    if page == "tool":
        lds = [{"@context": "https://schema.org", "@type": "WebApplication", "name": title.split(" | ")[0].split("｜")[0],
                "url": canon, "applicationCategory": "FinanceApplication", "operatingSystem": "Any",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "MYR"},
                "author": {"@id": CONFIG["domain"] + "/#victor-tai"}, "dateModified": CONFIG["updated"]}, person_ld()]
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in lds)
    calc = f'<script src="/assets/calc.js?v={ASSET_V}"></script><script>initCalc("{lang}")</script>' if page == "tool" else ""
    if page in ("home", "units"):
        calc = f'<script src="/assets/calc.js?v={ASSET_V}"></script><script>initFilter();initTabs();initVideos()</script>'
    if page == "space":
        calc = f'<script src="/assets/calc.js?v={ASSET_V}"></script><script>initBrief()</script>'
    return f'''<!DOCTYPE html>
<html lang="{"zh-Hans" if lang == "zh" else "en"}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canon}">{alts}
<meta property="og:type" content="website"><meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{canon}">
<meta name="author" content="Victor Tai (Tai Sing Thong)">
{FONTS}
<link rel="stylesheet" href="/assets/site.css?v={ASSET_V}">
{ld}
</head>
<body>
<div class="page">
{header(c, page)}
<main>
{BUILDERS[page](c)}
</main>
{footer(c)}
</div>
{calc}
</body>
</html>
'''

def build():
    css = open(os.path.join(HERE, "site.css"), encoding="utf-8").read()
    js = open(os.path.join(HERE, "calc.js"), encoding="utf-8").read()
    readme = os.path.join(OUT, "README.txt"); keep = open(readme).read() if os.path.exists(readme) else None
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(os.path.join(OUT, "assets"))
    open(os.path.join(OUT, "assets", "site.css"), "w", encoding="utf-8").write(css)
    open(os.path.join(OUT, "assets", "calc.js"), "w", encoding="utf-8").write(js)
    if CONFIG["photo"]:
        shutil.copy(os.path.join(HERE, CONFIG["photo"]), os.path.join(OUT, CONFIG["photo"]))
    urls = []
    for lang in LANGS:
        for page in PAGES:
            rel = real_url(lang, page).strip("/")
            d = os.path.join(OUT, rel)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(real_page(lang, page))
            urls.append(CONFIG["domain"] + real_url(lang, page))
    from PIL import Image
    for rel, (src, width, q) in MEDIA.items():
        dst = os.path.join(OUT, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        im = Image.open(src).convert("RGB"); im.thumbnail((width, width * 2))
        im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
    bots = ["Googlebot", "Bingbot", "OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User", "PerplexityBot"]
    robots = "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots) + f"User-agent: *\nAllow: /\n\nSitemap: {CONFIG['domain']}/sitemap.xml\n"
    open(os.path.join(OUT, "robots.txt"), "w").write(robots)
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{u}</loc><lastmod>{CONFIG['updated']}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    open(os.path.join(OUT, "sitemap.xml"), "w").write(sm)
    if keep: open(readme, "w").write(keep)

    # single-file preview
    views = ""
    for lang in LANGS:
        c = Ctx(lang, True)
        for page in PAGES:
            views += (f'<div class="page view" id="v-{lang}-{hid(page)}" lang="{"zh-Hans" if lang == "zh" else "en"}" hidden>'
                      f'{header(c, page)}<main>{BUILDERS[page](c)}</main>{footer(c)}</div>\n')
    router = '''
function show(){var h=(location.hash||"").slice(1);var el=document.getElementById("v-"+h)||document.getElementById("v-en-home");
document.querySelectorAll(".view").forEach(function(v){v.hidden=v!==el});window.scrollTo(0,0)}
window.addEventListener("hashchange",show);show();initCalc("en");initBrief();initFilter();initTabs();initVideos();'''
    os.makedirs(PREV, exist_ok=True)
    open(os.path.join(PREV, "index.html"), "w", encoding="utf-8").write(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Victor Tai 个人网站 v1</title>
{FONTS}
<style>{css}
.previewbar{{background:var(--flag);color:#3a2c00;font-size:13px;padding:8px 16px;text-align:center}}</style>
</head>
<body>
<div class="previewbar">Preview · not live yet</div>
{views}
<script>{js}</script>
<script>{router}</script>
</body>
</html>
''')
    print("built", len(urls), "pages")

if __name__ == "__main__":
    build()
