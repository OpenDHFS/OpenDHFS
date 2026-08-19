import sqlite3
from pathlib import Path
from opendhfs.analysis.analyzer import analyze_scan
def mk(case):
 case.mkdir(); c=sqlite3.connect(case/"scan.sqlite"); c.execute("CREATE TABLE dhav_records(absolute_offset INTEGER PRIMARY KEY,frame_type INTEGER,declared_size INTEGER,packed_datetime TEXT,packed_datetime_valid INTEGER,footer_valid INTEGER,annexb_found INTEGER,codec_guess TEXT,confidence_score INTEGER,confidence_grade TEXT)")
 rows=[(100,253,100,"2026-06-30 03:00:00",1,1,1,"H265",100,"A"),(200,252,100,"2026-06-30 03:00:01",1,1,1,"H265",100,"A"),(300,252,100,"2026-06-30 03:00:02",1,1,1,"H265",100,"A"),(10000,252,100,"2026-06-30 03:10:00",1,0,1,"H265",70,"B"),(10100,252,100,"2026-06-30 03:10:01",1,0,1,"H265",70,"B"),(50000,252,100,"2026-06-30 04:00:00",1,0,1,"H265",70,"B"),(90000,240,100,None,0,1,0,"UNKNOWN",30,"C")]
 c.executemany("INSERT INTO dhav_records VALUES(?,?,?,?,?,?,?,?,?,?)",rows); c.commit(); c.close()
def test_analysis(tmp_path:Path):
 case=tmp_path/"case"; mk(case); s=analyze_scan(case,2,0)
 assert (s["dhav_records"],s["video_like_records"],s["temporal_islands"],s["physical_continuity_sets"])==(7,6,3,4)
 assert (s["strong_anchors"],s["weak_anchors"],s["residual_candidates"])==(3,3,1)
def test_membership(tmp_path:Path):
 case=tmp_path/"case"; mk(case); analyze_scan(case,2,0); c=sqlite3.connect(case/"analysis.sqlite")
 rows=c.execute("SELECT absolute_offset,temporal_island_id,physical_set_id,anchor_class,residual_candidate FROM record_analysis ORDER BY absolute_offset").fetchall(); c.close()
 assert rows[0][1:4]==(1,1,"STRONG"); assert rows[3][1:4]==(2,2,"WEAK"); assert rows[5][4]==1; assert rows[6][4]==0
