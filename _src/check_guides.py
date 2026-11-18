#!/usr/bin/env python3
"""guides/<kod>.json dosyalarını denetler (anahtarlar, liste uzunlukları, <b> dışında HTML yok, sınırlar, slug, metin uzunluğu).
Kullanım: python3 _src/check_guides.py [kod ...]"""
import json
import os
import re
import sys

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
import guide_page  # noqa: E402
from build import TOPICS  # noqa: E402

D = os.path.join(SRC, 'guides')
tr = json.load(open(os.path.join(D, 'tr.json'), encoding='utf-8'))
codes = sys.argv[1:] or sorted(f[:-5] for f in os.listdir(D) if f.endswith('.json'))
bad = 0
for c in codes:
    try:
        t = json.load(open(os.path.join(D, c + '.json'), encoding='utf-8'))
    except Exception as ex:  # noqa: BLE001
        print(f'{c}: okunamadı: {ex}'); bad += 1; continue
    errs = guide_page.check(c, t, tr, TOPICS)
    if not errs:
        for x in TOPICS:
            for i, ((_, p), (_, rp)) in enumerate(zip(t[f'{x}_body'], tr[f'{x}_body'])):
                if p.count('<b>') != rp.count('<b>'):
                    errs.append(f'{x}_body[{i}]: <b> sayısı TR ile aynı olmalı ({p.count("<b>")} != {rp.count("<b>")})')
            if c != 'tr' and t[f'{x}_slug'] == tr[f'{x}_slug']:
                errs.append(f'{x}_slug: Türkçe slug kullanılmış; o dile göre yaz')
    lens = ' '.join(f'{x}={guide_page.plain_len(t, x)}' for x in TOPICS) if not errs else ''
    print(f'{c}: ' + ('TAMAM ' + lens if not errs else 'HATA\n  ' + '\n  '.join(errs)))
    bad += bool(errs)
sys.exit(1 if bad else 0)
