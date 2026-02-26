"""
InvestIQ AI — Admin Firestore Layer (Fixed)

The 403 PERMISSION_DENIED error happens because Firestore Security Rules
block cross-user reads by default. This module uses a 3-strategy approach:

STRATEGY 1 (Best): Collection group query with admin Firestore rules
  → Works after you update Firestore Security Rules (instructions below)

STRATEGY 2 (Fallback): Read known users from a shared 'platform_stats'
  collection that each user writes to on save

STRATEGY 3 (Always works): Admin reads their OWN data + aggregates
  from the public 'platform_stats' summary doc that all users update

HOW TO FIX THE 403 PERMANENTLY (5 minutes):
─────────────────────────────────────────────
1. Go to Firebase Console → Firestore Database → Rules tab
2. Replace ALL rules with this:

rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Each user can read/write their own analyses
    match /users/{userId}/analyses/{analysisId} {
      allow read, write: if request.auth != null
                         && request.auth.uid == userId;
    }

    // Anyone can read public analyses (for share link)
    match /{path=**}/analyses/{analysisId} {
      allow read: if resource.data.is_public == true;
    }

    // ADMIN: can read ALL analyses across all users
    match /{path=**}/analyses/{analysisId} {
      allow read: if request.auth != null
                  && request.auth.uid in ADMIN_UIDS;
    }

    // Platform stats: all authenticated users can write summary
    // Admin can read all summaries
    match /platform_stats/{docId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }

    // Admin full access
    match /admin/{document=**} {
      allow read, write: if request.auth != null
                         && request.auth.uid in ADMIN_UIDS;
    }
  }
}

NOTE: Replace ADMIN_UIDS with actual list like:
  ["E9lkGXzMKLd1DmG0dQq23fgDahr1"]

3. Click "Publish"
4. Refresh admin dashboard — data will load instantly
─────────────────────────────────────────────
"""

import requests
import json as _json
import streamlit as st
from datetime import datetime, timezone, timedelta
from typing import Optional
from auth.admin_auth import get_admin_uids


def _project_id() -> str:
    return st.secrets["firebase"]["projectId"]


def _api_key() -> str:
    return st.secrets["firebase"]["apiKey"]


def _id_token() -> Optional[str]:
    return st.session_state.get("id_token")


def _rest_url(path: str) -> str:
    p = _project_id()
    return (
        f"https://firestore.googleapis.com/v1"
        f"/projects/{p}/databases/(default)/documents/{path}"
    )


# ── VALUE CONVERTERS ──────────────────────────────────────────────────────────

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


def _to_value(val):
    if val is None:          return {"nullValue": None}
    if isinstance(val, bool):return {"booleanValue": val}
    if isinstance(val, int): return {"integerValue": str(val)}
    if isinstance(val, float):return {"doubleValue": val}
    if isinstance(val, str): return {"stringValue": val}
    if isinstance(val, list):return {"arrayValue": {"values": [_to_value(v) for v in val]}}
    if isinstance(val, dict):return {"mapValue": {"fields": {k: _to_value(v) for k, v in val.items()}}}
    return {"stringValue": str(val)}


def _from_doc(doc: dict) -> dict:
    fields = doc.get("fields", {})
    result = {k: _from_value(v) for k, v in fields.items()}
    name = doc.get("name", "")
    if "/" in name:
        parts = name.split("/")
        result["_doc_id"] = parts[-1]
        if "users" in parts:
            idx = parts.index("users")
            if idx + 1 < len(parts):
                result["_uid"] = parts[idx + 1]
    return result


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_id_token()}",
        "Content-Type": "application/json",
    }


# ── STRATEGY 1: Collection group query (requires updated Firestore rules) ─────

