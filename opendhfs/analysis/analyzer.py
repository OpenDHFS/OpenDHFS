from __future__ import annotations
import json, sqlite3
from datetime import datetime
from pathlib import Path

class AnalysisError(RuntimeError): pass

def _anchor(row):
    off,ft,size,dt,dv,fv,ab,codec,score,grade=row
    video=ft in (0xFC,0xFD); known=codec in ("H264","H265")
    reasons=[]
    if dv: reasons.append("VALID_PACKED_DATETIME")
    if fv: reasons.append("VALID_DHAV_FOOTER")
    if ab: reasons.append("ANNEXB_FOUND")
    if known: reasons.append("CODEC_RECOGNIZED")
    if video: reasons.append("VIDEO_LIKE_FRAME_TYPE")
    if grade=="A": reasons.append("GRADE_A")
    if dv and fv and ab and known and video and grade=="A": return "STRONG","|".join(reasons)
    if sum(map(bool,(dv,fv,ab,known,video,grade in ("A","B"))))>=3: return "WEAK","|".join(reasons)
    return "NONE","|".join(reasons)

def analyze_scan(case_dir:Path,temporal_gap_seconds:float=2.0,physical_gap_bytes:int=4096,overwrite:bool=False):
    case_dir=Path(case_dir).resolve(); scanp=case_dir/"scan.sqlite"; outp=case_dir/"analysis.sqlite"
    if not scanp.exists(): raise AnalysisError("scan.sqlite not found")
    if outp.exists():
        if not overwrite: raise AnalysisError("analysis.sqlite exists; use --overwrite")
        outp.unlink()
    scan=sqlite3.connect(f"file:{scanp}?mode=ro",uri=True); out=sqlite3.connect(outp)
    out.executescript("""
    CREATE TABLE record_analysis(
    absolute_offset INTEGER PRIMARY KEY,
    temporal_island_id INTEGER,
    physical_set_id INTEGER,
    anchor_class TEXT,
    video_like INTEGER NOT NULL,
    residual_candidate INTEGER,
    reasons TEXT
    );    
    CREATE TABLE temporal_islands(island_id INTEGER PRIMARY KEY,start_datetime TEXT,end_datetime TEXT,first_offset INTEGER,last_offset INTEGER,record_count INTEGER,strong_anchor_count INTEGER,weak_anchor_count INTEGER);
    CREATE TABLE physical_sets(set_id INTEGER PRIMARY KEY,first_offset INTEGER,last_offset INTEGER,record_count INTEGER,strong_anchor_count INTEGER,weak_anchor_count INTEGER);
    """)
    rowsql="SELECT absolute_offset,frame_type,declared_size,packed_datetime,packed_datetime_valid,footer_valid,annexb_found,codec_guess,confidence_score,confidence_grade FROM dhav_records"
    total=video=strong=weak=0
    for r in scan.execute(rowsql+" ORDER BY absolute_offset"):
        a,reasons=_anchor(r); total+=1; video+=r[1] in (252,253); strong+=a=="STRONG"; weak+=a=="WEAK"
        out.execute(
    "INSERT INTO record_analysis VALUES(?,?,?,?,?,?,?)",
    (
        r[0],
        None,
        None,
        a,
        int(r[1] in (0xFC, 0xFD)),
        0,
        reasons,
    ),
    )
    out.commit()
    # temporal streaming
    iid=0; state=None; members=[]
    for off,text in scan.execute("SELECT absolute_offset,packed_datetime FROM dhav_records WHERE packed_datetime_valid=1 AND packed_datetime IS NOT NULL ORDER BY packed_datetime,absolute_offset"):
        cur=datetime.fromisoformat(text)
        if state is None or (cur-state["last"]).total_seconds()>temporal_gap_seconds:
            if state:
                out.execute("INSERT INTO temporal_islands VALUES(?,?,?,?,?,?,?,?)",(iid,state["start"].isoformat(sep=" "),state["last"].isoformat(sep=" "),state["first"],state["lastoff"],state["n"],state["s"],state["w"]))
                out.executemany("UPDATE record_analysis SET temporal_island_id=? WHERE absolute_offset=?",members)
            iid+=1; state={"start":cur,"last":cur,"first":off,"lastoff":off,"n":0,"s":0,"w":0}; members=[]
        a=out.execute("SELECT anchor_class FROM record_analysis WHERE absolute_offset=?",(off,)).fetchone()[0]
        state["last"]=cur; state["lastoff"]=off; state["n"]+=1; state["s"]+=a=="STRONG"; state["w"]+=a=="WEAK"; members.append((iid,off))
    if state:
        out.execute("INSERT INTO temporal_islands VALUES(?,?,?,?,?,?,?,?)",(iid,state["start"].isoformat(sep=" "),state["last"].isoformat(sep=" "),state["first"],state["lastoff"],state["n"],state["s"],state["w"]))
        out.executemany("UPDATE record_analysis SET temporal_island_id=? WHERE absolute_offset=?",members)
    # physical streaming
    sid=0; st=None; members=[]
    for r in scan.execute(rowsql+" ORDER BY absolute_offset"):
        off,size=r[0],r[2]; gap=None if st is None else off-st["end"]
        if st is None or gap<0 or gap>physical_gap_bytes:
            if st:
                out.execute("INSERT INTO physical_sets VALUES(?,?,?,?,?,?)",(sid,st["first"],st["last"],st["n"],st["s"],st["w"]))
                out.executemany("UPDATE record_analysis SET physical_set_id=? WHERE absolute_offset=?",members)
            sid+=1; st={"first":off,"last":off,"end":off+size,"n":0,"s":0,"w":0}; members=[]
        a=out.execute("SELECT anchor_class FROM record_analysis WHERE absolute_offset=?",(off,)).fetchone()[0]
        st["last"]=off; st["end"]=off+size; st["n"]+=1; st["s"]+=a=="STRONG"; st["w"]+=a=="WEAK"; members.append((sid,off))
    if st:
        out.execute("INSERT INTO physical_sets VALUES(?,?,?,?,?,?)",(sid,st["first"],st["last"],st["n"],st["s"],st["w"]))
        out.executemany("UPDATE record_analysis SET physical_set_id=? WHERE absolute_offset=?",members)
    out.execute("""
    UPDATE record_analysis
    SET residual_candidate = 1
    WHERE absolute_offset IN (
        SELECT r.absolute_offset
        FROM record_analysis AS r
        LEFT JOIN temporal_islands AS t
            ON t.island_id = r.temporal_island_id
        LEFT JOIN physical_sets AS p
            ON p.set_id = r.physical_set_id
        WHERE r.video_like = 1
          AND r.anchor_class <> 'STRONG'
          AND COALESCE(t.record_count, 0) <= 1
          AND COALESCE(p.record_count, 0) <= 1
    )
    """)
    out.commit()
    residual=out.execute("SELECT COUNT(*) FROM record_analysis WHERE residual_candidate=1").fetchone()[0]
    summary={"dhav_records":total,"video_like_records":video,"temporal_islands":iid,"physical_continuity_sets":sid,"strong_anchors":strong,"weak_anchors":weak,"residual_candidates":residual,"camera_channel_assertion":False,"recovery_assertion":False}
    (case_dir/"analysis_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    scan.close(); out.close(); return summary
