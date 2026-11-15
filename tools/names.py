# Descriptive names, folders and detailed descriptions for GM E41 L5P calibration items
import re
# ---------------------------------------------------------------- vocab
STEM={'FUL':'Fuel Injection','FHP':'Rail Pressure','FCB':'Fuel Pump Control','AIC':'Air Charge (Boost/VGT/EGR)','ETQ':'Torque to Fuel','ECP':'Engine Torque Capability',
 'EAT':'Smoke Limit','TRQ':'Torque Control','ETM':'Engine Torque Model','DTR':'Driver Torque Request','DTM':'Driveline Torque Mgmt','OTM':'Over-Torque Mgmt',
 'TCS':'Traction Control','TTQ':'Trans Torque','EOS':'Engine Overspeed','VOS':'Vehicle Overspeed','SPD':'Engine Speed / Idle','TCO':'Torque Coordination',
 'ECS':'Engine Crank & Speed','VGT':'VGT Actuator','EXB':'Exhaust Brake','SCR':'SCR / DEF','DPF':'DPF','FFR':'Freeze Frame','DFI':'DTC Setup','CAN':'CAN Bus',
 'FAD':'Fuel Adaptation (Injector Learn)','OXY':'O2 / NOx Sensor','XOY':'O2 / NOx Sensor','NOX':'NOx Sensor','EGT':'Exhaust Gas Temp','EXM':'Exhaust Model','EXC':'Exhaust Config',
 'VIT':'Voltage','ASS':'Auto Start-Stop','AAS':'Active Air Shutter','THM':'Thermostat','MSF':'Misfire','CRZ':'Cruise Control','FWD':'4WD','IDN':'Calibration ID','CSE':'Cold Start Emissions',
 'ADP':'Adaptive Pedal','CEB':'Bypass Valve','ZPT':'Creep / Coast Torque','EGR':'EGR','SOT':'Soot Sensor','CFM':'Cooling Fan Monitor','LON':'Longitudinal Accel','GLO':'Glow Plug',
 'CAT':'Catalyst','VSP':'Vehicle Speed','TOS':'Trans Output Speed','ECT':'Coolant Temp','FLV':'Fuel Level','FAN':'Cooling Fan','BRK':'Brake','FEA':'Cooling Fan','FAF':'Fuel Pump Module',
 'ESS':'Engine Service','DIC':'Driver Info','HCI':'HC Dosing','ACC':'A/C Clutch','EOD':'Oil Life','EPS':'Crank/Cam Position','VSD':'Vehicle Speed','FDB':'Fuel Delivery','LUB':'Lubrication',
 'TPS':'Throttle','FEAD':'Fan','TRG':'Trans Range','CSS':'Clutch / Speed Sensor','EIT':'Intake Air Temp','IDR':'Data Recorder','CET':'Charge Air Temp','EGP':'Exhaust Pressure',
 'DDC':'Driveline','APS':'Pedal Sensor','DQM':'DEF Quality','MAF':'Mass Air Flow','EOP':'Oil Pressure','CIT':'Charge Air Temp','OAT':'Outside Air Temp','UCC':'Ultracapacitor',
 'MTC':'Manual Clutch','TLN':'Torque Learn','LVT':'Battery Voltage','EOT':'Oil Temp','CMB':'Combustion Mode','INS':'Instrumentation','STR':'Starter','VSL':'Speed Limiter',
 'MEM':'Memory','LAT':'Lateral Accel','EHP':'Fuel Heater/Pump','ACT':'A/C Torque','AFT':'Aux Fan','CAS':'Charge Air','HSW':'Hood Switch','SIL':'Engine Silence','TSX':'Trans Spin Loss',
 'MPM':'Monitor Manager','RRD':'Rough Road','FAB':'Fuel Pump Feedback','MTC':'Manual Trans Clutch','AAP':'Barometric Pressure','FDA':'Fuel Vapor','DMD':'Drive Mode','BBV':'Brake Booster Vacuum',
 'FDP':'Fuel Pump Prime','MCT':'Clutch','OAT':'Outside Air Temp','ACZ':'Cruise','PTA':'Powertrain Torque','FOD':'Fan Driver','SPI':'Speed Input','INM':'Intake Manifold',
 'EPM':'Exhaust Pipe Model','LUB':'Oil Pressure Control','EAB':'Electric Brake','FLC':'Fuel Level','LAT':'Lateral','THR':'Turbo Temp','TTH':'Turbo Temp','CED':'Cold Start Diag',
 'CID':'Cold Start','DCL':'TCC','TCC':'TCC','GEN':'Generator','PBR':'Elevated Idle','HUM':'Humidity','PIS':'Piston Cooling','FFM':'Fuel Filter / Water in Fuel','RVS':'Remote Start',
 'LDT':'Engine Speed','HAT':'Hood Alarm','DMF':'Driveline','AXL':'Axle Torque','STM':'Torque Monitor','SPC':'Security','FPM':'Fuel Pump','TPSO':'Throttle','IMO':'Immobilizer',
 'PTO':'PTO','EOL':'End of Line','MIL':'Check Engine Lamp','ODA':'OBD Data','ODC':'OBD','RPO':'Rear PTO','EMD':'Engine Mode','DPL':'Driveline','SHD':'Shutdown Driver','TSC':'Turbo Speed',
 'TCG':'Turbo Control','GRD':'Grade','RIN':'Rear Inhibit','SBR':'Starter Relay','SRA':'Fuel Run-Out','ACP':'Accessory Power','TLP':'Cold Start Temp','CML':'Piston Cooling Jets',
 'PRS':'PTO Speed','MAP':'Manifold Pressure','LIN':'LIN Bus','EPS':'Engine Position','EGTR':'EGT','INF':'Hybrid','VIO':'Oil Level','PSA':'PID','TRN':'Transmission','TRT':'Trans Ratio',
 'BSE':'Battery Sensor','TFT':'Trans Fluid Temp','VLD':'Feature','TBN':'Trans','ICT':'Clutch Torque','IFR':'MAP Correlation','PMD':'Power Mode','PLC':'Launch Control','CSS':'Clutch Speed'}
