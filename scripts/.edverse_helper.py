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
"""
import json, re, difflib, sys

def strip_html(s):
    s=re.sub(r'<sup[^>]*>.*?</sup>','',s); s=re.sub(r'<[^>]+>','',s)
    return re.sub(r'\s+',' ',s).strip()
def norm(k): return (re.sub(r'^[^\w]+|[^\w]+$','',k[0]), re.sub(r'^[^\w]+|[^\w]+$','',k[1]))

spec=json.load(sys.stdin)
book=spec["book"]
extra={norm((e[0],e[1])):e[2] for e in spec.get("extra",[])}

# new principes
if spec.get("new_principes"):
    P="data/wijzigingsprincipes.json"; pj=json.load(open(P,encoding="utf-8"))
    have={it["id"] for it in pj["principes"]}
    added=[]
    for np in spec["new_principes"]:
        if np["id"] not in have:
            pj["principes"].append(np); added.append(np["id"])
    if added:
        json.dump(pj,open(P,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
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
    path=f"data/{book}/{ch}.json"; d=json.load(open(path,encoding="utf-8"))
    verses={str(v["number"]):v for v in d["verses"]}
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
    json.dump(d,open(path,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("DONE")
