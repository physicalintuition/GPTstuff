#!/usr/bin/env python3
"""Refresh the Research Radar feeds from verified source candidates."""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import requests
from openai import OpenAI

TODAY = dt.datetime.now(dt.timezone.utc).date()
ROOT = Path(__file__).resolve().parents[1] / "data"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
CATS = ("gr-qc", "hep-th", "quant-ph", "astro-ph.CO", "astro-ph.HE")
COUNTRIES = ("Austria", "Germany", "Slovenia", "Slovakia", "Czechia", "Czech Republic", "Switzerland")
TERMS = {"q-desic":20,"geodesic":7,"autoparallel":12,"nonmetricity":14,
         "metric-affine":13,"christoffel":14,"connection operator":20,
         "expectation value":10,"metric operator":20,"quantum spacetime":14,
         "quantum geometry":10,"spherically symmetric":12,"spherical symmetry":8,
         "schwarzschild":11,"minisuperspace":15,"canonical quantization":14,
         "canonical quantisation":14,"operator ordering":12,
         "semiclassical gravity":9,"quantum gravity":4,
         "gravitational spin hall":11,"neutron gravitational":15,
         "quantum fluctuation":8,"photon sphere":8,"killing vector":9}
PAPER_PROMPT = """
Review recent candidate arXiv abstracts as a research specialist for Benjamin Koch.
Select at most FIVE genuinely relevant papers, but ZERO is fine.
The TWO core strands are equally important:
(A) q-desics: effective particle motion using the expectation of quantum
connection operators, <Gamma-hat> vs Gamma(<g-hat>), nonmetricity, light,
symmetries and observables;
(B) canonical quantisation of static spherically symmetric geometries
(Koch and Riahinia, Quantum Uncertainties of Static Spherically Symmetric
Spacetimes, Universe 12(3):59, 2026): metric/connection operators,
quantum expectation values, uncertainties, ordering, Schwarzschild-(A)dS,
Heisenberg and Schrodinger representations.
Exclude generic black-hole, cosmological and quantum papers unless they
contribute something precisely to A or B.
Use only the candidate ID keys given below. In GERMAN give 2-4 accurate
sentences on each selected work's actual idea and a specific reason
it matters to A or B, clearly distinguishing your own interpretations.
Return ONLY a valid JSON object of this shape:
{"items":[{"id":"arxiv-NNNN-NNNNN","summary":"...","relevance":"...",
"topic":"..."}]}. No markdown. Do not invent claims or fill slots.
"""
JOB_PROMPT = """
You are a conservative academic opportunity analyst. WEB SEARCH for new,
current senior research jobs and grants, checking official sources such as
INSPIRE-HEP, EURAXESS, university sites, FWF, DFG, SNSF and ERC.
Researcher: habilitated theoretical physicist, internationally experienced,
working in quantum gravity, q-desics, canonical SER quantisation, GR,
black holes, modified/semiclassical gravity, neutron gravitational physics.
JOBS only if location-bound in AUSTRIA, GERMANY, SLOVENIA, SLOVAKIA,
CZECHIA or SWITZERLAND. Outside those countries ONLY fully remote positions
explicitly workable from a listed country. Prefer professorships,
permanent research positions, group leaders and senior fellowships;
no routine PhD / junior postdoc. GRANTS can be international if the person
can actually apply as PI or with a realistically suitable eligible host.
Avoid duplicate, expired, speculative or marginal matches.
Provide a direct, verifiable HTTPS link to the OFFICIAL page for every item.
Verify deadline and basic eligibility or exclude the item. For
continuously open programmes deadline is null.
Zero items is preferable to weak recommendations. Maximum FIVE new
opportunities combined. Return ONLY valid JSON, without markdown:
{"jobs":[{"title":"...","institution":"...","country":"Austria",
"url":"https://...","deadline":"YYYY-MM-DD or null",
"eligibility":"...","relevance":"...","notes":"..."}],
"grants":[{"title":"...","funder":"...","country":"...",
"url":"https://...","deadline":"YYYY-MM-DD or null",
"eligibility":"...","relevance":"...","notes":"..."}]}.
"""
def read(path, empty):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else empty

