"""
InvestIQ AI — Firestore Database Layer

All database operations:
  - Save analysis
  - Fetch single analysis
  - List user's analyses
  - Generate & resolve public share tokens
  - Delete analysis

Collection path: users/{uid}/analyses/{analysisId}
"""

import uuid
import streamlit as st
from datetime import datetime, timezone
from typing import Optional

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    ADMIN_OK = True
except ImportError:
    ADMIN_OK = False

# ── FIRESTORE CLIENT ───────────────────────────────────────────────────────────

def _get_db():
    """
    Initialize Firebase Admin SDK once and return Firestore client.
    Uses Streamlit secrets for service account config.
    Falls back gracefully if firebase_admin not available.
    """
    if not ADMIN_OK:
        return None

    if not firebase_admin._apps:
        cfg = dict(st.secrets["firebase"])

        # Build a service account credential dict from secrets
        # Users must add service_account section to secrets.toml
        # OR we use pyrebase REST API as fallback (see below)
        try:
            sa = st.secrets.get("service_account", {})
            if sa:
                cred = credentials.Certificate(dict(sa))
            else:
                # Minimal anonymous-style init (read-only public only)
                cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                "projectId": cfg.get("projectId", "")
            })
        except Exception:
            pass

    try:
        return firestore.client()
    except Exception:
        return None


# ── PYREBASE REST FALLBACK ─────────────────────────────────────────────────────
# We use pyrebase (already installed for auth) with the user's ID token
# to perform authenticated Firestore REST operations.
# This avoids needing a service account JSON entirely.

import requests
import json as _json


def _firestore_rest_url(project_id: str, path: str) -> str:
    base = "https://firestore.googleapis.com/v1"
    return f"{base}/projects/{project_id}/databases/(default)/documents/{path}"


def _id_token() -> Optional[str]:
    return st.session_state.get("id_token")


def _project_id() -> str:
    return st.secrets["firebase"]["projectId"]


def _to_firestore_value(val):
    """Convert a Python value to Firestore REST API value format."""
    if val is None:
        return {"nullValue": None}
    elif isinstance(val, bool):
        return {"booleanValue": val}
    elif isinstance(val, int):
        return {"integerValue": str(val)}
    elif isinstance(val, float):
        return {"doubleValue": val}
    elif isinstance(val, str):
        return {"stringValue": val}
    elif isinstance(val, list):
        return {"arrayValue": {"values": [_to_firestore_value(v) for v in val]}}
    elif isinstance(val, dict):
        return {"mapValue": {"fields": {k: _to_firestore_value(v) for k, v in val.items()}}}
    else:
        return {"stringValue": str(val)}


def _from_firestore_value(val: dict):
    """Convert a Firestore REST API value to Python."""
    if "nullValue" in val:
        return None
    elif "booleanValue" in val:
        return val["booleanValue"]
    elif "integerValue" in val:
        return int(val["integerValue"])
    elif "doubleValue" in val:
        return float(val["doubleValue"])
    elif "stringValue" in val:
        return val["stringValue"]
    elif "arrayValue" in val:
        items = val["arrayValue"].get("values", [])
        return [_from_firestore_value(v) for v in items]
    elif "mapValue" in val:
        fields = val["mapValue"].get("fields", {})
        return {k: _from_firestore_value(v) for k, v in fields.items()}
    elif "timestampValue" in val:
        return val["timestampValue"]
    return None


def _from_firestore_doc(doc: dict) -> dict:
    """Convert full Firestore REST document to flat Python dict."""
    fields = doc.get("fields", {})
    result = {}
    for k, v in fields.items():
        result[k] = _from_firestore_value(v)
    # Add doc id from name field
    name = doc.get("name", "")
    if "/" in name:
        result["_doc_id"] = name.split("/")[-1]
    return result


def _to_firestore_doc(data: dict) -> dict:
    """Convert flat Python dict to Firestore REST document fields."""
    return {"fields": {k: _to_firestore_value(v) for k, v in data.items()}}


# ── SAVE ANALYSIS ──────────────────────────────────────────────────────────────

