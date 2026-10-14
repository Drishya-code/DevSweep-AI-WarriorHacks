from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

ROOT = Path(__file__).resolve().parents[1]
W, H = 1920, 1080
BG0=(7,12,24); BG1=(12,22,42); PANEL=(15,28,49); PANEL2=(20,38,64)
WHITE=(239,246,255); MUTED=(153,174,201); CYAN=(54,220,235); BLUE=(78,150,255); PURPLE=(161,113,255)
GREEN=(66,210,145); AMBER=(255,187,79); RED=(255,102,117); STROKE=(46,68,99)
FONT_DIR=Path(r'C:\Windows\Fonts')
FONT_REG=FONT_DIR/'segoeui.ttf'; FONT_BOLD=FONT_DIR/'seguisb.ttf'; FONT_HEAVY=FONT_DIR/'segoeuib.ttf'

def font(size, bold=False):
    path=FONT_HEAVY if bold else FONT_REG
    if bold and not path.exists(): path=FONT_BOLD
    return ImageFont.truetype(str(path), size)

def background(seed=0):
    im=Image.new('RGB',(W,H)); pix=im.load()
    for y in range(H):
        t=y/(H-1)
        col=tuple(int(BG0[i]*(1-t)+BG1[i]*t) for i in range(3))
        for x in range(W): pix[x,y]=col
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(glow)
    gd.ellipse((1250,-260,2050,620),fill=(20,113,255,44))
    gd.ellipse((-300,540,620,1400),fill=(37,211,222,24))
    glow=glow.filter(ImageFilter.GaussianBlur(125)); im=Image.alpha_composite(im.convert('RGBA'),glow)
    d=ImageDraw.Draw(im,'RGBA')
    for x in range(70,W,80): d.line((x,0,x,H),fill=(83,130,192,9),width=1)
    for y in range(70,H,80): d.line((0,y,W,y),fill=(83,130,192,9),width=1)
    return im

def rounded(d, box, fill=PANEL, outline=STROKE, radius=24, width=2):
    d.rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=width)

def text(d,xy,s,size=32,color=WHITE,bold=False,anchor=None): d.text(xy,s,font=font(size,bold),fill=color,anchor=anchor)
def wrap_lines(d,s,f,maxw):
    words=s.split(); lines=[]; cur=''
    for word in words:
        trial=(cur+' '+word).strip()
        if d.textbbox((0,0),trial,font=f)[2] <= maxw: cur=trial
        else:
            if cur: lines.append(cur)
            cur=word
    if cur: lines.append(cur)
    return lines

def paragraph(d,xy,s,size,maxw,color=MUTED,bold=False,leading=1.32):
    f=font(size,bold); x,y=xy
    for line in wrap_lines(d,s,f,maxw):
        d.text((x,y),line,font=f,fill=color); y+=int(size*leading)
    return y

def arrow(d,a,b,color=CYAN,width=5):
    d.line((a,b),fill=color,width=width)
    angle=math.atan2(b[1]-a[1],b[0]-a[0]); size=17
    p1=(b[0]-size*math.cos(angle-.55),b[1]-size*math.sin(angle-.55))
    p2=(b[0]-size*math.cos(angle+.55),b[1]-size*math.sin(angle+.55))
    d.polygon([b,p1,p2],fill=color)

def header(im,kicker,title,subtitle):
    d=ImageDraw.Draw(im,'RGBA'); d.rounded_rectangle((92,76,110,144),radius=7,fill=CYAN)
    text(d,(140,79),kicker.upper(),22,CYAN,True)
    text(d,(92,157),title,54,WHITE,True)
    text(d,(94,229),subtitle,25,MUTED)
    d.line((92,287,W-92,287),fill=(67,95,132,150),width=2)
    text(d,(94,H-62),'DEVSWEEP AI   â€¢   CLEAN. KEEP. RESTORE.',19,(112,151,196),True)
    return d

def save(im,name):
    # Keep generated explainers and historical evidence cards out of the
    # Devpost upload root. Only the cover and the two implementation diagrams
    # are intended as designed gallery assets.
    designed_names={'01-cover.png','09-system-architecture.png','10-cleanup-workflow.png'}
    path=(ROOT/name) if name in designed_names else (ROOT/'source-assets'/'designed'/name)
    path.parent.mkdir(parents=True,exist_ok=True); im.convert('RGB').save(path,'PNG',optimize=True)

