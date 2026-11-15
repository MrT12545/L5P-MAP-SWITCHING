"""Minimal PowerPC VLE (e200) disassembler for analysis. Big-endian."""
import struct
def sx(v,b): return v-(1<<b) if v&(1<<(b-1)) else v
R4=lambda x: x if x<8 else x+16          # 4-bit reg field: 0-7 -> r0-r7, 8-15 -> r24-r31
X31={0:'cmp',32:'cmpl',8:'subfc',10:'addc',11:'mulhwu',19:'mfcr',23:'lwzx',24:'slw',26:'cntlzw',28:'and',40:'subf',55:'lwzux',
     60:'andc',75:'mulhw',83:'mfmsr',87:'lbzx',104:'neg',119:'lbzux',124:'nor',131:'wrtee',136:'subfe',138:'adde',144:'mtcrf',
     146:'mtmsr',151:'stwx',163:'wrteei',183:'stwux',200:'subfze',202:'addze',215:'stbx',235:'mullw',247:'stbux',266:'add',
     279:'lhzx',284:'eqv',316:'xor',339:'mfspr',343:'lhax',407:'sthx',412:'orc',444:'or',459:'divwu',467:'mtspr',476:'nand',
     491:'divw',536:'srw',792:'sraw',824:'srawi',922:'extsh',954:'extsb',14:'e_cmph',46:'e_cmphl',56:'e_slwi',568:'e_srwi',
     280:'e_rlw',312:'e_rlwi',16:'e_mcrf',33:'e_crnor',129:'e_crandc',193:'e_crxor',225:'e_crnand',257:'e_crand',289:'e_creqv',
     417:'e_crorc',449:'e_cror',598:'msync',854:'mbar',470:'dcbi',86:'dcbf',54:'dcbst',982:'icbi',1014:'dcbz',375:'lhaux',
     311:'lhzux',439:'sthux',520:'subfc?',138+512:'adde?'}
SPE={704:'efsadd',705:'efssub',708:'efsabs',709:'efsnabs',710:'efsneg',712:'efsmul',713:'efsdiv',716:'efscmpgt',717:'efscmplt',
     718:'efscmpeq',720:'efscfui',721:'efscfsi',722:'efscfuf',723:'efscfsf',724:'efsctui',725:'efsctsi',728:'efsctuiz',730:'efsctsiz',
     732:'efststgt',733:'efststlt',734:'efststeq',727:'efsctsf',726:'efsctuf'}
def dis(buf,off,addr):
    h=struct.unpack_from('>H',buf,off)[0]; top=h>>12
    if top in (1,3,5,7):
        w=struct.unpack_from('>I',buf,off)[0]; return 4,dis32(w,addr)
    return 2,dis16(h,addr)
