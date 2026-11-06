import re,os,json
from datetime import datetime,timedelta
URL=re.compile(r'https?://\S+')
PHONE=re.compile(r'01[016-9][-\s]?\d{3,4}[-\s]?\d{4}')
ACCT=re.compile(r'\b\d{2,6}-\d{2,6}-\d{2,8}(?:-\d{1,4})?\b')
def mask(t): return ACCT.sub('[계좌]',PHONE.sub('[전화]',t))
WD={'월':0,'화':1,'수':2,'목':3,'금':4,'토':5,'일':6}
def extract_due(t,sent):
    """규칙 기반 마감 추출. 불분명하면 None (추측 금지)."""
    base=sent.date(); d=None
    if '모레' in t: d=base+timedelta(2)
    elif '내일' in t: d=base+timedelta(1)
    elif '오늘' in t: d=base
    else:
        m=re.search(r'(다음\s*주\s*)?([월화수목금토일])(?:요일|욜)',t)
        if m:
            wd=WD[m.group(2)]; d=base+timedelta((wd-base.weekday())%7 or 7)
            if m.group(1): d+=timedelta(7) if (d-base).days<7 else timedelta(0)
    m=re.search(r'(\d{1,2})/(\d{1,2})(?!\d)',t) or re.search(r'(\d{1,2})월\s*(\d{1,2})일',t)
    if m and not d:
        try:
            d=datetime(base.year,int(m.group(1)),int(m.group(2))).date()
            if d<base: d=d.replace(year=d.year+1)
        except ValueError: pass
    if not d: return None
    h,mi=None,0
    m=re.search(r'(오전|오후)?\s*(\d{1,2})시\s*(?:(\d{1,2})분|반)?',t)
    if m:
        h=int(m.group(2)); mi=int(m.group(3)) if m.group(3) else (30 if '반' in m.group(0) else 0)
        if m.group(1)=='오후' and h<12: h+=12
        elif not m.group(1) and 1<=h<=7: h+=12
    return datetime(d.year,d.month,d.day,h if h is not None else 23,mi if h is not None else 59), h is not None
TODO=re.compile(r'해야|써야|제출|과제|사야|신청|예약|까지|보내기|확인|준비|챙기')
IDEA=re.compile(r'어때|아이디어|하면 좋|만들면|해볼까|\?$')
EVENT=re.compile(r'회의|미팅|모임|면접|시험|수업|발표|약속|세미나|MT|행사|스터디|OT')
def rule(t,sent):
    urls=URL.findall(t); due=extract_due(t,sent)
    title=URL.sub('',t).strip().split('\n')[0][:60] or (urls[0] if urls else t[:60])
    if urls: typ='link'
    elif due and EVENT.search(t) and due[1]: typ='event'
    elif due or TODO.search(t): typ='todo'
    elif EVENT.search(t): typ='event'
    elif IDEA.search(t): typ='idea'
    else: typ='etc'
    if len(t.strip())<=3 and not urls: typ='etc'
    return {'type':typ,'title':title,'due':due[0] if due else None,'tags':[],'urls':urls}
def llm(batch):
    """선택: OpenAI 호환 API. 키가 없으면 None."""
    key=os.getenv('LLM_API_KEY')
    if not key: return None
    from openai import OpenAI
    c=OpenAI(api_key=key,base_url=os.getenv('LLM_BASE_URL','https://openrouter.ai/api/v1'))
    pr="각 메시지를 JSON {\"items\":[{\"i\":번호,\"type\":\"todo|event|link|idea|etc\",\"title\":str,\"due\":\"YYYY-MM-DD HH:MM\"|null,\"tags\":[str]}]}로 분류. 발신일 기준으로 상대날짜 변환, 불분명하면 due=null(추측 금지).\n"
    pr+="\n".join(f"{i}|발신 {m['sent']:%Y-%m-%d %a}|{mask(m['text'])}" for i,m in batch)
    try:
        r=c.chat.completions.create(model=os.getenv('LLM_MODEL','openai/gpt-4o-mini'),temperature=0,response_format={'type':'json_object'},messages=[{'role':'user','content':pr}])
        return {x['i']:x for x in json.loads(r.choices[0].message.content)['items']}
    except Exception: return None
def classify_all(msgs,use_llm=False):
    out=[];seen=set();ai={}
    if use_llm:
        for s in range(0,len(msgs),30): ai.update(llm(list(enumerate(msgs))[s:s+30]) or {})
    for i,m in enumerate(msgs):
        k=m['text'].strip()
        if k in seen: continue
        seen.add(k); r=rule(m['text'],m['sent'])
        a=ai.get(i)
        if a:
            try:
                r['type']=a['type'] if a['type'] in('todo','event','link','idea','etc') else r['type']
                r['title']=a.get('title') or r['title']; r['tags']=a.get('tags',[])
                r['due']=datetime.strptime(a['due'],'%Y-%m-%d %H:%M') if a.get('due') else None
            except Exception: pass
        if r['urls']: r['type']='link'   # URL은 정규식으로 확정
        r['sent']=m['sent'];r['raw']=m['text'];out.append(r)
    return out