def publish(path, old, fresh):
    a = {k:v for k,v in old.items() if k != "updatedAt"}
    b = {k:v for k,v in fresh.items() if k != "updatedAt"}
    if a == b:
        print("No changes passed the relevance threshold:", path.name)
        return
    fresh["updatedAt"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    path.write_text(json.dumps(fresh,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Updated:",path)

def ask(client, prompt, web=False):
    options={"model":MODEL,"input":prompt,"reasoning":{"effort":"medium"}}
    if web:
        options.update({"tools":[{"type":"web_search"}],"tool_choice":"required"})
    response = client.responses.create(**options)
    raw=response.output_text.strip()
    if raw.startswith("~~~"): raw=raw.split("\n",1)[1].rsplit("~~~",1)[0].strip()
    if raw.startswith("json\n"):raw=raw[5:]
    # Refuse to modify feeds if the model fails to return pure JSON.
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Unparseable model report; old feed preserved") from exc

def arxiv(category):
    params={"search_query":"cat:"+category,"start":0,"max_results":125,
            "sortBy":"submittedDate","sortOrder":"descending"}
    for pause in (0,2,5):
        if pause:time.sleep(pause)
        try:
            response=requests.get("https://export.arxiv.org/api/query",params=params,
                                  timeout=35,headers={"User-Agent":"ResearchRadar/1.0"})
            response.raise_for_status()
            entries=ET.fromstring(response.content)
            ns={"a":"http://www.w3.org/2005/Atom"}
            rows=[]
            for e in entries.findall("a:entry",ns):
                link=e.findtext("a:id",default="",namespaces=ns)
                m=re.search(r"/abs/(\d{4}\.\d{4,5})(?:v\d+)?$",link)
                if not m:continue
                stamp=e.findtext("a:published",default="",namespaces=ns)[:10]
                try:date=dt.date.fromisoformat(stamp)
                except ValueError:continue
                if date<TODAY-dt.timedelta(days=10):continue
                title=" ".join(e.findtext("a:title",default="",namespaces=ns).split())
                abstract=" ".join(e.findtext("a:summary",default="",namespaces=ns).split())
                authors=", ".join(x.findtext("a:name",default="",namespaces=ns)
                                  for x in e.findall("a:author",ns))
                rows.append({"id":"arxiv-"+m.group(1).replace(".","-"),
                             "url":"https://arxiv.org/abs/"+m.group(1),
                             "title":title,"abstract":abstract,
                             "date":stamp,"authors":authors})
            return rows
        except (ET.ParseError,requests.RequestException) as exc:
            print("arXiv retry",category,exc,file=sys.stderr)
    return None

def paper_scan(client):
    path=ROOT/"papers.json"
    old=read(path,{"updatedAt":None,"items":[]})
    found={};working=0
    for category in CATS:
        entries=arxiv(category)
        if entries is None:continue
        working+=1
        for e in entries:found[e["id"]]=e
    if working<2:raise RuntimeError("arXiv unavailable: not overwriting the papers feed")
    seen={p["id"] for p in old.get("items",[]) if isinstance(p,dict) and p.get("id")}
    def score(entry):
        full=(entry["title"]+" "+entry["abstract"]).lower()
        return sum(weight for term,weight in TERMS.items() if term in full)
    candidates=sorted((e for e in found.values() if e["id"] not in seen and score(e)>=8),
                      key=score,reverse=True)[:50]
    if not candidates:
        print("No new candidate papers")
        return
    submitted=[{k:e[k] for k in ("id","title","authors","date","abstract")} for e in candidates]
    result=ask(client,PAPER_PROMPT+"\nCandidates:\n"+json.dumps(submitted,ensure_ascii=False))
    if not isinstance(result,dict) or not isinstance(result.get("items"),list):
        raise ValueError("Unexpected paper response structure")
    by_id={e["id"]:e for e in candidates}
    new=[]
    for x in result["items"][:5]:
        if not isinstance(x,dict) or x.get("id") not in by_id:continue
        summary=x.get("summary","");relevance=x.get("relevance","")
        if not isinstance(summary,str) or not isinstance(relevance,str):continue
        if len(summary.strip())<75 or len(relevance.strip())<65:continue
        base=by_id[x["id"]]
        row={k:base[k] for k in ("id","title","authors","date","url")}
        row.update({"summary":summary[:1500],"relevance":relevance[:1000],
                    "topic":str(x.get("topic",""))[:120],"priority":"High relevance"})
        new.append(row)
    if not new:
        print("No new preprints passed the high threshold")
        return
    merged=[];ids=set()
    for e in new+old.get("items",[]):
        if e.get("id") not in ids:
            ids.add(e["id"]);merged.append(e)
    publish(path,old,{"items":merged[:100]})

def check_url(url):
    if not isinstance(url,str):return False
    p=urlparse(url)
    if p.scheme!="https" or not p.hostname or p.username:return False
    if p.hostname.lower() in ("example.com","google.com","www.google.com"):return False
    if not p.path or p.path=="/":return False
    if any(p.hostname.lower().endswith(host) for host in ("facebook.com","linkedin.com","twitter.com","x.com")):return False
    return True

def date_or_none(value):
    try:return dt.date.fromisoformat(value) if value else None
    except (ValueError,TypeError):return None

def opportunities_scan(client):
    path=ROOT/"opportunities.json"
    old=read(path,{"updatedAt":None,"jobs":[],"grants":[]})
    titles=[e.get("title","") for kind in ("jobs","grants") for e in old.get(kind,[])]
    prompt=JOB_PROMPT+"\nDate: "+str(TODAY)+"\nAlready listed, do not repeat: "+json.dumps(titles,ensure_ascii=False)
    result=ask(client,prompt,web=True)
    if not isinstance(result,dict) or not isinstance(result.get("jobs"),list) or not isinstance(result.get("grants"),list):
        raise ValueError("Unexpected jobs/grants response structure")
    output={}
    remaining=5
    for kind in ("jobs","grants"):
        previous=old.get(kind,[])
        prior_urls={e.get("url","").rstrip("/") for e in previous}
        fresh=[]
        for x in result[kind]:
            if remaining<=0:break
            if not isinstance(x,dict):continue
            url=x.get("url");title=x.get("title")
            if not check_url(url) or not isinstance(title,str) or len(title)<8:continue
            if url.rstrip("/") in prior_urls:continue
            deadline=x.get("deadline")
            if deadline and (date_or_none(deadline) is None or date_or_none(deadline)<TODAY):continue
            if len(str(x.get("relevance","")))<65 or len(str(x.get("eligibility","")))<35:continue
            if kind=="jobs":
                location=str(x.get("country",""))
                valid=any(c.lower() in location.lower() for c in COUNTRIES)
                remote="fully remote" in str(x.get("notes","")).lower() and "remote" in location.lower()
                if not valid and not remote:continue
            code=hashlib.sha256(url.rstrip("/").encode()).hexdigest()[:14]
            clean={"id":kind+"-"+code,"title":title[:250],"url":url,
                   "priority":"High relevance","deadline":deadline}
            for key in ("country","institution","funder","eligibility","relevance","notes"):
                if isinstance(x.get(key),str):clean[key]=x[key][:1200]
            fresh.append(clean);remaining-=1
        # Keep existing programmes while open; remove dated expired listings.
        carry=[e for e in previous if not date_or_none(e.get("deadline")) or date_or_none(e["deadline"])>=TODAY]
        output[kind]=(fresh+carry)[:75]
    publish(path,old,output)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("feed",choices=("papers","opportunities"))
    args=p.parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY missing: set repository Actions secret.")
    client=OpenAI(timeout=180.0,max_retries=2)
    if args.feed=="papers":paper_scan(client)
    else:opportunities_scan(client)

if __name__=="__main__":
    main()
