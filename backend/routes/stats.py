"""GET /api/stats - English text

English text
  - totalDecisions: English text
  - modeDistribution: English text
  - avgConfidence: brief.confidence English textbrief English text None English text
  - executedRate: executed=True English text
  - regretRate: regret=True English text
  - weekTrend: English text 7 English text [{date, count}, ...]

English text 0 English text StatsEnglish text mock English text
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter

import db
from models.schemas import Stats
from services.modes_data import MODES

router = APIRouter()

# English text ponytail: English textEnglish text
_MAX_SCAN = 100_000


@router.get("/api/stats", response_model=Stats)
def get_stats() -> Stats:
    """English textEnglish textEnglish textEnglish textEnglish textEnglish text 7 English text"""
    total = db.count_decisions()
    if total == 0:
        return Stats(
            totalDecisions=0,
            modeDistribution={m.id: 0 for m in MODES},
            avgConfidence=0.0,
            executedRate=0.0,
            regretRate=0.0,
            weekTrend=_empty_week_trend(),
        )

    decisions = db.list_decisions(limit=_MAX_SCAN, offset=0)

    # English text
    distribution: Dict[str, int] = {m.id: 0 for m in MODES}
    for d in decisions:
        mode = d.get("mode") or "auto"
        distribution[mode] = distribution.get(mode, 0) + 1

    # English textbrief English text None English text
    confidences: List[int] = []
    for d in decisions:
        brief = d.get("brief")
        if isinstance(brief, dict):
            try:
                confidences.append(int(brief.get("confidence", 0)))
            except (TypeError, ValueError):
                pass
    avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    # English text / English text
    executed_n = sum(1 for d in decisions if d.get("executed"))
    regret_n = sum(1 for d in decisions if d.get("regret"))
    executed_rate = round(executed_n / total, 4) if total else 0.0
    regret_rate = round(regret_n / total, 4) if total else 0.0

    # English text 7 English textEnglish textoldest → newest
    today = date.today()
    counts_by_date: Dict[str, int] = defaultdict(int)
    for d in decisions:
        created = d.get("createdAt")
        if not created:
            continue
        try:
            day = datetime.fromisoformat(created).date().isoformat()
        except (ValueError, TypeError):
            continue
        counts_by_date[day] += 1
    week_trend = [
        {"date": (today - timedelta(days=i)).isoformat(),
         "count": counts_by_date.get((today - timedelta(days=i)).isoformat(), 0)}
        for i in range(6, -1, -1)
    ]

    return Stats(
        totalDecisions=total,
        modeDistribution=distribution,
        avgConfidence=avg_confidence,
        executedRate=executed_rate,
        regretRate=regret_rate,
        weekTrend=week_trend,
    )


def _empty_week_trend() -> List[Dict[str, Any]]:
    """English text 7 English textcount English text 0"""
    today = date.today()
    return [
        {"date": (today - timedelta(days=i)).isoformat(), "count": 0}
        for i in range(6, -1, -1)
    ]