def _fetch_via_collection_group(limit: int = 500) -> list:
    """
    Cross-user collection group query.
    Works ONLY after Firestore rules are updated to grant admin read access.
    Returns [] on 403 — caller will try next strategy.
    """
    token = _id_token()
    if not token:
        return []

    project = _project_id()
    url = (
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
            url,
            headers=_headers(),
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
            if docs:
                print(f"[Admin] Strategy 1 (collection group): {len(docs)} analyses")
            return docs
        else:
            print(f"[Admin] Strategy 1 failed ({resp.status_code}) — trying fallback")
            return []
    except Exception as e:
        print(f"[Admin] Strategy 1 exception: {e}")
        return []


# ── STRATEGY 2: Read platform_stats summary + known user UIDs ─────────────────

def _fetch_via_platform_stats() -> list:
    """
    Reads the shared platform_stats collection where each user
    writes a summary row when they save an analysis.
    Returns aggregated summary data (not full analyses).
    """
    token = _id_token()
    if not token:
        return []

    url = _rest_url("platform_stats")
    try:
        resp = requests.get(url, headers=_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            docs = data.get("documents", [])
            results = [_from_doc(d) for d in docs]
            print(f"[Admin] Strategy 2 (platform_stats): {len(results)} user summaries")
            return results
        return []
    except Exception as e:
        print(f"[Admin] Strategy 2 exception: {e}")
        return []


# ── STRATEGY 3: Admin reads own analyses (always works) ──────────────────────

def _fetch_admin_own_analyses() -> list:
    """
    Admin reads their own analyses as a baseline.
    Always works since admin is reading their own data.
    """
    from db.firestore import list_analyses
    uid = st.session_state.get("user_uid", "")
    if not uid:
        return []
    analyses = list_analyses(uid, limit=200)
    for a in analyses:
        a["_uid"] = uid
        a["user_email"] = st.session_state.get("user_email", "")
    print(f"[Admin] Strategy 3 (own data): {len(analyses)} analyses")
    return analyses


# ── STRATEGY 4: Read each known user's analyses individually ──────────────────

def _fetch_per_known_user(known_uids: list) -> list:
    """
    For each UID stored in platform_stats, try to read their analyses
    using admin's token. Works if Firestore rules allow admin cross-read.
    """
    all_analyses = []
    token = _id_token()
    if not token:
        return []

    for uid in known_uids[:20]:  # cap at 20 users for performance
        url = _rest_url(f"users/{uid}/analyses")
        try:
            resp = requests.get(
                url, headers=_headers(),
                params={"pageSize": 100}, timeout=8
            )
            if resp.status_code == 200:
                docs = resp.json().get("documents", [])
                for d in docs:
                    a = _from_doc(d)
                    a["_uid"] = uid
                    all_analyses.append(a)
        except Exception:
            pass

    if all_analyses:
        print(f"[Admin] Strategy 4 (per-user): {len(all_analyses)} analyses from {len(known_uids)} users")
    return all_analyses


# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────

def fetch_all_analyses(limit: int = 500) -> list:
    """
    Smart multi-strategy fetch with automatic fallback chain.

    Tries strategies in order:
    1. Collection group query (best, needs updated Firestore rules)
    2. Per-known-user reads from platform_stats registry
    3. Admin's own data only (always works as minimum)

    Returns whatever it can get — never crashes.
    """
    # ── Strategy 1: Collection group (best result) ────────────────────────────
    results = _fetch_via_collection_group(limit)
    if results:
        return results

    # ── Strategy 2: Get known UIDs from platform_stats, then read per-user ────
    stats_docs = _fetch_via_platform_stats()
    known_uids = []
    for doc in stats_docs:
        uid = doc.get("uid") or doc.get("_doc_id", "")
        if uid and uid not in known_uids:
            known_uids.append(uid)

    # Also add admin UIDs to known list
    for uid in get_admin_uids():
        if uid not in known_uids:
            known_uids.append(uid)

    if known_uids:
        per_user = _fetch_per_known_user(known_uids)
        if per_user:
            # Sort newest first
            per_user.sort(key=lambda x: x.get("created_at",""), reverse=True)
            return per_user[:limit]

    # ── Strategy 3: Admin's own data as minimum fallback ─────────────────────
    own = _fetch_admin_own_analyses()
    own.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return own


def write_platform_stat(uid: str, email: str, analysis: dict) -> bool:
    """
    Write/update a summary entry in platform_stats/{uid} whenever
    a user saves an analysis. This registers users in the admin-readable
    registry so Strategy 2 can find their UIDs later.

    Called automatically from db/firestore.py save_analysis().
    """
    token = _id_token()
    if not token or not uid:
        return False

    url = _rest_url(f"platform_stats/{uid}")

    # Read existing doc to get current count
    try:
        resp = requests.get(url, headers=_headers(), timeout=5)
        existing = {}
        if resp.status_code == 200:
            existing = _from_doc(resp.json())
    except Exception:
        existing = {}

    new_count = existing.get("total_analyses", 0) + 1

    doc = {
        "fields": {
            "uid":             _to_value(uid),
            "email":           _to_value(email),
            "total_analyses":  _to_value(new_count),
            "last_active":     _to_value(datetime.now(timezone.utc).isoformat()),
            "avg_score":       _to_value(
                round(
                    (existing.get("avg_score", 0) * (new_count - 1) +
                     analysis.get("overall_investment_score", 0)) / new_count
                )
            ),
        }
    }

    try:
        resp = requests.patch(
            url, headers=_headers(),
            data=_json.dumps(doc), timeout=8
        )
        return resp.status_code == 200
    except Exception:
        return False


# ── ADMIN ACTIONS ─────────────────────────────────────────────────────────────

def revoke_public_access(uid: str, doc_id: str) -> bool:
    token = _id_token()
    if not token:
        return False
    url  = _rest_url(f"users/{uid}/analyses/{doc_id}")
    body = {"fields": {"is_public": {"booleanValue": False}}}
    try:
        resp = requests.patch(
            url, headers=_headers(),
            params={"updateMask.fieldPaths": ["is_public"]},
            data=_json.dumps(body), timeout=8,
        )
        return resp.status_code == 200
    except Exception:
        return False


def admin_delete_analysis(uid: str, doc_id: str) -> bool:
    token = _id_token()
    if not token:
        return False
    url = _rest_url(f"users/{uid}/analyses/{doc_id}")
    try:
        resp = requests.delete(url, headers=_headers(), timeout=8)
        return resp.status_code in (200, 204)
    except Exception:
        return False


# ── AGGREGATION HELPERS ───────────────────────────────────────────────────────

def compute_platform_stats(analyses: list) -> dict:
    total = len(analyses)
    if total == 0:
        return {
            "total": 0, "avg_score": 0, "strong_invest": 0,
            "consider": 0, "reject": 0, "today": 0,
            "this_week": 0, "this_month": 0,
            "public_count": 0, "unique_users": 0,
        }

    now       = datetime.now(timezone.utc)
    today_d   = now.date()
    week_ago  = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    avg_score     = round(sum(a.get("overall_investment_score", 0) for a in analyses) / total)
    strong_invest = sum(1 for a in analyses if "invest"   in a.get("final_recommendation","").lower())
    consider      = sum(1 for a in analyses if "consider" in a.get("final_recommendation","").lower())
    reject        = sum(1 for a in analyses if "reject"   in a.get("final_recommendation","").lower())
    public_count  = sum(1 for a in analyses if a.get("is_public"))
    unique_users  = len(set(
        a.get("_uid","") or a.get("uid","") for a in analyses
    ))

    today_c = week_c = month_c = 0
    for a in analyses:
        try:
            dt = datetime.fromisoformat(a.get("created_at","").replace("Z","+00:00"))
            if dt.date() == today_d:   today_c += 1
            if dt >= week_ago:         week_c  += 1
            if dt >= month_ago:        month_c += 1
        except Exception:
            pass

    return {
        "total": total, "avg_score": avg_score,
        "strong_invest": strong_invest, "consider": consider, "reject": reject,
        "today": today_c, "this_week": week_c, "this_month": month_c,
        "public_count": public_count, "unique_users": unique_users,
    }


def get_user_table(analyses: list) -> list:
    from collections import defaultdict
    users = defaultdict(lambda: {
        "uid": "", "email": "", "total": 0,
        "avg_score": 0, "scores": [],
        "last_active": "", "strong_invest": 0,
    })

    for a in analyses:
        uid   = a.get("_uid") or a.get("uid", "unknown")
        email = a.get("user_email","")
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

    rows = []
    for uid, u in users.items():
        avg = round(sum(u["scores"]) / len(u["scores"])) if u["scores"] else 0
        u["avg_score"] = avg
        rows.append(u)

    rows.sort(key=lambda x: x["total"], reverse=True)
    return rows


def get_daily_counts(analyses: list, days: int = 30) -> tuple:
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

    dates, values = [], []
    for i in range(days - 1, -1, -1):
        d = (now - timedelta(days=i)).strftime("%b %d")
        dates.append(d)
        values.append(counts.get(d, 0))

    return dates, values


def check_api_health() -> dict:
    results = {"groq": "unknown", "gemini": "unknown"}
    try:
        groq_key = st.secrets.get("groq", {}).get("api_key", "")
        if groq_key:
            resp = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {groq_key}"},
                timeout=5,
            )
            results["groq"] = "✅ Online" if resp.status_code == 200 else f"⚠️ HTTP {resp.status_code}"
        else:
            results["groq"] = "❌ No key in secrets"
    except Exception:
        results["groq"] = "❌ Unreachable"

    try:
        gem_key = st.secrets.get("google", {}).get("api_key", "")
        if gem_key:
            resp = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={gem_key}",
                timeout=5,
            )
            results["gemini"] = "✅ Online" if resp.status_code == 200 else f"⚠️ HTTP {resp.status_code}"
        else:
            results["gemini"] = "❌ No key in secrets"
    except Exception:
        results["gemini"] = "❌ Unreachable"

    return results
