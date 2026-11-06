from parser import parse
from classify import classify_all
def test_sample():
    r={i['raw']:i for i in classify_all(parse(open('sample.txt',encoding='utf-8').read()))}
    assert r['내일 3시 국 회의']['type']=='event' and str(r['내일 3시 국 회의']['due'])=='2026-11-04 15:00:00'
    assert r['보고서 써야됨 금욜까지']['due'].weekday()==4
    assert r['보고서 써야됨']['due'] is None
    assert r["앱 이름 '모아' 어때"]['type']=='idea' and r['ㅋㅋ']['type']=='etc'