SUFFIX={'C':'Control','D':'Diagnostic','I':'Input','O':'Output Driver','R':'','G':'Config','F':'','N':'Network','S':'','A':'','E':''}
TOK={'Eng':'Engine','Hi':'High','Lo':'Low','Lim':'Limit','Lm':'Limit','Lmt':'Limit','Thrsh':'Threshold','Thresh':'Threshold','Thrs':'Threshold','Thr':'Threshold','Thsh':'Threshold','Th':'Threshold',
 'Enbl':'Enable','Enbld':'Enabled','Dsbl':'Disable','Dsbld':'Disabled','Ptn':'Pattern','Temp':'Temp','Spd':'Speed','Pt':'Point','Qnty':'Quantity','Pres':'Pressure','Press':'Pressure','Diag':'Diagnostic',
 'Torq':'Torque','Trq':'Torque','Tq':'Torque','Smpl':'Sample','Smpls':'Samples','Crtn':'Correction','Corr':'Correction','Bst':'Boost','Veh':'Vehicle','Tm':'Time','Filt':'Filter','Fltr':'Filter','Ftr':'Filter',
 'Hys':'Hysteresis','Hyst':'Hysteresis','Chk':'Check','Snsr':'Sensor','Sens':'Sensor','Dyn':'Dynamic','Pstn':'Position','Pos':'Positive','Neg':'Negative','Ckt':'Circuit','Dly':'Delay',
 'Exh':'Exhaust','Req':'Request','Rqst':'Request','Ofst':'Offset','Perf':'Performance','Tst':'Test','Err':'Error','Er':'Error','Incr':'Increase','Decr':'Decrease','Init':'Initial','Volt':'Voltage',
 'Vlt':'Voltage','Lvl':'Level','Delt':'Delta','Dlt':'Delta','Rgn':'Regen','Cntrl':'Control','Ctrl':'Control','Fd':'Feed','Fwd':'Forward','Trans':'Trans','Deb':'Debounce','Dbnc':'Debounce',
 'Serv':'Service','Rng':'Range','Amb':'Ambient','Cal':'Calibration','Eff':'Efficiency','Gr':'Gear','Grs':'Gears','Sys':'System','Inj':'Injection','Rat':'Ratio','Dflt':'Default','Diff':'Difference',
 'Throt':'Throttle','Stp':'Stop','Comp':'Compensation','Cmp':'Compensation','Intgl':'Integral','Intg':'Integral','Intgr':'Integrator','Lrn':'Learn','Dsrd':'Desired','Fx':'Factor','Htr':'Heater','Ht':'Heat',
 'Govn':'Governor','Immed':'Immediate','Imm':'Immediate','Montr':'Monitor','Mntr':'Monitor','Pmp':'Pump','Strt':'Start','Grp':'Group','Actv':'Active','Stk':'Stuck','Shtr':'Shutter','Mdl':'Model',
 'Arfl':'Airflow','Sply':'Supply','Plaus':'Plausibility','Chg':'Change','Chng':'Change','Trnstn':'Transition','Trnsnt':'Transient','Trnst':'Transient','Prdtd':'Predicted','Prdtn':'Prediction',
 'Mnfd':'Manifold','Est':'Estimated','Cnst':'Constant','Wrng':'Warning','Freq':'Frequency','Avg':'Average','Cond':'Condition','Bat':'Battery','Cap':'Capacity','Strg':'Strategy','Acceltn':'Acceleration',
 'Accel':'Acceleration','Decel':'Deceleration','Elec':'Electrical','Neut':'Neutral','Manl':'Manual','Tgt':'Target','Dist':'Distance','Byp':'Bypass','Dvtn':'Deviation','Dev':'Deviation','Clch':'Clutch',
 'Whl':'Wheel','Baro':'Baro','Clsd':'Closed','Opn':'Open','Ovrrd':'Override','Ovrd':'Override','Wght':'Weight','Ign':'Ignition','Crnk':'Crank','Crnkg':'Cranking','Crk':'Crank','Qck':'Quick','Cmd':'Command',
 'Cmnd':'Command','Thst':'Thermostat','Excsv':'Excessive','Prog':'Progression','Srg':'Surge','Fdbck':'Feedback','Prtct':'Protection','Pdl':'Pedal','Ped':'Pedal','Pls':'Pulse','Puls':'Pulse',
 'Rdct':'Reduction','Ovrrn':'Overrun','Inhb':'Inhibit','Chrg':'Charge','Wdw':'Window','Lrg':'Large','Sml':'Small','Shrt':'Short','Sht':'Short','Fst':'Fast','Lmp':'Lamp','Msrd':'Measured','Dty':'Duty',
 'Frzn':'Frozen','Engy':'Energy','Cpcty':'Capacity','Rqrd':'Required','Slnd':'Solenoid','Drt':'Derate','Trnsfr':'Transfer','Xfer':'Transfer','Axl':'Axle','Tmrs':'Timers','Tmr':'Timer','Rmp':'Ramp',
 'Cntrlr':'Controller','Dtctn':'Detection','Evaln':'Evaluation','Den':'Density','Deriv':'Derivative','Prop':'Proportional','Mult':'Multiplier','Tot':'Total','Stab':'Stability','Act':'Actual','Inc':'Increment',
 'Num':'Number','Rel':'Relative','Dwn':'Down','Norm':'Normalized','Ref':'Reference','Brk':'Brake','Cyl':'Cylinder','Resp':'Response','Sw':'Switch','Gen':'Generator','Vlv':'Valve','Rvrs':'Reverse',
 'Intk':'Intake','Tamp':'Tamper','Ovr':'Over','Dur':'Duration','Trp':'Trip','Shf':'Shift','Lat':'Lateral','Lon':'Longitudinal','Hum':'Humidity','Mx':'Max','Pri':'Priority','Fac':'Factor','Fctr':'Factor',
 'Coef':'Coefficient','Coeff':'Coefficient','Cf':'Coefficient','Turb':'Turbine','Comb':'Combustion','Cmb':'Combustion','Cool':'Coolant','Ox':'Oxygen','PN':'Park/Neutral','Gsht':'Ground Short','Psht':'Power Short',
 'Stdy':'Steady','Ind':'Indicated','Trnsfr':'Transfer','Dsngage':'Disengage','Cst':'Coast','Crp':'Creep','Drvr':'Driver','Drv':'Drive','Fx':'Factor','Lin':'Linear','Exp':'Expected','Tbl':'Table',
 'Cvrtr':'Converter','Prsnt':'Present','Equip':'Equipped','Stat':'Status','Rlsd':'Released','Ctr':'Counter','Bnc':'Bounce','Cnt':'Count','Lrng':'Learning','Lng':'Long','Nrml':'Normal','Ptn1':'Pattern 1',
 'Ptn2':'Pattern 2','Arm':'Arm','Rnd':'Round','Wt':'Weight','Hold':'Hold','Inh':'Inhibit','Mtg':'Mitigation','Rotn':'Rotation','Dsnge':'Disengage','Ps':'Per Second','Gain':'Gain','Fltd':'Filtered',
 'Nom':'Nominal','Vac':'Vacuum','Slip':'Slip','Res':'Reset','Fail':'Fail','Ratl':'Rationality','RatCntrlr':'Rate Controller','Sync':'Sync','Ofs':'Offset','Pwr':'Power','Stuck':'Stuck','Tmpr':'Tamper','Wrng':'Warning','Alwd':'Allowed','Prmt':'Permit','Rcvry':'Recovery','Slct':'Select','Cfg':'Config','Pwrtrn':'Powertrain'}
