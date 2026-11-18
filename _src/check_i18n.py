#!/usr/bin/env python3
"""i18n/<kod>.json dosyalarını tr.json'a göre denetler.  Kullanım: python3 _src/check_i18n.py [kod ...]  (kodsuz: hepsi)"""
import json
import os
import re
import sys

SRC = os.path.dirname(os.path.abspath(__file__))
I18N = os.path.join(SRC, 'i18n')
LIMITS = {
    'seo_title': 60, 'seo_desc': 155, 'u_d': 5, 'u_h': 5, 'u_m': 5, 'u_s': 5, 'cd_label': 16, 'kick': 20,
    'cue': 24, 'k_invitation': 24, 'k_families': 24, 'k_date': 24, 'k_venue': 24, 'k_rsvp': 24, 'side1': 24, 'side2': 24,
    'wx_kick': 24, 'kick_fc': 24, 'kick_arch': 24, 'season': 24,
    'yes': 22, 'no': 22, 'change': 22, 'cal': 22, 'map': 22, 'f_send': 22, 'sweep': 22, 'blow': 26, 'blow_now': 22, 'tap': 22, 'swipe': 24,
    'invite': 180, 'close': 180, 'close2': 70, 'wind': 16, 'rain': 16, 'rain_prob': 18, 'tip_rain': 80, 'tip_hot': 90, 'tip_mild': 80, 'tip_cool': 80,
}
PH = re.compile(r'\{(\w+)\}')


def load(code):
    with open(os.path.join(I18N, code + '.json'), encoding='utf-8') as f:
        return json.load(f)


def check(code, tr):
    errs = []
    try:
        t = load(code)
    except Exception as ex:   # noqa: BLE001
        return [f'okunamadı: {ex}']
    if set(t) != set(tr):
        errs.append(f'eksik: {sorted(set(tr) - set(t))} fazla: {sorted(set(t) - set(tr))}')
    for k, v in t.items():
        if not isinstance(v, str) or not v.strip():
            errs.append(f'{k}: boş/metin değil')
            continue
        if '<' in v or '>' in v:
            errs.append(f'{k}: HTML işareti var')
        if k in tr and set(PH.findall(v)) != set(PH.findall(tr[k])):
            errs.append(f'{k}: yer tutucu farklı {sorted(set(PH.findall(v)))} != {sorted(set(PH.findall(tr[k])))}')
        if k in LIMITS and len(v) > LIMITS[k]:
            errs.append(f'{k}: {len(v)} > {LIMITS[k]} karakter ({v!r})')
    return errs


def main():
    tr = load('tr')
    codes = sys.argv[1:] or sorted(f[:-5] for f in os.listdir(I18N) if f.endswith('.json'))
    bad = 0
    for c in codes:
        errs = check(c, tr)
        print(f'{c}: ' + ('TAMAM' if not errs else 'HATA\n  ' + '\n  '.join(errs)))
        bad += bool(errs)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