# 01 â€” cover: existing mascot art plus separately typeset title.
im=background(); d=ImageDraw.Draw(im,'RGBA')
text(d,(115,100),'HACKATHON PROJECT',22,CYAN,True)
logo=Image.open(ROOT/'source-assets'/'devsweep-neon-logo.png').convert('RGB')
mascot=logo.crop((250,100,1030,830)); mascot.thumbnail((700,700),Image.Resampling.LANCZOS)
rounded(d,(88,196,824,932),(8,13,27,235),(53,94,151),38,3)
im.paste(mascot,(106+(700-mascot.width)//2,212+(690-mascot.height)//2))
d=ImageDraw.Draw(im,'RGBA')
text(d,(914,284),'DEVSWEEP',31,(170,198,231),True)
text(d,(904,354),'DevSweep AI',89,WHITE,True)
d.rounded_rectangle((914,485,1244,494),radius=5,fill=CYAN)
text(d,(914,548),'Clean. Keep. Restore.',43,BLUE,True)
paragraph(d,(918,639),'Safety-first workspace hygiene',33,760,MUTED)
text(d,(918,835),'React + Vite   /   FastAPI   /   Optional Nebius AI',22,(164,190,220))
text(d,(918,911),'Built by an individual developer',21,(125,152,187))
save(im,'01-cover.png')

# 04 â€” designed frame around an authentic provider/model status capture.
im=background(); d=header(im,'Earlier recorded run','AI analysis in the application','Genuine application status crop from the supplied screen recording.')
rounded(d,(110,350,1808,754),(13,25,44,248),(53,84,128),30,2)
ui=Image.open(ROOT/'source-assets'/'04-ai-status-ui-crop.png').convert('RGB')
ui=ui.resize((1600,188),Image.Resampling.LANCZOS)
im.paste(ui,(154,398))
d=ImageDraw.Draw(im,'RGBA')
text(d,(155,638),'The app displayed the Nebius provider and NVIDIA Nemotron model after analysis.',25,WHITE,True)
text(d,(155,690),'Earlier live request success is documented in ../demo/verification-report.md; this is not a current status.',20,AMBER,True)
save(im,'04-live-ai-analysis.png')
# 05 â€” implementation-aligned risk explanation.
im=background(); d=header(im,'Deterministic scanner','Risk-aware review','Scanner classifications anchor the review; AI can increase risk, never replace scanner validation.')
items=[('SAFE','Known regenerable patterns',GREEN,'Examples: build output, caches, temporary files. Candidate must still pass scanner allowlisting.'),('CAUTION','Uncertain or large directories',AMBER,'Requires explicit user approval when included in a deletion plan.'),('DANGEROUS','Never eligible for cleanup',RED,'Protected or disallowed paths are rejected by backend checks.')]
for i,(name,title,col,desc) in enumerate(items):
    x=105+i*585; rounded(d,(x,356,x+535,734),(14,27,47,245),(54,76,108),28,2)
    d.rounded_rectangle((x+34,391,x+215,451),radius=19,fill=(col[0],col[1],col[2],33),outline=col,width=2)
    text(d,(x+64,401),name,25,col,True)
    paragraph(d,(x+34,492),title,30,450,WHITE,True)
    d.line((x+34,578,x+490,578),fill=STROKE,width=2)
    paragraph(d,(x+34,610),desc,22,450,MUTED)
text(d,(110,807),'AI may raise the effective risk. It cannot turn an unvalidated path into a permitted candidate.',24,CYAN,True)
text(d,(110,871),'Summary of backend implementation; not a screenshot of a live classification panel.',19,MUTED)
save(im,'05-risk-classification.png')

# 07 â€” architecture checked against backend route and scanner code.
im=background(); d=header(im,'System design','A guarded path from UI to filesystem','AI informs the review; deterministic backend checks and user approval govern execution.')
cols=[100,550,1000,1450]; y1=364; y2=676
nodes=[
 (cols[0],y1,'01  INTERFACE','React + Vite','Workspace selection, scan review, plan and explicit approval.'),
 (cols[1],y1,'02  API','FastAPI â€¢ loopback','CORS allowlist; route handlers; project-scoped requests.'),
 (cols[2],y1,'03  ACCESS','Workspace grant','Canonical path, directory identity and revalidation.'),
 (cols[3],y1,'04  SCANNER','Deterministic rules','Find candidates, classify risk and protect project files.'),
 (cols[3],y2,'05  OPTIONAL AI','Nebius provider','Explains candidates; returned analysis is tied to the project.'),
 (cols[2],y2,'06  PLAN CHECKS','Server re-scan','Candidate allowlist and effective risk are checked again.'),
 (cols[1],y2,'07  USER GATE','Explicit approval','No chat action triggers cleanup; the app approval is required.'),
 (cols[0],y2,'08  OPERATIONS','Backup â†’ cleanup','Verified backup before deletion; restore validates and avoids overwrite.'),
]
for x,y,k,t,desc in nodes:
    rounded(d,(x,y,x+390,y+214),(14,28,49,250),(58,82,117),25,2)
    text(d,(x+25,y+22),k,17,CYAN,True); text(d,(x+25,y+62),t,27,WHITE,True); paragraph(d,(x+25,y+110),desc,18,337,MUTED)
for i in range(3): arrow(d,(cols[i]+398,y1+106),(cols[i+1]-14,y1+106),CYAN,5)
arrow(d,(cols[3]+194,y1+226),(cols[3]+194,y2-18),PURPLE,5)
for i in range(3,0,-1): arrow(d,(cols[i]+10,y2+106),(cols[i-1]+398,y2+106),BLUE,5)
text(d,(110,949),'Backup bytes and source integrity are verified before removal; restore revalidates access and will not overwrite.',19,(170,198,229))
save(im,'09-system-architecture.png')

# 10 â€” workflow in two rows, serpentine sequence.
im=background(); d=header(im,'User journey','Review first. Approve explicitly.','A workspace-scoped flow with path checks around filesystem operations.')
steps=[
 ('1','Choose workspace','Select the synthetic sandbox or an authorized project folder.',CYAN),
 ('2','Validate path','Resolve and register exact project directory.',CYAN),
 ('3','Scan','Find known candidates and assign deterministic risk.',BLUE),
 ('4','AI analysis','Optional provider explains the real scan findings.',PURPLE),
 ('5','Review plan','Server validates analysis and re-scans candidates.',BLUE),
 ('6','Approve','User confirms in the application; no chat execution.',AMBER),
 ('7','Revalidate','Check project authorization and allowed paths again.',AMBER),
 ('8','Back up','Copy and verify backup before each deletion.',CYAN),
 ('9','Clean','Execute only plan items allowed by backend checks.',BLUE),
 ('10','Verify / restore','Check protected files; restore verified backup without overwrite.',GREEN),
]
xs=[90,450,810,1170,1530]; cardw=280; rows=[390,662]; cardh=202
for i,(n,title,desc,col) in enumerate(steps):
    row=0 if i<5 else 1; colidx=i if row==0 else 9-i; x=xs[colidx]; y=rows[row]
    rounded(d,(x,y,x+cardw,y+cardh),(14,28,49,250),(57,80,114),25,2)
    d.ellipse((x+20,y+20,x+68,y+68),fill=(col[0],col[1],col[2],45),outline=col,width=2)
    d.text((x+44,y+44),n,font=font(23,True),fill=WHITE,anchor="mm")
    paragraph(d,(x+20,y+88),title,24,240,WHITE,True)
    paragraph(d,(x+20,y+130),desc,16,240,MUTED,leading=1.25)
for i in range(4): arrow(d,(xs[i]+cardw+5,rows[0]+101),(xs[i+1]-14,rows[0]+101),CYAN,4)
arrow(d,(xs[4]+cardw//2,rows[0]+cardh+9),(xs[4]+cardw//2,rows[1]-15),PURPLE,4)
for i in range(4,0,-1): arrow(d,(xs[i]+3,rows[1]+101),(xs[i-1]+cardw+14,rows[1]+101),BLUE,4)
text(d,(110,932),'The AI recommendation is advisory; scanner allowlists, approval, backup checks and authorization remain backend-enforced.',19,(170,198,229))
save(im,'10-cleanup-workflow.png')

# 09 â€” factual summary card based on verification report.
im=background(); d=header(im,'Earlier synthetic run','Verification after cleanup','The recorded run reported one approved item removed and the protected project files preserved.')
metrics=[('1 / 1','item deleted',GREEN),('0','items failed',CYAN),('PASS','post-cleanup checks',GREEN)]
for i,(value,label,col) in enumerate(metrics):
    x=108+i*586; rounded(d,(x,375,x+540,620),(14,28,49,250),(52,82,110),26)
    text(d,(x+36,422),value,62,col,True); text(d,(x+36,518),label,25,WHITE)
rounded(d,(108,680,1800,861),(13,25,44,245),(52,82,110),24)
text(d,(150,713),'PRESERVED',19,CYAN,True)
text(d,(150,761),'src/ and package.json',31,WHITE,True)
text(d,(880,713),'CONTEXT',19,AMBER,True)
paragraph(d,(880,760),'The fixture was not a Git repository; Git integrity was skipped.',23,820,MUTED)
text(d,(110,902),'Historical application result from verification-report.md; this is a designed evidence summary, not a screenshot.',19,MUTED)
save(im,'09-verification.png')

# 10 â€” restore evidence card with the historical recorded digest.
im=background(); d=header(im,'Earlier synthetic run','Restore with integrity evidence','A verified backup was restored without overwriting an existing destination.')
rounded(d,(112,366,1808,772),(13,25,44,248),(55,83,117),30,2)
text(d,(164,411),'RESTORE STATUS',20,CYAN,True)
text(d,(164,464),'Completed',56,GREEN,True)
text(d,(164,552),'temp-artifact.tmp  â€¢  98,304 bytes',27,WHITE)
d.line((164,615,1746,615),fill=STROKE,width=2)
text(d,(164,650),'SHA-256 recorded after restore',19,MUTED,True)
text(d,(164,692),'3CA214406425182510CF49A0EB3EA233D5CA5A81FF4DA343E47762F4DEB982BC',23,(196,215,241))
text(d,(112,825),'The verification report records this as a match to the pre-cleanup artifact hash.',21,WHITE,True)
text(d,(112,884),'Historical report evidence; not extracted from the supplied screen recordings.',19,AMBER,True)
save(im,'10-restoration-proof.png')

# 12 â€” current checkout test/build evidence.
im=background(); d=header(im,'Current checkout â€¢ 13 October 2026','Quality checks passed','Fresh results from this repository working tree.')
checks=[('BACKEND','123 passed','3 skipped â€¢ 1 deprecation warning',CYAN),('FRONTEND','66 passed','13 test files',BLUE),('PRODUCTION BUILD','Succeeded','TypeScript + Vite production output',GREEN)]
for i,(label,result,detail,col) in enumerate(checks):
    x=108+i*586; rounded(d,(x,388,x+540,690),(14,28,49,250),(52,80,113),28,2)
    text(d,(x+34,427),label,20,col,True)
    paragraph(d,(x+34,488),result,40,470,WHITE,True)
    paragraph(d,(x+34,568),detail,20,470,MUTED)
rounded(d,(110,760,1800,870),(13,25,44,245),(52,82,110),22)
text(d,(146,787),'Commands:',18,CYAN,True)
text(d,(286,783),r'backend: .venv\Scripts\python.exe -m pytest -q -p no:cacheprovider',17,WHITE)
text(d,(286,817),'frontend: npm.cmd test -- --reporter=dot  â€¢  npm.cmd run build',17,WHITE)
text(d,(110,912),'No application behavior was changed to produce this evidence graphic.',19,MUTED)
save(im,'12-testing-evidence.png')
# 13 â€” implemented capability summary.
im=background(); d=header(im,'Project highlights','Cleanup with a recovery path','Capabilities grounded in the current React and FastAPI implementation.')
highlights=[('01','Workspace-scoped access','Canonical folder registration and grant revalidation.'),('02','Explainable candidates','Deterministic scanner results with optional AI context.'),('03','Risk-aware plans','Backend rescans the workspace and checks eligible paths.'),('04','Human approval','Explicit approval gate before eligible cleanup execution.'),('05','Verified backup','Backup manifest and file content checked before deletion.'),('06','Restore safeguards','Integrity verification and no-overwrite restoration behavior.')]
for i,(n,title,desc) in enumerate(highlights):
    col=i%3; row=i//3; x=105+col*585; y=365+row*255
    rounded(d,(x,y,x+535,y+215),(14,28,49,250),(54,78,110),25,2)
    text(d,(x+28,y+25),n,18,CYAN,True)
    paragraph(d,(x+28,y+67),title,27,475,WHITE,True)
    paragraph(d,(x+28,y+125),desc,19,470,MUTED)
text(d,(110,915),'No universal safety or guaranteed recovery claim: operations remain constrained by the checks above.',20,(170,198,229))
save(im,'13-project-highlights.png')

# 14 â€” closing card.
im=background(); d=ImageDraw.Draw(im,'RGBA')
logo=Image.open(ROOT/'source-assets'/'devsweep-neon-logo.png').convert('RGB').crop((250,100,1030,850)); logo.thumbnail((560,560),Image.Resampling.LANCZOS)
rounded(d,(125,205,790,870),(8,13,27,235),(50,96,152),40,3)
im.paste(logo,(158+(600-logo.width)//2,226+(620-logo.height)//2))
d=ImageDraw.Draw(im,'RGBA'); text(d,(900,300),'DevSweep AI',76,WHITE,True)
text(d,(904,414),'CLEAN. KEEP. RESTORE.',35,CYAN,True)
text(d,(904,506),'Safety-first workspace hygiene',30,MUTED)
d.line((904,590,1740,590),fill=(63,93,132,190),width=2)
text(d,(904,650),'Explore the project',20,(158,190,224),True)
text(d,(904,704),'github.com/Drishya-code/DevSweep-AI',28,WHITE)
text(d,(904,846),'Built by an individual developer',20,(126,157,194))
save(im,'14-closing-card.png')