ACR={'NOX':'NOx','SOI':'SOI','VGT':'VGT','EGR':'EGR','DPF':'DPF','SCR':'SCR','DEF':'DEF','HC':'HC','EGT':'EGT','MU':'Metering Valve','PR':'Pressure Regulator','ET':'Energizing Time','TCC':'TCC','DFCO':'Decel Fuel Cut',
 'CAC':'Charge Air Cooler','MAP':'MAP','PPS':'Pedal Sensor','RPS':'Rail Pressure Sensor','IAT':'IAT','OAT':'OAT','ECT':'Coolant Temp','EOT':'Oil Temp','EOP':'Oil Pressure','RPM':'RPM','CB':'Cylinder Balance',
 'CL':'Closed Loop','OL':'Open Loop','PTO':'PTO','TCS':'Traction Control','DOC':'DOC','LNT':'LNT','NH':'NH3','HCI':'HC Injection','FIR':'FIR','EWMA':'EWMA','IUPR':'IUPR','PID':'PID','DT':'Dwell Time',
 'WG':'Wastegate','PWM':'PWM','DC':'Duty Cycle','ECM':'ECM','OBD':'OBD','DTC':'DTC','AC':'A/C','HPE':'HPE','SQA':'Small Quantity Adaptation','IFM':'IFM','CWA':'CWA','EIA':'EIA','RPWC':'Rail Pressure Wave Correction',
 'TSC':'TSC','NOx':'NOx','NO':'NO','GC':'Gear','PXL':'PXL','CXX':'CXX','EOL':'End of Line','IBS':'Battery Sensor','DCDC':'DC-DC','UCap':'Ultracap','ESS':'ESS','FPPM':'Fuel Pump Module'}
MODES={'C1':'Normal Mode (C1)','C2':'Combustion Mode C2','C3':'Combustion Mode C3','D1':'DPF Regen High-O2 (D1)','D2':'DPF Regen Low-O2 (D2)','D3':'DPF Regen Park/Neutral (D3)',
 'D4':'DPF Regen Rich Idle (D4)','S1':'SCR Heat Mode 1 (S1)','S2':'SCR Heat Mode 2 (S2)','S3':'SCR Heat Mode 3 (S3)','S4':'SCR Service Mode (S4)','V1':'LNT DeNOx (V1)','V2':'LNT DeSOx Lean (V2)','V3':'LNT DeSOx Rich (V3)'}
