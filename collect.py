"""Read-only Ethereum reconstruction. No keys, wallet, signatures or transactions."""
from __future__ import annotations
import argparse, concurrent.futures, gzip, hashlib, json, os, time
from datetime import datetime, timezone
from pathlib import Path
import requests
from eth_abi import encode, decode
from eth_hash.auto import keccak

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data/raw'
RPC = os.environ.get('ETH_ARCHIVE_RPC', 'https://eth.drpc.org')
USDC = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
POOL = '0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2'
ATOKEN = '0x98c23e9d8f34fefb1b7bd6a91b7ff122f4e16f5c'
MORPHO = '0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb'
VAULTS = {'steakhouse_v1':'0xbeef01735c132ada46aa9aa4c54623caa92a64cb',
          'gauntlet_v1':'0xdd0f28e19c1780eb6396170735d45153d261490d'}
WAD = 10**18
MARKET_TYPES = ['uint128'] * 6
PARAM_TYPES = ['address'] * 4 + ['uint256']
START, END = '2024-06-01', '2026-10-15'
EVENTS = {'2024-08-05':'August 2024 sell-off','2025-04-07':'April 2025 tariff sell-off',
          '2025-10-10':'October 2025 crypto sell-off'}

def now(): return datetime.now(timezone.utc).isoformat()
def stamp(s): return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    b=json.dumps(data, separators=(',',':')).encode()
    temp=p.with_suffix(p.suffix+'.tmp')
    temp.write_bytes(gzip.compress(b, mtime=0) if p.suffix=='.gz' else b)
    temp.replace(p)
def load(p):
    b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def request(url, payload=None, params=None):
    for n in range(7):
        try:
            r = requests.post(url,json=payload,timeout=50) if payload is not None else requests.get(url,params=params,timeout=50)
            r.raise_for_status();j=r.json()
            if isinstance(j,dict) and j.get('error'): raise RuntimeError(j['error'])
            return j
        except (requests.RequestException,ValueError,RuntimeError):
            if n==6: raise
            time.sleep(min(2**n,20))
def rpc(method,params):return request(RPC,{'jsonrpc':'2.0','id':1,'method':method,'params':params})['result']
def header(n):
    h=rpc('eth_getBlockByNumber',[hex(n),False])
    return {k:h[k] for k in ['number','hash','timestamp','parentHash']}