def dis16(h,addr):
    rx=R4(h&0xF); ry=R4((h>>4)&0xF)
    if h==0: return ('se_illegal',None)
    simple={1:'se_isync',2:'se_sc',4:'se_blr',5:'se_blrl',6:'se_bctr',7:'se_bctrl',8:'se_rfi'}
    if h in simple: return (simple[h],None)
    if (h>>8)==0:
        op={0x2:'se_not',0x3:'se_neg',0x8:'se_mflr',0x9:'se_mtlr',0xA:'se_mfctr',0xB:'se_mtctr',0xC:'se_extzb',0xD:'se_extsb',0xE:'se_extzh',0xF:'se_extsh'}.get((h>>4)&0xF)
        return (f'{op} r{rx}' if op else f'.short {h:#06x}',None)
    b0=h>>8
    rr={1:'se_mr',4:'se_add',5:'se_mullw',6:'se_sub',7:'se_subf',0xC:'se_cmp',0xD:'se_cmpl',0xE:'se_cmph',0xF:'se_cmphl',
        0x40:'se_srw',0x41:'se_sraw',0x42:'se_slw',0x44:'se_or',0x45:'se_andc',0x46:'se_and',0x47:'se_and.'}
    if b0 in rr: return (f'{rr[b0]} r{rx}, r{ry}',None)
    if b0==2: return (f'se_mtar r{(h&0xF)+8}, r{ry}',None)
    if b0==3: return (f'se_mfar r{rx}, r{((h>>4)&0xF)+8}',None)
    t=h&0xFE00; v5=(h>>4)&0x1F
    oim={0x2000:'se_addi',0x2200:'se_cmpli',0x2400:'se_subi',0x2600:'se_subi.'}
    if t in oim: return (f'{oim[t]} r{rx}, {v5+1}',None)
    im={0x2A00:'se_cmpi',0x2C00:'se_bmaski',0x2E00:'se_andi',0x6000:'se_bclri',0x6200:'se_bgeni',0x6400:'se_bseti',
        0x6600:'se_btsti',0x6800:'se_srwi',0x6A00:'se_srawi',0x6C00:'se_slwi'}
    if t in im: return (f'{im[t]} r{rx}, {v5}',None)
    if (h&0xF800)==0x4800: return (f'se_li r{rx}, {(h>>4)&0x7F}',None)
    top=h>>12
    if 8<=top<=0xD:
        sd=(h>>8)&0xF; rz=R4((h>>4)&0xF); nm,sc={8:('se_lbz',1),9:('se_stb',1),0xA:('se_lhz',2),0xB:('se_sth',2),0xC:('se_lwz',4),0xD:('se_stw',4)}[top]
        return (f'{nm} r{rz}, {sd*sc}(r{rx})',None)
    if (h>>11)==0b11100:
        bo=(h>>10)&1; bi=(h>>8)&3; t=addr+sx(h&0xFF,8)*2
        cond=['lt','gt','eq','so'][bi]; return (f"se_b{'' if bo else 'n'}{cond} {t:#x}",('bc',t))
    if (h>>9)==0b1110100:
        lk=(h>>8)&1; t=addr+sx(h&0xFF,8)*2; return (f"se_b{'l' if lk else ''} {t:#x}",('bl' if lk else 'b',t))
    return (f'.short {h:#06x}',None)
def sci8(w):
    ui=w&0xFF; scl=(w>>8)&3; f=(w>>10)&1; v=ui<<(8*scl)
    if f: v|=~(0xFF<<(8*scl))&0xFFFFFFFF; v&=0xFFFFFFFF
    return v
