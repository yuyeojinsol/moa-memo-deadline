import re
from datetime import datetime
# Android: "2026년 11월 3일 오후 3:20, 나 : 내용" / PC: "[나] [오후 3:20] 내용" + 날짜 헤더 / iOS: "2026. 11. 3. 15:20, 나 : 내용"
A=re.compile(r'^(\d{4})년 (\d{1,2})월 (\d{1,2})일 (오전|오후) (\d{1,2}):(\d{2}), (.+?) : (.*)$')
I=re.compile(r'^(\d{4})\. (\d{1,2})\. (\d{1,2})\. (\d{1,2}):(\d{2}), (.+?) : (.*)$')
H=re.compile(r'^-+\s*(\d{4})년 (\d{1,2})월 (\d{1,2})일.*-+$')
P=re.compile(r'^\[(.+?)\] \[(오전|오후) (\d{1,2}):(\d{2})\] (.*)$')
def _h(ap,h):
    h=int(h)%12
    return h+12 if ap=='오후' else h
def parse(text):
    msgs=[];cur=None;day=None
    for line in text.splitlines():
        line=line.rstrip()
        m=A.match(line)
        if m:
            y,mo,d,ap,h,mi,_,c=m.groups(); cur={'sent':datetime(int(y),int(mo),int(d),_h(ap,h),int(mi)),'text':c}; msgs.append(cur);continue
        m=I.match(line)
        if m:
            y,mo,d,h,mi,_,c=m.groups(); cur={'sent':datetime(int(y),int(mo),int(d),int(h),int(mi)),'text':c}; msgs.append(cur);continue
        m=H.match(line)
        if m: day=tuple(map(int,m.groups()));cur=None;continue
        m=P.match(line)
        if m and day:
            _,ap,h,mi,c=m.groups(); cur={'sent':datetime(*day,_h(ap,h),int(mi)),'text':c}; msgs.append(cur);continue
        if cur and line.strip(): cur['text']+='\n'+line
    return msgs