def block_for(ts):
    # Llama returns a nearby block, sometimes just AFTER the requested timestamp.
    lookup=request(f'https://coins.llama.fi/block/ethereum/{ts}')
    n=int(lookup['height']);h=header(n)
    while int(h['timestamp'],16)>ts:
        n-=max(1,(int(h['timestamp'],16)-ts)//12);h=header(n)
    hnext=header(n+1)
    while int(hnext['timestamp'],16)<=ts:
        n+=1;h=hnext;hnext=header(n+1)
    assert int(h['timestamp'],16)<=ts<int(hnext['timestamp'],16)
    return n,h,hnext,lookup

def spec(key,target,sig,types=(),args=(),out=('uint256',)):
    return {'key':key,'to':target,'data':'0x'+(keccak(sig.encode())[:4]+encode(types,args)).hex(),'out':list(out)}
def calls(specs,block,records):
    result={}
    for off in range(0,len(specs),60):
        sub=specs[off:off+60]
        packed=[(s['to'],True,bytes.fromhex(s['data'][2:])) for s in sub]
        calldata='0x'+(keccak(b'aggregate3((address,bool,bytes)[])')[:4]+encode(['(address,bool,bytes)[]'],[packed])).hex()
        raw_result=rpc('eth_call',[{'to':'0xca11bde05977b3631167028862be2a173976ca11','data':calldata},hex(block)])
        response=decode(['(bool,bytes)[]'],bytes.fromhex(raw_result[2:]))[0]
        for s,(success,raw) in zip(sub,response,strict=True):
            if not success:raise RuntimeError(f"Contract read failed: {s['key']}, block {block}, {raw.hex()}")
            v=decode(s['out'],raw)
            result[s['key']]=v[0] if len(v)==1 else list(v)
            records.append({'key':s['key'],'to':s['to'],'calldata':s['data'],'output_types':s['out'],'result':'0x'+raw.hex()})
    return result

def accrued_market(m, rate, block_ts):
    """Integer accounting from MorphoBalancesLib + SharesMathLib (1 asset/1e6 virtual shares)."""
    sa,ss,ba,bs,last,fee=map(int,m)
    elapsed=block_ts-last
    assert elapsed>=0
    if elapsed and ba and rate:
        a=rate*elapsed;b=a*a//(2*WAD);c=b*a//(3*WAD)
        interest=ba*(a+b+c)//WAD
        sa+=interest;ba+=interest
        fee_assets=interest*fee//WAD
        if fee_assets:ss+=fee_assets*(ss+10**6)//(sa-fee_assets+1)
    return sa,ss,ba,bs

def collect_one(ts, folder="states"):
    p=RAW/folder/f'{ts}.json.gz'
    if p.exists():return {'timestamp':ts,'cached':True}
    n,h,hn,lookup=block_for(ts);records=[];bt=int(h['timestamp'],16)
    base=[spec('aave_index',POOL,'getReserveNormalizedIncome(address)',['address'],[USDC]),
          spec('aave_claims',ATOKEN,'totalSupply()'),
          spec('aave_cash',USDC,'balanceOf(address)',['address'],[ATOKEN]),
          spec('aave_config',POOL,'getConfiguration(address)',['address'],[USDC]),
          spec('morpho_cash',USDC,'balanceOf(address)',['address'],[MORPHO])]
    for k,v in VAULTS.items():
        for key,sig,out in [('assets','totalAssets()',['uint256']),('shares','totalSupply()',['uint256']),('queue_length','withdrawQueueLength()',['uint256']),('asset','asset()',['address']),('morpho','MORPHO()',['address']),('decimals','decimals()',['uint8']),('fee','fee()',['uint256'])]:
            base.append(spec(k+'_'+key,v,sig,out=out))
        base.append(spec(k+'_price',v,'previewRedeem(uint256)',['uint256'],[10**24]))
    b=calls(base,n,records)
    qspec=[]
    for k,v in VAULTS.items():
        assert b[k+'_asset'].lower()==USDC and b[k+'_morpho'].lower()==MORPHO
        assert b[k+'_decimals']==18
        for i in range(b[k+'_queue_length']):qspec.append(spec(f'{k}_{i}',v,'withdrawQueue(uint256)',['uint256'],[i],['bytes32']))
    queues=calls(qspec,n,records)
    ids=sorted({x.hex() for x in queues.values()})
    mspec=[]
    for mid in ids:
        midb=bytes.fromhex(mid)
        mspec.extend([spec(mid+'_market',MORPHO,'market(bytes32)',['bytes32'],[midb],MARKET_TYPES),spec(mid+'_params',MORPHO,'idToMarketParams(bytes32)',['bytes32'],[midb],PARAM_TYPES)])
        for k,v in VAULTS.items():
            if midb in [val for key,val in queues.items() if key.startswith(k+'_')]:
                mspec.append(spec(mid+'_'+k,MORPHO,'position(bytes32,address)',['bytes32','address'],[midb,v],['uint256','uint128','uint128']))
    markets=calls(mspec,n,records)
    irms=[]
    for mid in ids:
        params=markets[mid+'_params'];m=markets[mid+'_market']
        assert params[0].lower()==USDC
        if int(params[3],16)!=0 and m[2] and m[4]!=bt:
            sig='borrowRateView((address,address,address,address,uint256),(uint128,uint128,uint128,uint128,uint128,uint128))'
            irms.append(spec(mid,params[3],sig,['(address,address,address,address,uint256)','(uint128,uint128,uint128,uint128,uint128,uint128)'],[params,m]))
    rates=calls(irms,n,records) if irms else {}
    positions={};result={}
    config=b['aave_config'];paused=bool((config>>60)&1);active=bool((config>>56)&1)
    result['aave']={'index':str(b['aave_index']),'claims_units':str(b['aave_claims']),'capacity_units':str(min(b['aave_claims'],b['aave_cash']) if active and not paused else 0),'cash_units':str(b['aave_cash']),'paused':paused,'active':active}
    for k,v in VAULTS.items():
        queue=[queues[f'{k}_{i}'].hex() for i in range(b[k+'_queue_length'])]
        assert len(queue)==len(set(queue))
        items=[]
        for mid in queue:
            m=markets[mid+'_market'];params=markets[mid+'_params'];sa,ss,ba,bs=accrued_market(m,rates.get(mid,0),bt)
            shares=markets[mid+'_'+k][0];assets=shares*(sa+1)//(ss+10**6)
            free=sa-ba
            assert free>=0
            items.append({'market':'0x'+mid,'collateral':params[1],'assets_units':str(assets),'market_cash_units':str(free),'capacity_units':str(min(assets,free))})
        total=sum(int(i['assets_units']) for i in items)
        # Independent reconstruction must agree with the contract before accepting a state.
        assert abs(total-b[k+'_assets'])<=max(10,len(queue)),(k,ts,total,b[k+'_assets'])
        capacity=min(total,b['morpho_cash'],sum(int(i['capacity_units']) for i in items))
        result[k]={'index':str(b[k+'_price']),'claims_units':str(b[k+'_assets']),'capacity_units':str(capacity),'shares':str(b[k+'_shares']),'fee':b[k+'_fee']/WAD,'reconciliation_units':total-b[k+'_assets'],'allocations':items}
    save(p,{'anchor_timestamp':ts,'retrieved_at':now(),'rpc_url':RPC if RPC == 'https://eth.drpc.org' else 'custom archive RPC','block':h,'next_block':hn,'block_lookup':lookup,'calls':records,'products':result})
    return {'timestamp':ts,'cached':False}

def timestamps():
    ts=set(range(stamp(START),stamp(END)+1,86400))
    for s in EVENTS:
        ts.update(range(stamp(s)-3*86400,stamp(s)+7*86400+1,6*3600))
    return sorted(ts)
def prices():
    # Daily bars have explicit open/close timestamps; they are market context, not protocol inputs.
    start,end=stamp(START)-86400,stamp(END)
    for a in range(start,end,250*86400):
        b=min(a+250*86400,end);p=RAW/'prices'/f'eth_{a}_{b}.json.gz'
        if p.exists():continue
        url='https://api.exchange.coinbase.com/products/ETH-USD/candles'
        params={'start':datetime.fromtimestamp(a,timezone.utc).isoformat(),'end':datetime.fromtimestamp(b,timezone.utc).isoformat(),'granularity':86400}
        save(p,{'url':url,'params':params,'retrieved_at':now(),'data':request(url,params=params)})
def manifest():
    files=sorted(p for p in RAW.rglob('*') if p.is_file() and not p.name.endswith('.tmp'))
    save(ROOT/'data/manifest.json',{'created_at':now(),'protocol_sha256':sha(ROOT/'docs/PROTOCOL.md'),'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]})
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--smoke',action='store_true');ap.add_argument('--workers',type=int,default=3);args=ap.parse_args()
    ts=[stamp(START),stamp('2025-04-07'),stamp(END)] if args.smoke else timestamps()
    failures=[];t=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(collect_one,x):x for x in ts}
        for i,f in enumerate(concurrent.futures.as_completed(futures),1):
            try:f.result()
            except Exception as e:failures.append({'timestamp':futures[f],'error':repr(e)});print('FAILED',failures[-1],flush=True)
            if i%25==0 or len(ts)<5:print(f'{i}/{len(ts)} states; {len(failures)} failures; elapsed {time.monotonic()-t:.1f}s',flush=True)
    save(ROOT/'reports/collection_status.json',{'requested':len(ts),'failures':failures,'seconds':time.monotonic()-t,'as_of':now()})
    if not args.smoke:prices()
    manifest()
    if failures:raise SystemExit(1)
if __name__=='__main__':main()
