"""Build one AdVerdict deck per spec: py build.py specs/<slug>.json -> ../<slug>/index.html

Same engine as the SharePay / VistaMails decks (reveal.js 1280x720, phone mode), AdVerdict copy and colours
(bg #0c0a09, cream #f4f1ea, emerald #34d399, Archivo / Inter / JetBrains Mono, taken from adverdict.io).
4 slides: Cover (AdVerdict x lead, verdict card), How we work (the message 1 offer), Stickytales proof, Let's talk (Calendly).

Spec fields (JSON):
  slug          folder name and URL part (required), <company>-<first>-<last> via tools/slug.py
  company       lead company as it reads in text (required)
  first_name, last_name   cover: "Prepared for <first> <last>, <company>"
  sender        optional, default "Mykolas Belickas": the LinkedIn account that sent the message. Its first name picks
                the last-slide photo (PHOTOS: mykolas.jpg, augustas.jpg in assets/img). Mykolas Belickas leads: sender default. Augustas Labanauskas leads: "sender": "Augustas Labanauskas".
  shot          cover screenshot in assets/shots/, made by tools/shot.py (py tools/shot.py <slug> ../assets/shots https://<domain>);
                no shot = verdict card
  domain        optional, the lead's site (only needed for tools/logo.py)
  logo          optional, file in assets/leadlogos/, ALWAYS made by tools/logo.py
                (py tools/logo.py <slug> "<Company>" https://<domain> --bg #0c0a09 --out ../assets/leadlogos --preview ../assets/leadlogos/_preview --spec specs/<slug>.json --badge-key logo_badge --on-none remove)
                No logo = company name in text.
  logo_badge    true = logo on a white badge
  cover_line    optional, default "30% more revenue for <company>, here is how."
  proof_head    optional, default "What it did for Stickytales."
  booking_url   optional, default Mykolas's Calendly
"""
import json, sys, os, html
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
BG = '#0c0a09'
BOOK = 'https://calendly.com/belickas-mykolas'
# sender = the LinkedIn account the lead talks to; the last slide shows that person's photo (assets/img/)
PHOTOS = {'mykolas': 'mykolas.jpg', 'augustas': 'augustas.jpg'}
O_HEAD = ("We plug {co} into the same delivery ecosystem we built for Stickytales. Every client gets a branded AdVerdict workspace: "
          "their ads, spend and ROAS in one place, a Scale, Hold or Kill verdict on every new ad each morning with the evidence "
          "behind it, and our team on hand to act on it. Clients see the work, stay longer and buy more.")
O_TARGET = "30% more revenue for {co}, from keeping and upselling the clients you already have."
O_COND = "A guaranteed model: you pay for results, not for promises. Setup, support and consulting are done with you."
O_MISS = "No results, no pay."
for path in sys.argv[1:]:
    sp = json.load(open(path, encoding='utf-8'))
    e = html.escape
    for k in ('slug', 'company'):
        assert sp.get(k), f'{path}: missing {k}'
    co = e(sp['company'])
    name = ' '.join(x for x in (sp.get('first_name', '').strip(), sp.get('last_name', '').strip()) if x)
    prep = f"{e(name)}, {co}" if name else co
    mark = f'<span class="co">{co}</span>'
    if sp.get('logo'):
        lp = os.path.join(ROOT, 'assets', 'leadlogos', sp['logo'])
        assert os.path.exists(lp), f'{path}: logo file missing'
        sys.path.insert(0, os.path.join(HERE, 'tools')); from logo import guard
        bad = guard(lp, BG, sp.get('logo_badge'))
        assert not bad, f"{path}: logo {sp['logo']} is {bad}. Run tools/logo.py (see the docstring)."
        fb = "var s=document.createElement('span');s.className='co';s.textContent=this.alt;(this.closest('.llb')||this).replaceWith(s)"
        img = f'<img class="ll" src="../assets/leadlogos/{sp["logo"]}" alt="{co}" onerror="{fb}">'
        mark = f'<span class="llb">{img}</span>' if sp.get('logo_badge') else img
    sender = sp.get('sender') or 'Mykolas Belickas'
    photo = PHOTOS.get(sender.split()[0].lower())
    assert photo and os.path.exists(os.path.join(ROOT, 'assets', 'img', photo)), f'{path}: no photo for sender {sender} in assets/img'
    if sp.get('shot'):
        assert os.path.exists(os.path.join(ROOT, 'assets', 'shots', sp['shot'])), f'{path}: shot missing'
        vis = f'<figure class="site in"><img src="../assets/shots/{sp["shot"]}" alt=""><figcaption>{e(sp.get("domain", ""))}</figcaption></figure>'
    else:
        vis = ('<div class="vcard" aria-hidden="true"><div class="h"><span>Today&#39;s verdicts</span><span>' + co + '</span></div>'
               '<div class="vrow"><div><b>Client A · Spring launch</b><span>3.1× ROAS vs 1.8× median</span></div><span class="vp sc">Scale</span></div>'
               '<div class="vrow"><div><b>Client B · UGC test 04</b><span>day 3, inside normal variance</span></div><span class="vp ho">Hold</span></div>'
               '<div class="vrow"><div><b>Client C · Retargeting</b><span>0.6× ROAS, move the budget</span></div><span class="vp ki">Kill</span></div>'
               '<div class="ft">Every morning, in your client&#39;s own branded workspace.</div></div>')
    out = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
    for k, v in {'COMPANY': co, 'PREPARED': prep, 'CO_MARK': mark,
                 'COVER_LINE': e(sp.get('cover_line') or f"30% more revenue for {sp['company']}, here is how."),
                 'PROOF_HEAD': e(sp.get('proof_head') or "What it did for Stickytales."),
                 'O_HEAD': O_HEAD.format(co=co), 'O_TARGET': O_TARGET.format(co=co), 'O_COND': O_COND.format(co=co), 'O_MISS': O_MISS.format(co=co),
                 'SENDER': e(sender), 'SENDER_PHOTO': photo, 'COVER_VISUAL': vis, 'BOOKING_URL': sp.get('booking_url') or BOOK}.items():
        out = out.replace('{{' + k + '}}', v)
    assert '{{' not in out, path
    d = os.path.join(ROOT, sp['slug']); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(out)
    print('built', sp['slug'])
