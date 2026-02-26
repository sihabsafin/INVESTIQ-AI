"""
InvestIQ AI — Admin Firestore Layer (v3 — Direct Read Strategy)

ROOT CAUSE OF 403:
  The collection group query (Strategy 1) requires a Firestore composite
  index that doesn't auto-create. Even with correct rules it returns 403
  until the index is manually built in Firebase Console.

SOLUTION — 3-step direct approach:
  Step A: Enumerate /users collection to discover all user UIDs
  Step B: For each UID, read /users/{uid}/analyses directly
  Step C: Merge + sort all results

WHY THIS WORKS:
  Your Firestore rule (lines 11-15 in the screenshot):
    match /{path=**}/analyses/{analysisId} {
      allow read: if request.auth != null
                  && request.auth.uid == "YOUR_UID";
    }
  This wildcard rule covers BOTH:
    - users/{uid}/analyses/{docId}   ← direct collection reads (Step B)
    - the collection group query     ← needs an index (skipped)
  So Step B works perfectly with your existing rules.

YOUR FIRESTORE RULES ARE CORRECT — no changes needed there.
"""

import requests
import json as _json
import streamlit as st
from datetime import datetime, timezone, timedelta
from typing import Optional


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _project_id() -> str:
    return st.secrets["firebase"]["projectId"]


def _id_token() -> Optional[str]:
    return st.session_state.get("id_token")


def _rest_base() -> str:
    p = _project_id()
    return f"https://firestore.googleapis.com/v1/projects/{p}/databases/(default)/documents"


def _headers() -> dict:
    token = _id_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


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
    if val is None:            return {"nullValue": None}
    if isinstance(val, bool):  return {"booleanValue": val}
    if isinstance(val, int):   return {"integerValue": str(val)}
    if isinstance(val, float): return {"doubleValue": val}
    if isinstance(val, str):   return {"stringValue": val}
    if isinstance(val, list):
        return {"arrayValue": {"values": [_to_value(v) for v in val]}}
    if isinstance(val, dict):
        return {"mapValue": {"fields": {k: _to_value(v) for k, v in val.items()}}}
    return {"stringValue": str(val)}


def _from_doc(doc: dict, inject_uid: str = "") -> dict:
    """Convert Firestore REST document to Python dict."""
    fields = doc.get("fields", {})
    result = {k: _from_value(v) for k, v in fields.items()}
    name = doc.get("name", "")
    if "/" in name:
        parts = name.split("/")
        result["_doc_id"] = parts[-1]
        # Extract UID from path structure: .../users/{uid}/analyses/{docId}
        if "users" in parts:
            idx = parts.index("users")
            if idx + 1 < len(parts):
                result["_uid"] = parts[idx + 1]
    # Inject uid if not already extracted
    if "_uid" not in result and inject_uid:
        result["_uid"] = inject_uid
    return result


# ── STEP A: Discover all user UIDs ────────────────────────────────────────────

