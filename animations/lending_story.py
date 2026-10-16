"""Current V4/V2 snapshot, read only from the validated notebook's saved results.

Chart contract: zero-based quote bars with explicit rate conventions; signed
90-day net-income differences; shared cash amounts without a safety ranking.
The April V3 observation is a separate, labelled historical callout.
"""
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
import math
import manimgx as m

ROOT=Path(__file__).resolve().parents[1]
INK,MUTED,GRID='#17324A','#59636E','#E7EAED'
KEYS=['aave_v4','steakhouse_v2','gauntlet_v2']
COLORS=['#3476A8','#C87936','#8E4D20','#637A66']
m.config.background_color=m.WHITE

def rows(path):
    with (ROOT/path).open() as f:return list(csv.DictReader(f))

def evidence():
    manifest=json.loads((ROOT/'data/current_manifest.json').read_text())
    for name,digest in manifest['inputs'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
    rates={r['product']:r for r in rows('reports/current_rates.csv')}
    scenario={r['product']:r for r in rows('reports/current_scenarios.csv')
              if float(r['capital'])==10000 and int(r['days'])==90 and r['scenario']=='Base'}
    assert set(rates)==set(KEYS+['sgov']) and set(scenario)==set(rates)
    for key,r in rates.items():
        rate=float(r['effective_scenario_rate']);f,s=(0,.00005) if key=='sgov' else (10,.0005)
        final=(10000-f)*(1-s)*(1+rate)**(90/365)*(1-s)-f
        assert math.isclose(final,float(scenario[key]['net_final']),abs_tol=1e-8)
        assert math.isclose(float(scenario[key]['extra_vs_sgov']),final-float(scenario['sgov']['net_final']),abs_tol=1e-8)
    old=[r for r in rows('data/processed/daily_panel.csv') if r['product']=='aave' and r['date'].startswith('2026-04-21')]
    assert len(old)==1
    return rates,scenario,manifest,old[0]

def text(s,x,y,size=24,color=INK):
    return m.Text(s,font='Noto Sans',font_size=size,color=color).move_to([x,y,0])

def line(x1,y1,x2,y2,color=GRID,width=1):
    return m.Line([x1,y1,0],[x2,y2,0],color=color,stroke_width=width)

class LendingStory(m.Scene):
    def construct(self):
        rates,costs,manifest,old=evidence()
        stamp=datetime.fromisoformat(manifest['finished_utc']).strftime('%d %b %Y, %H:%M UTC')
        footer=text('Official Aave / Morpho APIs + iShares | Exact sources and assumptions in the notebook',0,-3.65,16,MUTED)
        self.add(footer)
        def heading(title,subtitle):return m.VGroup(text(title,0,3.2,36),text(subtitle,0,2.55,21,MUTED))
        # 0–12 seconds: original quote conventions, not an earned-return backtest.
        frame=heading('Is stablecoin lending worth it?',f'Current Ethereum USDC products | {stamp}')
        bottom=-1.3
        for tick in [0,2,4,6]:
            y=bottom+tick*.43
            frame.add(line(-5.65,y,5.8 if tick==0 else -5.5,y),text(f'{tick}%',-6.1,y,20,MUTED))
        names=['Aave V4','Morpho V2','Morpho V2','SGOV']
        details=['Core / Main','Steakhouse Prime','Gauntlet Prime','Treasury ETF']
        conventions=['Variable APY','6-hour realized APY','6-hour realized APY','30-day SEC yield']
        for i,key in enumerate(KEYS+['sgov']):
            x=-4.45+i*2.95;v=float(rates[key]['quote_rate'])*100;h=v*.43
            frame.add(m.Rectangle(width=1.35,height=h,fill_color=COLORS[i],fill_opacity=1,stroke_width=0).move_to([x,bottom+h/2,0]),
                      text(f'{v:.2f}%',x,bottom+h+.25,29,COLORS[i]),text(names[i],x,-1.7,24),
                      text(details[i],x,-2.1,19),text(conventions[i],x,-2.5,18,MUTED))
        frame.add(text(f"Different windows and conventions; SGOV as of {rates['sgov']['source_as_of']}. Not fixed future returns.",0,-3.1,18,MUTED))
        self.play(m.FadeIn(frame),run_time=.6);self.wait(10.8);self.play(m.FadeOut(frame),run_time=.6)
        # 12–20.3: explicit scenario, common signed dollar scale.
        frame=heading('The holding period changes the answer','USD 10,000 · 90 days · net extra income versus SGOV')
        for tick in [-20,-10,0,10,20]:
            y=tick*.06
            frame.add(line(-5.5,y,5.5,y,MUTED if tick==0 else GRID,2 if tick==0 else 1),text(f'{tick:+d}' if tick else '0',-6,y,20,MUTED))
        for i,key in enumerate(KEYS):
            v=float(costs[key]['extra_vs_sgov']);x=-3.7+i*3.7;y=v*.06
            frame.add(m.Rectangle(width=1.5,height=abs(y),fill_color=COLORS[i],fill_opacity=1,stroke_width=0).move_to([x,y/2,0]),
                      text(f'USD {v:+.0f}',x,y+(.3 if y>0 else -.3),27,COLORS[i]),
                      text(['Aave V4','Steakhouse V2','Gauntlet V2'][i],x,-1.9,23))
        frame.add(text('If rates stayed constant — not a forecast',0,1.8,26),
                  text('Each side: DeFi USD 10 + 5 bp; SGOV 0.5 bp',0,-2.6,22,MUTED),
                  text('USDC at par; rewards/tax excluded. SEC yield converted for compounding.',0,-3.12,18,MUTED))
        self.play(m.FadeIn(frame),run_time=.6);self.wait(7.1);self.play(m.FadeOut(frame),run_time=.6)
        # 20.3–31.3: current liquidity and clearly separate historical context.
        frame=heading('Shared cash can limit withdrawals','Current reported USDC amounts · not guaranteed withdrawals')
        labels=['Aave V4 Core Hub','Morpho V2 Steakhouse','Morpho V2 Gauntlet']
        for i,key in enumerate(KEYS):
            y=1.55-i*.78;amount=float(rates[key]['available_usdc'])/1e6
            frame.add(text(labels[i],-3.2,y,25,COLORS[i]),text(f'{amount:.2f}m USDC',1.3,y,28,COLORS[i]),
                      text('shared pool cash' if i==0 else 'reported access',4.25,y,20,MUTED))
        frame.add(text('Morpho amounts may overlap: do not add them.',0,-.84,20,MUTED),
                  text('SGOV: sell during market hours; cash settles the next business day.',0,-1.19,18,MUTED),
                  line(-5.8,-1.55,5.8,-1.55),
                  text('April example: older Aave V3, not V4',0,-1.94,24),
                  text(f"Aave V3 Core: {float(old['capacity_usdc']):,.0f} USDC available on 21 April 2026",0,-2.5,24),
                  text('Low available cash does not establish that depositors lost money.',0,-3.1,19,MUTED))
        self.play(m.FadeIn(frame),run_time=.6);self.wait(9.8);self.play(m.FadeOut(frame),run_time=.6)
        # 31.3–38.1: a concise product conclusion.
        closing=m.VGroup(text('Fees can erase the extra earnings.',0,2.4,38),
            text('Better apps should make two things clear:',0,1.25,25,MUTED),
            text('Earnings after fees',0,.5,32),
            text('What could delay getting your money back',0,-.16,30),
            text('Notebook · code · data',0,-1.4,23,MUTED),
            text('github.com/fredLuv/defi-lending-research',0,-2.15,30,'#3476A8'))
        self.play(m.FadeIn(closing),run_time=.8);self.wait(6)
