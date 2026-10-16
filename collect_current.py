"""Capture official current-product quotes. No wallet, transaction or API key.

Offline analysis never calls this module's network functions. Refreshes are explicit.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data/raw/current'
USDC = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
VAULTS = {
    'steakhouse_v2': '0xbeef088055857739C12CD3765F20b7679Def0f51',
    'gauntlet_v2': '0x8c106EEDAd96553e64287A5A6839c3Cc78afA3D0',
}
SGOV = 'https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf'
AAVE_QUERY = '''{ reserves(request:{query:{chainIds:[1]},filter:SUPPLY,orderBy:{assetName:ASC}}) {
 id onChainId chain {chainId name} spoke {name address} status {active paused frozen}
 summary {supplyApy {value normalized} supplied {amount {value}}}
 asset {onchainAssetId underlying {address info {symbol decimals}} hub {name address}
 summary {availableLiquidity {amount {value}} supplied {amount {value}} utilizationRate {value}}}
}}'''

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def capture(name, url, query=None):
    start = now()
    r = requests.post(url, json={'query':query}, timeout=60) if query else requests.get(url, timeout=60)
    r.raise_for_status()
    body = r.json()
    if body.get('errors'):
        raise RuntimeError(body['errors'])
    record = dict(url=url, method='POST' if query else 'GET', query=query,
                  request_started_utc=start, retrieved_utc=now(), response=body)
    (RAW/f'{name}.json').write_text(json.dumps(record, indent=2)+'\n')
    return body

def main(refresh=False):
    manifest = ROOT/'data/current_manifest.json'
    if manifest.exists() and not refresh:
        print('Saved snapshot preserved. Pass --refresh to collect a new vintage.'); return
    RAW.mkdir(parents=True, exist_ok=True)
    started = now()
    capture('aave_v4', 'https://api.v4.aave.com/graphql', AAVE_QUERY)
    capture('morpho_v2_directory', 'https://api.morpho.org/v0/vaults-v2?chain_ids=1&limit=100')
    for key, address in VAULTS.items():
        base = f'https://api.morpho.org/v1/vaults-v2/1:{address}'
        capture(key+'_state', base+'/state')
        for lookback in ['six_hours','thirty_days']:
            capture(key+'_'+lookback, base+'/apy-averages?lookback='+lookback)
    start=now(); r=requests.get(SGOV,timeout=60);r.raise_for_status()
    cache=ROOT/'.cache/current';cache.mkdir(parents=True,exist_ok=True)
    html=cache/'sgov.html';html.write_bytes(r.content)
    plain=BeautifulSoup(r.text,'html.parser').get_text(' ',strip=True)
    fields={}
    for name, label in [('sec_yield','30 Day SEC Yield'),('median_spread','30 Day Median Bid/Ask Spread')]:
        # Issuer layout places the date either before or after the number.
        matches=re.findall(re.escape(label)+r'\s+(?:as of\s+([A-Za-z]+ \d{1,2}, \d{4})\s+([\d.]+)%|([\d.]+)%\s+as of\s+([A-Za-z]+ \d{1,2}, \d{4}))',plain)
        assert matches, f'Missing issuer field: {name}'
        values={(a or d, float(b or c)/100) for a,b,c,d in matches}
        assert len(values)==1, f'Ambiguous issuer field: {name}'
        date,value=values.pop();fields[name]={'value':value,'as_of':datetime.strptime(date,'%b %d, %Y').date().isoformat()}
    match=re.search(r'Expense Ratio:?\s+(?:Fees as stated in the prospectus\s+)?([\d.]+)%',plain)
    assert match, 'Missing expense ratio'
    fields['expense_ratio']={'value':float(match[1])/100}
    (RAW/'sgov_quote.json').write_text(json.dumps(dict(url=SGOV,request_started_utc=start,
        retrieved_utc=now(),source_html_sha256=sha(html),extraction='Numeric fields from issuer product page; full HTML retained only in local cache.',fields=fields),indent=2)+'\n')
    files=sorted(RAW.glob('*.json'))
    manifest.write_text(json.dumps(dict(started_utc=started,finished_utc=now(),
        selection='Ethereum native USDC; Aave V4 Core/Main; two named Morpho Vaults V2; SGOV income proxy',
        block_pinning='Aave is not block-pinned. Morpho indexed blocks retained per endpoint; requests are sequential, not atomic.',
        inputs={str(p.relative_to(ROOT)):sha(p) for p in files},
        protocol_sha256=sha(ROOT/'docs/CURRENT_COMPARISON.md')),indent=2)+'\n')
    print(manifest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');main(p.parse_args().refresh)
