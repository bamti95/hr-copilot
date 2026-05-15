"""채용공고 실험 케이스 유효성을 점검하는 스크립트다."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def main() -> None:
    root = Path("sample_data/source_data")
    meta_files = sorted(root.rglob("meta.json"))

    known_risk_types = {
        "GENDER_DISCRIMINATION",
        "AGE_DISCRIMINATION",
        "IRRELEVANT_PERSONAL_INFO",
        "PHYSICAL_CONDITION",
        "FALSE_JOB_AD",
        "UNFAVORABLE_CONDITION_CHANGE",
        "WORKING_CONDITION_AMBIGUITY",
        "SALARY_MISSING",
        "JOB_DESCRIPTION_VAGUE",
        "CULTURE_RED_FLAG",
        "BENEFIT_VAGUE",
        "REPEATED_POSTING",
        "OVERTIME_RISK",
    }

    mismatch_count = 0
    dup_count = 0
    unknown_count = 0

    for meta_path in meta_files:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        case_id = meta.get("case_id", str(meta_path.parent))
        risk_types = meta.get("risk_types") or []
        risk_factors = meta.get("risk_factors") or []

        if len(risk_types) != len(risk_factors):
            mismatch_count += 1
            print(
                f"[MISMATCH] {case_id}: risk_types={len(risk_types)} risk_factors={len(risk_factors)}"
            )

        duplicates = [name for name, cnt in Counter(risk_types).items() if cnt > 1]
        if duplicates:
            dup_count += 1
            print(f"[DUPLICATE] {case_id}: {duplicates}")

        unknown = [name for name in risk_types if name not in known_risk_types]
        if unknown:
            unknown_count += 1
            print(f"[UNKNOWN] {case_id}: {unknown}")

    print("---")
    print(f"meta_files={len(meta_files)}")
    print(f"risk_count_mismatch_cases={mismatch_count}")
    print(f"duplicate_risk_type_cases={dup_count}")
    print(f"unknown_risk_type_cases={unknown_count}")


if __name__ == "__main__":
    main()

