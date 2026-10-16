"""Download issuer NAV/distribution facts for a Treasury-bill ETF benchmark.

The complete issuer workbook stays in ignored local cache. Only numerical facts
used by this analysis, retrieval metadata and checksums enter the repository.
"""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import requests
from collect import ROOT, now, sha

PAGE = 'https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf'
URL = ('https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document'
       '?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US'
       '&portfolioId=314116&component=fundDownload&userType=individual')
NS = {'s': 'urn:schemas-microsoft-com:office:spreadsheet'}


def sheets(content):
    # The issuer XML has bare ampersands in hyperlink attributes. Preserve original
    # bytes for hashing; escape only those malformed ampersands in the parser copy.
    fixed = re.sub(r'&(?!#?[A-Za-z0-9]+;)', '&amp;', content.decode('utf-8-sig'))
    root = ET.fromstring(fixed)
    result = {}
    for sheet in root.findall('s:Worksheet', NS):
        rows = []
        for row in sheet.findall('s:Table/s:Row', NS):
            values = []
            for cell in row.findall('s:Cell', NS):
                index = int(cell.get('{'+NS['s']+'}Index', len(values)+1))
                values += [None] * (index-1-len(values))
                data = cell.find('s:Data', NS)
                values.append(data.text if data is not None else None)
            rows.append(values)
        result[sheet.get('{'+NS['s']+'}Name')] = rows
    return result


def main(refresh=False):
    out = ROOT / 'data/raw/treasury/sgov.json'
    if out.exists() and not refresh:
        print('Using saved issuer numerical extract:', out)
        return
    response = requests.get(URL, timeout=45)
    response.raise_for_status()
    cache = ROOT / '.cache/sgov_workbook.xml'
    cache.parent.mkdir(exist_ok=True)
    cache.write_bytes(response.content)
    data = sheets(response.content)
    hist = []
    for row in data['Historical'][1:]:
        date = pd.to_datetime(row[0], format='%b %d, %Y').strftime('%Y-%m-%d')
        if '2024-05-01' <= date <= '2026-10-14':
            hist.append({'date': date, 'nav': row[1], 'ex_distribution': '0' if row[2] in [None,'--'] else row[2]})
    distributions = []
    for row in data['Distributions'][1:]:
        date = pd.to_datetime(row[1], format='%b %d, %Y').strftime('%Y-%m-%d')
        if '2024-05-01' <= date <= '2026-10-14':
            distributions.append({'ex_date': date, 'pay_date': pd.to_datetime(row[2],format='%b %d, %Y').strftime('%Y-%m-%d'), 'distribution': row[3]})
    monthly = []
    for row in data['Performance']:
        if len(row) != 2:
            continue
        try:
            date = pd.to_datetime(row[0], format='%b %d, %Y').strftime('%Y-%m-%d')
            val = float(row[1])
        except (ValueError,TypeError):
            continue
        if '2024-06-01' <= date <= '2026-09-30':
            monthly.append({'month_end': date, 'nav_total_return_pct': val})
    assert hist and distributions and len(monthly)==28
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {'source_url': URL, 'product_page': PAGE, 'retrieved_at': now(),
               'source_workbook_sha256': hashlib.sha256(response.content).hexdigest(),
               'historical': sorted(hist,key=lambda x:x['date']), 'distributions': distributions,
               'monthly_published_returns': monthly,
               'extraction_note': 'Numeric fields only from issuer Historical, Distributions and Performance sheets. Full workbook in ignored cache.'}
    out.write_text(json.dumps(payload,indent=2)+'\n')
    manifest={'retrieved_at':payload['retrieved_at'],'protocol_sha256':sha(ROOT/'docs/TREASURY_COMPARISON.md'),
              'files':[{'path':str(out.relative_to(ROOT)),'sha256':sha(out)}]}
    (ROOT/'data/treasury_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Saved',len(hist),'NAVs;',len(monthly),'monthly cross-checks')


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true')
    main(p.parse_args().refresh)