def dis32(w,addr):
    op=w>>26; rd=(w>>21)&31; ra=(w>>16)&31; d16=sx(w&0xFFFF,16)
    mem={12:'e_lbz',13:'e_stb',14:'e_lha',20:'e_lwz',21:'e_stw',22:'e_lhz',23:'e_sth'}
    if op in mem: return (f'{mem[op]} r{rd}, {d16:#x}(r{ra})' if d16>=0 else f'{mem[op]} r{rd}, -{-d16:#x}(r{ra})',('mem',ra,d16))
    if op==7: return (f'e_add16i r{rd}, r{ra}, {d16:#x}',('add16i',rd,ra,d16))
    if op==6:
        x4=(w>>12)&0xF
        if x4==0:
            x8=(w>>8)&0xFF; d8=sx(w&0xFF,8)
            nm={0:'e_lbzu',1:'e_lhzu',2:'e_lwzu',3:'e_lhau',4:'e_stbu',5:'e_sthu',6:'e_stwu',8:'e_lmw',9:'e_stmw'}.get(x8,f'e_d8?{x8:#x}')
            return (f'{nm} r{rd}, {d8}(r{ra})',None)
        v=sci8(w); rc='.' if (w>>11)&1 else ''
        if x4==8: return (f'e_addi{rc} r{rd}, r{ra}, {sx(v,32) if v&0x80000000 else v:#x}',('addi',rd,ra,sx(v,32)))
        if x4==9: return (f'e_addic{rc} r{rd}, r{ra}, {v:#x}',None)
        if x4==0xA:
            if (w>>11)&1:
                cl='e_cmpli' if (w>>21)&1 else 'e_cmpi'; return (f'{cl} cr{(w>>21)>>1&3}, r{ra}, {v:#x}',None)
            return (f'e_mulli r{rd}, r{ra}, {v:#x}',None)
        if x4==0xB: return (f'e_subfic{rc} r{rd}, r{ra}, {v:#x}',None)
        nm={0xC:'e_andi',0xD:'e_ori',0xE:'e_xori'}.get(x4,'e_sci8?')
        return (f'{nm}{rc} r{ra}, r{rd}, {v:#x}',None)
    if op==28:
        if not (w>>15)&1:
            li=sx((((w>>11)&0xF)<<16)|(((w>>16)&0x1F)<<11)|(w&0x7FF),20); return (f'e_li r{rd}, {li:#x}',('li',rd,li))
        xo=(w>>11)&0x1F; ui=(((w>>16)&0x1F)<<11)|(w&0x7FF); si=sx((((w>>21)&0x1F)<<11)|(w&0x7FF),16)
        nm={0b11000:'e_or2i',0b11001:'e_and2i.',0b11010:'e_or2is',0b11100:'e_lis',0b11101:'e_and2is.'}
        if xo in nm: return (f'{nm[xo]} r{rd}, {ui:#x}',(nm[xo],rd,ui))
        nm2={0b10001:'e_add2i.',0b10010:'e_add2is',0b10011:'e_cmp16i',0b10100:'e_mull2i',0b10101:'e_cmpl16i',0b10110:'e_cmph16i',0b10111:'e_cmphl16i'}
        if xo in nm2:
            v=si if xo not in (0b10101,0b10111) else ((((w>>21)&0x1F)<<11)|(w&0x7FF))
            return (f'{nm2[xo]} r{ra}, {v:#x}',(nm2[xo],ra,v))
        return (f'e_i16?{xo:#x} {w:#010x}',None)
    if op==29:
        sh=(w>>11)&31; mb=(w>>6)&31; me=(w>>1)&31
        return (f"{'e_rlwinm' if w&1 else 'e_rlwimi'} r{ra}, r{rd}, {sh}, {mb}, {me}",None)
    if op==30:
        if not (w>>25)&1:
            t=addr+sx((w>>1)&0xFFFFFF,24)*2; lk=w&1; return (f"e_b{'l' if lk else ''} {t:#x}",('bl' if lk else 'b',t))
        bo=(w>>20)&3; bi=(w>>16)&0xF; t=addr+sx((w>>1)&0x7FFF,15)*2; lk=w&1
        cond=['lt','gt','eq','so'][bi&3]; cr=bi>>2
        bon={0:'n',1:'',2:'dnz',3:'dz'}[bo]
        m=f"e_b{'dnz' if bo==2 else ('dz' if bo==3 else bon+cond)}{'l' if lk else ''} {'cr%d,'%cr if cr and bo<2 else ''}{t:#x}"
        return (m,('bc',t))
    if op==31:
        xo=(w>>1)&0x3FF; rb=(w>>11)&31; nm=X31.get(xo,f'x31?{xo}')
        if nm=='mfspr' or nm=='mtspr':
            spr=((w>>16)&31)|(((w>>11)&31)<<5); return (f'{nm} r{rd}, spr{spr}',None)
        if nm in ('cmp','cmpl','e_cmph','e_cmphl'): return (f'{nm} cr{rd>>2}, r{ra}, r{rb}',None)
        if nm=='or' and rd==rb: return (f'mr r{ra}, r{rd}',None)
        if nm in ('and','or','xor','slw','srw','sraw','andc','nor','nand','orc','eqv','e_rlw'): return (f"{nm}{'.' if w&1 else ''} r{ra}, r{rd}, r{rb}",None)
        if nm in ('extsb','extsh','cntlzw'): return (f'{nm} r{ra}, r{rd}',None)
        if nm in ('srawi','e_slwi','e_srwi','e_rlwi'): return (f'{nm} r{ra}, r{rd}, {rb}',None)
        return (f"{nm}{'.' if w&1 else ''} r{rd}, r{ra}, r{rb}",None)
    if op==4:
        xo=w&0x7FF; rb=(w>>11)&31; nm=SPE.get(xo,f'spe?{xo}')
        if 'cmp' in nm or 'tst' in nm: return (f'{nm} cr{rd>>2}, r{ra}, r{rb}',None)
        if nm.startswith('efsc') or nm in ('efsabs','efsneg','efsnabs'): return (f'{nm} r{rd}, r{rb}',None)
        return (f'{nm} r{rd}, r{ra}, r{rb}',None)
    return (f'.long {w:#010x}',None)
def disasm(buf,file_off,cpu,length,labels=None):
    out=[]; i=0
    while i<length:
        n,(txt,info)=dis(buf,file_off+i,cpu+i)
        out.append((cpu+i,buf[file_off+i:file_off+i+n].hex(),txt,info)); i+=n
    return out
