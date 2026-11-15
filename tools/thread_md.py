import json,re,sys,os
src,out=sys.argv[1:3]
turns=[]
def clean_user(t):
    t=re.sub(r'<system-reminder>.*?</system-reminder>','',t,flags=re.S)
    t=re.sub(r'@"?/root/\.claude/uploads/[^/\s"]+/([0-9a-f]{8}-)?([^"\n]+?)"?(?=\s|$)',lambda m:f'[uploaded file: {m.group(2)}]',t)
    return t.strip()
with open(src) as f:
    for line in f:
        d=json.loads(line)
        if d.get('type') not in ('user','assistant') or d.get('isMeta') or d.get('isCompactSummary') or d.get('isSidechain'): continue
        c=d.get('message',{}).get('content')
        if d['type']=='user':
            if not isinstance(c,str): continue          # tool results
            t=clean_user(c)
            if not t or t.startswith('[Request interrupted') or 'This session is being continued' in t: continue
            turns.append(['You',d.get('timestamp',''),[t]])
        else:
            if not isinstance(c,list): continue
            txt='\n\n'.join(x['text'].strip() for x in c if x.get('type')=='text' and x.get('text','').strip())
            if not txt: continue
            txt=re.sub(r'(?m)^(#{1,4}) ',lambda m:'#'*min(6,len(m.group(1))+2)+' ',txt)
            if turns and turns[-1][0]=='Claude': turns[-1][2].append(txt)
            else: turns.append(['Claude',d.get('timestamp',''),[txt]])
L=['# L5P Duramax SOTF tuning thread','',
   'Conversation between you and Claude about the GM E41 L5P stock P1B, HPT SOTF 9843 and 9844 (10-29 and 11-10-26 V2) files.',
   'Only the visible messages are included: tool calls, tool output and internal notes are left out. One response that an automated safety check stopped was withheld and is not part of this record.','']
n=0
for who,ts,parts in turns:
    if who=='You': n+=1; L+=['---','',f'## {n}. You' + (f'  ·  {ts[:16].replace("T"," ")} UTC' if ts else ''),'']
    else: L+=['### Claude','']
    L+=['\n\n'.join(parts),'']
open(out,'w').write('\n'.join(L))
print(n,'user turns,',sum(1 for t in turns if t[0]=='Claude'),'Claude turns ->',out)
