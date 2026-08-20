from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class ReportingError(RuntimeError):
    pass


def _connect_ro(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise ReportingError(f"required database not found: {path}")
    return sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)


def _metadata(conn: sqlite3.Connection, table: str) -> dict:
    try:
        rows = conn.execute(f"SELECT key, value FROM {table}").fetchall()
    except sqlite3.OperationalError:
        return {}

    out = {}
    for key, value in rows:
        try:
            out[key] = json.loads(value)
        except Exception:
            out[key] = value
    return out


def _scalar(conn: sqlite3.Connection, sql: str):
    row = conn.execute(sql).fetchone()
    return row[0] if row else 0


def build_report(case_dir: Path, *, overwrite: bool = False) -> dict:
    """
    Build a faithful report from prior OpenDHFS stages.

    REPORT MUST NOT UPGRADE EVIDENCE.
    """
    case_dir = Path(case_dir).resolve()

    scan_path = case_dir / "scan.sqlite"
    analysis_path = case_dir / "analysis.sqlite"
    plan_path = case_dir / "recovery_plan.sqlite"
    recovery_path = case_dir / "recovery.sqlite"
    validation_path = case_dir / "validation.sqlite"

    report_json = case_dir / "report.json"
    report_md = case_dir / "report.md"

    for output in (report_json, report_md):
        if output.exists() and not overwrite:
            raise ReportingError(
                f"{output.name} already exists; use overwrite=True"
            )

    scan = _connect_ro(scan_path)
    analysis = _connect_ro(analysis_path)
    plan = _connect_ro(plan_path)
    recovery = _connect_ro(recovery_path)
    validation = _connect_ro(validation_path)

    scan_meta = _metadata(scan, "metadata")
    plan_meta = _metadata(plan, "planning_metadata")
    recovery_meta = _metadata(recovery, "recovery_metadata")

    dhav_records = _scalar(scan, "SELECT COUNT(*) FROM dhav_records")
    scan_blocks = _scalar(scan, "SELECT COUNT(*) FROM scan_blocks")

    temporal_islands = _scalar(
        analysis, "SELECT COUNT(*) FROM temporal_islands"
    )
    physical_sets = _scalar(
        analysis, "SELECT COUNT(*) FROM physical_sets"
    )
    strong_anchors = _scalar(
        analysis,
        "SELECT COUNT(*) FROM record_analysis WHERE anchor_class='STRONG'"
    )
    weak_anchors = _scalar(
        analysis,
        "SELECT COUNT(*) FROM record_analysis WHERE anchor_class='WEAK'"
    )
    residual_candidates = _scalar(
        analysis,
        "SELECT COUNT(*) FROM record_analysis WHERE residual_candidate=1"
    )

    planned_targets = _scalar(
        plan, "SELECT COUNT(*) FROM recovery_targets"
    )

    tier_counts = dict(
        plan.execute(
            "SELECT tier,COUNT(*) FROM recovery_targets GROUP BY tier"
        ).fetchall()
    )

    recovery_status_counts = dict(
        recovery.execute(
            "SELECT status,COUNT(*) FROM recovery_results GROUP BY status"
        ).fetchall()
    )

    validation_counts = dict(
        validation.execute(
            "SELECT classification,COUNT(*) FROM validation_results GROUP BY classification"
        ).fetchall()
    )

    validated_targets = validation.execute(
        """
        SELECT target_id,candidate_path,codec_name,width,height,
               frames_decoded,candidate_sha256
        FROM validation_results
        WHERE classification='VIDEO_VALIDATED'
        ORDER BY target_id
        """
    ).fetchall()

    nonvalidated_targets = validation.execute(
        """
        SELECT target_id,classification,candidate_path,codec_name,frames_decoded
        FROM validation_results
        WHERE classification<>'VIDEO_VALIDATED'
        ORDER BY target_id
        """
    ).fetchall()

    source = {
        "image_path": scan_meta.get("image_path"),
        "image_size": scan_meta.get("image_size"),
        "source_fingerprint": scan_meta.get("source_fingerprint"),
        "source_access": scan_meta.get("source_access", "READ_ONLY"),
        "camera_channel_assertion": False,
    }

    report = {
        "report_policy": {
            "evidence_upgrade": False,
            "camera_channel_assertion": False,
            "new_forensic_inference": False,
        },
        "source": source,
        "scan": {
            "dhav_records": dhav_records,
            "scan_blocks": scan_blocks,
        },
        "analysis": {
            "temporal_islands": temporal_islands,
            "physical_continuity_sets": physical_sets,
            "strong_anchors": strong_anchors,
            "weak_anchors": weak_anchors,
            "residual_candidates": residual_candidates,
        },
        "plan": {
            "target_count": planned_targets,
            "tiers": {
                "TIER_A_ANCHORED": tier_counts.get("TIER_A_ANCHORED", 0),
                "TIER_B_SUPPORTED": tier_counts.get("TIER_B_SUPPORTED", 0),
                "TIER_C_RESIDUAL": tier_counts.get("TIER_C_RESIDUAL", 0),
            },
            "unresolved_not_scheduled": plan_meta.get(
                "unresolved_not_scheduled", 0
            ),
        },
        "recovery": {
            "status_counts": recovery_status_counts,
            "payload_bytes": recovery_meta.get("payload_bytes", 0),
            "recovery_assertion": False,
        },
        "validation": {
            "classification_counts": validation_counts,
            "validated_targets": [
                {
                    "target_id": row[0],
                    "candidate_path": row[1],
                    "codec_name": row[2],
                    "width": row[3],
                    "height": row[4],
                    "frames_decoded": row[5],
                    "candidate_sha256": row[6],
                }
                for row in validated_targets
            ],
            "nonvalidated_targets": [
                {
                    "target_id": row[0],
                    "classification": row[1],
                    "candidate_path": row[2],
                    "codec_name": row[3],
                    "frames_decoded": row[4],
                }
                for row in nonvalidated_targets
            ],
        },
        "conclusion": {
            "validated_video_targets": validation_counts.get(
                "VIDEO_VALIDATED", 0
            ),
            "partial_decode_targets": validation_counts.get(
                "PARTIAL_DECODE", 0
            ),
            "no_decoded_frames_targets": validation_counts.get(
                "NO_DECODED_FRAMES", 0
            ),
            "decoder_rejected_targets": validation_counts.get(
                "DECODER_REJECTED", 0
            ),
            "bitstream_unrecognized_targets": validation_counts.get(
                "BITSTREAM_UNRECOGNIZED", 0
            ),
            "statement": (
                "Only targets classified by OpenDHFS Validate as "
                "VIDEO_VALIDATED are reported as validated video. "
                "All other recovered payloads remain candidates or "
                "non-validated results."
            ),
        },
    }

    md = [
        "# OpenDHFS Forensic Recovery Report",
        "",
        "## Reporting policy",
        "",
        (
            "This report reproduces findings from prior OpenDHFS stages. "
            "It does not upgrade evidence, infer camera identity from raw "
            "header values, or convert recovered payload into validated "
            "video without decoder-based validation."
        ),
        "",
        "## Source",
        "",
        f"- Source: `{source['image_path']}`",
        f"- Size: {source['image_size']}",
        f"- Fingerprint: `{source['source_fingerprint']}`",
        f"- Access mode: {source['source_access']}",
        "- Camera/channel assertion: No",
        "",
        "## Scan",
        "",
        f"- DHAV records: {dhav_records:,}",
        f"- Completed scan blocks: {scan_blocks:,}",
        "",
        "## Analysis",
        "",
        f"- Temporal islands: {temporal_islands:,}",
        f"- Physical continuity sets: {physical_sets:,}",
        f"- Strong anchors: {strong_anchors:,}",
        f"- Weak anchors: {weak_anchors:,}",
        f"- Residual candidates: {residual_candidates:,}",
        "",
        "## Recovery plan",
        "",
        f"- Targets: {planned_targets:,}",
        f"- Tier A anchored: {tier_counts.get('TIER_A_ANCHORED', 0):,}",
        f"- Tier B supported: {tier_counts.get('TIER_B_SUPPORTED', 0):,}",
        f"- Tier C residual: {tier_counts.get('TIER_C_RESIDUAL', 0):,}",
        (
            f"- Unresolved / not scheduled: "
            f"{plan_meta.get('unresolved_not_scheduled', 0):,}"
        ),
        "",
        "## Recovery",
        "",
    ]

    for status, count in sorted(recovery_status_counts.items()):
        md.append(f"- {status}: {count:,}")

    md.extend(
        [
            f"- Total recovered payload bytes: "
            f"{recovery_meta.get('payload_bytes', 0):,}",
            "",
            "## Validation",
            "",
        ]
    )

    for classification, count in sorted(validation_counts.items()):
        md.append(f"- {classification}: {count:,}")

    md.append("")

    if validated_targets:
        md.extend(["### Validated video targets", ""])
        for row in validated_targets:
            target_id, candidate, codec, width, height, frames, sha256 = row
            md.append(
                f"- `{target_id}` — codec={codec}, {width}x{height}, "
                f"frames={frames}, candidate=`{candidate}`, sha256=`{sha256}`"
            )
        md.append("")

    if nonvalidated_targets:
        md.extend(["### Non-validated targets", ""])
        for row in nonvalidated_targets:
            target_id, classification, candidate, codec, frames = row
            md.append(
                f"- `{target_id}` — {classification}; codec={codec}; "
                f"frames={frames}; candidate=`{candidate}`"
            )
        md.append("")

    md.extend(
        [
            "## Conclusion",
            "",
            report["conclusion"]["statement"],
            "",
            (
                f"Validated video targets: "
                f"{report['conclusion']['validated_video_targets']:,}"
            ),
            "",
        ]
    )

    report_json.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_md.write_text("\n".join(md), encoding="utf-8")

    scan.close()
    analysis.close()
    plan.close()
    recovery.close()
    validation.close()

    return {
        "report_json": str(report_json),
        "report_markdown": str(report_md),
        "validated_video_targets": report["conclusion"]["validated_video_targets"],
        "camera_channel_assertion": False,
        "evidence_upgrade": False,
    }
