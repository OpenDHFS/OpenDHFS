#!/usr/bin/env python3
import argparse
from pathlib import Path
from opendhfs.analysis.analyzer import AnalysisError,analyze_scan
def main():
 p=argparse.ArgumentParser(description="OpenDHFS structural DHAV analyzer"); p.add_argument("case",type=Path); p.add_argument("--temporal-gap",type=float,default=2.0); p.add_argument("--physical-gap",type=int,default=4096); p.add_argument("--overwrite",action="store_true"); a=p.parse_args()
 try:s=analyze_scan(a.case,a.temporal_gap,a.physical_gap,a.overwrite)
 except AnalysisError as e:p.error(str(e))
 print("OpenDHFS Structural Analysis Complete"); print("="*72)
 for k,l in [("dhav_records","DHAV records"),("video_like_records","Video-like records"),("temporal_islands","Temporal islands"),("physical_continuity_sets","Physical continuity sets"),("strong_anchors","Strong anchors"),("weak_anchors","Weak anchors"),("residual_candidates","Residual candidates")]: print(f"{l+':':27}{s[k]:,}")
 print("Camera/channel assertion: No"); print("Recovery assertion:       No")
if __name__=="__main__": main()
