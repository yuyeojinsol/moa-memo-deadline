import streamlit as st,os,pandas as pd
from datetime import datetime
from parser import parse
from classify import classify_all
from ics import to_ics
st.set_page_config(page_title="모아 - 나에게 보내기 정리기",page_icon="📌",layout="wide")
st.title("📌 모아 · 던져두기만 해, 마감은 내가 챙길게")
st.caption("노션처럼 '정리하는 앱'이 아니라, 정리 없이 쌓인 메모에서 **마감만 뽑아 캘린더로** 보냅니다. 가입·정리 습관 불필요.")
NAMES={'todo':'✅ 할일','event':'📅 일정','link':'🔗 링크','idea':'💡 아이디어','etc':'🗂 기타'}
with st.sidebar:
    st.markdown("**사용법**\n1. 카톡 '나에게 보내기' 대화 내보내기(.txt)\n2. 업로드\n3. 확인·수정\n4. .ics 다운로드")
    use_llm=st.toggle("AI 분류 사용",value=bool(os.getenv('LLM_API_KEY')),help="LLM_API_KEY 없으면 규칙 기반으로 동작")
    st.info("🔒 전화·계좌번호는 AI 전송 전 마스킹, 원문은 저장하지 않습니다.")
    sample=st.button("예시 데이터로 체험")
f=st.file_uploader("카톡 대화 txt",type=["txt"])
text=None
if sample: text=open("sample.txt",encoding="utf-8").read()
elif f:
    try: text=f.getvalue().decode("utf-8-sig")
    except UnicodeDecodeError: st.error("UTF-8 txt 파일만 지원해요. 카톡에서 '텍스트로 내보내기'를 사용하세요.")
if text is not None:
    msgs=parse(text)
    if not msgs: st.error("메시지를 찾지 못했어요. 카톡 내보내기 형식(안드로이드/iOS/PC)인지 확인해 주세요.")
    else:
        items=classify_all(msgs,use_llm); st.session_state['items']=items
if 'items' in st.session_state:
    items=st.session_state['items']
    due=sorted([i for i in items if i['due']],key=lambda x:x['due'])
    c1,c2,c3=st.columns(3); c1.metric("전체 메모",len(items)); c2.metric("마감/일정 감지",len(due))
    c3.metric("⚠ 7일 내 임박",sum(1 for i in due if 0<=(i['due']-datetime.now()).days<7))
    st.subheader("⏰ 마감 타임라인 (임박 순)")
    for i in due[:8]: st.write(f"**{i['due']:%m/%d %a %H:%M}** · {NAMES[i['type']]} · {i['title']}")
    st.divider()
    tabs=st.tabs([f"{v} ({sum(1 for i in items if i['type']==k)})" for k,v in NAMES.items()])
    for t,k in zip(tabs,NAMES):
        with t:
            rows=[i for i in items if i['type']==k]
            if not rows: st.write("없음"); continue
            rows.sort(key=lambda x:(x['due'] is None,x['due'] or x['sent']))
            df=pd.DataFrame([{'유형':NAMES[k],'제목':r['title'],'마감':r['due'],'원문':r['raw']} for r in rows])
            ed=st.data_editor(df,column_config={'유형':st.column_config.SelectboxColumn(options=list(NAMES.values()))},key=f"e{k}",use_container_width=True,hide_index=True)
            for r,(_,e) in zip(rows,ed.iterrows()):
                r['title']=e['제목']; r['due']=None if pd.isna(e['마감']) else pd.Timestamp(e['마감']).to_pydatetime()
                r['type']=[a for a,b in NAMES.items() if b==e['유형']][0]
    ok=[i for i in items if i['due']]
    st.download_button(f"📆 캘린더(.ics) 내보내기 ({len(ok)}건, 하루 전 알림 포함)",to_ics(ok),"deadlines.ics","text/calendar",disabled=not ok)
