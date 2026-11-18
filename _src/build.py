#!/usr/bin/env python3
"""WeddingInvite sitesini üretir: 16 dilde davetiye (tek dosya index.html), dil başına takvim.ics, sitemap.xml, llms.txt.

Kullanım (depo kökünden):  python3 _src/build.py

- Şablon: _src/template.html (görseller ve fontlar base64 gömülü; metinler {{anahtar}}, JS metinleri L.anahtar)
- Metinler: _src/i18n/<dil>.json (yalnızca dosyası olan diller üretilir; tr zorunlu, kaynak dil). Denetim: _src/check_i18n.py
- Türkçe kökte (/WeddingInvite/), diğer diller /WeddingInvite/<dil>/ klasöründe. muzik.m4a kökte ortak.
- Ek fontlar: _src/fonts/ (Google Fonts, SIL OFL). Gömülü fontlar yalnız Latin + Türkçe harfleri kapsar; bir dilin metinlerinde
  latin-ext (ą ę ł …) ya da kiril harf varsa o parça otomatik gömülür. CJK, Arapça, Devanagari sistem fontlarına düşer (FONT_STACK).
- Demo verisi (isimler, tarih, mekân, adres) her dilde aynı; yalnız metinler çevrilir. Katılım formu örnek: hiçbir yere veri göndermez.
Jekyll "_" ile başlayan klasörleri yayınlamaz; _src sitede görünmez.
"""
import base64
import datetime
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guide_page  # noqa: E402

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
SITE = 'https://anbertech.github.io/'
BASE = SITE + 'WeddingInvite/'
ORG = SITE + '#org'

# kod, yön, og:locale, Intl yerel ayarı, yazı sistemi
LANGS = [
    ('tr', 'ltr', 'tr_TR', 'tr-TR', 'latn'), ('en', 'ltr', 'en_US', 'en-US', 'latn'), ('ar', 'rtl', 'ar_AR', 'ar-u-nu-latn', 'arab'),
    ('de', 'ltr', 'de_DE', 'de-DE', 'latn'), ('es', 'ltr', 'es_ES', 'es-ES', 'latn'), ('fr', 'ltr', 'fr_FR', 'fr-FR', 'latn'),
    ('hi', 'ltr', 'hi_IN', 'hi-IN', 'deva'), ('id', 'ltr', 'id_ID', 'id-ID', 'latn'), ('it', 'ltr', 'it_IT', 'it-IT', 'latn'),
    ('ja', 'ltr', 'ja_JP', 'ja-JP', 'jpan'), ('ko', 'ltr', 'ko_KR', 'ko-KR', 'kore'), ('nl', 'ltr', 'nl_NL', 'nl-NL', 'latn'),
    ('pl', 'ltr', 'pl_PL', 'pl-PL', 'latn'), ('pt', 'ltr', 'pt_BR', 'pt-BR', 'latn'), ('ru', 'ltr', 'ru_RU', 'ru-RU', 'latn'),
    ('zh-Hans', 'ltr', 'zh_CN', 'zh-CN', 'hans'),
]
LANG = {l[0]: l for l in LANGS}
NAMES = {'tr': 'Türkçe', 'en': 'English', 'ar': 'العربية', 'de': 'Deutsch', 'es': 'Español', 'fr': 'Français', 'hi': 'हिन्दी',
         'id': 'Bahasa Indonesia', 'it': 'Italiano', 'ja': '日本語', 'ko': '한국어', 'nl': 'Nederlands', 'pl': 'Polski', 'pt': 'Português',
         'ru': 'Русский', 'zh-Hans': '简体中文'}
