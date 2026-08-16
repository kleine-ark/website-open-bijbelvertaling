#!/usr/bin/env python3
"""Publiceer TR-woordnummers voor een hoofdstuk uit Romeinen."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from rebuild_johannes2_tr_strongs import mapping,r
from rebuild_nt_tr_strongs import load_tr_chapter
ROOT=Path(__file__).resolve().parents[1]
def build(utr:Path,osis:Path,chapter_number:int,write:bool=False)->dict[str,int]:
 s=load_tr_chapter(utr,osis,chapter=chapter_number,osis_book="Rom");p=ROOT/"data"/"romeinen"/f"{chapter_number}.json";d=json.loads(p.read_text(encoding="utf-8"));q={"book":"romeinen","chapter":chapter_number,"reviewed_through":len(s),"verses":{}}
 for v in d["verses"]:
  n=int(v["number"])
  if n not in s:
   v["grondtekst"]=[];v["woordnummers"]=[];continue
  t=s[n];ids=r(0,len(t)-1);a=v["text2026"];v["grondtekst"]=[{"woord":x["woord"],"strongs":x["display_strong"],"lemma_strongs":x["lemma_strong"],"morfologie":x["morphology"]}for x in t];v["woordnummers"]=[mapping(a,ids,t,n)];v["woordnummers"][0]["herkomst"]["referentie"]=f"ROM {chapter_number}:{n}";q["verses"][str(n)]=[{"tekst":a,"bronindices":ids,"reviewstatus":"handmatig_gecontroleerd"}]
 if write:
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");(ROOT/"data"/"woordnummers-review"/f"romeinen-{chapter_number}.json").write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");ip=ROOT/"data"/"woordnummers-inline"/"romeinen.json";i=json.loads(ip.read_text(encoding="utf-8"));i[str(chapter_number)]=q;ip.write_text(json.dumps(i,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return {"verses":len(s),"tokens":sum(len(x)for x in s.values())}
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--utr",type=Path,required=True);a.add_argument("--osis",type=Path,required=True);a.add_argument("--chapter",type=int,required=True);a.add_argument("--write",action="store_true");z=a.parse_args();print(json.dumps(build(z.utr,z.osis,z.chapter,z.write),indent=2))