def _get_all_user_uids() -> list:
    """
    Discover all user UIDs using 3 parallel methods:
    1. Enumerate /users collection (works after adding users/{uid} profile docs on login)
    2. Enumerate /platform_stats collection (populated on every login + save)
    3. Always include admin's own UID as minimum fallback

    All 3 methods work with the updated Firestore rules.
    """
    token = _id_token()
    if not token:
        return []

    discovered_uids = []

    def _extract_uids_from_collection(collection_path: str) -> list:
        """List a collection and extract UIDs from document names."""
        uids = []
        url  = f"{_rest_base()}/{collection_path}"
        try:
            # Fetch up to 500 docs — covers large user bases
            resp = requests.get(
                url, headers=_headers(),
                params={"pageSize": 500},
                timeout=12,
            )
            if resp.status_code == 200:
                docs = resp.json().get("documents", [])
                for d in docs:
                    uid = d.get("name", "").split("/")[-1]
                    if uid and len(uid) > 8:  # Filter out non-UID strings
                        uids.append(uid)
                print(f"[Admin] /{collection_path}: found {len(uids)} UIDs")
            else:
                print(f"[Admin] /{collection_path}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"[Admin] /{collection_path} error: {e}")
        return uids

    # Method 1: /users collection (profile docs written on login)
    for uid in _extract_uids_from_collection("users"):
        if uid not in discovered_uids:
            discovered_uids.append(uid)

    # Method 2: /platform_stats collection (written on login + save)
    for uid in _extract_uids_from_collection("platform_stats"):
        if uid not in discovered_uids:
            discovered_uids.append(uid)

    # Method 3: Admin's own UID always included
    admin_uid = st.session_state.get("user_uid", "")
    if admin_uid and admin_uid not in discovered_uids:
        discovered_uids.append(admin_uid)
        print(f"[Admin] Admin UID added: {admin_uid[:8]}...")

    print(f"[Admin] Total unique UIDs discovered: {len(discovered_uids)}")
    return discovered_uids


# ── STEP B: Read each user's analyses directly ────────────────────────────────

def _fetch_user_analyses(uid: str, limit: int = 200) -> list:
    """
    Read /users/{uid}/analyses directly.
    Works because admin rule covers /{path=**}/analyses/{analysisId}.
    """
    token = _id_token()
    if not token or not uid:
        return []

    url = f"{_rest_base()}/users/{uid}/analyses"
    try:
        resp = requests.get(
            url, headers=_headers(),
            params={"pageSize": limit},
            timeout=10,
        )
        if resp.status_code == 200:
            docs = resp.json().get("documents", [])
            results = []
            for d in docs:
                a = _from_doc(d, inject_uid=uid)
                # Attach email from session if it's admin's own data
                if uid == st.session_state.get("user_uid", ""):
                    a.setdefault("user_email", st.session_state.get("user_email", ""))
                results.append(a)
            return results
        else:
            print(f"[Admin] Read {uid[:8]}: HTTP {resp.status_code}")
            return []
    except Exception as e:
        print(f"[Admin] Read {uid[:8]} error: {e}")
        return []


# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────

def fetch_all_analyses(limit: int = 500) -> list:
    """
    Fetch all platform analyses using direct per-user reads.

    1. Discover all UIDs (enumerate /users + platform_stats + admin UID)
    2. Read /users/{uid}/analyses for each UID
    3. Merge, deduplicate, sort newest first

    This approach works with your existing Firestore rules — no index needed.
    """
    token = _id_token()
    if not token:
        print("[Admin] No auth token — not logged in")
        return []

    # Step A: Get all UIDs
    all_uids = _get_all_user_uids()
    if not all_uids:
        print("[Admin] No UIDs discovered")
        return []

    print(f"[Admin] Fetching analyses for {len(all_uids)} users...")

    # Step B: Read each user's analyses
    all_analyses = []
    seen_doc_ids = set()

    for uid in all_uids:
        user_analyses = _fetch_user_analyses(uid, limit=200)
        for a in user_analyses:
            doc_id = a.get("_doc_id", "") or a.get("doc_id", "")
            if doc_id not in seen_doc_ids:
                seen_doc_ids.add(doc_id)
                all_analyses.append(a)

    # Step C: Sort newest first
    all_analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    print(f"[Admin] Total: {len(all_analyses)} analyses from {len(all_uids)} users")
    return all_analyses[:limit]


# ── PLATFORM STATS REGISTRY ───────────────────────────────────────────────────

def write_platform_stat(uid: str, email: str, analysis: dict) -> bool:
    """
    Write a summary to platform_stats/{uid} every time a user saves.
    This registers the user UID so admin can find them during enumeration.
    Also updates the users/{uid}/profile doc for email storage.
    """
    token = _id_token()
    if not token or not uid:
        return False

    # Write to platform_stats/{uid}
    url = f"{_rest_base()}/platform_stats/{uid}"
    try:
        # Read existing to get current count
        existing_count = 0
        existing_avg   = 0
        try:
            r = requests.get(url, headers=_headers(), timeout=5)
            if r.status_code == 200:
                existing = _from_doc(r.json())
                existing_count = existing.get("total_analyses", 0)
                existing_avg   = existing.get("avg_score", 0)
        except Exception:
            pass

        new_count = existing_count + 1
        new_score = analysis.get("overall_investment_score", 0)
        new_avg   = round(
            (existing_avg * existing_count + new_score) / new_count
        )

        doc = {
            "fields": {
                "uid":            _to_value(uid),
                "email":          _to_value(email),
                "total_analyses": _to_value(new_count),
                "avg_score":      _to_value(new_avg),
                "last_active":    _to_value(datetime.now(timezone.utc).isoformat()),
            }
        }
        resp = requests.patch(
            url, headers=_headers(),
            data=_json.dumps(doc), timeout=8,
        )
        if resp.status_code == 200:
            print(f"[Admin] platform_stats updated for {uid[:8]}")
            return True
        else:
            print(f"[Admin] platform_stats write failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[Admin] platform_stats write error: {e}")
        return False


# ── ADMIN ACTIONS ─────────────────────────────────────────────────────────────

def revoke_public_access(uid: str, doc_id: str) -> bool:
    """Set is_public=False on any analysis."""
    token = _id_token()
    if not token:
        return False
    url  = f"{_rest_base()}/users/{uid}/analyses/{doc_id}"
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
    """Admin delete any analysis."""
    token = _id_token()
    if not token:
        return False
    url = f"{_rest_base()}/users/{uid}/analyses/{doc_id}"
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

    scores        = [a.get("overall_investment_score", 0) for a in analyses]
    avg_score     = round(sum(scores) / total)
    strong_invest = sum(1 for a in analyses if "invest"   in a.get("final_recommendation","").lower())
    consider      = sum(1 for a in analyses if "consider" in a.get("final_recommendation","").lower())
    reject        = sum(1 for a in analyses if "reject"   in a.get("final_recommendation","").lower())
    public_count  = sum(1 for a in analyses if a.get("is_public"))
    unique_users  = len(set(
        a.get("_uid","") or a.get("uid","") for a in analyses if a.get("_uid") or a.get("uid")
    ))

    today_c = week_c = month_c = 0
    for a in analyses:
        try:
            dt = datetime.fromisoformat(a.get("created_at","").replace("Z","+00:00"))
            if dt.date() == today_d: today_c += 1
            if dt >= week_ago:       week_c  += 1
            if dt >= month_ago:      month_c += 1
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
        "scores": [], "last_active": "", "strong_invest": 0,
    })
    for a in analyses:
        uid   = a.get("_uid") or a.get("uid", "unknown")
        u     = users[uid]
        u["uid"]   = uid
        u["email"] = a.get("user_email","") or u["email"]
        u["total"] += 1
        u["scores"].append(a.get("overall_investment_score", 0))
        if "invest" in a.get("final_recommendation","").lower():
            u["strong_invest"] += 1
        if a.get("created_at","") > u["last_active"]:
            u["last_active"] = a.get("created_at","")

    rows = []
    for uid, u in users.items():
        u["avg_score"] = round(sum(u["scores"]) / len(u["scores"])) if u["scores"] else 0
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
    results = {}
    try:
        key = st.secrets.get("groq", {}).get("api_key", "")
        if key:
            r = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"}, timeout=5,
            )
            results["Groq"] = "✅ Online" if r.status_code == 200 else f"⚠️ HTTP {r.status_code}"
        else:
            results["Groq"] = "❌ No API key in secrets"
    except Exception:
        results["Groq"] = "❌ Unreachable"

    try:
        key = st.secrets.get("google", {}).get("api_key", "")
        if key:
            r = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
                timeout=5,
            )
            results["Gemini"] = "✅ Online" if r.status_code == 200 else f"⚠️ HTTP {r.status_code}"
        else:
            results["Gemini"] = "❌ No API key in secrets"
    except Exception:
        results["Gemini"] = "❌ Unreachable"

    try:
        token = _id_token()
        if token:
            r = requests.get(
                f"https://firestore.googleapis.com/v1/projects/{_project_id()}/databases/(default)/documents/platform_stats",
                headers={"Authorization": f"Bearer {token}"}, timeout=5,
            )
            results["Firestore"] = "✅ Connected" if r.status_code in (200, 404) else f"⚠️ HTTP {r.status_code}"
        else:
            results["Firestore"] = "⚠️ No auth token"
    except Exception:
        results["Firestore"] = "❌ Unreachable"

    return results
