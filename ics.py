from datetime import timedelta
def to_ics(items):
    L=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//memo-to-deadline//KO"]
    for n,i in enumerate(items):
        if not i['due']: continue
        d=i['due'];f=lambda x:x.strftime('%Y%m%dT%H%M%S')
        L+=["BEGIN:VEVENT",f"UID:{n}-{f(d)}@memo",f"DTSTAMP:{f(i['sent'])}",f"DTSTART:{f(d)}",f"DTEND:{f(d+timedelta(hours=1))}",f"SUMMARY:{i['title']}",
            "BEGIN:VALARM","TRIGGER:-P1D","ACTION:DISPLAY","DESCRIPTION:마감 하루 전","END:VALARM","END:VEVENT"]
    return "\r\n".join(L+["END:VCALENDAR"])