KIND={'B':'Base','A':'Air Temp Correction','C':'Coolant Temp Correction','F':'Fuel Temp Correction','M':'Boost Deviation Correction','S':'Vehicle Speed Correction','G':'Gear Group'}
BARO={'Lo':'Low Baro (Altitude)','Mid':'Mid Baro','Sea':'Sea Level'}
QTY={'t':'time','K':'factor','k':'factor/filter','Cnt':'count','b':'on/off','Pct':'percent','pct':'percent','T':'temperature','V':'fuel volume','e':'selection','n':'engine speed','p':'pressure','M':'torque',
 'r':'ratio','cmp':'compensated value','v':'vehicle speed','U':'voltage','m':'mass','phi':'crank angle','dm':'mass flow','a':'acceleration','l':'length','R':'resistance','Cf':'coefficient','I':'current',
 'dV':'volume rate','dM':'torque rate','dp':'pressure rate','DC':'duty cycle','dT':'temperature rate','dn':'speed rate','P':'power','E':'energy','A':'area','rho':'density','ppm':'concentration','nv':'engine or vehicle speed'}
# ---------------------------------------------------------------- curated families
FAM=[ # (regex on body after 'Kt|Ke|Ka<MOD>_', readable stem, tuning note)
 (r'^FULC_phi_SOI_M_(Ptn\d_)?','Main Injection Timing (SOI)','Start of the main injection in crank degrees before TDC - higher number = more advance. More advance raises cylinder pressure, power and noise and lowers EGT; too much advance can damage pistons and head gaskets.'),
 (r'^FULC_K_SOI_M_(Ptn\d_)?','Main Timing Correction Factor','Weighting factor that scales how much the main-injection timing correction is applied (1.0 = full correction, 0 = none).'),
 (r'^FULC_phi_SOI_P1','Post Injection (P1) Timing','Timing of the late post pulse P1 in crank degrees. Late posts mostly heat the exhaust and add little torque.'),
 (r'^FULC_V_QntyR1_(Ptn\d_)?','Pilot 1 Quantity','Fuel volume of the first pilot pulse (mm3 per stroke). Pilot fuel softens combustion and reduces diesel knock; less pilot = louder combustion.'),
 (r'^FULC_V_QntyR2_(Ptn\d_)?','Pilot 2 Quantity','Fuel volume of the second pilot pulse (mm3 per stroke), the pilot closest to the main pulse.'),
 (r'^FULC_t_DT_R1_(Ptn\d_)?','Pilot 1 Dwell Time','Gap between the pilot 1 pulse and the next pulse (microseconds). Longer dwell moves the pilot earlier relative to the main injection.'),
 (r'^FULC_t_DT_R2_(Ptn\d_)?','Pilot 2 Dwell Time','Gap between the pilot 2 pulse and the main pulse (microseconds).'),
 (r'^FULC_K_(Qnty|DT_)?R1_(Ptn\d_)?','Pilot 1 Correction Factor','Weighting factor for the pilot 1 corrections (1.0 = full correction).'),
 (r'^FULC_K_(Qnty|DT_)?R2_(Ptn\d_)?','Pilot 2 Correction Factor','Weighting factor for the pilot 2 corrections (1.0 = full correction).'),
 (r'^FULC_V_QntyA(\d+)_','Post (After) Injection {0} Quantity','Fuel volume of after-injection {0} (mm3 per stroke). Close after-pulses help burn soot; later after-pulses mainly add exhaust heat for DPF/SCR.'),
 (r'^FULC_t_DT_A(\d+)_','Post (After) Injection {0} Dwell Time','Gap between the main pulse (or previous after-pulse) and after-injection {0} (microseconds).'),
 (r'^FULC_K_(Qnty|DT_)?A(\d+)_','Post (After) Injection Correction Factor','Weighting factor for the after-injection corrections.'),
 (r'^FULC_t_DT_Post','Post Injection Dwell Time','Gap before the post pulse (microseconds).'),
 (r'^FULC_V_QntyM_(Ptn\d_)?','Main Injection Quantity','Fuel volume of the main pulse (mm3 per stroke).'),
 (r'^FULC_t_ET_InjTbl','Injector Energizing Time (Pulse Width)','Injector characterization: how long the injector is energized (microseconds) to deliver a fuel quantity at a given rail pressure. Change only for different injectors; editing it for power distorts every fuel calculation.'),
 (r'^FULC_V_MainCrtn','Main Quantity Correction',''),(r'^FULC_V_MinMain','Minimum Main Quantity',''),
 (r'^FHPC_p_PresSetPt_(Ptn\d_)?','Rail Pressure Target','Target common-rail fuel pressure (MPa) by engine speed and fuel quantity. Higher pressure = finer atomization and faster injection; stay inside the pump and injector limits.'),
 (r'^FHPC_I_MU_FlowToCurrCvrtr','Fuel Metering Valve Flow-to-Current','Converts the required pump fuel flow into metering-unit (MU) valve current. Pump hardware characterization - do not change for power.'),
 (r'^AICC_p_BstSetPt_','Boost Pressure Target','Target boost pressure in ABSOLUTE kPa (subtract about 100 kPa at sea level for gauge boost).'),
 (r'^AICC_Pct_VGT_FdFwd_','VGT Vane Position Feed-Forward','Base vane position the boost controller starts from (%). Higher % = vanes more closed = faster spool and more boost and drive pressure.'),
 (r'^AICC_Pct_VGT_Max_','VGT Vane Position Max Limit','Upper limit on vane closing (%). Higher % allows the vanes to close further (more boost and drive pressure).'),
 (r'^ETQC_m_TorqToFuel_','Torque to Fuel Conversion','Converts the requested engine torque into fuel mass per stroke (mg). Raising values adds fuel for the same torque request.'),
 (r'^EATC_r_SmokeLim_','Smoke Limit (Fuel to Air)','Maximum fuel allowed for the measured air - limits black smoke. Higher values allow more fuel per unit of air (more smoke and EGT).'),
 (r'^EATC_K_SmokeLim_','Smoke Limit Correction Factor',''),
 (r'^ECPC_M_IndMax','Maximum Indicated Engine Torque','Overall engine torque ceiling (shown in lb-ft). Requests above this are clipped.'),
 (r'^DTRC_P_M_PedProgReq([ABC])','Pedal Map {0} (Driver Power Request)','Driver demand: requested power from pedal position and engine/vehicle speed. Shapes throttle response.'),
 (r'^DTRC_M_EngTrqReqForRPM','Park/Neutral Pedal Torque Request','Torque requested from pedal and RPM when the truck is stationary (0 kph - Park/Neutral). Blends into the normal pedal maps by 15 kph. Raise the upper-RPM cells to let the engine free-rev to the fuel cut when parked.'),
 (r'^DTRC_v_MinARM','Pedal Map Takeover Speed','Vehicle speed above which the normal pedal maps fully replace the Park/Neutral torque table.'),
 (r'^DTRC_b_UseBaseProgOnly','Use Rolling-Neutral Pedal Maps at Standstill (Base Progression Only)','1 = bypass GM\'s Neutral Control (Park/Neutral) table and launch assist, so the normal pedal maps are used at every vehicle speed - standstill then uses the same driver-demand path as rolling in neutral. Also changes in-gear launches from a stop. 0 = stock.'),
 (r'^DTRC_b_EnblRPM_PedProg','Pedal Maps Use Road Speed (Fixed n/v Ratio)','1 = the pedal maps are looked up with road speed times the n/v ratio instead of engine RPM.'),
 (r'^DTRC_r_VTS_NV_Ratio','Pedal Map Road-Speed Ratio (n/v)','Ratio used to turn road speed into the pedal-map lookup value when road-speed lookup is on.'),
 (r'^EOSC_n_RPM_EngExtremeHystHi','Rev Limiter - Fuel Cut RPM','Engine speed at which fuel is cut (rev limiter).'),
 (r'^EOSC_n_RPM_EngExtremeHystLo','Rev Limiter - Fuel Resume RPM','Engine speed at which fuel returns after a rev-limiter cut.'),
]
def _tokens(s):
    out=[]
    for part in s.split('_'):
        if not part: continue
        for t in re.findall(r'[A-Z][a-z]+|[A-Z]+(?![a-z])|[a-z]+|\d+',part): out.append(t)
    return out
