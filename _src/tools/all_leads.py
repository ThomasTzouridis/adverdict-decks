# -*- coding: utf-8 -*-
"""Pre-build one AdVerdict deck for EVERY lead in the AdVerdict HeyReach campaigns (Thomas, 2026-11-15:
"if I ask for a presentation for this lead, it is already ready").

    py tools/all_leads.py pull            # HeyReach lists + Prospeo sheet -> leads.json (in OUT_DIR)
    py tools/all_leads.py shots           # screenshots of every lead website, 12 in parallel, rerun-safe
    py tools/all_leads.py build           # specs/<slug>.json for every lead ("auto" specs rewritten, hand-made ones untouched) + build all + index

Sources:
  HeyReach workspace AdVerdict (HEYREACH_ADVERDICT_API_KEY in AIOS .env): list 1150153 = campaign 728282 Mykolas Belickas,
  list 1150152 = campaign 728283 Augustas Labanauskas. HeyReach has no website, so the domain comes from the Prospeo
  sheet the leads were pulled from (matched on the personal LinkedIn URL).
  Company name = HeyReach custom field normalizedcompanyname (the name the LinkedIn message uses).
Shots: assets/shots/<domain-key>.jpg, one per domain (several leads of one company share it). No website or no
usable shot = the deck shows the verdict card on the cover.
Index (lead -> deck URL) goes to the sales resource folder, never into this public repo:
  AIOS\\brain\\notes\\sales-resources\\adverdict\\deck_index.csv (+ Drive Sales Resources / AdVerdict).
"""
import csv, json, os, re, subprocess, sys, urllib.request, concurrent.futures as cf
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); ROOT = os.path.dirname(SRC)
sys.path.insert(0, HERE); from slug import slug as mkslug
AIOS = r'C:\Users\Thomas\Desktop\AIOS'
OUT_DIR = os.path.join(AIOS, 'brain', 'notes', 'sales-resources', 'adverdict')
LISTS = [(1150153, 'Mykolas Belickas'), (1150152, 'Augustas Labanauskas')]
PROSPEO_SHEET = '1lh60dT36udhZtXwT3T-BdRzT_SOGJET5MbjMxbjcN4Q'   # Prospeo India Advertising-Marketing ... 2026-11-11
SHOTS = os.path.join(ROOT, 'assets', 'shots'); RAW = os.path.join(os.environ['TEMP'], 'advshots')
BASE = 'https://adverdict-cases.com/'


def env():
    return {k: v.strip().strip('"') for k, v in re.findall(r'^([A-Z0-9_]+)=(.*)$', open(os.path.join(AIOS, '.env'), encoding='utf-8').read(), re.M)}


def li(u):
    return re.sub(r'^https?://([a-z]{2,3}\.)?(www\.)?', '', (u or '').lower().split('?')[0].rstrip('/'))


def dkey(d):
    return re.sub(r'[^a-z0-9]+', '-', re.sub(r'^https?://(www\.)?', '', d.lower()).split('/')[0]).strip('-')


def cap(s):
    # all-lowercase names (netfitmedia) get a capital first letter on the deck; any other casing stays as written
    return s[:1].upper() + s[1:] if s and s == s.lower() else s