EMAIL = 'destek.anbertech@gmail.com'
ICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath fill='%23d81b3c' d='M16 29S2.5 20.6 2.5 11.2C2.5 6.8 5.9 3.5 10 3.5c2.6 0 4.8 1.3 6 3.4 1.2-2.1 3.4-3.4 6-3.4 4.1 0 7.5 3.3 7.5 7.7C29.5 20.6 16 29 16 29z'/%3E%3C/svg%3E"   # davetiyedeki kalp simgesi (rehber sayfaları için)
TOPICS = ('make', 'engage', 'rsvp')   # rehberler: online davetiye, nişan davetiyesi, katılım formu (_src/guides/<dil>.json)
GUIDE_THEME = (":root{--bg:#f6f3ee;--card:#fffdf9;--soft:#efe8de;--line:#e2d9cc;--ink:#3f342b;--muted:#6f6154;--acc:#7a2c3b;"
               "--f-head:'Cormorant Garamond','Iowan Old Style','Palatino Linotype',Georgia,serif;--f-text:'Iowan Old Style','Palatino Linotype',Georgia,serif;"
               "--f-ui:-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif}"
               "html[lang=ja],html[lang=zh-Hans],html[lang=ar],html[lang=hi]{--f-head:serif;--f-text:serif}"
               "html[lang=ko]{--f-head:'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif;--f-text:'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif}")

# Latin dışı yazılar: gömülü Latin fontların ardından denenecek sistem fontları (serif, sans)
FONT_STACK = {
    'jpan': ("'Hiragino Mincho ProN','Yu Mincho','YuMincho','Noto Serif JP','Noto Serif CJK JP'",
             "'Hiragino Sans','Hiragino Kaku Gothic ProN','Yu Gothic','Meiryo','Noto Sans JP'"),
    'kore': ("'AppleMyungjo','Nanum Myeongjo','Noto Serif KR','Noto Serif CJK KR','Batang'",
             "'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR'"),
    'hans': ("'Songti SC','STSong','Noto Serif SC','Noto Serif CJK SC','Source Han Serif SC','SimSun'",
             "'PingFang SC','Microsoft YaHei','Noto Sans SC'"),
    'arab': ("'Amiri','Noto Naskh Arabic','Geeza Pro','Times New Roman'",
             "'Geeza Pro','Noto Sans Arabic','Segoe UI','Tahoma'"),
    'deva': ("'Noto Serif Devanagari','Kohinoor Devanagari','Devanagari Sangam MN','Nirmala UI','Mangal'",
             "'Kohinoor Devanagari','Noto Sans Devanagari','Nirmala UI','Mangal'"),
}
# Gömülü fontların zaten kapsadığı harfler (template.html'deki unicode-range'ler)
COVERED = re.compile('[\u0000-\u007e\u00a0-\u00ff\u0131\u011e\u011f\u0130\u015e\u015f\u2013\u2014\u2018-\u201e\u2022\u2026\u2032\u2033'
                     '\u00b7\u2665\u00a9]')
SUBSET_TEST = {'latin-ext': re.compile('[\u0100-\u02ff\u1e00-\u1eff]'), 'cyrillic': re.compile('[\u0400-\u045f\u0490\u0491\u04b0\u04b1]')}

# yağış birimi (milimetre) Latin dışı yazılarda
MM = {'ar': 'مم', 'ru': 'мм', 'hi': 'मिमी'}
# Bütün dillerde: kapanış notu çerçeve içinde kalsın; geniş aralıklı küçük başlıklar yuvarlak/kemerli kartlara sığsın (QA 2026-11-18)
BASE_CSS = ('.t7 .alt7{padding:0 46px}.t7 .smp{text-wrap:balance}'
            '.t6 .kick{letter-spacing:.14em;text-indent:.14em;max-width:150px;line-height:1.35;text-wrap:balance}'
            '.t4>.kick,.t5 .band .kick{letter-spacing:.22em;text-indent:.22em;max-width:210px;line-height:1.35}')

DEMO = {'p1': 'Elif', 'p2': 'Ege', 'venue': 'Mehtap Yalı Davet Bahçesi',
        'address': 'Kandilli Caddesi No: 18, Kandilli, 34684 Üsküdar / İstanbul',
        'start': '20270612T160000Z', 'end': '20270612T210000Z', 'stamp': '20261118T120000Z'}


def e(s):
    return html.escape(str(s), quote=True)


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def sub_dir(code):
    return '' if code == 'tr' else code.lower() + '/'


def url(code):
    return BASE + sub_dir(code)


# ---------------------------------------------------------------- dil başına parçalar

