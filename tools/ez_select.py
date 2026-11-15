import re
GROUPS=['Injection - Main Timing (SOI)','Injection - Pilot (R1 R2)','Injection - Main Quantity and Pulse Width','Injection - Post (A1-A4 and P1)',
        'Fuel Control - Other','Rail Pressure','Boost and VGT','Exhaust Brake','Torque to Fuel and Smoke Limits','Torque Management (Driver Trans Traction)',
        'Driver Demand (Pedal)','Rev and Speed Limits','Idle and Engine Speed Control']
MODGROUP={'FHPC':'Rail Pressure','FCBR':'Rail Pressure','FHPF':'Rail Pressure','AICC':'Boost and VGT','VGTC':'Boost and VGT','EXBC':'Exhaust Brake',
          'ETQC':'Torque to Fuel and Smoke Limits','ECPC':'Torque to Fuel and Smoke Limits','EATC':'Torque to Fuel and Smoke Limits','TRQC':'Torque to Fuel and Smoke Limits',
          'ETMC':'Torque Management (Driver Trans Traction)','DTMC':'Torque Management (Driver Trans Traction)','OTMC':'Torque Management (Driver Trans Traction)',
          'TCSC':'Torque Management (Driver Trans Traction)','TTQC':'Torque Management (Driver Trans Traction)','TTQN':'Torque Management (Driver Trans Traction)',
          'DTRC':'Driver Demand (Pedal)','EOSC':'Rev and Speed Limits','EOSR':'Rev and Speed Limits','VOSC':'Rev and Speed Limits','VOSI':'Rev and Speed Limits',
          'SPDC':'Idle and Engine Speed Control','TCOC':'Idle and Engine Speed Control','ECSC':'Idle and Engine Speed Control'}
WHITE=set(MODGROUP)|{'FULC'}
EXCL=re.compile(r'EGR|DPF|SCR|NOx|NOX|DEF|Rgn|Regen|HCI|HCS|Cat\b|Cat[A-Z_0-9]|Soot|LNT|DeSOx|DeNOx|DeHC|Urea|Dosing|OxCat|_PN\b|RichIdle|_PN_|CMSR|SrvRgn|ServRgn',re.I)
AFT=re.compile(r'_(?:Lo|Mid|Sea)?[A-Z]?[DSV]\d{1,2}[A-Z]?$|Temp[A-Z][DSV]\d')   # DPF / SCR / LNT combustion-mode copies
INJ=re.compile(r'^KtFULC_(phi_SOI_M_Ptn\d|phi_SOI_P1|V_QntyR\d(_Ptn\d)?|t_DT_R\d(_Ptn\d)?|V_QntyA\d+|t_DT_A\d+|t_DT_Post|V_QntyM_Ptn\d)_(Lo|Mid|Sea)BC1$')
KEY={'KtDTRC_M_EngTrqReqForRPM','KeDTRC_v_MinARM','KeEOSC_n_RPM_EngExtremeHystHi','KeEOSC_n_RPM_EngExtremeHystLo',
     'KtECPC_M_IndMax','KtFULC_t_ET_InjTbl','KtDTRC_P_M_PedProgReqA','KtDTRC_P_M_PedProgReqB','KtDTRC_P_M_PedProgReqC'}
def module(n):
    m=re.match(r'[KICk][a-z]?[a-z]?([A-Z]{4})_',n); return m.group(1) if m else None
def group(n):
    if module(n)=='FULC':
        if re.search(r'_(?:V_Qnty|t_DT_|K_Qnty|K_DT_|K_)R\d',n): return GROUPS[1]
        if re.search(r'_(?:V_Qnty|t_DT_|K_Qnty|K_DT_|K_)A\d|DT_Post|SOI_P(?:\d|_|$)',n): return GROUPS[3]
        if 'SOI' in n: return GROUPS[0]
        if re.search(r'QntyM|_K_M_|InjTbl|MainCrtn|MinMain|_ET_',n): return GROUPS[2]
        return GROUPS[4]
    return MODGROUP.get(module(n),'Other')
KIND={'B':'Base tables','A':'Air temp corrections (A)','C':'Coolant corrections (C)','F':'Fuel temp corrections (F)','M':'Boost deviation corrections (M)','S':'Vehicle speed compensation (S)'}
def kind(n):
    m=re.search(r'_(?:Lo|Mid|Sea)?([BACFMS])C\d\d?[A-Z]?$',n)
    return KIND[m.group(1)] if m else 'Tables and curves'
def selected(n,changed,conf):
    if conf not in ('high','medium'): return False
    if n in KEY: return True
    if module(n) not in WHITE or EXCL.search(n) or AFT.search(n): return False
    if module(n)=='VGTC' and re.search(r'Lrn|EOL|SmartFS|Clean|AntiStick|Smart',n): return False   # vane learn / cleaning routines
    return changed or bool(INJ.match(n))