def pull():
    key = env()['HEYREACH_ADVERDICT_API_KEY']
    def post(p, b):
        r = urllib.request.Request('https://api.heyreach.io/api/public/' + p, data=json.dumps(b).encode(),
                                   headers={'X-API-KEY': key, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        return json.load(urllib.request.urlopen(r, timeout=60))
    sys.path.insert(0, AIOS); from google_auth import get_creds; from googleapiclient.discovery import build
    v = build('sheets', 'v4', credentials=get_creds()).spreadsheets().values().get(spreadsheetId=PROSPEO_SHEET, range="'Leads'").execute()['values']
    pm = {li(r.get('Person LinkedIn')): r for r in (dict(zip(v[0], x)) for x in v[1:])}
    leads = []
    for lid, sender in LISTS:
        off = 0
        while True:
            d = post('list/GetLeadsFromList', {'listId': lid, 'offset': off, 'limit': 1000}); it = d.get('items') or []
            for x in it:
                cf_ = {f.get('name'): f.get('value') for f in (x.get('customFields') or [])}
                p = pm.get(li(x['profileUrl']), {})
                dom = (p.get('Company Domain') or p.get('Company Website') or '').strip()
                leads.append({'sender': sender, 'first_name': (x.get('firstName') or '').strip(), 'last_name': (x.get('lastName') or '').strip(),
                              'company': cap((cf_.get('normalizedcompanyname') or x.get('companyName') or p.get('Company Name') or '').strip()),
                              'linkedin': x['profileUrl'], 'domain': re.sub(r'^https?://(www\.)?', '', dom).rstrip('/'), 'heyreach_id': x['id']})
            off += len(it)
            if not it or off >= d.get('totalCount', 0):
                break
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(leads, open(os.path.join(OUT_DIR, 'leads.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('leads', len(leads), 'with domain', sum(1 for l in leads if l['domain']))


def shots():
    # bulk_shot.py: one Chromium, 24 tabs (shot.py one process per site took ~3.5 h for 2,542 domains)
    subprocess.run(['py', os.path.join(HERE, 'bulk_shot.py')])


# parked, for sale, dead or placeholder pages never go on a cover (the deck falls back to the verdict card)
JUNK = re.compile(r"domain (is )?for sale|buy this domain|this domain (name )?(may be|is) for sale|parked (free|domain)|"
                  r"domain has expired|account (has been )?suspended|website (is )?(coming soon|under construction)|"
                  r"^\s*coming soon|under maintenance|404|page not found|not found|default (web )?page|index of /|"
                  r"welcome to nginx|apache2? .*default|it works!|hostinger|godaddy|site can.t be reached|"
                  r"launching soon|website expired|this site is not available|forbidden|access denied|error establishing|"
                  r"sample page|example page|hello world|registration has expired|is registered at|domain (has )?expired", re.I)
# a platform or builder given as the company domain shows the platform, not the lead (carrd.co -> carrd.com)
PLATFORM = re.compile(r"^(carrd|linktr|wix|wixsite|squarespace|webflow|facebook|instagram|linkedin|youtube|twitter|x|"
                      r"google|sites-google|business-site|blogspot|wordpress|medium|notion|beacons|godaddysites|"
                      r"hubspot|shopify|myshopify|behance|dribbble|upwork|fiverr|github|framer|vimeo|studio|canva|tumblr|"
                      r"substack|calendly|odoo)-(com|co|io|me|ee|so|site|website|page|net|org|in)$", re.I)


def bad_shot(k):
    if PLATFORM.search(k):
        return True
    m = os.path.join(RAW, k + '_meta.json')
    if not os.path.exists(m):
        return False
    j = json.load(open(m, encoding='utf-8'))
    if PLATFORM.search(dkey(j.get('url') or '')):
        return True   # framer.website redirected to framer.com: the builder's homepage, not the lead
    head = (j.get('title') or '') + ' ' + (j.get('text') or '')[:400]
    return bool(JUNK.search(head)) or len((j.get('text') or '').strip()) < 40


def build_all():
    from PIL import Image
    leads = json.load(open(os.path.join(OUT_DIR, 'leads.json'), encoding='utf-8'))
    bad = set(json.load(open(os.path.join(OUT_DIR, 'bad_shots.json')))) if os.path.exists(os.path.join(OUT_DIR, 'bad_shots.json')) else set()
    # one domain claimed by 3+ different companies is a platform (studio.com, vimeo.com), never a lead's own site
    cos = {}
    for l in leads:
        if l['domain']:
            cos.setdefault(dkey(l['domain']), set()).add(l['company'].lower())
    bad |= {k for k, v in cos.items() if len(v) >= 3}
    # copy usable raw shots into the repo, smaller (one per domain)
    for f in os.listdir(RAW) if os.path.isdir(RAW) else []:
        if f.endswith('_1.jpg'):
            k = f[:-6]; dst = os.path.join(SHOTS, k + '.jpg')
            if k in bad or bad_shot(k):
                if os.path.exists(dst):
                    os.remove(dst)   # a stricter filter later drops a shot copied by an earlier build
            elif not os.path.exists(dst):
                Image.open(os.path.join(RAW, f)).convert('RGB').resize((960, 600), Image.LANCZOS).save(dst, quality=78, optimize=True)
    used, rows, paths = {}, [], []
    # a hand-made spec for the same person wins (story-it-sabapathy-narayanan: HeyReach says Stickytales, the deck says Story It)
    hand = {}
    for f in os.listdir(os.path.join(SRC, 'specs')):
        j = json.load(open(os.path.join(SRC, 'specs', f), encoding='utf-8'))
        if not j.get('auto'):
            hand[(j.get('first_name', '').lower(), j.get('last_name', '').lower())] = j['slug']
    for l in leads:
        if not l['company']:
            continue
        s = base = hand.get((l['first_name'].lower(), l['last_name'].lower())) or mkslug(l['company'], l['first_name'], l['last_name']); n = 2
        while s in used and used[s] != l['linkedin']:
            s = f'{base}-{n}'; n += 1
        used[s] = l['linkedin']
        p = os.path.join(SRC, 'specs', s + '.json')
        # hand-made specs (no "auto") are never touched; auto specs are rewritten so a later shot or name fix lands
        if not os.path.exists(p) or json.load(open(p, encoding='utf-8')).get('auto'):
            sp = {'slug': s, 'company': l['company'], 'first_name': l['first_name'], 'last_name': l['last_name'], 'sender': l['sender'], 'auto': True}
            k = dkey(l['domain']) if l['domain'] else ''
            if k and k not in bad and os.path.exists(os.path.join(SHOTS, k + '.jpg')):
                sp.update(domain=l['domain'], shot=k + '.jpg')
            json.dump(sp, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        paths.append(p)
        sp = json.load(open(p, encoding='utf-8'))
        rows.append({'name': f"{l['first_name']} {l['last_name']}".strip(), 'company': sp['company'], 'sender': l['sender'],
                     'deck_url': BASE + s + '/', 'website_shot': 'yes' if sp.get('shot') else 'no (verdict card)',
                     'domain': l['domain'], 'linkedin': l['linkedin'], 'heyreach_id': l['heyreach_id']})
    for i in range(0, len(paths), 150):
        r = subprocess.run(['py', os.path.join(SRC, 'build.py')] + paths[i:i + 150], capture_output=True, text=True, encoding='utf-8')
        if r.returncode:
            sys.exit(r.stderr[-2000:])
    with open(os.path.join(OUT_DIR, 'deck_index.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print('built', len(paths), 'decks;', sum(1 for r in rows if r['website_shot'] == 'yes'), 'with website shot; index', len(rows), 'rows')


def find():
    """py tools/all_leads.py find <words>   -> every lead whose name, company, LinkedIn or domain contains all words"""
    q = [w.lower() for w in sys.argv[2:]]
    for r in csv.DictReader(open(os.path.join(OUT_DIR, 'deck_index.csv'), encoding='utf-8-sig')):
        hay = ' '.join(r.values()).lower()
        if all(w in hay for w in q):
            print(f"{r['name']} | {r['company']} | {r['sender']} | {r['deck_url']} | shot: {r['website_shot']}")


if __name__ == '__main__':
    {'pull': pull, 'shots': shots, 'build': build_all, 'find': find}[sys.argv[1]]()