def save_analysis(uid: str, result: dict) -> Optional[str]:
    """
    Save an assembled analysis result to Firestore.

    Args:
        uid:    Firebase user UID.
        result: Assembled result dict from pipeline.assemble_final_result()

    Returns:
        Document ID string, or None on failure.
    """
    token = _id_token()
    if not token or not uid:
        return None

    doc_id = str(uuid.uuid4()).replace("-", "")[:20]
    public_token = str(uuid.uuid4()).replace("-", "")

    document = {
        **result,
        "uid": uid,
        "doc_id": doc_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_public": False,
        "public_token": public_token,
    }

    # Remove non-serializable keys just in case
    document.pop("timings", None)
    document.pop("pipeline_errors", None)

    project = _project_id()
    path = f"users/{uid}/analyses/{doc_id}"
    url = _firestore_rest_url(project, path)

    try:
        resp = requests.patch(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            data=_json.dumps(_to_firestore_doc(document)),
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return doc_id
        else:
            print(f"Firestore save error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"Firestore save exception: {e}")
        return None


# ── FETCH SINGLE ANALYSIS ──────────────────────────────────────────────────────

def fetch_analysis(uid: str, doc_id: str) -> Optional[dict]:
    """
    Fetch a single analysis document.

    Args:
        uid:    Firebase user UID.
        doc_id: Document ID.

    Returns:
        Python dict of analysis data, or None if not found.
    """
    token = _id_token()
    if not token or not uid:
        return None

    project = _project_id()
    path = f"users/{uid}/analyses/{doc_id}"
    url = _firestore_rest_url(project, path)

    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=8,
        )
        if resp.status_code == 200:
            doc = resp.json()
            return _from_firestore_doc(doc)
        return None
    except Exception as e:
        print(f"Firestore fetch exception: {e}")
        return None


# ── LIST USER ANALYSES ─────────────────────────────────────────────────────────

def list_analyses(uid: str, limit: int = 50) -> list:
    """
    List all analyses for a user, sorted newest first.

    Args:
        uid:   Firebase user UID.
        limit: Maximum number of results.

    Returns:
        List of analysis dicts, sorted by created_at descending.
    """
    token = _id_token()
    if not token or not uid:
        return []

    project = _project_id()
    path = f"users/{uid}/analyses"
    url = _firestore_rest_url(project, path)

    params = {"pageSize": limit}

    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            docs = data.get("documents", [])
            results = [_from_firestore_doc(d) for d in docs]
            # Sort by created_at descending
            results.sort(
                key=lambda x: x.get("created_at", ""),
                reverse=True,
            )
            return results
        return []
    except Exception as e:
        print(f"Firestore list exception: {e}")
        return []


# ── DELETE ANALYSIS ────────────────────────────────────────────────────────────

def delete_analysis(uid: str, doc_id: str) -> bool:
    """
    Delete a single analysis document.

    Returns True on success.
    """
    token = _id_token()
    if not token or not uid:
        return False

    project = _project_id()
    path = f"users/{uid}/analyses/{doc_id}"
    url = _firestore_rest_url(project, path)

    try:
        resp = requests.delete(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=8,
        )
        return resp.status_code in (200, 204)
    except Exception as e:
        print(f"Firestore delete exception: {e}")
        return False


# ── PUBLIC SHARE TOKEN ─────────────────────────────────────────────────────────

def make_analysis_public(uid: str, doc_id: str) -> Optional[str]:
    """
    Set is_public=True on a document and return its public_token.
    If already public, just returns the existing token.
    """
    existing = fetch_analysis(uid, doc_id)
    if not existing:
        return None

    if existing.get("is_public") and existing.get("public_token"):
        return existing["public_token"]

    token = _id_token()
    project = _project_id()
    path = f"users/{uid}/analyses/{doc_id}"
    url = _firestore_rest_url(project, path)

    public_token = existing.get("public_token") or str(uuid.uuid4()).replace("-", "")

    update_fields = {
        "is_public": True,
        "public_token": public_token,
    }

    try:
        resp = requests.patch(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            params={
                "updateMask.fieldPaths": ["is_public", "public_token"],
            },
            data=_json.dumps(_to_firestore_doc(update_fields)),
            timeout=8,
        )
        if resp.status_code == 200:
            return public_token
        return None
    except Exception as e:
        print(f"Make public exception: {e}")
        return None


def fetch_public_analysis(public_token: str) -> Optional[dict]:
    """
    Fetch an analysis by public_token (no auth required — uses API key).

    This queries all users' collections via Firestore REST with an API key.
    We do a collection group query.
    """
    api_key = st.secrets["firebase"]["apiKey"]
    project = _project_id()

    # Firestore collection group query via REST
    query_url = (
        f"https://firestore.googleapis.com/v1/projects/{project}"
        f"/databases/(default)/documents:runQuery?key={api_key}"
    )

    query_body = {
        "structuredQuery": {
            "from": [{"collectionId": "analyses", "allDescendants": True}],
            "where": {
                "compositeFilter": {
                    "op": "AND",
                    "filters": [
                        {
                            "fieldFilter": {
                                "field": {"fieldPath": "public_token"},
                                "op": "EQUAL",
                                "value": {"stringValue": public_token},
                            }
                        },
                        {
                            "fieldFilter": {
                                "field": {"fieldPath": "is_public"},
                                "op": "EQUAL",
                                "value": {"booleanValue": True},
                            }
                        },
                    ],
                }
            },
            "limit": 1,
        }
    }

    try:
        resp = requests.post(
            query_url,
            data=_json.dumps(query_body),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            results = resp.json()
            for item in results:
                doc = item.get("document")
                if doc:
                    return _from_firestore_doc(doc)
        return None
    except Exception as e:
        print(f"Public fetch exception: {e}")
        return None


# ── FIRESTORE SETUP NOTE ───────────────────────────────────────────────────────
# In Firebase Console → Firestore → Rules, add:
#
# rules_version = '2';
# service cloud.firestore {
#   match /databases/{database}/documents {
#     match /users/{userId}/analyses/{analysisId} {
#       allow read, write: if request.auth != null
#                          && request.auth.uid == userId;
#     }
#     match /{path=**}/analyses/{analysisId} {
#       allow read: if resource.data.is_public == true;
#     }
#   }
# }