def _expand(s):
    s=re.sub(r'Qnty([RAM])(\d)',lambda m:{'R':'Pilot ','A':'Post ','M':'Main '}[m.group(1)]+m.group(2)+' Quantity',s)
    s=re.sub(r'DT_([RA])(\d)',lambda m:{'R':'Pilot ','A':'Post '}[m.group(1)]+m.group(2)+' Dwell',s)
    s=re.sub(r'SOI_M','Main SOI',s); s=re.sub(r'SOI_P','Post SOI',s); s=s.replace('NOx','NOX')
    w=[]
    for t in _tokens(s):
        if t in ACR: w.append(ACR[t])
        elif t in TOK: w.append(TOK[t])
        elif t.isupper() and len(t)>1: w.append(t)
        else: w.append(t[0].upper()+t[1:] if t else t)
    out=' '.join(w)
    out=re.sub(r'\b(\w+) \1\b',r'\1',out)
    return out
def parse(n):
    m=re.match(r'^([A-Z][a-z]{0,2})([A-Z]{4})_(.*)$',n)
    if not m: return None
    pre,mod,rest=m.groups(); idx=''
    mi=re.search(r'(\[.*\])$',rest)
    if mi: idx=mi.group(1); rest=rest[:mi.start()]
    q=None; mq=re.match(r'^([A-Za-z]+?)_(.*)$',rest)
    if mq and mq.group(1) in QTY: q,rest=mq.group(1),mq.group(2)
    return pre,mod,q,rest,idx
SUFX=re.compile(r'_(?:(Lo|Mid|Sea))?([BACFMSG])?(C|D|S|V)(\d)(\d?)([A-IHL])?$')
def mode_suffix(rest):
    m=SUFX.search('_'+rest) if not rest.startswith('_') else SUFX.search(rest)
    if not m: 
        m2=re.search(r'_?(Lo|Mid|Sea)(BC|PXL[CDM]?|CXX)?$',rest)
        if m2: return rest[:m2.start()].rstrip('_'),[BARO[m2.group(1)]]+([{'BC':'Base','PXLC':'PXL Coolant Gain','PXLD':'PXL Dynamic Gain','PXLM':'PXL Gain','PXL':'PXL','CXX':'Engine Temp Factor'}.get(m2.group(2),m2.group(2))] if m2.group(2) else []),None
        return rest,[],None
    baro,kind,ml,md,idx,sub=m.groups(); q=[]
    if baro: q.append(BARO[baro])
    if kind: q.append(KIND[kind])
    mode=ml+md; q.append(MODES.get(mode,'Mode '+mode))
    if idx: q.append('#'+idx)
    if sub: q.append({'H':'High Gear Group','L':'Low Gear Group'}.get(sub,'Table '+sub) if kind=='G' else 'Table '+sub)
    body=('_'+rest)[:m.start()].lstrip('_') if not rest.startswith('_') else rest[:m.start()]
    return body,q,mode