def font_css(code, t):
    """Dilin metinleri gömülü fontların kapsamadığı Latin/Kiril harf içeriyorsa o parçayı göm; Latin dışı yazıya sistem fontu."""
    text = COVERED.sub('', ''.join(t.values()))
    out = [BASE_CSS]
    if len(t['invite']) > 145:   # uzun davet metni: aile adları alttaki inci çerçeveye binmesin
        out.append('.t2{padding-top:50px}.t2 .inv{font-size:17px;line-height:1.36;max-width:236px}.t2 .orn2{margin:14px 0 10px}')
    meta = json.loads(read(os.path.join(SRC, 'fonts', 'fonts.json')))
    for sub, rx in SUBSET_TEST.items():
        if rx.search(text):
            for f in meta:
                if f['sub'] != sub:
                    continue
                with open(os.path.join(SRC, 'fonts', f['file']), 'rb') as fh:
                    b64 = base64.b64encode(fh.read()).decode()
                out.append(f"@font-face{{font-family:'{f['family']}';font-style:{f['style']};font-weight:{f['weight']};font-display:swap;"
                           f"src:url(data:font/woff2;base64,{b64}) format('woff2');unicode-range:{f['range']}}}")
    script = LANG[code][4]
    if script in FONT_STACK:
        serif, sans = FONT_STACK[script]
        out.append(f":root{{--f-serif:'Cormorant Garamond',{serif},Georgia,serif;--f-script:'Pinyon Script','Cormorant Garamond',{serif},Georgia,serif;"
                   f"--f-sans:'Jost',{sans},'Helvetica Neue',Arial,sans-serif;--f-caps:'Cinzel','Cormorant Garamond',{serif},Georgia,serif}}")
        # bu yazılarda eğik (italik) harf yapay üretilir ve bozuk görünür; harf aralığı da yazıyı dağıtır (Arapçada harfleri ayırır)
        out.append('#app :not(.amp),.dondur{font-style:normal!important}')
        sp = '0' if script == 'arab' else '.06em'
        out.append('#app{font-variant-numeric:lining-nums}.slip .tip{font-size:12px;line-height:1.3}.slip .src{font-size:8px}')
        if script == 'kore':
            out.append('#app,.dondur{word-break:keep-all;overflow-wrap:anywhere}')
        if script == 'jpan':
            out.append('#app,.dondur{line-break:strict}')
        if script == 'arab':   # Arapça harfler küçük puntoda okunmuyor
            out.append('.kick,.t7 .kick{font-size:12px!important}.cdn i,.t2 .fams small,.rsvp .fld span,.kisi span,.t6 .row dt,.cdl{font-size:11px!important}'
                       '.cdl{width:auto;min-width:50px;color:var(--ink)}')
        out.append(f'.kick,.cue,.cta .how,.swipe,.cdl,.cdn i,.t3 .mon,.t3 .when,.t3 .yr,.pill,.t2 .fams small,.rsvp .fld span,.kisi span,'
                   f'.t6 .row dt,.t7 .kick{{letter-spacing:{sp}!important;text-indent:0!important}}')
    if LANG[code][1] == 'rtl':
        out.append('[dir=rtl] .rsvp .fld,[dir=rtl] .kisi span,[dir=rtl] .cdl,[dir=rtl] .blow{text-align:right}'
                   '[dir=rtl] #mapBtn svg{transform:scaleX(-1)}')
    return f'<style>\n{chr(10).join(out)}\n</style>'


def head(code, t, built):
    u = url(code)
    alts = ''.join(f'<link rel="alternate" hreflang="{c}" href="{url(c)}">\n' for c in built)
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Organization', '@id': ORG, 'name': 'AnberTech', 'url': SITE, 'logo': SITE + 'assets/img/icon-512.png'},
        {'@type': 'WebPage', '@id': u + '#page', 'url': u, 'name': t['seo_title'], 'description': t['seo_desc'], 'inLanguage': code,
         'isPartOf': {'@type': 'WebSite', '@id': BASE + '#site', 'name': 'WeddingInvite', 'url': BASE, 'publisher': {'@id': ORG}},
         'publisher': {'@id': ORG}, 'author': {'@id': ORG}}]}
    return (f'<title>{e(t["seo_title"])}</title>\n'
            f'<meta name="description" content="{e(t["seo_desc"])}">\n'
            f'<link rel="canonical" href="{u}">\n'
            f'{alts}<link rel="alternate" hreflang="x-default" href="{url("en")}">\n'
            f'<meta property="og:type" content="website">\n'
            f'<meta property="og:site_name" content="WeddingInvite">\n'
            f'<meta property="og:url" content="{u}">\n'
            f'<meta property="og:locale" content="{LANG[code][2]}">\n'
            f'<meta property="og:title" content="{e(t["og_title"])}">\n'
            f'<meta property="og:description" content="{e(t["date_long"] + " · " + DEMO["venue"] + ", " + t["wx_city"])}">\n'
            f'<meta name="twitter:card" content="summary">\n'
            '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>')


