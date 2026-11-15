# -*- coding: utf-8 -*-
"""Bulk website screenshots for all_leads.py (2026-11-15): ONE headless Chromium, 24 tabs in parallel, reuses the
popup, consent, bot check and blank logic of shot.py. Writes <TEMP>/advshots/<domain-key>_1.jpg (+ _meta.json with
final url, title, first text for the parked/dead page filter) or <domain-key>.fail. Rerun-safe: skips what exists.
"""
import asyncio, json, os, re, sys
SHOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'shot.py')
src=open(SHOT,encoding='utf-8').read(); src=src[:src.index('async def main')]
src=src.replace('slug, out = sys.argv[1], sys.argv[2]; urls = sys.argv[3:]','').replace('os.makedirs(out, exist_ok=True)','')
g={'__name__':'x'}; exec(src,g)
from playwright.async_api import async_playwright
from PIL import Image
RAW=os.environ['TEMP']+r'\advshots'
L=json.load(open(r'C:\Users\Thomas\Desktop\AIOS\brain\notes\sales-resources\adverdict\leads.json',encoding='utf-8'))
dk=lambda d:re.sub(r'[^a-z0-9]+','-',re.sub(r'^https?://(www\.)?','',d.lower()).split('/')[0]).strip('-')
doms={dk(l['domain']):'https://'+l['domain'] for l in L if l['domain']}
todo=[(k,u) for k,u in doms.items() if not os.path.exists(f'{RAW}/{k}_1.jpg') and not os.path.exists(f'{RAW}/{k}.fail')]
print('todo',len(todo),flush=True)
async def load(pg,u):
    try: await pg.goto(u,wait_until='domcontentloaded',timeout=25000)
    except Exception: return False
    try: await pg.wait_for_load_state('networkidle',timeout=6000)
    except Exception: pass
    await pg.wait_for_timeout(1500)
    for n in range(4):
        t,x=await g['ev'](pg,g['HEAD_JS'],['',''])
        if len(x)>=1500 or not g['CHALLENGE'].search(t+' '+x): return True
        await pg.wait_for_timeout(2500)
    return False
done=0
async def one(b,k,u,sem):
    global done
    async with sem:
        ctx=None
        try:
            ctx=await b.new_context(viewport={'width':1440,'height':900},user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',locale='en-US',ignore_https_errors=True)
            pg=await ctx.new_page()
            ok=await asyncio.wait_for(load(pg,u),60)
            if ok:
                await asyncio.wait_for(g['consent'](pg),15)
                await g['ev'](pg,g['KILL'],0); await g['ev'](pg,'window.scrollTo(0,0)',0); await pg.wait_for_timeout(700)
                png=f'{RAW}/{k}_1.png'; await pg.screenshot(path=png,timeout=20000)
                im=Image.open(png).convert('RGB'); im=im.crop((0,0,im.width,int(im.width*0.625))).resize((1200,750),Image.LANCZOS)
                if g['blank'](png): ok=False
                else: im.save(f'{RAW}/{k}_1.jpg',quality=86)
                os.remove(png)
                if ok:
                    t,x=await g['ev'](pg,g['HEAD_JS'],['',''])
                    json.dump({'url':pg.url,'title':t,'text':x[:600]},open(f'{RAW}/{k}_meta.json','w',encoding='utf-8'),ensure_ascii=False)
        except Exception as e: ok=False
        finally:
            if ctx:
                try: await asyncio.wait_for(ctx.close(),10)
                except Exception: pass
        if not ok: open(f'{RAW}/{k}.fail','w').write(u)
        done+=1
        if done%100==0: print(done,flush=True)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--disable-blink-features=AutomationControlled','--no-sandbox'])
        sem=asyncio.Semaphore(24)
        await asyncio.gather(*[one(b,k,u,sem) for k,u in todo])
        await b.close()
    print('FINISHED',flush=True)
asyncio.run(main())
