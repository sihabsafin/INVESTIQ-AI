"""
InvestIQ AI — Admin Firestore Layer

Fetches platform-wide data using Firestore collection group queries.
Uses the admin's own id_token — no service account required.

Firestore rules must allow admins to read all analyses.
Add this rule in Firebase Console:

  match /{path=**}/analyses/{analysisId} {
    allow read: if request.auth != null
                && request.auth.uid in ['uid1', 'uid2'];
  }
"""

import requests
import json as _json
import streamlit as st
from datetime import datetime, timezone, timedelta
from typing import Optional


def _project_id() -> str:
    return st.secrets["firebase"]["projectId"]


def _api_key() -> str:
    return st.secrets["firebase"]["apiKey"]


def _id_token() -> Optional[str]:
    return st.session_state.get("id_token")


def _rest_url(path: str) -> str:
    p = _project_id()
    return f"https://firestore.googleapis.com/v1/projects/{p}/databases/(default)/documents/{path}"


def _from_value(val: dict):
    if "nullValue"      in val: return None
    if "booleanValue"   in val: return val["booleanValue"]
    if "integerValue"   in val: return int(val["integerValue"])
    if "doubleValue"    in val: return float(val["doubleValue"])
    if "stringValue"    in val: return val["stringValue"]
    if "timestampValue" in val: return val["timestampValue"]
    if "arrayValue"     in val:
        return [_from_value(v) for v in val["arrayValue"].get("values", [])]
    if "mapValue"       in val:
        return {k: _from_value(v) for k, v in val["mapValue"].get("fields", {}).items()}
    return None


def _from_doc(doc: dict) -> dict:
    fields = doc.get("fields", {})
    result = {k: _from_value(v) for k, v in fields.items()}
    name = doc.get("name", "")
    if "/" in name:
        parts = name.split("/")
        result["_doc_id"]  = parts[-1]
        # Extract uid from path: .../users/{uid}/analyses/{docId}
        if "users" in parts:
            idx = parts.index("users")
            if idx + 1 < len(parts):
                result["_uid"] = parts[idx + 1]
    return result


# ── PLATFORM-WIDE QUERIES ─────────────────────────────────────────────────────

def fetch_all_analyses(limit: int = 500) -> list:
    """
    Collection group query — fetch all analyses across all users.
    Requires admin token + Firestore rule granting admin read access.
    Falls back to empty list gracefully.
    """
    token = _id_token()
    if not token:
        return []

    project = _project_id()
    query_url = (
        f"https://firestore.googleapis.com/v1/projects/{project}"
        f"/databases/(default)/documents:runQuery"
    )

    body = {
        "structuredQuery": {
            "from": [{"collectionId": "analyses", "allDescendants": True}],
            "orderBy": [{"field": {"fieldPath": "created_at"}, "direction": "DESCENDING"}],
            "limit": limit,
        }
    }

    try:
        resp = requests.post(
            query_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            data=_json.dumps(body),
            timeout=15,
        )
        if resp.status_code == 200:
            results = resp.json()
            docs = []
            for item in results:
                doc = item.get("document")
                if doc:
                    docs.append(_from_doc(doc))
            return docs
        else:
            print(f"Admin query error {resp.status_code}: {resp.text[:200]}")
            return []
    except Exception as e:
        print(f"Admin fetch exception: {e}")
        return []


def revoke_public_access(uid: str, doc_id: str) -> bool:
    """Set is_public=False on any analysis (admin action)."""
    token = _id_token()
    if not token:
        return False

    project = _project_id()
    path    = f"users/{uid}/analyses/{doc_id}"
    url     = _rest_url(path)

    body = {
        "fields": {
            "is_public": {"booleanValue": False}
        }
    }

    try:
        resp = requests.patch(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            params={"updateMask.fieldPaths": ["is_public"]},
            data=_json.dumps(body),
            timeout=8,
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"Revoke public exception: {e}")
        return False


def admin_delete_analysis(uid: str, doc_id: str) -> bool:
    """Admin delete any analysis document."""
    token = _id_token()
    if not token:
        return False

    project = _project_id()
    url     = _rest_url(f"users/{uid}/analyses/{doc_id}")

    try:
        resp = requests.delete(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=8,
        )
        return resp.status_code in (200, 204)
    except Exception as e:
        print(f"Admin delete exception: {e}")
        return False


# ── AGGREGATION HELPERS ───────────────────────────────────────────────────────

