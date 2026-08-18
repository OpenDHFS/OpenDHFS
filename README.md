{\rtf1\ansi\ansicpg1252\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\froman\fcharset0 Times-Roman;\f2\froman\fcharset0 Times-Bold;
\f3\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;\red109\green109\blue109;}
{\*\expandedcolortbl;;\cssrgb\c0\c0\c0;\cssrgb\c50196\c50196\c50196;}
{\*\listtable{\list\listtemplateid1\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat0\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid1\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid1}
{\list\listtemplateid2\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat0\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid101\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid2}
{\list\listtemplateid3\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat0\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid201\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid3}
{\list\listtemplateid4\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat0\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid301\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid4}
{\list\listtemplateid5\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat0\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid401\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid5}
{\list\listtemplateid6\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat0\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid501\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid6}
{\list\listtemplateid7\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat0\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid601\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid7}}
{\*\listoverridetable{\listoverride\listid1\listoverridecount0\ls1}{\listoverride\listid2\listoverridecount0\ls2}{\listoverride\listid3\listoverridecount0\ls3}{\listoverride\listid4\listoverridecount0\ls4}{\listoverride\listid5\listoverridecount0\ls5}{\listoverride\listid6\listoverridecount0\ls6}{\listoverride\listid7\listoverridecount0\ls7}}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 # OpenDHFS\
\
**Open-source forensic recovery toolkit for DHFS/DHAV analysis, HEVC reconstruction, and advanced DVR/NVR video recovery.**\
\
OpenDHFS is an experimental open-source forensic toolkit designed to investigate proprietary DVR/NVR storage when conventional recovery workflows appear to have reached their limit.\
\
Its purpose is not to promise that additional evidence exists.\
\
Its purpose is to test whether it does.\
\
---\
\
## Why OpenDHFS Exists\
\
OpenDHFS was created for a forensic recovery problem in which conventional analysis had reached an apparent endpoint.\
\
Usable video had been recovered, but significant portions of the target timeline remained unresolved. There was no clear evidence that additional usable video still existed.\
\
Instead of treating that apparent absence as proof of exhaustion, the investigation continued at the physical, structural, temporal, and codec levels.\
\
That process demonstrated an important principle:\
\
> **An apparently exhausted recovery surface is not necessarily an exhausted evidence source.**\
\
Regions initially presenting as isolated frames, minimal fragments, incomplete structures, or low-support candidates were examined as potential physical and temporal anchors.\
\
In some cases, expansion around those anchors exposed substantially larger recoverable video regions.\
\
OpenDHFS grew from that investigation.\
\
It is intended for the point at which the obvious recovery paths have already been tried and the remaining question is:\
\
**Is there anything else that the surviving structure can still support?**\
\
---\
\
## Recovery Philosophy\
\
OpenDHFS follows a conservative forensic principle:\
\
> **When conventional recovery ends, investigation does not necessarily have to.**\
\
This does not mean that additional video will always be recoverable.\
\
A storage image may genuinely contain no further usable video. Relevant regions may have been overwritten, fragmented beyond reconstruction, corrupted beyond decoder tolerance, or may contain structural patterns that resemble video without supporting valid decoding.\
\
OpenDHFS therefore distinguishes between:\
\
- structural detection;\
- plausible video data;\
- decoder-validated video;\
- recoverable video;\
- and exhausted recovery surfaces.\
\
The existence of one does not automatically prove the next.\
\
OpenDHFS is designed to preserve those distinctions.\
\
---\
\
## Core Principles\
\
### Evidence first\
\
OpenDHFS should never assume that recoverable video exists merely because a structural signature has been detected.\
\
Recovery conclusions must be supported by the surviving evidence.\
\
### Read-only analysis\
\
Forensic source images should be accessed read-only.\
\
OpenDHFS recovery operations are intended to create derived artifacts without modifying the source evidence.\
\
### Physical context matters\
\
A weak or apparently insignificant fragment may still identify a physical region containing additional related data.\
\
OpenDHFS therefore treats physical location as evidence, not merely as an implementation detail.\
\
### Temporal context matters\
\
Surviving timestamps, frame sequences, metadata, and neighboring records can provide recovery context even when higher-level filesystem structures are damaged or unavailable.\
\
### Decoder validation matters\
\
Recognizing HEVC structures is not equivalent to recovering valid video.\
\
Where possible, reconstructed material should be independently validated by established decoders and media inspection tools.\
\
### Negative results matter\
\
A failed reconstruction is still an investigative result.\
\
OpenDHFS records unsuccessful candidates, structurally incomplete regions, and exhausted recovery surfaces rather than silently discarding them.\
\
### No unsupported attribution\
\
OpenDHFS does not assign camera, lens, or channel identity unless surviving evidence supports that conclusion.\
\
---\
\
## Current Scope\
\
OpenDHFS is being developed around forensic analysis and recovery techniques for storage containing DHFS/DHAV structures and HEVC video data commonly encountered in DVR/NVR environments.\
\
The project focuses on techniques including:\
\
- physical image analysis;\
- DHAV record discovery and validation;\
- physical mapping of surviving records;\
- timestamp-guided analysis;\
- video lineage reconstruction;\
- recovery-anchor identification;\
- adaptive physical and temporal expansion;\
- HEVC structural analysis;\
- VPS/SPS/PPS and VCL validation;\
- residual video recovery;\
- decoder-assisted validation;\
- recovery coverage measurement;\
- duplicate detection;\
- and recovery-surface exhaustion auditing.\
\
The architecture is intended to evolve as additional storage layouts, devices, codecs, and recovery scenarios are studied.\
\
---\
\
## Recovery Model\
\
A typical OpenDHFS investigation may conceptually follow this progression:\
\
```text\
Forensic Image\
      |\
      v\
Physical Discovery\
      |\
      v\
DHFS / DHAV Mapping\
      |\
      v\
Temporal and Physical Analysis\
      |\
      v\
Video Lineage Identification\
      |\
      v\
Recovery Anchor Detection\
      |\
      v\
Adaptive Expansion\
      |\
      v\
HEVC Reconstruction\
      |\
      v\
Residual Recovery\
      |\
      v\
Decoder Validation\
      |\
      v\
Coverage and Exhaustion Audit\
      |\
      v\
Recovered Evidence + Technical Report\
\
\pard\pardeftab720\sa240\partightenfactor0

\f1 \cf0 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 Not every investigation requires every stage.\
The surviving evidence determines which recovery paths are technically justified.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Recovery Anchors\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 One of the central concepts behind OpenDHFS is the 
\f2\b recovery anchor
\f1\b0 .\
A candidate that produces little or no immediately useful video should not always be interpreted as worthless.\
Depending on its physical and temporal context, it may indicate proximity to a larger surviving video region.\
Potential anchors may include:\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls1\ilvl0\cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 isolated decodable frames;\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 minimal video fragments;\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 incomplete DHAV sequences;\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 low-support structural candidates;\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 residual frame groups;\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 valid parameter structures;\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 and other physically localized video indicators.\
\pard\pardeftab720\sa240\partightenfactor0
\cf0 OpenDHFS can use these candidates as starting points for controlled expansion rather than treating their initial classification as a final recovery conclusion.\
This distinction is important:\
\pard\pardeftab720\sa240\partightenfactor0

\f2\b \cf0 A weak recovery result may still be a strong recovery lead.
\f1\b0 \
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Structural HEVC Detection\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS distinguishes between finding HEVC-like structures and proving the existence of recoverable HEVC video.\
Analysis may consider structures such as:\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls2\ilvl0\cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 VPS;\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 SPS;\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 PPS;\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 VCL NAL units;\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 IRAP frames;\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 IDR/CRA structures;\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 access unit delimiters;\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 and related HEVC syntax.\
\pard\pardeftab720\sa240\partightenfactor0
\cf0 However:\
\pard\pardeftab720\partightenfactor0

\f3\fs26 \cf0 \
\
HEVC signature\
      !=\
valid HEVC stream\
      !=\
decodable video\
      !=\
forensically relevant video\
\
\pard\pardeftab720\sa240\partightenfactor0

\f1\fs24 \cf0 Where possible, OpenDHFS evaluates parameter-set coherence and uses independent decoding tools to determine whether reconstructed structures represent usable video.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Exhaustion Auditing\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS does not define recovery completion simply as:\
\pard\pardeftab720\sa240\partightenfactor0
\cf0 "The recovery tool finished."\
A recovery process may terminate successfully while potentially valuable regions remain unexplored.\
OpenDHFS therefore supports the concept of a 
\f2\b recovery-surface exhaustion audit
\f1\b0 .\
The objective is to determine whether known high-value recovery surfaces remain, including:\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls3\ilvl0\cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 unexplained DHAV populations;\
\ls3\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 weak residual anchors;\
\ls3\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 untested physical neighborhoods;\
\ls3\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 unidentified video families;\
\ls3\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 structurally significant HEVC territories;\
\ls3\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 and other unresolved recovery candidates.\
\pard\pardeftab720\sa240\partightenfactor0
\cf0 An exhaustion conclusion should describe what was tested and what remains unresolved.\
It should not claim that deleted data never existed or that physically overwritten evidence can be recovered.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 What OpenDHFS Does Not Promise\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS does 
\f2\b not
\f1\b0  guarantee recovery.\
It does not claim that every formatted, deleted, corrupted, or overwritten DVR/NVR recording can be reconstructed.\
It does not assume that every detected DHAV or HEVC structure represents usable video.\
It does not infer camera or channel identity without supporting evidence.\
It does not treat successful media decoding as proof of evidentiary relevance.\
It does not claim complete recovery solely because an automated process completed successfully.\
It cannot recover information that is no longer physically present or sufficiently represented in the available evidence.\
OpenDHFS is an investigative recovery toolkit, not a guarantee of results.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Forensic Integrity\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS is intended to support reproducible forensic workflows.\
Where applicable, recovery operations should preserve or record:\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls4\ilvl0\cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 source image identification;\
\ls4\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 source hashes;\
\ls4\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 physical offsets;\
\ls4\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 input and output lineage;\
\ls4\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 analysis parameters;\
\ls4\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 timestamps;\
\ls4\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 tool versions;\
\ls4\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 derived artifact hashes;\
\ls4\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 validation results;\
\ls4\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 and recovery classifications.\
\pard\pardeftab720\sa240\partightenfactor0
\cf0 Recovered artifacts should always remain distinguishable from original source evidence.\
OpenDHFS should never modify the forensic source image as part of a recovery operation.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Validation\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 A recovered file is not considered reliable solely because an MP4 container can be created.\
Validation may include:\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls5\ilvl0\cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 codec parsing;\
\ls5\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 frame decoding;\
\ls5\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 resolution verification;\
\ls5\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 frame-count analysis;\
\ls5\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 temporal consistency;\
\ls5\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 parameter-set validation;\
\ls5\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 structural continuity;\
\ls5\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 independent FFmpeg/FFprobe inspection;\
\ls5\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 and, where appropriate, visual review.\
\pard\pardeftab720\sa240\partightenfactor0
\cf0 Different levels of validation should be reported explicitly.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Project Origin\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS originated from an extended forensic investigation involving a proprietary DVR/NVR storage image for which conventional recovery approaches had already produced useful results but left significant unresolved areas.\
The project evolved through iterative physical analysis, DHAV mapping, temporal reconstruction, HEVC validation, residual-region analysis, anchor-based expansion, and full-image structural auditing.\
The original investigation demonstrated that regions initially appearing to contain only isolated frames or minimal recoverable material could, in appropriate circumstances, identify substantially larger surviving video regions.\
The public OpenDHFS project extracts the general recovery methodology from that research.\
No case evidence, client information, recovered private footage, or identifying forensic data is included in this repository.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Project Status\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS is currently under active development.\
The first public releases will focus on extracting, cleaning, documenting, and testing the general-purpose techniques developed during the original research process.\
Interfaces, command-line syntax, internal modules, and recovery classifications may change before the project reaches a stable release.\
OpenDHFS should therefore currently be considered:\
\pard\pardeftab720\sa240\partightenfactor0

\f2\b \cf0 Experimental forensic research software.
\f1\b0 \
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Planned Architecture\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 The public implementation is expected to be organized around reusable components rather than the individual experiments from which the methodology originated.\
Planned areas include:\
\pard\pardeftab720\partightenfactor0

\f3\fs26 \cf0 \
\
opendhfs/\
\uc0\u9500 \u9472 \u9472  dhav/\
\uc0\u9474    \u9500 \u9472 \u9472  parser\
\uc0\u9474    \u9500 \u9472 \u9472  validation\
\uc0\u9474    \u9492 \u9472 \u9472  mapping\
\uc0\u9474 \
\uc0\u9500 \u9472 \u9472  hevc/\
\uc0\u9474    \u9500 \u9472 \u9472  nal\
\uc0\u9474    \u9500 \u9472 \u9472  parameter_sets\
\uc0\u9474    \u9492 \u9472 \u9472  reconstruction\
\uc0\u9474 \
\uc0\u9500 \u9472 \u9472  recovery/\
\uc0\u9474    \u9500 \u9472 \u9472  anchors\
\uc0\u9474    \u9500 \u9472 \u9472  expansion\
\uc0\u9474    \u9500 \u9472 \u9472  residual\
\uc0\u9474    \u9492 \u9472 \u9472  lineage\
\uc0\u9474 \
\uc0\u9500 \u9472 \u9472  analysis/\
\uc0\u9474    \u9500 \u9472 \u9472  temporal\
\uc0\u9474    \u9500 \u9472 \u9472  physical\
\uc0\u9474    \u9492 \u9472 \u9472  coverage\
\uc0\u9474 \
\uc0\u9500 \u9472 \u9472  validation/\
\uc0\u9474    \u9500 \u9472 \u9472  decoder\
\uc0\u9474    \u9500 \u9472 \u9472  media\
\uc0\u9474    \u9492 \u9472 \u9472  exhaustion\
\uc0\u9474 \
\uc0\u9492 \u9472 \u9472  reporting/\
\
\pard\pardeftab720\sa240\partightenfactor0

\f1\fs24 \cf0 The historical experimental workflow will be documented separately from the production-oriented implementation.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Requirements\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 Exact requirements will be documented as the public implementation is released.\
Expected dependencies include:\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls6\ilvl0\cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 Python 3;\
\ls6\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 FFmpeg;\
\ls6\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 FFprobe;\
\ls6\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 sufficient local storage for derived recovery artifacts;\
\ls6\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 and read access to a legally obtained forensic image or storage device.\
\pard\pardeftab720\sa240\partightenfactor0
\cf0 Large forensic images may require substantial processing time and storage capacity.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Responsible Use\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS is intended for legitimate forensic research, incident response, data recovery, interoperability research, and authorized analysis.\
Users are responsible for ensuring that they have lawful authority to access and analyze the source media involved.\
The project maintainers do not authorize the use of OpenDHFS to obtain data from systems or storage media without appropriate permission or legal authority.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Documentation\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 Technical documentation will be maintained under:\
\pard\pardeftab720\partightenfactor0

\f3\fs26 \cf0 \
\
docs/\
\
\pard\pardeftab720\sa240\partightenfactor0

\f1\fs24 \cf0 Planned documentation includes:\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls7\ilvl0\cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 DHAV structure notes;\
\ls7\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 recovery methodology;\
\ls7\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 physical mapping;\
\ls7\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 HEVC reconstruction;\
\ls7\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 recovery-anchor methodology;\
\ls7\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 validation criteria;\
\ls7\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 exhaustion auditing;\
\ls7\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 forensic reporting;\
\ls7\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 and research history.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Contributing\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS welcomes technically rigorous contributions related to DVR/NVR storage analysis, DHFS/DHAV structures, video reconstruction, codec analysis, forensic validation, and reproducible recovery methodology.\
Contribution guidelines will be published in 
\f3\fs26 CONTRIBUTING.md
\f1\fs24 .\
When reporting a recovery case or technical issue, contributors must not upload private surveillance footage, confidential evidence, credentials, or other sensitive material to public GitHub issues.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Professional Assistance\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS is an open-source project and may be used independently.\
If you are working with a difficult DVR/NVR recovery case and require assistance with analysis, interpretation, recovery methodology, or development of device-specific recovery techniques, you may contact the OpenDHFS project through the contact information published on the official project profile.\
The availability of professional assistance does not restrict access to the open-source software or its documentation.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Security\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 Security issues should not be disclosed through public GitHub issues.\
A responsible disclosure process will be documented in 
\f3\fs26 SECURITY.md
\f1\fs24 .\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 License\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS will be distributed under an open-source license.\
See 
\f3\fs26 LICENSE
\f1\fs24  for the applicable terms.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Citation\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 Citation information for research, forensic methodology, and academic use will be provided in 
\f3\fs26 CITATION.cff
\f1\fs24 .\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa298\partightenfactor0

\f2\b\fs36 \cf0 \strokec2 Disclaimer\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 OpenDHFS is provided for research, forensic, and authorized recovery purposes.\
Recovery results depend on the physical condition of the source media, surviving data structures, recording format, fragmentation, overwrite history, codec integrity, and other factors outside the control of the software.\
No recovery result should be relied upon without appropriate technical validation.\
The software is provided without any guarantee that additional video or other evidence will be recovered.\
}