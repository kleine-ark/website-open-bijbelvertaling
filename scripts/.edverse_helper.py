#!/usr/bin/env python3
"""Reusable verse-editor: applies text edits, regenerates phraseDiff (project's
difflib convention), optionally adds new principes. Spec via stdin JSON:
{
 "book":"romeinen",
 "new_principes":[{"id":"V794",...}],
 "extra":[["old","new","principe_or_null"],...],   # principe hints for new (old,new) pairs
 "edits":{"21":[["derzelve","daarvan"]], ...}      # chapter -> list of [old,new] (html+text)
}
Idempotent: skips an edit whose 'old' is absent. Only replaces in text2026_html + text2026.

Schrijft een bestand alleen terug als er echt iets veranderd is, en houdt de
opmaak van het origineel aan: de repo mengt inspringing van 1 en 2 spaties, en
wijzigingsprincipes.json staat op CRLF terwijl de databestanden LF gebruiken.
Zonder die twee controles herschrijft elke kleine wijziging het hele bestand en
is de diff niet meer te lezen.
"""
import json, re, difflib, sys

def strip_html(s):
    s=re.sub(r'<sup[^>]*>.*?</sup>','',s); s=re.sub(r'<[^>]+>','',s)
    return re.sub(r'\s+',' ',s).strip()
def norm(k): return (re.sub(r'^[^\w]+|[^\w]+$','',k[0]), re.sub(r'^[^\w]+|[^\w]+$','',k[1]))

def lees(pad):
    """Leest JSON en onthoudt hoe het bestand eruitzag."""
    ruw=open(pad,encoding="utf-8",newline="").read()
    m=re.search(r'\n( +)"',ruw)
    return json.loads(ruw), {
        "indent": len(m.group(1)) if m else 2,
        "newline": "\r\n" if "\r\n" in ruw else "\n",
        "eindregel": ruw.endswith("\n"),
    }

def schrijf(pad, data, vorm):
    tekst=json.dumps(data,ensure_ascii=False,indent=vorm["indent"])
    if vorm["eindregel"]: tekst+="\n"
    if vorm["newline"]!="\n": tekst=tekst.replace("\n",vorm["newline"])
    open(pad,"w",encoding="utf-8",newline="").write(tekst)

spec=json.load(sys.stdin)
book=spec["book"]
extra={norm((e[0],e[1])):e[2] for e in spec.get("extra",[])}

# new principes
if spec.get("new_principes"):
    P="data/wijzigingsprincipes.json"; pj,vorm=lees(P)
    have={it["id"] for it in pj["principes"]}
    added=[]
    for np in spec["new_principes"]:
        if np["id"] not in have:
            pj["principes"].append(np); added.append(np["id"])
    if added:
        schrijf(P,pj,vorm)
        print("ADDED principes:", added, "total", len(pj["principes"]))

def regen(sv,ov,old_pd):
    pmap={norm((e["old"],e["new"])):e.get("principe") for e in old_pd}; pmap.update(extra)
    a=sv.split(); b=ov.split(); out=[]
    for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b).get_opcodes():
        if tag=='equal': continue
        old=" ".join(a[i1:i2]); new=" ".join(b[j1:j2])
        if old or new: out.append({"old":old,"new":new,"principe":pmap.get(norm((old,new)))})
    return out

for ch, edits in spec["edits"].items():
    path=f"data/{book}/{ch}.json"; d,vorm=lees(path)
    verses={str(v["number"]):v for v in d["verses"]}
    gewijzigd=False
    # edits keyed by verse number
    for vnum, pairs in edits.items():
        v=verses.get(str(vnum))
        if not v: print("!! no verse", ch, vnum); continue
        touched=False
        for o,n in pairs:
            if o in v["text2026_html"]:
                v["text2026_html"]=v["text2026_html"].replace(o,n)
                v["text2026"]=v["text2026"].replace(o,n); touched=True
            else:
                print(f"  -- skip {ch}:{vnum} '{o}' (absent)")
        if touched:
            v["phraseDiff"]=regen(strip_html(v.get("textSV1888","")),strip_html(v["text2026"]),v.get("phraseDiff",[]))
            print(f"{ch}:{vnum}: {v['text2026']}")
            gewijzigd=True
    if gewijzigd: schrijf(path,d,vorm)
    else: print(f"  -- {path} ongewijzigd, niet herschreven")
print("DONE")