def compute_platform_stats(analyses: list) -> dict:
    """Compute KPI metrics from all analyses."""
    total = len(analyses)
    if total == 0:
        return {
            "total": 0, "avg_score": 0, "strong_invest": 0,
            "consider": 0, "reject": 0,
            "today": 0, "this_week": 0, "this_month": 0,
            "public_count": 0, "unique_users": 0,
        }

    now        = datetime.now(timezone.utc)
    today_d    = now.date()
    week_ago   = now - timedelta(days=7)
    month_ago  = now - timedelta(days=30)

    avg_score     = round(sum(a.get("overall_investment_score", 0) for a in analyses) / total)
    strong_invest = sum(1 for a in analyses if "invest"   in a.get("final_recommendation","").lower())
    consider      = sum(1 for a in analyses if "consider" in a.get("final_recommendation","").lower())
    reject        = sum(1 for a in analyses if "reject"   in a.get("final_recommendation","").lower())
    public_count  = sum(1 for a in analyses if a.get("is_public"))
    unique_users  = len(set(a.get("_uid","") or a.get("uid","") for a in analyses))

    today_count = week_count = month_count = 0
    for a in analyses:
        try:
            dt = datetime.fromisoformat(a.get("created_at","").replace("Z","+00:00"))
            if dt.date() == today_d:
                today_count += 1
            if dt >= week_ago:
                week_count += 1
            if dt >= month_ago:
                month_count += 1
        except Exception:
            pass

    return {
        "total": total, "avg_score": avg_score,
        "strong_invest": strong_invest, "consider": consider, "reject": reject,
        "today": today_count, "this_week": week_count, "this_month": month_count,
        "public_count": public_count, "unique_users": unique_users,
    }


def get_user_table(analyses: list) -> list:
    """
    Build per-user summary rows from all analyses.
    Returns list of dicts sorted by total analyses desc.
    """
    from collections import defaultdict
    users = defaultdict(lambda: {
        "uid": "", "email": "", "total": 0,
        "avg_score": 0, "scores": [],
        "last_active": "", "analyses": [],
        "strong_invest": 0,
    })

    for a in analyses:
        uid   = a.get("_uid") or a.get("uid", "unknown")
        email = a.get("user_email", "")
        u     = users[uid]
        u["uid"]   = uid
        u["email"] = email or u["email"]
        u["total"] += 1
        score = a.get("overall_investment_score", 0)
        u["scores"].append(score)
        if "invest" in a.get("final_recommendation","").lower():
            u["strong_invest"] += 1
        created = a.get("created_at","")
        if created > u["last_active"]:
            u["last_active"] = created
        u["analyses"].append(a)

    rows = []
    for uid, u in users.items():
        avg = round(sum(u["scores"]) / len(u["scores"])) if u["scores"] else 0
        u["avg_score"] = avg
        rows.append(u)

    rows.sort(key=lambda x: x["total"], reverse=True)
    return rows


def get_daily_counts(analyses: list, days: int = 30) -> tuple:
    """Return (dates, counts) for analyses per day over last N days."""
    from collections import defaultdict
    now    = datetime.now(timezone.utc)
    counts = defaultdict(int)

    for a in analyses:
        try:
            dt = datetime.fromisoformat(a.get("created_at","").replace("Z","+00:00"))
            if (now - dt).days <= days:
                counts[dt.strftime("%b %d")] += 1
        except Exception:
            pass

    # Build ordered list for last N days
    dates, values = [], []
    for i in range(days - 1, -1, -1):
        d   = (now - timedelta(days=i)).strftime("%b %d")
        dates.append(d)
        values.append(counts.get(d, 0))

    return dates, values


def check_api_health() -> dict:
    """Ping Groq and Gemini to verify API keys are alive."""
    results = {"groq": "unknown", "gemini": "unknown"}

    # Groq check
    try:
        groq_key = st.secrets.get("groq", {}).get("api_key", "")
        if groq_key:
            resp = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {groq_key}"},
                timeout=5,
            )
            results["groq"] = "✅ Online" if resp.status_code == 200 else f"⚠️ Error {resp.status_code}"
        else:
            results["groq"] = "❌ No API key"
    except Exception:
        results["groq"] = "❌ Unreachable"

    # Gemini check
    try:
        gem_key = st.secrets.get("google", {}).get("api_key", "")
        if gem_key:
            resp = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={gem_key}",
                timeout=5,
            )
            results["gemini"] = "✅ Online" if resp.status_code == 200 else f"⚠️ Error {resp.status_code}"
        else:
            results["gemini"] = "❌ No API key"
    except Exception:
        results["gemini"] = "❌ Unreachable"

    return results
