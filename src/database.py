import sqlite3
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from src.config import settings

DB_PATH = settings.SQLITE_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database tables and indices."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                prompt_preview TEXT NOT NULL,
                prompt_hash TEXT NOT NULL,
                complexity_tier TEXT NOT NULL,
                complexity_score REAL NOT NULL,
                routed_model TEXT NOT NULL,
                routed_provider TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                baseline_model TEXT NOT NULL,
                baseline_cost_usd REAL NOT NULL,
                cost_saved_usd REAL NOT NULL,
                cost_reduction_pct REAL NOT NULL,
                latency_ms REAL NOT NULL,
                quality_score REAL,
                verified INTEGER DEFAULT 0,
                is_escalated INTEGER DEFAULT 0,
                escalation_reason TEXT,
                output_text TEXT,
                is_retrain_sample INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_req_timestamp ON request_logs(timestamp);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_req_tier ON request_logs(complexity_tier);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_req_model ON request_logs(routed_model);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_req_hash ON request_logs(prompt_hash);
        """)
        conn.commit()

def compute_prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()

def log_request(data: Dict[str, Any]) -> int:
    """Inserts a new request record into the SQLite database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO request_logs (
                request_id, timestamp, prompt_preview, prompt_hash,
                complexity_tier, complexity_score, routed_model, routed_provider,
                input_tokens, output_tokens, total_tokens, cost_usd,
                baseline_model, baseline_cost_usd, cost_saved_usd, cost_reduction_pct,
                latency_ms, quality_score, verified, is_escalated,
                escalation_reason, output_text, is_retrain_sample
            ) VALUES (
                :request_id, :timestamp, :prompt_preview, :prompt_hash,
                :complexity_tier, :complexity_score, :routed_model, :routed_provider,
                :input_tokens, :output_tokens, :total_tokens, :cost_usd,
                :baseline_model, :baseline_cost_usd, :cost_saved_usd, :cost_reduction_pct,
                :latency_ms, :quality_score, :verified, :is_escalated,
                :escalation_reason, :output_text, :is_retrain_sample
            )
        """, data)
        conn.commit()
        return cursor.lastrowid

def update_verification(
    request_id: str,
    quality_score: float,
    is_escalated: bool = False,
    escalation_reason: Optional[str] = None,
    escalated_output: Optional[str] = None,
    is_retrain_sample: bool = False
):
    """Updates request record with async verification results."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if escalated_output:
            cursor.execute("""
                UPDATE request_logs
                SET quality_score = :quality_score,
                    verified = 1,
                    is_escalated = :is_escalated,
                    escalation_reason = :escalation_reason,
                    output_text = :output_text,
                    is_retrain_sample = :is_retrain_sample
                WHERE request_id = :request_id
            """, {
                "request_id": request_id,
                "quality_score": round(quality_score, 4),
                "is_escalated": 1 if is_escalated else 0,
                "escalation_reason": escalation_reason,
                "output_text": escalated_output,
                "is_retrain_sample": 1 if is_retrain_sample else 0
            })
        else:
            cursor.execute("""
                UPDATE request_logs
                SET quality_score = :quality_score,
                    verified = 1,
                    is_escalated = :is_escalated,
                    escalation_reason = :escalation_reason,
                    is_retrain_sample = :is_retrain_sample
                WHERE request_id = :request_id
            """, {
                "request_id": request_id,
                "quality_score": round(quality_score, 4),
                "is_escalated": 1 if is_escalated else 0,
                "escalation_reason": escalation_reason,
                "is_retrain_sample": 1 if is_retrain_sample else 0
            })
        conn.commit()

def get_stats() -> Dict[str, Any]:
    """Retrieves high-level cost savings and quality KPI metrics."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_requests,
                COALESCE(SUM(cost_usd), 0) as total_cost_usd,
                COALESCE(SUM(baseline_cost_usd), 0) as total_baseline_cost_usd,
                COALESCE(SUM(cost_saved_usd), 0) as total_saved_usd,
                COALESCE(AVG(latency_ms), 0) as avg_latency_ms,
                COALESCE(AVG(quality_score), 0) as avg_quality_score,
                COALESCE(SUM(is_escalated), 0) as total_escalations,
                COALESCE(SUM(verified), 0) as total_verified
            FROM request_logs
        """)
        row = cursor.fetchone()
        
        total_req = row["total_requests"]
        total_cost = row["total_cost_usd"]
        baseline_cost = row["total_baseline_cost_usd"]
        saved = row["total_saved_usd"]
        
        savings_pct = (saved / baseline_cost * 100.0) if baseline_cost > 0 else 0.0
        escalation_rate = (row["total_escalations"] / total_req * 100.0) if total_req > 0 else 0.0

        return {
            "total_requests": total_req,
            "total_cost_usd": round(total_cost, 4),
            "baseline_cost_usd": round(baseline_cost, 4),
            "total_saved_usd": round(saved, 4),
            "savings_percentage": round(savings_pct, 2),
            "average_latency_ms": round(row["avg_latency_ms"], 2),
            "average_quality_score": round(row["avg_quality_score"], 3),
            "total_escalations": row["total_escalations"],
            "escalation_rate_pct": round(escalation_rate, 2),
            "total_verified": row["total_verified"]
        }

def get_model_distribution() -> List[Dict[str, Any]]:
    """Returns request count, total cost, and percentages by routed model."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                routed_model,
                complexity_tier,
                COUNT(*) as count,
                SUM(cost_usd) as total_cost,
                AVG(latency_ms) as avg_latency
            FROM request_logs
            GROUP BY routed_model, complexity_tier
            ORDER BY count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_recent_requests(limit: int = 100) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM request_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_retrain_candidates() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM request_logs
            WHERE is_retrain_sample = 1
            ORDER BY id DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

# Auto-initialize database schema
init_db()
