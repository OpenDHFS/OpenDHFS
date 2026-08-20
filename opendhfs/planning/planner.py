from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class PlanningError(RuntimeError):
    pass


PLAN_SCHEMA = """
CREATE TABLE recovery_targets(
    target_id TEXT PRIMARY KEY,
    priority INTEGER NOT NULL,
    tier TEXT NOT NULL,
    strategy TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset_exclusive INTEGER NOT NULL,
    temporal_start TEXT,
    temporal_end TEXT,
    record_count INTEGER NOT NULL,
    strong_anchors INTEGER NOT NULL,
    weak_anchors INTEGER NOT NULL,
    reason TEXT NOT NULL
);

CREATE TABLE planning_metadata(
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _connect_ro(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise PlanningError(f"required database not found: {path}")

    return sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )


def _last_record_end(
    scan: sqlite3.Connection,
    last_offset: int,
) -> int:
    row = scan.execute(
        """
        SELECT declared_size
        FROM dhav_records
        WHERE absolute_offset = ?
        """,
        (last_offset,),
    ).fetchone()

    if row is None:
        raise PlanningError(
            f"declared_size not found for offset {last_offset}"
        )

    declared_size = int(row[0])

    return last_offset + declared_size


def _write_target(
    plan: sqlite3.Connection,
    *,
    target_id: str,
    priority: int,
    tier: str,
    strategy: str,
    start_offset: int,
    end_offset_exclusive: int,
    temporal_start: str | None,
    temporal_end: str | None,
    record_count: int,
    strong_anchors: int,
    weak_anchors: int,
    reasons: list[str],
) -> None:
    plan.execute(
        """
        INSERT INTO recovery_targets(
            target_id,
            priority,
            tier,
            strategy,
            start_offset,
            end_offset_exclusive,
            temporal_start,
            temporal_end,
            record_count,
            strong_anchors,
            weak_anchors,
            reason
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            target_id,
            priority,
            tier,
            strategy,
            start_offset,
            end_offset_exclusive,
            temporal_start,
            temporal_end,
            record_count,
            strong_anchors,
            weak_anchors,
            "|".join(reasons),
        ),
    )