def js_strings(code, t):
    L = dict(t)
    for k in ('seo_title', 'seo_desc', 'og_title', 'ics_desc', 'ics_alarm'):
        L.pop(k, None)
    L['locale'] = LANG[code][3]
    L['music'] = 'muzik.m4a' if code == 'tr' else '../muzik.m4a'
    L['ymd'] = LANG[code][4] in ('jpan', 'kore', 'hans')   # ilk kartta tarih yıl-ay-gün sırasıyla
    L['mm'] = MM.get(code, 'mm')
    return json.dumps(L, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')


def render(tpl, code, t, built):
    def ph(m):
        k = m.group(1)
        if k == '@lang':
            return code
        if k == '@dir':
            return LANG[code][1]
        if k == '@head':
            return head(code, t, built)
        if k == '@css':
            return font_css(code, t)
        if k == '@L':
            return js_strings(code, t)
        if k not in t:
            sys.exit(f'{code}: şablonda {k} var, i18n dosyasında yok')
        return e(t[k])
    return re.sub(r'\{\{(@?\w+)\}\}', ph, tpl)


def ics_text(s):
    return s.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def ics_fold(line):
    """RFC 5545: satırlar en çok 75 bayt; devam satırı bir boşlukla başlar (çok baytlı harf bölünmez)."""
    out, cur, size = [], '', 0
    for ch in line:
        b = len(ch.encode('utf-8'))
        if size + b > (75 if not out else 74):
            out.append(cur)
            cur, size = '', 0
        cur += ch
        size += b
    out.append(cur)
    return '\r\n '.join(out)


def ics(code, t):
    title = f'{DEMO["p1"]} & {DEMO["p2"]} {t["event"]}'
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', f'PRODID:-//AnberTech//WeddingInvite//{code.upper()}', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
             'BEGIN:VEVENT', f'UID:{DEMO["start"]}-ElifEge@weddinginvite', f'DTSTAMP:{DEMO["stamp"]}',
             f'DTSTART:{DEMO["start"]}', f'DTEND:{DEMO["end"]}', 'SUMMARY:' + ics_text(title),
             'LOCATION:' + ics_text(DEMO['venue'] + ', ' + DEMO['address']), 'DESCRIPTION:' + ics_text(t['ics_desc']),
             'BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:' + ics_text(t['ics_alarm'].replace('{title}', title)), 'TRIGGER:-P1D',
             'END:VALARM', 'END:VEVENT', 'END:VCALENDAR']
    return '\r\n'.join(ics_fold(x) for x in lines) + '\r\n'


def guide_url(code, G, x):
    return url(code) + G[code][f'{x}_slug'] + '/'


def build_guides(G, gbuilt):
    org = {'@type': 'Organization', '@id': ORG, 'name': 'AnberTech', 'url': SITE, 'email': EMAIL}
    for c in gbuilt:
        for x in TOPICS:
            page = guide_page.render(code=c, dirn=LANG[c][1], og_locale=LANG[c][2], lang_names=NAMES, built=gbuilt, x=x, t=G[c], topics=TOPICS,
                                     url_of=lambda k, y: guide_url(k, G, y), home_url=url, cta_url=url(c), brand='WeddingInvite',
                                     site_name='WeddingInvite', org=org, email=EMAIL, theme_css=GUIDE_THEME, icon=ICON)
            write(os.path.join(ROOT, sub_dir(c), G[c][f'{x}_slug'], 'index.html'), page)


