"""Heuristic analysis layer — runs before the LLM.

All computation uses pandas for vectorised performance.
Target: process 1M events in <30 seconds.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from app.schemas.event import NormalizedEvent
from app.schemas.report import (
    Anomaly,
    HeuristicReport,
    TimePoint,
    TopIpItem,
    TopItem,
    TopRuleItem,
)

logger = logging.getLogger(__name__)

TOP_N = 10
_IP_DOMINANCE_THRESHOLD = 0.05       # >5% of all requests
_RULE_HOTSPOT_MIN_COUNT = 100        # single rule triggered > 100 times
_MULTI_VECTOR_DISTINCT_RULES = 10    # distinct rules per IP
_SPIKE_STDDEV_FACTOR = 3.0           # stddev > 3x median
_BOT_FINGERPRINT_MIN_IPS = 50        # same UA seen across 50+ IPs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze(events: list[NormalizedEvent]) -> HeuristicReport:
    """Run full heuristic analysis on a list of normalised events."""
    if not events:
        raise ValueError("Cannot analyse an empty event list.")

    df = _build_dataframe(events)
    total = len(df)

    logger.info("heuristics.analyze: processing %d events", total)

    return HeuristicReport(
        total_events=total,
        time_range=_time_range(df),
        top_source_ips=_top_ips(df, total),
        top_user_agents=_top_values(df, "user_agent"),
        top_countries=_top_values(df, "country"),
        top_uris=_top_values(df, "uri"),
        top_rules_triggered=_top_rules(df),
        action_distribution=_action_dist(df),
        requests_per_minute=_requests_per_minute(df),
        anomalies=_detect_anomalies(df, total),
    )


# ---------------------------------------------------------------------------
# DataFrame builder
# ---------------------------------------------------------------------------

def _build_dataframe(events: list[NormalizedEvent]) -> pd.DataFrame:
    rows = [
        {
            "timestamp": e.timestamp,
            "source_ip": e.source_ip,
            "action": e.action,
            "rule_id": e.rule_id or "",
            "rule_message": e.rule_message or "",
            "uri": e.uri,
            "method": e.method,
            "country": e.country or "unknown",
            "user_agent": e.user_agent or "unknown",
            "request_id": e.request_id or "",
        }
        for e in events
    ]
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def _time_range(df: pd.DataFrame) -> tuple[datetime, datetime]:
    return (df["timestamp"].min().to_pydatetime(),
            df["timestamp"].max().to_pydatetime())


def _top_ips(df: pd.DataFrame, total: int) -> list[TopIpItem]:
    counts = df["source_ip"].value_counts().head(TOP_N)
    return [
        TopIpItem(
            ip=ip,
            count=int(cnt),
            percentage=round(float(cnt) / total * 100, 2),
        )
        for ip, cnt in counts.items()
    ]


def _top_values(df: pd.DataFrame, column: str) -> list[TopItem]:
    counts = df[column].value_counts().head(TOP_N)
    return [TopItem(value=str(v), count=int(c)) for v, c in counts.items()]


def _top_rules(df: pd.DataFrame) -> list[TopRuleItem]:
    active = df[df["rule_id"] != ""]
    if active.empty:
        return []
    agg = (
        active.groupby(["rule_id", "rule_message"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(TOP_N)
    )
    return [
        TopRuleItem(
            rule_id=row["rule_id"],
            rule_message=row["rule_message"] or None,
            count=int(row["count"]),
        )
        for _, row in agg.iterrows()
    ]


def _action_dist(df: pd.DataFrame) -> dict[str, int]:
    return {str(k): int(v) for k, v in df["action"].value_counts().items()}


def _requests_per_minute(df: pd.DataFrame) -> list[TimePoint]:
    bucketed = (
        df.set_index("timestamp")
        .resample("1min")
        .size()
        .reset_index(name="count")
    )
    return [
        TimePoint(
            timestamp=row["timestamp"].to_pydatetime(),
            count=int(row["count"]),
        )
        for _, row in bucketed.iterrows()
    ]


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

def _detect_anomalies(df: pd.DataFrame, total: int) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    anomalies.extend(_check_ip_dominance(df, total))
    anomalies.extend(_check_rule_hotspot(df))
    anomalies.extend(_check_multi_vector(df))
    anomalies.extend(_check_traffic_spike(df))
    anomalies.extend(_check_bot_fingerprint(df))
    return sorted(anomalies, key=lambda a: a.severity, reverse=True)


def _check_ip_dominance(df: pd.DataFrame, total: int) -> list[Anomaly]:
    """Rule 1: Any IP responsible for >5% of total requests."""
    ip_counts = df["source_ip"].value_counts()
    dominant = ip_counts[ip_counts / total > _IP_DOMINANCE_THRESHOLD]
    result = []
    for ip, count in dominant.items():
        pct = float(count) / total * 100
        result.append(
            Anomaly(
                type="ip_dominance",
                severity=min(10, 5 + int(pct / 10)),
                description=f"IP {ip} tüm trafiğin %{pct:.1f}'ini oluşturuyor.",
                affected_entity=ip,
                supporting_data={"request_count": int(count), "percentage": round(pct, 2)},
            )
        )
    return result


def _check_rule_hotspot(df: pd.DataFrame) -> list[Anomaly]:
    """Rule 2: Any single rule triggered >100 times."""
    active = df[df["rule_id"] != ""]
    if active.empty:
        return []
    rule_counts = active.groupby(["rule_id", "rule_message"]).size()
    hotspots = rule_counts[rule_counts > _RULE_HOTSPOT_MIN_COUNT]
    result = []
    for (rule_id, rule_msg), count in hotspots.items():
        result.append(
            Anomaly(
                type="rule_hotspot",
                severity=min(10, 4 + int(count / 100)),
                description=f"'{rule_id}' kuralı {count} kez tetiklendi.",
                affected_entity=rule_id,
                supporting_data={
                    "count": int(count),
                    "rule_message": rule_msg or None,
                },
            )
        )
    return result


def _check_multi_vector(df: pd.DataFrame) -> list[Anomaly]:
    """Rule 3: >10 distinct rules triggered by the same IP."""
    active = df[(df["rule_id"] != "") & (df["source_ip"] != "")]
    if active.empty:
        return []
    per_ip = active.groupby("source_ip")["rule_id"].nunique()
    multi = per_ip[per_ip > _MULTI_VECTOR_DISTINCT_RULES]
    result = []
    for ip, n_rules in multi.items():
        result.append(
            Anomaly(
                type="multi_vector_attack",
                severity=min(10, 6 + int((n_rules - 10) / 2)),
                description=f"IP {ip} {n_rules} farklı kural tetikledi.",
                affected_entity=ip,
                supporting_data={"distinct_rules": int(n_rules)},
            )
        )
    return result


def _check_traffic_spike(df: pd.DataFrame) -> list[Anomaly]:
    """Rule 4: Time-bucketed traffic where stddev > 3x median."""
    bucketed = (
        df.set_index("timestamp")
        .resample("1min")
        .size()
    )
    if len(bucketed) < 3:
        return []
    median = float(bucketed.median())
    std = float(bucketed.std())
    if median == 0 or std <= _SPIKE_STDDEV_FACTOR * median:
        return []
    peak_ts = bucketed.idxmax()
    peak_val = int(bucketed.max())
    return [
        Anomaly(
            type="traffic_spike",
            severity=min(10, 5 + int(std / max(median, 1))),
            description=(
                f"Trafik ani artışı: zirve {peak_val} istek/dk "
                f"(medyan={median:.0f}, std={std:.0f})."
            ),
            affected_entity=str(peak_ts),
            supporting_data={
                "peak_count": peak_val,
                "median_rpm": round(median, 2),
                "stddev_rpm": round(std, 2),
                "spike_at": str(peak_ts),
            },
        )
    ]


def _check_bot_fingerprint(df: pd.DataFrame) -> list[Anomaly]:
    """Rule 6: Same user-agent seen across 50+ distinct IPs."""
    known_unknown = {"unknown", ""}
    filtered = df[~df["user_agent"].isin(known_unknown)]
    if filtered.empty:
        return []
    ua_ip_counts = filtered.groupby("user_agent")["source_ip"].nunique()
    bots = ua_ip_counts[ua_ip_counts >= _BOT_FINGERPRINT_MIN_IPS]
    result = []
    for ua, n_ips in bots.items():
        result.append(
            Anomaly(
                type="bot_fingerprint",
                severity=min(10, 5 + int(n_ips / 50)),
                description=f"'{ua[:60]}' kullanıcı ajanı {n_ips} farklı IP'de görüldü.",
                affected_entity=ua[:120],
                supporting_data={"distinct_ips": int(n_ips)},
            )
        )
    return result