def module_label(mod):
    s=STEM.get(mod[:3]); suf=SUFFIX.get(mod[3],'')
    if not s: return mod
    if mod[:3] in ('FUL','FHP','AIC','ETQ','ECP','EAT','DTR','EOS','VOS','SPD','EXB','VGT','CRZ','GLO','PTO','EGR','DPF','SCR','NOX','SOT','CAT','HCI','EGT') and suf=='Control': suf=''
    return (s+' '+suf).strip()
def readable(n):
    """descriptive name for a GM calibration name"""
    base=re.sub(r'_SOTF_T(\d)$','',n); tune=re.search(r'_SOTF_T(\d)$',n)
    p=parse(base)
    if not p: return n
    pre,mod,q,rest,idx=p
    body,quals,mode=mode_suffix(rest)
    key=f'{mod}_{q}_{rest}' if q else f'{mod}_{rest}'
    name=None
    for rx,stem,note in FAM:
        m=re.match(rx,key)
        if m:
            g=[x for x in m.groups() if x and not x.startswith('Ptn')]
            name=stem.format(*([g[-1]] if g else ['']))
            pm=re.search(r'Ptn(\d)',rest)
            if pm: quals=['Pattern '+pm.group(1)]+quals
            if 'Crnkg' in rest: quals=['Cranking']+quals
            if re.search(r'_(Lo|Mid|Sea)?CXX$',rest): quals=[q_ for q_ in quals if q_!='Engine Temp Factor']+['Engine Temp Factor']
            if re.search(r'PXL',rest) and not any('PXL' in x for x in quals): quals.append('PXL')
            break
    if name is None:
        name=module_label(mod)+' - '+_expand(body if body else rest)
        if pre=='Kn': name+=' Breakpoints'
        if q and q in QTY: name+=f' ({QTY[q]})'
    if quals: name+=' - '+' - '.join(quals)
    if idx:
        lab=', '.join(_expand(re.sub(r'^C[eiac][A-Z]{4}_[ei]_','',x)) for x in re.findall(r'\[([^\]]*)\]',idx))
        name+=f' [{lab}]'
    if tune: name=f'Tune {tune.group(1)} - '+name
    return re.sub(r'\s+',' ',name).strip()
def family_note(n):
    p=parse(re.sub(r'_SOTF_T\d$','',n))
    if not p: return ''
    pre,mod,q,rest,idx=p; key=f'{mod}_{q}_{rest}' if q else f'{mod}_{rest}'
    for rx,stem,note in FAM:
        m=re.match(rx,key)
        if m:
            g=[x for x in m.groups() if x and not x.startswith('Ptn')]
            return note.format(*([g[-1]] if g else ['']))
    return ''
def mode_note(n):
    p=parse(re.sub(r'_SOTF_T\d$','',n))
    if not p: return ''
    body,quals,mode=mode_suffix(p[3]); out=[]
    b=re.search(r'(Lo|Mid|Sea)',p[3])
    if any(q in BARO.values() for q in quals):
        out.append('The ECU blends the Low / Mid / Sea-level versions of this table by barometric pressure (altitude); edit all three to change behaviour everywhere.')
    if mode:
        if mode=='C1': out.append('Used in normal combustion mode (C1) - the mode the truck runs in almost all the time.')
        elif mode[0] in 'DSV': out.append(f'Only used in {MODES.get(mode,mode)} - an emissions/aftertreatment mode, not normal driving.')
        else: out.append(f'Used in {MODES.get(mode,mode)} (special combustion mode, not normal driving).')
    k=[q for q in quals if q in KIND.values() and q!='Base']
    if k: out.append(f'This is a {k[0].lower()} applied on top of the base table.')
    return ' '.join(out)
# ---------------------------------------------------------------- categories / folders
PERF_ORDER=['Injection - Main Timing (SOI)','Injection - Pilot (R1 R2)','Injection - Main Quantity and Pulse Width','Injection - Post (A1-A4 and P1)','Fuel Control - Other','Rail Pressure',
 'Boost and VGT','Exhaust Brake','Torque to Fuel and Smoke Limits','Torque Management (Driver Trans Traction)','Driver Demand (Pedal)','Rev and Speed Limits','Idle and Engine Speed Control']
PERF_NUM={g:i+1 for i,g in enumerate(PERF_ORDER)}
PERF_TITLE={'Injection - Main Timing (SOI)':'Injection - Main Timing (SOI)','Injection - Pilot (R1 R2)':'Injection - Pilot (R1 R2)','Injection - Main Quantity and Pulse Width':'Injection - Main Quantity and Pulse Width',
 'Injection - Post (A1-A4 and P1)':'Injection - Post (A1-A4 P1)','Fuel Control - Other':'Injection - Other Fuel Control','Rail Pressure':'Rail Pressure and Fuel Pump','Boost and VGT':'Boost and VGT',
 'Exhaust Brake':'Exhaust Brake','Torque to Fuel and Smoke Limits':'Torque to Fuel and Smoke Limits','Torque Management (Driver Trans Traction)':'Torque Management (Driver Trans Traction)',
 'Driver Demand (Pedal)':'Driver Demand (Pedal)','Rev and Speed Limits':'Rev and Speed Limiters','Idle and Engine Speed Control':'Idle and Engine Speed Control'}