def sitemap(built, G=None, gbuilt=()):
    today = datetime.date.today().isoformat()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for c in built:
        out.append(f'  <url><loc>{url(c)}</loc><lastmod>{today}</lastmod>')
        out += [f'    <xhtml:link rel="alternate" hreflang="{c2}" href="{url(c2)}" />' for c2 in built]
        out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{url("en")}" />')
        out.append('  </url>')
    for x in TOPICS:
        for c in gbuilt:
            out.append(f'  <url><loc>{guide_url(c, G, x)}</loc><lastmod>{today}</lastmod>')
            out += [f'    <xhtml:link rel="alternate" hreflang="{c2}" href="{guide_url(c2, G, x)}" />' for c2 in gbuilt]
            out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{guide_url("en" if "en" in gbuilt else gbuilt[0], G, x)}" />')
            out.append('  </url>')
    out.append('</urlset>')
    return '\n'.join(out) + '\n'


def llms(built, G=None, gbuilt=()):
    langs = '\n'.join(f'- {c}: {url(c)}' for c in built)
    guides = ''
    if 'en' in gbuilt:
        guides = '\n## Guides\n\n' + '\n'.join(f'- [{G["en"][f"{x}_name"]}]({guide_url("en", G, x)}): {G["en"][f"{x}_card"]}' for x in TOPICS) + \
                 f'\n\nGuides are available in {len(gbuilt)} languages (same paths under each language folder).\n'
    return f'''# WeddingInvite

> WeddingInvite is an online wedding and engagement invitation that opens in the browser, made by AnberTech ({SITE}).
> Guests open one link: a sealed marble door opens (sweep the petals with a finger or blow into the microphone, then tap the seal),
> then the invitation shows the couple, the invitation text and families, the date with add-to-calendar, the venue with directions,
> an RSVP form, the weather for the day and a closing card, with background music and a countdown. No app or account is needed.

## Live demo

This site is a live demo with sample data (Elif & Ege, 12 June 2027, Istanbul). Names, date, venue and families are examples.
The demo RSVP form does not send data anywhere; answers stay only on the visitor's device.
The demo is available in {len(built)} languages:

{langs}
{guides}
## Contact

- Developer: AnberTech, {SITE}
'''


def main():
    tpl = read(os.path.join(SRC, 'template.html'))
    T = {}
    for code, *_ in LANGS:
        p = os.path.join(SRC, 'i18n', f'{code}.json')
        if os.path.exists(p):
            T[code] = json.loads(read(p))
    if 'tr' not in T:
        sys.exit('i18n/tr.json gerekli')
    tr = set(T['tr'])
    for c, t in T.items():
        if set(t) != tr:
            sys.exit(f'i18n/{c}.json anahtarları tr.json ile aynı değil: eksik {sorted(tr - set(t))} fazla {sorted(set(t) - tr)}')
    built = [c for c, *_ in LANGS if c in T]
    for c in built:
        d = os.path.join(ROOT, sub_dir(c))
        write(os.path.join(d, 'index.html'), render(tpl, c, T[c], built))
        write(os.path.join(d, 'takvim.ics'), ics(c, T[c]))
    G, gbuilt = {}, []
    gdir = os.path.join(SRC, 'guides')
    if os.path.isdir(gdir):
        for c in built:
            p = os.path.join(gdir, f'{c}.json')
            if os.path.exists(p):
                G[c] = json.loads(read(p))
        if G and 'tr' not in G:
            sys.exit('guides/tr.json gerekli')
        for c, g in G.items():
            errs = guide_page.check(c, g, G.get('tr'), TOPICS)
            if errs:
                sys.exit(f'guides/{c}.json hatalı:\n  ' + '\n  '.join(errs))
        gbuilt = [c for c in built if c in G]
        build_guides(G, gbuilt)
    write(os.path.join(ROOT, 'sitemap.xml'), sitemap(built, G, gbuilt))
    write(os.path.join(ROOT, 'llms.txt'), llms(built, G, gbuilt))
    print('üretildi:', ', '.join(built), '| rehber:', ', '.join(gbuilt) or '-')


if __name__ == '__main__':
    main()
