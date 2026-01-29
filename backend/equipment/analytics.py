"""Parse CSV and compute summary statistics using Pandas."""
from __future__ import annotations

import io
from typing import Any

import pandas as pd


# Expected columns (case-insensitive match)
COLUMNS = ['equipment name', 'type', 'flowrate', 'pressure', 'temperature']


def parse_and_analyze(csv_file) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Read CSV, validate columns, compute summary. Return (rows, summary).
    """
    raw = csv_file.read()
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    df = pd.read_csv(io.StringIO(raw))

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Ensure numeric types
    for col in ['flowrate', 'pressure', 'temperature']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['flowrate', 'pressure', 'temperature'])

    rows = df.to_dict('records')
    for r in rows:
        for k, v in list(r.items()):
            if pd.isna(v):
                r[k] = None
            elif isinstance(v, (int, float)):
                r[k] = round(float(v), 4) if isinstance(v, float) else int(v)
            else:
                r[k] = str(v)

    # Summary (ensure JSON-serializable types)
    type_dist = {str(k): int(v) for k, v in df['type'].value_counts().items()}
    summary = {
        'total_count': int(len(df)),
        'averages': {
            'flowrate': round(float(df['flowrate'].mean()), 4),
            'pressure': round(float(df['pressure'].mean()), 4),
            'temperature': round(float(df['temperature'].mean()), 4),
        },
        'type_distribution': type_dist,
    }
    return rows, summary