OTHER=[('20 Starting and Glow Plugs',('STR','GLO','RVS','SBR','TLP','CSE','CID','CED')),('21 Cruise Control and Speed Limiter',('CRZ','ACZ','VSL','PBE')),('22 PTO',('PTO','PRS','RPO')),
 ('23 Transmission and Driveline Interface',('TRG','TOS','TCG','TSX','TTH','TRN','TRT','TGR','DDC','DPL','DMF','AXL','TFT','TBN','ICT','MTC','MCT','SKS','SHT','TCC','DCL','FWD','LDT','CSS','TSC','ZPT','LON','LAT','GRD','RRD','WSS','TIS','PLC')),
 ('24 Cooling Fans and Thermal Management',('FAN','FEA','THM','ECT','EOT','CTR','CFM','AFT','FOD','FDA','HAT','CEB','EPM','CML','PIS')),
 ('25 Oil System and Engine Protection',('EOP','EOD','LUB','VIO','STM','OTM')),
 ('26 Electrical Battery and Accessories',('ACT','ACC','GEN','VIT','LVT','VLT','UCC','BSE','ACP','PMD','ASS','AAS','ESS','DIC','INS','HSW','SIL','IMO','SPC','MIL','EAB','BRK','BBV','DMD','INF','HUM')),
 ('41 Diagnostics - Monitors and Thresholds',('MIS','MSF')),('27 Engine and Vehicle Sensors and Fuel Supply',('MAF','MAP','AAP','OAT','EIT','CIT','CET','EGP','APS','TPS','INM','IFR','FLV','FLC','FFM','FDB','FAB','FAF','FPM','EHP','FDP','SRA','EPS','SPI','VSP','VSD')),
 ('30 Emissions - EGR',('EGR',)),('31 Emissions - DPF and Soot',('DPF','SOT')),('32 Emissions - SCR DEF and NOx',('SCR','NOX','DQM','DEF')),
 ('33 Emissions - Catalyst HC Dosing O2 and Exhaust Models',('CAT','HCI','EXM','EXC','EGT','OXY','XOY','LNT','EPM')),
 ('40 Diagnostics - DTC Setup and Freeze Frame',('DFI','FFR','MPM','ODA','ODC','DRE','PSA','AEC','CAN')),
 ('42 Fuel System Learning and Cylinder Balance',('FAD','TLN','ADP')),('50 Communication (CAN LIN)',('LIN','CMG','ILC','IMO')),('51 Calibration ID and Checksums',('IDN','IDR','ENG','VIN','MEM','OVI','OSA'))]
EMI_RX=re.compile(r'EGR|DPF|SCR|NOx|NOX|DEF|Rgn|Regen|HCI|HCS|Soot|LNT|DeSOx|DeNOx|DeHC|Urea|Dosing|OxCat|RichIdle|SrvRgn|ServRgn|_DOC|Cat[A-Z0-9_]',re.I)
def category(n,perf_group=None,mod_in_perf=False,aft=False):
    """WinOLS / EZ top folder. perf_group from ez_select.group when module is a performance module."""
    if re.search(r'_SOTF_T(\d)$',n): return f'14 SOTF Steering-Wheel Tune {n[-1]}'
    p=parse(n); mod=p[1] if p else '????'
    if not mod_in_perf and n.startswith(('Cs','Is','Ca','Ct')): return '51 Calibration ID and Checksums'
    if mod_in_perf:
        if aft or EMI_RX.search(n): return '34 Emissions - Regen and SCR Mode Copies of Engine Tables'
        return '%02d %s'%(PERF_NUM[perf_group],PERF_TITLE[perf_group])
    for cat,stems in OTHER:
        if mod[:3] in stems: return cat
    if mod[3]=='D': return '41 Diagnostics - Monitors and Thresholds'
    if mod[3]=='O': return '41 Diagnostics - Monitors and Thresholds'
    if mod[3]=='I': return '28 Other Sensors and Inputs'
    return '99 Other and Miscellaneous'
def subfolder(n,kind_hint=None):
    """second-level folder for performance tables"""
    p=parse(re.sub(r'_SOTF_T\d$','',n))
    if not p: return 'Other'
    body,quals,mode=mode_suffix(p[3])
    if 'Crnkg' in p[3]: return 'Cranking'
    if 'Engine Temp Factor' in quals: return 'Engine Temp Factors'
    if any('PXL' in q for q in quals) or 'PXL' in p[3]: return 'Dynamic Boost (PXL) Factors'
    k=[q for q in quals if q in KIND.values()]
    b=[q for q in quals if q in BARO.values()]
    if mode and mode not in ('C1',): return 'Other Combustion Modes (C2 C3)'
    if k and k[0]!='Base': return {'Air Temp Correction':'Air Temp Corrections','Coolant Temp Correction':'Coolant Temp Corrections','Fuel Temp Correction':'Fuel Temp Corrections',
        'Boost Deviation Correction':'Boost Deviation Corrections','Vehicle Speed Correction':'Vehicle Speed Corrections','Gear Group':'Gear Group Tables'}[k[0]]
    if b: return 'Base Tables - '+b[0]
    if k: return 'Base Tables'
    return None
def clean_note(cm):
    """split a WinOLS comment into (map note, X axis note, Y axis note)"""
    t=cm.replace('\r',' ').replace('\n',' ')
    parts=re.split(r'<br><br>O.{0,3}? ?([XY]):<br>',t)
    main=parts[0]; ax={}
    for i in range(1,len(parts)-1,2): ax[parts[i]]=parts[i+1]
    def c(s): 
        s=re.sub(r'Mapa:|Calibration Note:','',s); s=re.sub(r'<br>',' ',s); s=re.sub(r'<[^>]+>',' ',s)
        s=''.join(ch if 32<=ord(ch)<127 else ' ' for ch in s)
        return re.sub(r'\s+',' ',s).strip()
    return c(main),c(ax.get('X','')),c(ax.get('Y',''))