def build_recovery_plan(
    case_dir: Path,
    *,
    overwrite: bool = False,
) -> dict:
    case_dir = Path(case_dir).resolve()

    scan_path = case_dir / "scan.sqlite"
    analysis_path = case_dir / "analysis.sqlite"
    plan_path = case_dir / "recovery_plan.sqlite"
    json_path = case_dir / "recovery_plan.json"

    if plan_path.exists():
        if not overwrite:
            raise PlanningError(
                "recovery_plan.sqlite already exists; use overwrite=True"
            )
        plan_path.unlink()

    scan = _connect_ro(scan_path)
    analysis = _connect_ro(analysis_path)

    plan = sqlite3.connect(plan_path)
    plan.executescript(PLAN_SCHEMA)

    targets: list[dict] = []

    target_number = 0
    priority = 0

    #
    # TIER A
    # Strong anchors supported by a physical continuity set.
    #
    for row in analysis.execute(
        """
        SELECT
            p.set_id,
            p.first_offset,
            p.last_offset,
            p.record_count,
            p.strong_anchor_count,
            p.weak_anchor_count,
            MIN(t.start_datetime),
            MAX(t.end_datetime)
        FROM physical_sets AS p
        JOIN record_analysis AS r
            ON r.physical_set_id = p.set_id
        LEFT JOIN temporal_islands AS t
            ON t.island_id = r.temporal_island_id
        WHERE p.strong_anchor_count > 0
        GROUP BY
            p.set_id,
            p.first_offset,
            p.last_offset,
            p.record_count,
            p.strong_anchor_count,
            p.weak_anchor_count
        ORDER BY p.first_offset
        """
    ):
        (
            set_id,
            first_offset,
            last_offset,
            record_count,
            strong_count,
            weak_count,
            temporal_start,
            temporal_end,
        ) = row

        target_number += 1
        priority += 1
        target_id = f"TGT-{target_number:06d}"

        end_offset = _last_record_end(
            scan,
            last_offset,
        )

        reasons = [
            "STRONG_ANCHOR_PRESENT",
            "PHYSICAL_CONTINUITY_SUPPORTED",
        ]

        if temporal_start is not None:
            reasons.append("TEMPORAL_CONTINUITY_SUPPORTED")

        _write_target(
            plan,
            target_id=target_id,
            priority=priority,
            tier="TIER_A_ANCHORED",
            strategy="PHYSICAL_CONTINUITY",
            start_offset=first_offset,
            end_offset_exclusive=end_offset,
            temporal_start=temporal_start,
            temporal_end=temporal_end,
            record_count=record_count,
            strong_anchors=strong_count,
            weak_anchors=weak_count,
            reasons=reasons,
        )

        targets.append(
            {
                "target_id": target_id,
                "priority": priority,
                "tier": "TIER_A_ANCHORED",
                "strategy": "PHYSICAL_CONTINUITY",
                "start_offset": first_offset,
                "end_offset_exclusive": end_offset,
                "temporal_start": temporal_start,
                "temporal_end": temporal_end,
                "record_count": record_count,
                "strong_anchors": strong_count,
                "weak_anchors": weak_count,
                "reason": reasons,
            }
        )

    #
    # TIER B
    # Weak anchors supported by a multi-record physical set.
    #
    for row in analysis.execute(
        """
        SELECT
            p.set_id,
            p.first_offset,
            p.last_offset,
            p.record_count,
            p.strong_anchor_count,
            p.weak_anchor_count,
            MIN(t.start_datetime),
            MAX(t.end_datetime)
        FROM physical_sets AS p
        JOIN record_analysis AS r
            ON r.physical_set_id = p.set_id
        LEFT JOIN temporal_islands AS t
            ON t.island_id = r.temporal_island_id
        WHERE p.strong_anchor_count = 0
          AND p.weak_anchor_count > 0
          AND p.record_count > 1
        GROUP BY
            p.set_id,
            p.first_offset,
            p.last_offset,
            p.record_count,
            p.strong_anchor_count,
            p.weak_anchor_count
        ORDER BY p.first_offset
        """
    ):
        (
            set_id,
            first_offset,
            last_offset,
            record_count,
            strong_count,
            weak_count,
            temporal_start,
            temporal_end,
        ) = row

        target_number += 1
        priority += 1
        target_id = f"TGT-{target_number:06d}"

        end_offset = _last_record_end(
            scan,
            last_offset,
        )

        reasons = [
            "WEAK_ANCHOR_PRESENT",
            "MULTI_RECORD_PHYSICAL_SUPPORT",
        ]

        if temporal_start is not None:
            reasons.append("TEMPORAL_SUPPORT_PRESENT")

        _write_target(
            plan,
            target_id=target_id,
            priority=priority,
            tier="TIER_B_SUPPORTED",
            strategy="PHYSICAL_CONTINUITY",
            start_offset=first_offset,
            end_offset_exclusive=end_offset,
            temporal_start=temporal_start,
            temporal_end=temporal_end,
            record_count=record_count,
            strong_anchors=strong_count,
            weak_anchors=weak_count,
            reasons=reasons,
        )

        targets.append(
            {
                "target_id": target_id,
                "priority": priority,
                "tier": "TIER_B_SUPPORTED",
                "strategy": "PHYSICAL_CONTINUITY",
                "start_offset": first_offset,
                "end_offset_exclusive": end_offset,
                "temporal_start": temporal_start,
                "temporal_end": temporal_end,
                "record_count": record_count,
                "strong_anchors": strong_count,
                "weak_anchors": weak_count,
                "reason": reasons,
            }
        )

    #
    # TIER C
    # Residual isolated video-like candidates.
    #
    for row in analysis.execute(
        """
        SELECT
            r.absolute_offset,
            r.temporal_island_id,
            r.physical_set_id
        FROM record_analysis AS r
        WHERE r.residual_candidate = 1
        ORDER BY r.absolute_offset
        """
    ):
        (
            absolute_offset,
            temporal_island_id,
            physical_set_id,
        ) = row

        scan_row = scan.execute(
            """
            SELECT
                declared_size,
                packed_datetime
            FROM dhav_records
            WHERE absolute_offset = ?
            """,
            (absolute_offset,),
        ).fetchone()

        if scan_row is None:
            raise PlanningError(
                f"scan record not found for residual offset "
                f"{absolute_offset}"
            )

        declared_size = int(scan_row[0])
        packed_datetime = scan_row[1]

        target_number += 1
        priority += 1
        target_id = f"TGT-{target_number:06d}"

        end_offset = absolute_offset + declared_size

        reasons = [
            "RESIDUAL_VIDEO_LIKE_RECORD",
            "NOT_EXPLAINED_BY_SUPPORTED_GROUP",
        ]

        _write_target(
            plan,
            target_id=target_id,
            priority=priority,
            tier="TIER_C_RESIDUAL",
            strategy="ISOLATED_RECORD",
            start_offset=absolute_offset,
            end_offset_exclusive=end_offset,
            temporal_start=packed_datetime,
            temporal_end=packed_datetime,
            record_count=1,
            strong_anchors=0,
            weak_anchors=1,
            reasons=reasons,
        )

        targets.append(
            {
                "target_id": target_id,
                "priority": priority,
                "tier": "TIER_C_RESIDUAL",
                "strategy": "ISOLATED_RECORD",
                "start_offset": absolute_offset,
                "end_offset_exclusive": end_offset,
                "temporal_start": packed_datetime,
                "temporal_end": packed_datetime,
                "record_count": 1,
                "strong_anchors": 0,
                "weak_anchors": 1,
                "reason": reasons,
            }
        )

    unresolved_not_scheduled = analysis.execute(
        """
        SELECT COUNT(*)
        FROM record_analysis
        WHERE anchor_class = 'NONE'
          AND residual_candidate = 0
        """
    ).fetchone()[0]

    tier_a = sum(
        target["tier"] == "TIER_A_ANCHORED"
        for target in targets
    )

    tier_b = sum(
        target["tier"] == "TIER_B_SUPPORTED"
        for target in targets
    )

    tier_c = sum(
        target["tier"] == "TIER_C_RESIDUAL"
        for target in targets
    )

    summary = {
        "target_count": len(targets),
        "tier_a": tier_a,
        "tier_b": tier_b,
        "tier_c": tier_c,
        "unresolved_not_scheduled": unresolved_not_scheduled,
        "recovery_assertion": False,
        "camera_channel_assertion": False,
        "plan_database": str(plan_path),
    }

    for key, value in summary.items():
        plan.execute(
            """
            INSERT INTO planning_metadata(key, value)
            VALUES(?, ?)
            """,
            (
                key,
                json.dumps(
                    value,
                    ensure_ascii=False,
                ),
            ),
        )

    plan.commit()
    plan.close()

    scan.close()
    analysis.close()

    json_path.write_text(
        json.dumps(
            {
                "summary": summary,
                "targets": targets,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return summary