def _fmtnum(v):
    if v!=v: return 'nan'
    a=abs(v)
    return ('%.0f'%v) if a>=1000 or v==int(v) else ('%.1f'%v) if a>=10 else ('%.2f'%v) if a>=1 else ('%.3g'%v)
def describe(n,r,ctx,sep):
    """detailed description. r = WinOLS definition row (stock definition), ctx = dict, sep = line separator"""
    L=[]; title=readable(n)
    C,R=int(r['Columns']),int(r['Rows']); ty=r['Type']
    shape='single value' if (ty=='eEinzel' or C*R==1) else (f'curve ({C*R} points)' if (ty=='eEindim' or R==1 or C==1) else f'table ({R} rows x {C} columns)')
    L.append(title)
    L.append(f'GM name: {re.sub(r"_SOTF_T[1-5]$","",n) if ctx.get("tune") else n}  |  {shape}  |  units: {ctx.get("unit") or "-"}')
    main,axx,axy=clean_note(ctx.get('comment',r['Comment']))
    if main: L.append('What it does: '+main.replace(' ,',','))
    fn=family_note(n)
    if fn: L.append('Tuning note: '+fn)
    mn=mode_note(n)
    if mn: L.append(mn)
    def axline(w,lab,note):
        a=ctx.get('axes',{}).get(w)
        if not a: return
        nm,unit,first,last,cnt=a
        txt=f'{lab}: {axis_label(nm)} ({cnt} points{", "+unit if unit and unit!="-" else ""}{", "+_fmtnum(first)+" to "+_fmtnum(last) if first is not None else ""})'
        if note: txt+=' - '+note.replace(' ,',',')
        L.append(txt)
    if shape.startswith('table'):
        if ty=='eZweiInv': axline('X','Rows',axx); axline('Y','Columns',axy)
        else: axline('Y','Rows',axy); axline('X','Columns',axx)
    elif shape.startswith('curve'): axline('X' if C>1 or R==1 else 'Y','Axis',axx or axy)
    if ctx.get('vmin') is not None and ctx['vmin']==ctx['vmax']:
        L.append(f'Current value in this bin: {_fmtnum(ctx["vmin"])} {ctx.get("unit") or ""}'.rstrip()+('' if not ctx.get('lbft') else ' (shown in lb-ft - the ECU stores Nm)'))
    elif ctx.get('vmin') is not None:
        L.append(f'Current values in this bin: {_fmtnum(ctx["vmin"])} to {_fmtnum(ctx["vmax"])} {ctx.get("unit") or ""}'.rstrip()+('' if not ctx.get('lbft') else ' (shown in lb-ft - the ECU stores Nm)'))
    if ctx.get('tune'): L.append(f'Steering-wheel tune {ctx["tune"]}: the ECU uses this copy instead of the base table while tune {ctx["tune"]} is selected (HP Tuners SOTF). Tune 0 / SOTF off uses the base table.')
    elif ctx.get('switched'): L.append('Steering-wheel tune 0 (SOTF off) table. Tunes 1-5 each have their own copy in the SOTF folders.')
    elif ctx.get('perf'): L.append('Not switched by the steering-wheel tunes - this table is shared by all six tunes.')
    st=[]
    if ctx.get('edited') is not None: st.append('Edited vs stock P1B: '+('YES' if ctx['edited'] else 'no'))
    if ctx.get('how'): st.append('Address check: '+ctx['how'])
    if ctx.get('cpu') is not None: st.append(f'ECU address 0x{ctx["cpu"]:X}')
    if st: L.append(' | '.join(st))
    return sep.join(L)

AXQ={'nv':'Engine or vehicle speed','n':'Engine speed','cmp':'Load (fuel quantity)','v':'Vehicle speed','T':'Temperature','p':'Pressure','Pct':'Percent','pct':'Percent','t':'Time','M':'Torque','V':'Fuel quantity','phi':'Crank angle',
     'dm':'Mass flow','r':'Ratio','K':'Factor','k':'Factor','e':'Selector','U':'Voltage','m':'Mass','a':'Acceleration','I':'Current','P':'Power','Cnt':'Count','l':'Distance','dp':'Pressure rate','dT':'Temperature rate'}
def axis_label(nm):
    if not nm or nm in ('-',''): return 'Index'
    p=parse(nm)
    if not p: return nm
    lab=AXQ.get(p[2]) or _expand(p[3])
    return f'{lab} ({nm})'
def unique_names(pairs):
    """pairs: list of (gm_name, readable) -> dict gm_name -> unique readable"""
    import collections
    c=collections.Counter(r for _,r in pairs); out={}
    for g,r in pairs: out[g]=r if c[r]==1 else f'{r} ({g})'
    return out

HOW={'os':'confirmed by the HP Tuners SOTF record','code+relocation agree':'ECU code reference + table layout agree','code+neighbours agree':'ECU code reference + neighbouring tables agree',
     'code+content':'ECU code reference + table contents','relocation+neighbours agree':'table layout + neighbouring tables agree','neighbours+content':'neighbouring tables + contents',
     'relocation+content':'table layout + contents','neighbours':'between two code-verified tables','code':'ECU code reference','content':'unique table contents',
     'relocation (one-side neighbour)':'table layout + one neighbouring table','code alignment via 9843':'ECU code aligned against the 9843 bin','from HP Tuners SOTF record':'HP Tuners SOTF record',
     'HPT SOTF descriptor':'HP Tuners SOTF record','axis values matched in 9844':'axis values matched in this bin'}
