"""
The complete BRO Risk Oracle application (FastAPI), all features included.

Wires every feature group onto the tested foundations:
  - persistence + RBAC          (Group A)
  - core lifecycle + scoring    (Group B, ported engine)
  - four intelligence engines   (Group C, deterministic-local)
  - monitoring lifecycle        (Group D)
  - notifications + email + webhooks (Group E)
  - conversational + autopilot  (Group F)
  - admin + MCP tools + procurement (Group G)

Persistence is SQLAlchemy on SQLite by default (runs offline) or Postgres via
BRO_DB_URL. Auth is a simple bearer/session actor for API use. Every
consequential mutation appends to the hash-chained audit log.
"""
from __future__ import annotations

import json
import re as _re

_EMAIL_RE = _re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = _re.compile(r"^\+?[0-9]+$")

def _can_view_assessment(u, a) -> bool:
    """CR-3: assessment record visibility by role.
    - admin (reviewer) and vrm (assessor): see ALL records
    - buyer (business user): see ONLY their own (owner / SPOC)
    - vendor: see NONE
    """
    role = getattr(getattr(u, "role", None), "key", None)
    if role in ("admin", "vrm"):
        return True
    if role == "vendor":
        return False
    if role == "buyer":
        return u.username in (a.engagement_owner, a.spoc_user)
    return u.username in (a.engagement_owner, a.spoc_user, a.assessor_user)

def _validate_typed_fields(data: dict):
    """CR-8: server-side validation backing the typed inputs. Returns an error
    string if any email/phone/date value is malformed, else None. Empty values pass."""
    for k, v in (data or {}).items():
        if v in (None, "", []):
            continue
        key = str(k).lower()
        sval = str(v)
        if "email" in key and not _EMAIL_RE.match(sval):
            return f"'{k}' must be a valid email address"
        if _re.search(r"phone|telephone|mobile|contact_number", key) and not _PHONE_RE.match(sval):
            return f"'{k}' may contain only '+' and digits"
        if _re.search(r"date$|_date|dob$", key):
            if not _re.match(r"^\d{4}-\d{2}-\d{2}$", sval):
                return f"'{k}' must be a valid date (YYYY-MM-DD)"
    return None
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .features import bro_engine as eng
from .features import intel
from .features.models_db import (
    Base, EngagementRow, Role, User, Vendor,
    make_engine, make_session_factory, verify_password,
)
from .features.models_feature import (
    Acceptance, AuditLog, Certification, Contract, ConversationMessage,
    ConversationSession, Document, EmailOutbox, Finding, FourthParty,
    Incident, IntelResult, MethodologyVersion, Monitoring, Notification,
    Offboarding, Reassessment, Webhook,
)
from .features.rbac import has_permission, seed
from .features.auth import bearer_subject, issue_token, TokenError


# ---------- request schemas ----------

class VendorIn(BaseModel):
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    contact_email: Optional[str] = None
    tier: str = "Tier 3"

class CriticalIn(BaseModel):
    reason: str

class EngagementIn(BaseModel):
    vendor_id: int
    title: str
    service_description: Optional[str] = None
    business_contact_email: Optional[str] = None

class IRQIn(BaseModel):
    answers: dict

class DDQIn(BaseModel):
    answers: dict

class OverrideIn(BaseModel):
    band: str
    reason: str
    second_approver: str

class FindingIn(BaseModel):
    engagement_id: Optional[int] = None
    title: str
    severity: str = "medium"

class IntelIn(BaseModel):
    vendor_id: int
    payload: dict = {}

class LoginIn(BaseModel):
    username: str
    password: str

class ChatStart(BaseModel):
    engagement_id: Optional[int] = None
    actor_role: str = "assessor"

class ChatTurn(BaseModel):
    session_id: int
    message: str

class MethIn(BaseModel):
    version: str
    note: Optional[str] = None

class POIn(BaseModel):
    vendor_name: str
    amount: float
    ext_ref: Optional[str] = None

class CertIn(BaseModel):
    vendor_id: int
    name: str
    valid_until: Optional[str] = None

class DocIn(BaseModel):
    vendor_id: Optional[int] = None
    engagement_id: Optional[int] = None
    name: str
    doc_type: str = "other"
    next_validation: Optional[str] = None

class FourthIn(BaseModel):
    vendor_id: int
    name: str
    service: Optional[str] = None

class AcceptIn(BaseModel):
    engagement_id: int
    rationale: str
    expires_at: Optional[str] = None

class ReassessIn(BaseModel):
    engagement_id: int
    mode: str = "periodic"

# --- new: CRUD / admin / self-service schemas ---
class VendorUpdateIn(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    contact_email: Optional[str] = None
    tier: Optional[str] = None

class EngagementUpdateIn(BaseModel):
    title: Optional[str] = None
    service_description: Optional[str] = None
    business_contact_email: Optional[str] = None

class FindingUpdateIn(BaseModel):
    title: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None

class UserIn(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: str
    role_key: str

class UserUpdateIn(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_key: Optional[str] = None
    is_active: Optional[bool] = None

class RolePermsIn(BaseModel):
    permission_keys: list[str]

class PasswordIn(BaseModel):
    current_password: str
    new_password: str

class ProfileIn(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None

class WebhookIn(BaseModel):
    url: str
    event: str = "*"

class SignoffIn(BaseModel):
    decision: str = "approved"
    note: Optional[str] = None

class EmailIn(BaseModel):
    to_addr: str
    subject: str
    body: str

class ChatSessionIn(BaseModel):
    engagement_id: Optional[int] = None

class ChatSendIn(BaseModel):
    session_id: int
    message: str
    agent: Optional[str] = None

class LearningIn(BaseModel):
    rating: int = 3
    agent: Optional[str] = None
    stage: int = 0
    issue: Optional[str] = None
    note: Optional[str] = None

# --- v2 registry schemas ---
class V2VendorIn(BaseModel):
    legal_name: str
    trading_name: Optional[str] = None
    registration_number: Optional[str] = None
    hq_country: Optional[str] = None
    website: Optional[str] = None
    listing_status: Optional[str] = None
    tier: Optional[str] = "Tier 3"
    group_id: Optional[str] = None
    parent_company: Optional[str] = None
    industries: Optional[list[str]] = None
    procurement_ref: Optional[str] = None
    created_via: Optional[str] = "button"

class GroupOverrideIn(BaseModel):
    group_id: str

class V2ContactIn(BaseModel):
    owner_type: str
    owner_id: str
    name: str
    is_primary: bool = False
    email: Optional[str] = None
    phone_country_code: Optional[str] = None
    phone_number: Optional[str] = None
    designation: Optional[str] = None
    country: Optional[str] = None
    mailing_address: Optional[str] = None

class V2EngagementIn(BaseModel):
    vendor_id: str
    title: str
    service_description: Optional[str] = None
    material_group_id: Optional[str] = None
    business_unit: Optional[str] = None
    deployment_model: Optional[str] = None
    owner_user: Optional[str] = None
    annual_value: Optional[float] = None
    currency: Optional[str] = None

class V2AssessmentIn(BaseModel):
    engagement_id: str
    vendor_id: Optional[str] = None
    session_id: Optional[int] = None
    inherent_band: Optional[str] = None
    residual_band: Optional[str] = None

class ReassignIn(BaseModel):
    assessor_user: str

class V2FindingIn(BaseModel):
    title: str
    severity: Optional[str] = "Medium"
    source: Optional[str] = "Assessor"
    description: Optional[str] = None
    domain: Optional[str] = None
    engagement_id: Optional[str] = None
    vendor_id: Optional[str] = None
    assessment_id: Optional[str] = None
    due_date: Optional[str] = None

class V2RemediationIn(BaseModel):
    finding_id: str
    plan: str
    owner: Optional[str] = None
    target_date: Optional[str] = None

class V2FourthPartyIn(BaseModel):
    legal_name: str
    service_provided: Optional[str] = None
    hq_country: Optional[str] = None
    vendor_ids: Optional[list[str]] = None
    vendor_id: Optional[str] = None

class V2ArtefactIn(BaseModel):
    vendor_id: str
    name: str
    artefact_type: Optional[str] = "certificate"
    expiry_date: Optional[str] = None
    issue_date: Optional[str] = None
    engagement_id: Optional[str] = None
    received_via: Optional[str] = "upload"
    supersedes: Optional[str] = None

class FinancialIn(BaseModel):
    figures: dict
    flags: Optional[dict] = None
    vendor_id: Optional[str] = None
    other_name: Optional[str] = None

class ReputationIn(BaseModel):
    events: Optional[list[dict]] = None
    customer_facing: bool = False
    vendor_id: Optional[str] = None
    other_name: Optional[str] = None

class ContractTermsIn(BaseModel):
    inherent_band: str = "MODERATE"
    exposure: Optional[dict] = None
    vendor_id: Optional[str] = None
    other_name: Optional[str] = None

class ContractGapIn(BaseModel):
    contract_text: str
    inherent_band: str = "MODERATE"
    exposure: Optional[dict] = None

class ContractDiffIn(BaseModel):
    inherent_band: str = "MODERATE"
    exposure: Optional[dict] = None
    prior_contract_texts: list[str]

class MgmtChatIn(BaseModel):
    question: str

class CaptureIn(BaseModel):
    session_id: int
    engagement_id: str
    vendor_id: Optional[str] = None

class EmailIntakeIn(BaseModel):
    sender: str
    subject: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_b64: Optional[str] = None
    body_text: Optional[str] = None
    vendor_id: Optional[str] = None

class _DocFile(BaseModel):
    filename: str
    content_type: Optional[str] = "application/octet-stream"
    data_b64: str

class DocUploadIn(BaseModel):
    files: list[_DocFile]
    vendor_id: Optional[str] = None
    engagement_id: Optional[str] = None
    purpose: Optional[str] = None

class CertIngestIn(BaseModel):
    files: list[_DocFile]
    vendor_id: str
    engagement_id: Optional[str] = None

class ContractGapDocIn(BaseModel):
    file: _DocFile
    engagement_id: Optional[str] = None
    vendor_id: Optional[str] = None
    other_name: Optional[str] = None
    inherent_band: Optional[str] = None

class PeerBenchmarkIn(BaseModel):
    figures: dict
    flags: Optional[dict] = None
    sector: str = "other"

class FinResearchIn(BaseModel):
    company: str
    jurisdiction: str = "UK"
    identifier: Optional[str] = ""
    year: Optional[str] = ""

class FinMonitorAddIn(BaseModel):
    vendor_id: Optional[str] = None
    other_name: Optional[str] = None

class FinMonitorSweepIn(BaseModel):
    monitor_id: Optional[int] = None   # sweep one, or all if None

# ---- Req 1/2/3 schemas ----
class VendorMasterIn(BaseModel):
    data: dict
    include_bank: bool = False

class ScreeningIn(BaseModel):
    screen_type: str
    result: Optional[str] = None
    detail: Optional[str] = None
    screened_date: Optional[str] = None
    next_due: Optional[str] = None

class AttrDomainIn(BaseModel):
    data: dict

class InsuranceIn(BaseModel):
    policy_type: str
    coverage_limit: Optional[float] = None
    currency: Optional[str] = None
    insurer: Optional[str] = None
    certificate_expiry: Optional[str] = None
    named_insured_verified: bool = False

class MonitorSignalIn(BaseModel):
    signal_type: str
    value: str
    source: Optional[str] = None

class EngExtIn(BaseModel):
    data: dict

class EngChildIn(BaseModel):
    kind: str   # deliverable/milestone/sla/obligation/personnel
    data: dict

# ---- R2 contract entity schemas ----
class ContractCreateIn(BaseModel):
    contract_type: str = "Contract"
    vendor_id: Optional[str] = None
    engagement_id: Optional[str] = None
    parent_msa: Optional[str] = None
    data: Optional[dict] = None

class ContractUpdateIn(BaseModel):
    data: dict

# ---- R3 critical vendors schemas ----
class CriticalityInputIn(BaseModel):
    customer_impact: Optional[int] = None
    downtime_tolerance: Optional[int] = None
    alternative_availability: Optional[int] = None
    substitution_complexity: Optional[int] = None

class CriticalAnalysisIn(BaseModel):
    vendor_id: Optional[str] = None

class CriticalOverrideIn(BaseModel):
    is_critical: bool
    reason: str

# ---- R4 performance management schemas ----
class ScorecardCreateIn(BaseModel):
    vendor_id: str
    period_label: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    cadence: str = "quarterly"

class PerfEnrolIn(BaseModel):
    vendor_ids: list[str]

class KPIScoreIn(BaseModel):
    actual: Optional[str] = None
    score: Optional[int] = None
    excluded: Optional[bool] = None
    exclude_reason: Optional[str] = None

class AgreeIn(BaseModel):
    party: str

class ReviewIn(BaseModel):
    data: dict

class PerfCapaIn(BaseModel):
    scorecard_id: str
    gap: str
    owner: str
    due_date: Optional[str] = None

class CapaVerifyIn(BaseModel):
    evidence: str

# ---- R5 ProAssess schemas ----
class ProAssessRunIn(BaseModel):
    vendor_id: Optional[str] = None
    engagement_id: Optional[str] = None
    irq: Optional[dict] = None
    ddq: Optional[dict] = None
    documents: Optional[list] = None
    extracted: Optional[dict] = None   # LLM-extracted structured inputs (financials, reputation_events, flags)

class ProAssessRegisterIn(BaseModel):
    report: dict

class ProAssessAutoIn(BaseModel):
    free_text: Optional[str] = ""
    documents: Optional[list] = None        # [{filename, content_type, data_b64}]
    vendor_id: Optional[str] = None         # existing vendor, OR:
    new_vendor_name: Optional[str] = None   # create a new vendor
    engagement_title: Optional[str] = None
    ddq: Optional[dict] = None
    create_records: bool = True


def create_app(db_url: Optional[str] = None) -> FastAPI:
    engine = make_engine(db_url or "sqlite:///:memory:")
    # ensure registry models are imported so their tables register on Base
    from .features import registry_models as _rm  # noqa: F401
    from .features import master_ext as _mx  # noqa: F401  (Req 1/2/3 tables)
    from .features import documents as _docs  # noqa: F401  (CR-4/5/12 document store)
    Base.metadata.create_all(engine)
    SessionFactory = make_session_factory(engine)

    with SessionFactory() as s:
        seed(s)
        from .features.registry_service import seed_masters
        seed_masters(s)
        s.commit()

    app = FastAPI(title="BRO Risk Oracle", version="4.0-unified")

    def db() -> Session:
        s = SessionFactory()
        try:
            yield s
        finally:
            s.close()

    # ----- actor + RBAC -----
    # Production auth: identity comes from a verified JWT bearer token, NOT a
    # client-supplied header. A test/dev escape hatch (BRO_TRUST_HEADER=1) keeps
    # the x-user header working for the existing test suite and local poking.
    def actor(authorization: str = Header(default=None),
              x_user: str = Header(default=None),
              s: Session = Depends(db)) -> User:
        username: Optional[str] = None
        if authorization:
            try:
                username = bearer_subject(authorization)
            except TokenError as e:
                raise HTTPException(401, str(e))
        elif _os.environ.get("BRO_TRUST_HEADER") == "1" and x_user:
            username = x_user  # dev/test only
        if not username:
            raise HTTPException(401, "authentication required")
        u = s.scalars(select(User).where(User.username == username)).first()
        if not u or not u.is_active:
            raise HTTPException(401, "unknown or inactive user")
        return u

    def require(perm: str):
        def dep(u: User = Depends(actor)):
            if not has_permission(u, perm):
                raise HTTPException(403, f"missing permission: {perm}")
            return u
        return dep

    # ----- audit (hash-chained, persisted) -----
    def audit(s: Session, action: str, actor_name: str, detail: dict) -> None:
        last = s.scalars(select(AuditLog).order_by(AuditLog.seq.desc())).first()
        prev = last.entry_hash if last else "genesis"
        seq = (last.seq + 1) if last else 0
        h = eng.chain_hash(prev, action, actor_name, detail)
        s.add(AuditLog(seq=seq, action=action, actor=actor_name,
                       detail=json.dumps(detail, sort_keys=True),
                       prev_hash=prev, entry_hash=h))

    def notify(s: Session, event: str, audience: str = "all",
               body: str = "") -> None:
        s.add(Notification(audience=audience, event=event, body=body))

    # ===== health =====
    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "version": "4.0-unified",
                "ai": "local-deterministic"}

    # ===== auth =====

    @app.post("/api/v1/login")
    def login(body: LoginIn, s: Session = Depends(db)):
        u = s.scalars(select(User).where(User.username == body.username)).first()
        if not u or not verify_password(body.password, u.password_hash):
            raise HTTPException(401, "invalid credentials")
        token = issue_token(u.username, u.role.key)
        return {"token": token, "token_type": "bearer",
                "username": u.username, "role": u.role.key,
                "permissions": [p.key for p in u.role.permissions]}

    # ===== vendors =====
    @app.post("/api/v1/vendors")
    def create_vendor(v: VendorIn, s: Session = Depends(db),
                      u: User = Depends(require("vendor.edit"))):
        row = Vendor(**v.model_dump())
        s.add(row); s.flush()
        audit(s, "vendor.created", u.username, {"vendor_id": row.id, "name": v.name})
        s.commit()
        return {"vendor_id": row.id, "name": row.name, "tier": row.tier}

    @app.get("/api/v1/vendors")
    def list_vendors(s: Session = Depends(db), u: User = Depends(require("vendor.view"))):
        return [{"vendor_id": v.id, "name": v.name, "tier": v.tier,
                 "is_critical": v.is_critical}
                for v in s.scalars(select(Vendor)).all()]

    @app.post("/api/v1/vendors/{vid}/critical")
    def designate_critical(vid: int, body: CriticalIn, s: Session = Depends(db),
                           u: User = Depends(require("vendor.critical"))):
        # Tier 0 = human-only (our Q5). RBAC already enforces a human role here.
        v = s.get(Vendor, vid)
        if not v:
            raise HTTPException(404, "vendor not found")
        v.is_critical = True
        v.critical_reason = body.reason
        v.critical_by = u.username
        audit(s, "vendor.critical_designated", u.username,
              {"vendor_id": vid, "reason": body.reason})
        notify(s, f"Critical vendor designated: {v.name}", "vrm")
        s.commit()
        return {"vendor_id": vid, "is_critical": True, "by": u.username}

    # ===== engagements + lifecycle =====
    @app.post("/api/v1/engagements")
    def create_engagement(e: EngagementIn, s: Session = Depends(db),
                          u: User = Depends(require("engagement.create"))):
        if not s.get(Vendor, e.vendor_id):
            raise HTTPException(404, "vendor not found")
        row = EngagementRow(vendor_id=e.vendor_id, title=e.title,
                            service_description=e.service_description,
                            business_contact_email=e.business_contact_email,
                            owner_id=u.id, stage="sourcing")
        s.add(row); s.flush()
        audit(s, "engagement.created", u.username, {"engagement_id": row.id})
        notify(s, f"Engagement created: {e.title}", "business")
        s.commit()
        return {"engagement_id": row.id, "stage": row.stage}

    @app.post("/api/v1/engagements/{eid}/irq")
    def submit_irq(eid: int, body: IRQIn, s: Session = Depends(db),
                   u: User = Depends(require("engagement.edit"))):
        e = s.get(EngagementRow, eid)
        if not e:
            raise HTTPException(404, "engagement not found")
        tier = eng.compute_tier(body.answers)
        inherent = eng.compute_inherent(body.answers)
        routing = eng.compute_route(body.answers, inherent, tier)
        e.inherent_band = inherent["band"]
        e.inherent_pct = inherent["weighted_pct"]
        e.route = routing["route"]
        e.stage = "inherent"
        audit(s, "irq.scored", u.username,
              {"engagement_id": eid, "tier": tier, "band": inherent["band"],
               "route": routing["route"]})
        notify(s, f"IRQ scored {inherent['band']} ({routing['route']})", "all")
        s.commit()
        return {"engagement_id": eid, "tier": tier,
                "inherent_band": inherent["band"],
                "inherent_pct": inherent["weighted_pct"],
                "cls": inherent["cls"], "routing": routing}

    @app.post("/api/v1/engagements/{eid}/ddq")
    def submit_ddq(eid: int, body: DDQIn, s: Session = Depends(db),
                   u: User = Depends(require("engagement.edit"))):
        e = s.get(EngagementRow, eid)
        if not e:
            raise HTTPException(404, "engagement not found")
        residual = eng.compute_residual(e.inherent_band or "LOW", body.answers)
        decision = eng.decision_for(residual["band"], residual["critical_marginal"])
        e.residual_band = residual["band"]
        e.decision = decision["text"]
        e.stage = "decision"
        audit(s, "ddq.residual", u.username,
              {"engagement_id": eid, "residual": residual["band"],
               "critical_marginal": residual["critical_marginal"],
               "decision": decision["text"]})
        notify(s, f"Residual {residual['band']}: {decision['text']}", "all")
        s.commit()
        return {"engagement_id": eid, "residual_band": residual["band"],
                "critical_marginal": residual["critical_marginal"],
                "decision": decision}

    @app.post("/api/v1/engagements/{eid}/override")
    def override(eid: int, body: OverrideIn, s: Session = Depends(db),
                 u: User = Depends(require("engagement.override"))):
        # human-only (RBAC) + justification + 2nd approver (two-gate model)
        e = s.get(EngagementRow, eid)
        if not e:
            raise HTTPException(404, "engagement not found")
        if not body.reason or not body.second_approver:
            raise HTTPException(400, "override needs justification and 2nd approver")
        e.residual_band = body.band
        audit(s, "decision.override", u.username,
              {"engagement_id": eid, "new_band": body.band,
               "reason": body.reason, "second_approver": body.second_approver})
        s.commit()
        return {"engagement_id": eid, "residual_band": body.band, "override": True}

    @app.post("/api/v1/engagements/{eid}/terminate")
    def terminate(eid: int, s: Session = Depends(db),
                  u: User = Depends(require("lifecycle.offboard"))):
        e = s.get(EngagementRow, eid)
        if not e:
            raise HTTPException(404, "engagement not found")
        e.stage = "terminate"
        e.status = "terminated"
        for key, label in eng.OFFBOARDING_STEPS:
            s.add(Offboarding(engagement_id=eid, step_key=key))
        audit(s, "engagement.terminated", u.username, {"engagement_id": eid})
        notify(s, "Offboarding initiated", "all")
        s.commit()
        return {"engagement_id": eid, "stage": "terminate",
                "offboarding_steps": len(eng.OFFBOARDING_STEPS)}

    @app.get("/api/v1/engagements/{eid}")
    def get_engagement(eid: int, s: Session = Depends(db),
                       u: User = Depends(require("engagement.view"))):
        e = s.get(EngagementRow, eid)
        if not e:
            raise HTTPException(404, "engagement not found")
        return {"engagement_id": e.id, "vendor_id": e.vendor_id,
                "stage": e.stage, "status": e.status, "route": e.route,
                "inherent_band": e.inherent_band, "residual_band": e.residual_band,
                "decision": e.decision}

    # ===== findings =====
    @app.post("/api/v1/findings")
    def create_finding(f: FindingIn, s: Session = Depends(db),
                       u: User = Depends(require("finding.manage"))):
        row = Finding(engagement_id=f.engagement_id, title=f.title, severity=f.severity)
        s.add(row); s.flush()
        audit(s, "finding.raised", u.username, {"finding_id": row.id})
        notify(s, f"Finding raised: {f.title}", "all")
        s.commit()
        return {"finding_id": row.id, "status": row.status,
                "sla_days": eng.SEVERITY_SLA.get(f.severity)}

    @app.post("/api/v1/findings/{fid}/advance")
    def advance_finding(fid: int, s: Session = Depends(db),
                        u: User = Depends(require("finding.manage"))):
        f = s.get(Finding, fid)
        if not f:
            raise HTTPException(404, "finding not found")
        order = eng.FINDING_STATUSES
        i = min(order.index(f.status) + 1, len(order) - 1)
        f.status = order[i]
        audit(s, "finding.advanced", u.username, {"finding_id": fid, "status": f.status})
        s.commit()
        return {"finding_id": fid, "status": f.status}

    # ===== intelligence engines =====
    @app.post("/api/v1/intel/financial")
    def intel_financial(b: IntelIn, s: Session = Depends(db),
                        u: User = Depends(require("intel.financial"))):
        out = intel.vera_financial(b.payload)
        s.add(IntelResult(vendor_id=b.vendor_id, engine="financial",
                          score=out.score, band=out.band, narrative=out.narrative))
        audit(s, "intel.financial", u.username, {"vendor_id": b.vendor_id, "band": out.band})
        s.commit()
        return out.__dict__

    @app.post("/api/v1/intel/reputation")
    def intel_reputation(b: IntelIn, s: Session = Depends(db),
                         u: User = Depends(require("intel.reputation"))):
        out = intel.mira_reputation(b.payload)
        s.add(IntelResult(vendor_id=b.vendor_id, engine="reputation",
                          score=out.score, band=out.band, narrative=out.narrative))
        audit(s, "intel.reputation", u.username, {"vendor_id": b.vendor_id, "band": out.band})
        s.commit()
        return out.__dict__

    @app.post("/api/v1/intel/contract")
    def intel_contract(b: IntelIn, s: Session = Depends(db),
                       u: User = Depends(require("intel.contract"))):
        v = s.get(Vendor, b.vendor_id)
        out = intel.matt_contract(v.tier if v else "Tier 3")
        audit(s, "intel.contract", u.username, {"vendor_id": b.vendor_id})
        s.commit()
        return out.__dict__

    @app.post("/api/v1/intel/evidence")
    def intel_evidence(b: IntelIn, s: Session = Depends(db),
                       u: User = Depends(require("intel.evidence"))):
        out = intel.isaac_evidence(b.payload.get("text", ""))
        s.add(IntelResult(vendor_id=b.vendor_id, engine="evidence",
                          score=out.score, band=out.band, narrative=out.narrative))
        audit(s, "intel.evidence", u.username, {"vendor_id": b.vendor_id, "band": out.band})
        s.commit()
        return out.__dict__

    # ===== monitoring lifecycle =====
    @app.post("/api/v1/monitoring/sweep")
    def monitoring_sweep(b: IntelIn, s: Session = Depends(db),
                         u: User = Depends(require("lifecycle.monitoring"))):
        fin = intel.vera_financial(b.payload)
        status = "OK" if (fin.score or 0) >= 55 else "ALERT" if (fin.score or 0) >= 35 else "CRITICAL"
        s.add(Monitoring(vendor_id=b.vendor_id, sweep_type="financial",
                         status=status, detail=fin.narrative))
        if status in ("ALERT", "CRITICAL"):
            # auto-raise a reassessment + notify VRM and business
            s.add(Reassessment(engagement_id=0, mode="triggered"))
            notify(s, f"Monitoring {status} for vendor {b.vendor_id}", "all")
        audit(s, "monitoring.sweep", u.username, {"vendor_id": b.vendor_id, "status": status})
        s.commit()
        return {"vendor_id": b.vendor_id, "status": status}

    @app.post("/api/v1/incidents")
    def create_incident(b: IntelIn, s: Session = Depends(db),
                        u: User = Depends(require("lifecycle.incident"))):
        row = Incident(vendor_id=b.vendor_id, title=b.payload.get("title", "Incident"),
                       severity=b.payload.get("severity", "medium"))
        s.add(row); s.flush()
        audit(s, "incident.raised", u.username, {"incident_id": row.id})
        notify(s, "Third-party incident raised", "all")
        s.commit()
        return {"incident_id": row.id, "status": row.status}

    # ===== conversational assessment (role-aware, our Q1 model) =====


    @app.post("/api/v1/assess/start")
    def assess_start(b: ChatStart, s: Session = Depends(db),
                     u: User = Depends(require("engagement.view"))):
        sess = ConversationSession(engagement_id=b.engagement_id,
                                   actor_role=b.actor_role)
        s.add(sess); s.flush()
        s.commit()
        return {"session_id": sess.id, "actor_role": sess.actor_role}

    @app.post("/api/v1/assess/turn")
    def assess_turn(b: ChatTurn, s: Session = Depends(db),
                    u: User = Depends(require("engagement.view"))):
        sess = s.get(ConversationSession, b.session_id)
        if not sess:
            raise HTTPException(404, "session not found")
        s.add(ConversationMessage(session_id=b.session_id,
                                  role=sess.actor_role, body=b.message))
        # deterministic adaptive reply: vendor claims are flagged to verify;
        # assessor input is trusted (our role/trust model)
        if sess.actor_role == "vendor":
            reply = ("Noted as a vendor assertion — this will be verified against "
                     "independent evidence before it affects the rating.")
            visibility = "shared"
        else:
            reply = "Recorded as assessor input and applied to the assessment."
            visibility = "internal"
        s.add(ConversationMessage(session_id=b.session_id, role="assistant", body=reply))
        s.commit()
        return {"session_id": b.session_id, "reply": reply, "visibility": visibility}

    # ===== autopilot (propose, human executes — two-gate) =====
    @app.post("/api/v1/engagements/{eid}/autopilot")
    def autopilot(eid: int, body: IRQIn, s: Session = Depends(db),
                  u: User = Depends(require("engagement.autopilot"))):
        e = s.get(EngagementRow, eid)
        if not e:
            raise HTTPException(404, "engagement not found")
        tier = eng.compute_tier(body.answers)
        inherent = eng.compute_inherent(body.answers)
        routing = eng.compute_route(body.answers, inherent, tier)
        # PROPOSES — does not finalise the decision; a human must record it.
        audit(s, "autopilot.proposed", u.username,
              {"engagement_id": eid, "proposed_band": inherent["band"]})
        s.commit()
        return {"engagement_id": eid, "proposed_tier": tier,
                "proposed_inherent": inherent, "proposed_routing": routing,
                "status": "PROPOSED — requires human to record decision"}

    # ===== notifications =====
    @app.get("/api/v1/notifications")
    def notifications(s: Session = Depends(db), u: User = Depends(require("notify.view"))):
        rows = s.scalars(select(Notification).order_by(Notification.id.desc())).all()
        unread = s.scalar(select(func.count()).select_from(Notification)
                          .where(Notification.is_read == False))  # noqa: E712
        return {"unread": unread,
                "items": [{"id": n.id, "event": n.event, "audience": n.audience,
                           "read": n.is_read} for n in rows[:50]]}

    # ===== methodology versioning =====

    @app.post("/api/v1/methodology/version")
    def meth_version(b: MethIn, s: Session = Depends(db),
                     u: User = Depends(require("methodology.version"))):
        s.add(MethodologyVersion(version=b.version, note=b.note))
        audit(s, "methodology.versioned", u.username, {"version": b.version})
        s.commit()
        return {"version": b.version}

    # ===== audit =====
    @app.get("/api/v1/audit")
    def audit_trail(s: Session = Depends(db), u: User = Depends(require("audit.view"))):
        rows = s.scalars(select(AuditLog).order_by(AuditLog.seq)).all()
        return [{"seq": r.seq, "action": r.action, "actor": r.actor,
                 "hash": r.entry_hash} for r in rows]

    @app.get("/api/v1/audit/verify")
    def audit_verify(s: Session = Depends(db), u: User = Depends(require("audit.view"))):
        rows = s.scalars(select(AuditLog).order_by(AuditLog.seq)).all()
        prev = "genesis"
        for r in rows:
            expect = eng.chain_hash(prev, r.action, r.actor,
                                    json.loads(r.detail) if r.detail else {})
            if r.prev_hash != prev or r.entry_hash != expect:
                return {"intact": False, "broke_at": r.seq}
            prev = r.entry_hash
        return {"intact": True, "entries": len(rows)}

    # ===== MCP-style read tools (Group G) =====
    @app.get("/api/v1/mcp/portfolio-summary")
    def portfolio_summary(s: Session = Depends(db), u: User = Depends(require("vendor.view"))):
        vendors = s.scalars(select(Vendor)).all()
        engagements = s.scalars(select(EngagementRow)).all()
        return {"vendors": len(vendors),
                "critical_vendors": sum(1 for v in vendors if v.is_critical),
                "engagements": len(engagements),
                "by_decision": _count_by(engagements, "decision")}

    @app.get("/api/v1/mcp/critical-vendors")
    def critical_vendors(s: Session = Depends(db), u: User = Depends(require("vendor.view"))):
        return [{"vendor_id": v.id, "name": v.name, "reason": v.critical_reason}
                for v in s.scalars(select(Vendor).where(Vendor.is_critical == True)).all()]  # noqa: E712

    @app.get("/api/v1/mcp/overdue-findings")
    def overdue_findings(s: Session = Depends(db), u: User = Depends(require("finding.view"))):
        rows = s.scalars(select(Finding).where(Finding.status != "closed")).all()
        return [{"finding_id": f.id, "title": f.title, "severity": f.severity,
                 "status": f.status} for f in rows]

    # ===== procurement integration (Group G) =====

    @app.post("/api/v1/procurement/po")
    def procurement_po(b: POIn, s: Session = Depends(db),
                       u: User = Depends(require("admin.integrations"))):
        # inbound PO auto-creates a vendor + sourcing engagement (straight-through)
        v = Vendor(name=b.vendor_name, ext_ref=b.ext_ref)
        s.add(v); s.flush()
        e = EngagementRow(vendor_id=v.id, title=f"PO {b.ext_ref or v.id}",
                          stage="sourcing")
        s.add(e); s.flush()
        audit(s, "procurement.po_ingested", u.username,
              {"vendor_id": v.id, "engagement_id": e.id, "amount": b.amount})
        s.commit()
        return {"vendor_id": v.id, "engagement_id": e.id, "stage": "sourcing"}

    # ===== certifications =====
    @app.post("/api/v1/certifications")
    def add_cert(b: CertIn, s: Session = Depends(db),
                 u: User = Depends(require("lifecycle.certs"))):
        from datetime import datetime as _dt
        vu = _dt.fromisoformat(b.valid_until) if b.valid_until else None
        row = Certification(vendor_id=b.vendor_id, name=b.name, valid_until=vu)
        s.add(row); s.flush()
        audit(s, "cert.added", u.username, {"cert_id": row.id, "vendor_id": b.vendor_id})
        s.commit()
        return {"cert_id": row.id, "name": row.name}

    @app.get("/api/v1/vendors/{vid}/certifications")
    def list_certs(vid: int, s: Session = Depends(db),
                   u: User = Depends(require("lifecycle.certs"))):
        rows = s.scalars(select(Certification).where(Certification.vendor_id == vid)).all()
        return [{"cert_id": c.id, "name": c.name,
                 "valid_until": c.valid_until.isoformat() if c.valid_until else None}
                for c in rows]

    # ===== documents + evidence expiry =====
    @app.post("/api/v1/documents")
    def add_document(b: DocIn, s: Session = Depends(db),
                     u: User = Depends(require("lifecycle.documents"))):
        from datetime import datetime as _dt
        nv = _dt.fromisoformat(b.next_validation) if b.next_validation else None
        row = Document(vendor_id=b.vendor_id, engagement_id=b.engagement_id,
                       name=b.name, doc_type=b.doc_type, next_validation=nv)
        s.add(row); s.flush()
        audit(s, "document.added", u.username, {"document_id": row.id})
        s.commit()
        return {"document_id": row.id, "name": row.name}

    @app.get("/api/v1/evidence/expiring")
    def expiring_evidence(s: Session = Depends(db),
                          u: User = Depends(require("lifecycle.evidence"))):
        from datetime import datetime as _dt, timedelta
        horizon = _dt.utcnow() + timedelta(days=90)
        rows = s.scalars(select(Document).where(
            Document.next_validation != None,  # noqa: E711
            Document.next_validation <= horizon)).all()
        return [{"document_id": d.id, "name": d.name,
                 "next_validation": d.next_validation.isoformat()} for d in rows]

    # ===== fourth parties + concentration =====
    @app.post("/api/v1/fourth-parties")
    def add_fourth(b: FourthIn, s: Session = Depends(db),
                   u: User = Depends(require("lifecycle.fourthparty"))):
        row = FourthParty(vendor_id=b.vendor_id, name=b.name, service=b.service)
        s.add(row); s.flush()
        # concentration: same 4th party serving many vendors
        count = s.scalar(select(func.count()).select_from(FourthParty)
                         .where(FourthParty.name == b.name))
        if count and count >= 3:
            row.concentration_flag = True
            notify(s, f"Concentration risk: {b.name} serves {count} vendors", "vrm")
        audit(s, "fourthparty.added", u.username, {"id": row.id})
        s.commit()
        return {"fourth_party_id": row.id, "concentration_flag": row.concentration_flag}

    @app.get("/api/v1/fourth-parties/concentration")
    def concentration(s: Session = Depends(db),
                      u: User = Depends(require("lifecycle.fourthparty"))):
        rows = s.scalars(select(FourthParty).where(
            FourthParty.concentration_flag == True)).all()  # noqa: E712
        return [{"id": f.id, "name": f.name, "vendor_id": f.vendor_id} for f in rows]

    # ===== acceptances =====
    @app.post("/api/v1/acceptances")
    def add_acceptance(b: AcceptIn, s: Session = Depends(db),
                       u: User = Depends(require("acceptance.manage"))):
        from datetime import datetime as _dt
        ex = _dt.fromisoformat(b.expires_at) if b.expires_at else None
        row = Acceptance(engagement_id=b.engagement_id, rationale=b.rationale,
                         accepted_by=u.username, expires_at=ex)
        s.add(row); s.flush()
        audit(s, "acceptance.recorded", u.username, {"id": row.id})
        s.commit()
        return {"acceptance_id": row.id, "accepted_by": u.username}

    # ===== contracts (Matt) =====
    @app.post("/api/v1/engagements/{eid}/contract")
    def gen_contract(eid: int, s: Session = Depends(db),
                     u: User = Depends(require("intel.contract"))):
        e = s.get(EngagementRow, eid)
        if not e:
            raise HTTPException(404, "engagement not found")
        v = s.get(Vendor, e.vendor_id)
        out = intel.matt_contract(v.tier if v else "Tier 3")
        row = Contract(engagement_id=eid, tier=v.tier if v else "Tier 3",
                       terms_json=json.dumps(list(out.signals)))
        s.add(row); s.flush()
        if e.stage == "decision":
            e.stage = "contract"
        audit(s, "contract.generated", u.username, {"engagement_id": eid})
        s.commit()
        return {"contract_id": row.id, "tier": row.tier, "terms": out.signals}

    # ===== reassessments =====
    @app.post("/api/v1/reassessments")
    def schedule_reassessment(b: ReassessIn, s: Session = Depends(db),
                              u: User = Depends(require("lifecycle.reassess"))):
        row = Reassessment(engagement_id=b.engagement_id, mode=b.mode)
        s.add(row); s.flush()
        audit(s, "reassessment.scheduled", u.username, {"id": row.id, "mode": b.mode})
        notify(s, f"Reassessment scheduled ({b.mode})", "all")
        s.commit()
        return {"reassessment_id": row.id, "mode": b.mode}

    @app.post("/api/v1/reassessments/{rid}/complete")
    def complete_reassessment(rid: int, s: Session = Depends(db),
                              u: User = Depends(require("lifecycle.reassess"))):
        r = s.get(Reassessment, rid)
        if not r:
            raise HTTPException(404, "reassessment not found")
        r.completed = True
        audit(s, "reassessment.completed", u.username, {"id": rid})
        s.commit()
        return {"reassessment_id": rid, "completed": True}

    # ===== corrective action plans (CAP) — modelled as findings =====
    @app.get("/api/v1/cap")
    def cap_board(s: Session = Depends(db),
                  u: User = Depends(require("lifecycle.cap"))):
        rows = s.scalars(select(Finding).where(Finding.status != "closed")).all()
        return {"open_actions": len(rows),
                "by_severity": _count_by(rows, "severity"),
                "items": [{"finding_id": f.id, "title": f.title,
                           "severity": f.severity, "status": f.status} for f in rows]}

    # ===== business impact analysis (BIA) =====
    @app.get("/api/v1/vendors/{vid}/bia")
    def bia(vid: int, s: Session = Depends(db),
            u: User = Depends(require("lifecycle.bia"))):
        v = s.get(Vendor, vid)
        if not v:
            raise HTTPException(404, "vendor not found")
        engagements = s.scalars(select(EngagementRow).where(
            EngagementRow.vendor_id == vid)).all()
        return {"vendor_id": vid, "is_critical": v.is_critical,
                "engagement_count": len(engagements),
                "impact": "HIGH" if v.is_critical else
                          "MEDIUM" if len(engagements) > 1 else "LOW"}

    # ===== dashboards =====
    @app.get("/api/v1/dashboard/executive")
    def dash_exec(s: Session = Depends(db),
                  u: User = Depends(require("dashboard.exec"))):
        vendors = s.scalars(select(VendorRecord)).all()
        engs = s.scalars(select(EngagementRecord)).all()
        findings = s.scalars(select(FindingRecord)).all()
        # include any legacy v1 rows so both creation paths are reflected
        v1v = s.scalar(select(func.count()).select_from(Vendor)) or 0
        v1e = s.scalar(select(func.count()).select_from(EngagementRow)) or 0
        v1f = s.scalar(select(func.count()).select_from(Finding)
                       .where(Finding.status != "closed")) or 0
        return {
            "vendors": len(vendors) + v1v,
            "critical_vendors": sum(1 for v in vendors if v.is_critical),
            "engagements": len(engs) + v1e,
            "by_residual": _count_by(engs, "residual_band"),
            "by_decision": _count_by(engs, "status"),
            "open_findings": sum(1 for f in findings if (f.status or "").lower() not in ("closed",)) + v1f,
        }

    @app.get("/api/v1/dashboard/operational")
    def dash_ops(s: Session = Depends(db),
                 u: User = Depends(require("dashboard.ops"))):
        engs = s.scalars(select(EngagementRecord)).all()
        return {"by_stage": _count_by(engs, "status"),
                "by_route": _count_by(engs, "inherent_band"),
                "in_flight": sum(1 for e in engs if (e.status or "") not in ("Terminated", "Exited"))}

    @app.get("/api/v1/dashboard/risk")
    def dash_risk(s: Session = Depends(db),
                  u: User = Depends(require("dashboard.risk"))):
        engs = s.scalars(select(EngagementRow)).all()
        monit = s.scalars(select(Monitoring)).all()
        return {"by_inherent": _count_by(engs, "inherent_band"),
                "by_residual": _count_by(engs, "residual_band"),
                "monitoring_alerts": sum(1 for m in monit if m.status in ("ALERT", "CRITICAL"))}

    # ===== document upload + extraction (feeds Isaac) =====
    @app.post("/api/v1/documents/upload")
    async def upload_document(
        file: UploadFile = File(...),
        vendor_id: Optional[int] = Form(default=None),
        engagement_id: Optional[int] = Form(default=None),
        s: Session = Depends(db),
        u: User = Depends(require("lifecycle.documents")),
    ):
        from .features import uploads
        data = await file.read()
        if len(data) > 25 * 1024 * 1024:
            raise HTTPException(413, "file exceeds 25 MB limit")
        try:
            res = uploads.process_upload(
                data=data, filename=file.filename or "upload",
                content_type=file.content_type or "application/octet-stream",
                org_id="org", engagement_id=str(engagement_id or ""),
                vendor_id=vendor_id,
            )
        except ValueError as e:
            raise HTTPException(415, str(e))

        from datetime import datetime as _dt
        nv = _dt.fromisoformat(res.next_validation) if res.next_validation else None
        doc = Document(vendor_id=vendor_id, engagement_id=engagement_id,
                       name=file.filename or "upload", doc_type=res.doc_type,
                       object_uri=res.object_key, next_validation=nv)
        s.add(doc); s.flush()

        if res.isaac and vendor_id:
            s.add(IntelResult(vendor_id=vendor_id, engine="evidence",
                              score=res.isaac["score"], band=res.isaac["band"],
                              narrative=res.isaac["narrative"]))

        audit(s, "document.uploaded", u.username,
              {"document_id": doc.id, "doc_type": res.doc_type,
               "classified_confidence": res.classification_confidence,
               "isaac_band": res.isaac["band"] if res.isaac else None,
               "evidence_count": res.evidence_count})
        if res.needs_human:
            notify(s, f"Document '{file.filename}' needs human classification review", "all")
        s.commit()

        return {
            "document_id": doc.id,
            "object_key": res.object_key,
            "doc_type": res.doc_type,
            "classification_confidence": res.classification_confidence,
            "needs_human_review": res.needs_human,
            "page_count": res.page_count,
            "scanned_pdf": res.scanned,
            "extracted_chars": res.extracted_chars,
            "isaac": res.isaac,
            "evidence_count": res.evidence_count,
            "next_validation": res.next_validation,
        }

    # ============================================================
    #  CRUD / edit, list+search, admin, VRM, auth, reporting, email
    # ============================================================
    from fastapi.responses import PlainTextResponse
    import csv as _csv, io as _io
    from datetime import datetime as _dt2

    # ---- Vendor: update, delete, list+search, detail ----
    @app.patch("/api/v1/vendors/{vid}")
    def update_vendor(vid: int, b: VendorUpdateIn, s: Session = Depends(db),
                      u: User = Depends(require("vendor.edit"))):
        v = s.get(Vendor, vid)
        if not v:
            raise HTTPException(404, "vendor not found")
        for f, val in b.model_dump(exclude_none=True).items():
            setattr(v, f, val)
        audit(s, "vendor.updated", u.username, {"vendor_id": vid, "fields": list(b.model_dump(exclude_none=True))})
        s.commit()
        return {"vendor_id": vid, "updated": True}

    @app.delete("/api/v1/vendors/{vid}")
    def delete_vendor(vid: int, s: Session = Depends(db),
                      u: User = Depends(require("vendor.edit"))):
        v = s.get(Vendor, vid)
        if not v:
            raise HTTPException(404, "vendor not found")
        # archive semantics: mark, don't hard-delete (preserves audit/history)
        v.ext_ref = (v.ext_ref or "") + "|archived"
        audit(s, "vendor.archived", u.username, {"vendor_id": vid})
        s.commit()
        return {"vendor_id": vid, "archived": True}

    @app.get("/api/v1/vendors/{vid}")
    def get_vendor(vid: int, s: Session = Depends(db),
                   u: User = Depends(require("vendor.view"))):
        v = s.get(Vendor, vid)
        if not v:
            raise HTTPException(404, "vendor not found")
        engs = s.scalars(select(EngagementRow).where(EngagementRow.vendor_id == vid)).all()
        return {"vendor_id": v.id, "name": v.name, "industry": v.industry,
                "country": v.country, "contact_email": v.contact_email,
                "tier": v.tier, "is_critical": v.is_critical,
                "critical_reason": v.critical_reason, "critical_by": v.critical_by,
                "engagements": [{"engagement_id": e.id, "title": e.title, "stage": e.stage} for e in engs]}

    # ---- Vendor: list with search/filter (replaces the plain list inline) ----
    @app.get("/api/v1/vendors-search")
    def search_vendors(q: Optional[str] = None, tier: Optional[str] = None,
                       critical: Optional[bool] = None,
                       s: Session = Depends(db), u: User = Depends(require("vendor.view"))):
        stmt = select(Vendor)
        rows = s.scalars(stmt).all()
        out = []
        for v in rows:
            if "|archived" in (v.ext_ref or ""):
                continue
            if q and q.lower() not in v.name.lower():
                continue
            if tier and v.tier != tier:
                continue
            if critical is not None and v.is_critical != critical:
                continue
            out.append({"vendor_id": v.id, "name": v.name, "tier": v.tier,
                        "is_critical": v.is_critical})
        return out

    # ---- Vendor: remove critical designation (VRM) ----
    @app.delete("/api/v1/vendors/{vid}/critical")
    def remove_critical(vid: int, s: Session = Depends(db),
                        u: User = Depends(require("vendor.critical"))):
        v = s.get(Vendor, vid)
        if not v:
            raise HTTPException(404, "vendor not found")
        v.is_critical = False; v.critical_reason = None; v.critical_by = None
        audit(s, "vendor.critical_removed", u.username, {"vendor_id": vid})
        s.commit()
        return {"vendor_id": vid, "is_critical": False}

    # ---- Engagement: update, list-all, delete ----
    @app.patch("/api/v1/engagements/{eid}")
    def update_engagement(eid: int, b: EngagementUpdateIn, s: Session = Depends(db),
                          u: User = Depends(require("engagement.edit"))):
        e = s.get(EngagementRow, eid)
        if not e:
            raise HTTPException(404, "engagement not found")
        for f, val in b.model_dump(exclude_none=True).items():
            setattr(e, f, val)
        audit(s, "engagement.updated", u.username, {"engagement_id": eid})
        s.commit()
        return {"engagement_id": eid, "updated": True}

    @app.get("/api/v1/engagements")
    def list_engagements(stage: Optional[str] = None, vendor_id: Optional[int] = None,
                         s: Session = Depends(db), u: User = Depends(require("engagement.view"))):
        rows = s.scalars(select(EngagementRow)).all()
        out = []
        for e in rows:
            if stage and e.stage != stage:
                continue
            if vendor_id and e.vendor_id != vendor_id:
                continue
            out.append({"engagement_id": e.id, "vendor_id": e.vendor_id, "title": e.title,
                        "stage": e.stage, "route": e.route, "inherent_band": e.inherent_band,
                        "residual_band": e.residual_band, "decision": e.decision})
        return out

    @app.delete("/api/v1/engagements/{eid}")
    def delete_engagement(eid: int, s: Session = Depends(db),
                          u: User = Depends(require("engagement.edit"))):
        e = s.get(EngagementRow, eid)
        if not e:
            raise HTTPException(404, "engagement not found")
        e.status = "cancelled"
        audit(s, "engagement.cancelled", u.username, {"engagement_id": eid})
        s.commit()
        return {"engagement_id": eid, "cancelled": True}

    # ---- Finding: update, reopen ----
    @app.patch("/api/v1/findings/{fid}")
    def update_finding(fid: int, b: FindingUpdateIn, s: Session = Depends(db),
                       u: User = Depends(require("finding.manage"))):
        f = s.get(Finding, fid)
        if not f:
            raise HTTPException(404, "finding not found")
        for fld, val in b.model_dump(exclude_none=True).items():
            setattr(f, fld, val)
        audit(s, "finding.updated", u.username, {"finding_id": fid})
        s.commit()
        return {"finding_id": fid, "updated": True}

    @app.post("/api/v1/findings/{fid}/reopen")
    def reopen_finding(fid: int, s: Session = Depends(db),
                       u: User = Depends(require("finding.manage"))):
        f = s.get(Finding, fid)
        if not f:
            raise HTTPException(404, "finding not found")
        f.status = "open"
        audit(s, "finding.reopened", u.username, {"finding_id": fid})
        s.commit()
        return {"finding_id": fid, "status": "open"}

    # ---- VRM: sign-off + review queue ----
    @app.post("/api/v1/engagements/{eid}/signoff")
    def signoff(eid: int, b: SignoffIn, s: Session = Depends(db),
                u: User = Depends(require("engagement.review"))):
        e = s.get(EngagementRow, eid)
        if not e:
            raise HTTPException(404, "engagement not found")
        e.status = "signed_off" if b.decision == "approved" else "returned"
        audit(s, "engagement.signoff", u.username,
              {"engagement_id": eid, "decision": b.decision, "note": b.note})
        notify(s, f"Engagement #{eid} {b.decision} by VRM", "business")
        s.commit()
        return {"engagement_id": eid, "status": e.status}

    @app.get("/api/v1/review-queue")
    def review_queue(s: Session = Depends(db), u: User = Depends(require("engagement.review"))):
        rows = s.scalars(select(EngagementRow).where(
            EngagementRow.stage == "decision",
            EngagementRow.residual_band.in_(["HIGH", "ELEVATED"]))).all()
        return [{"engagement_id": e.id, "vendor_id": e.vendor_id, "title": e.title,
                 "residual_band": e.residual_band, "decision": e.decision} for e in rows]

    # ---- Auth self-service: change password, profile ----
    @app.post("/api/v1/me/password")
    def change_password(b: PasswordIn, s: Session = Depends(db), u: User = Depends(actor)):
        from .features.models_db import hash_password
        if not verify_password(b.current_password, u.password_hash):
            raise HTTPException(403, "current password incorrect")
        if len(b.new_password) < 6:
            raise HTTPException(400, "new password too short")
        u.password_hash = hash_password(b.new_password)
        audit(s, "user.password_changed", u.username, {"username": u.username})
        s.commit()
        return {"changed": True}

    @app.get("/api/v1/me")
    def my_profile(u: User = Depends(actor)):
        return {"username": u.username, "full_name": u.full_name,
                "email": u.email, "role": u.role.key}

    @app.patch("/api/v1/me")
    def update_profile(b: ProfileIn, s: Session = Depends(db), u: User = Depends(actor)):
        for f, val in b.model_dump(exclude_none=True).items():
            setattr(u, f, val)
        audit(s, "user.profile_updated", u.username, {"username": u.username})
        s.commit()
        return {"updated": True}

    # ---- Admin: users ----
    @app.get("/api/v1/admin/users")
    def list_users(s: Session = Depends(db), u: User = Depends(require("admin.users"))):
        return [{"id": x.id, "username": x.username, "full_name": x.full_name,
                 "email": x.email, "role": x.role.key, "is_active": x.is_active}
                for x in s.scalars(select(User)).all()]

    @app.post("/api/v1/admin/users")
    def create_user(b: UserIn, s: Session = Depends(db), u: User = Depends(require("admin.users"))):
        from .features.models_db import hash_password
        if s.scalars(select(User).where(User.username == b.username)).first():
            raise HTTPException(409, "username exists")
        role = s.scalars(select(Role).where(Role.key == b.role_key)).first()
        if not role:
            raise HTTPException(400, "unknown role")
        row = User(username=b.username, full_name=b.full_name, email=b.email,
                   password_hash=hash_password(b.password), role_id=role.id)
        s.add(row); s.flush()
        audit(s, "user.created", u.username, {"username": b.username, "role": b.role_key})
        s.commit()
        return {"id": row.id, "username": row.username}

    @app.patch("/api/v1/admin/users/{uid}")
    def update_user(uid: int, b: UserUpdateIn, s: Session = Depends(db),
                    u: User = Depends(require("admin.users"))):
        target = s.get(User, uid)
        if not target:
            raise HTTPException(404, "user not found")
        data = b.model_dump(exclude_none=True)
        if "role_key" in data:
            role = s.scalars(select(Role).where(Role.key == data.pop("role_key"))).first()
            if not role:
                raise HTTPException(400, "unknown role")
            target.role_id = role.id
        for f, val in data.items():
            setattr(target, f, val)
        audit(s, "user.updated", u.username, {"user_id": uid})
        s.commit()
        return {"user_id": uid, "updated": True}

    @app.delete("/api/v1/admin/users/{uid}")
    def deactivate_user(uid: int, s: Session = Depends(db), u: User = Depends(require("admin.users"))):
        target = s.get(User, uid)
        if not target:
            raise HTTPException(404, "user not found")
        if target.username == "admin":
            raise HTTPException(400, "cannot deactivate the seed admin")
        target.is_active = False
        audit(s, "user.deactivated", u.username, {"user_id": uid})
        s.commit()
        return {"user_id": uid, "is_active": False}

    # ---- Admin: roles & permissions ----
    @app.get("/api/v1/admin/roles")
    def list_roles(s: Session = Depends(db), u: User = Depends(require("admin.roles"))):
        return [{"key": r.key, "label": r.label, "is_system": r.is_system,
                 "permissions": [p.key for p in r.permissions]}
                for r in s.scalars(select(Role)).all()]

    @app.get("/api/v1/admin/permissions")
    def list_permissions(s: Session = Depends(db), u: User = Depends(require("admin.roles"))):
        from .features.models_db import Permission
        return [{"key": p.key, "label": p.label, "category": p.category}
                for p in s.scalars(select(Permission)).all()]

    @app.put("/api/v1/admin/roles/{rkey}/permissions")
    def set_role_perms(rkey: str, b: RolePermsIn, s: Session = Depends(db),
                       u: User = Depends(require("admin.roles"))):
        from .features.models_db import Permission
        role = s.scalars(select(Role).where(Role.key == rkey)).first()
        if not role:
            raise HTTPException(404, "role not found")
        perms = s.scalars(select(Permission).where(Permission.key.in_(b.permission_keys))).all()
        role.permissions = list(perms)
        audit(s, "role.permissions_set", u.username, {"role": rkey, "count": len(perms)})
        s.commit()
        return {"role": rkey, "permissions": [p.key for p in perms]}

    # ---- Admin: webhooks ----
    @app.get("/api/v1/admin/webhooks")
    def list_webhooks(s: Session = Depends(db), u: User = Depends(require("admin.webhooks"))):
        return [{"id": w.id, "url": w.url, "event": w.event, "active": w.active}
                for w in s.scalars(select(Webhook)).all()]

    @app.post("/api/v1/admin/webhooks")
    def add_webhook(b: WebhookIn, s: Session = Depends(db), u: User = Depends(require("admin.webhooks"))):
        row = Webhook(url=b.url, event=b.event); s.add(row); s.flush()
        audit(s, "webhook.added", u.username, {"id": row.id, "url": b.url})
        s.commit()
        return {"webhook_id": row.id}

    @app.delete("/api/v1/admin/webhooks/{wid}")
    def del_webhook(wid: int, s: Session = Depends(db), u: User = Depends(require("admin.webhooks"))):
        w = s.get(Webhook, wid)
        if not w:
            raise HTTPException(404, "webhook not found")
        s.delete(w); audit(s, "webhook.deleted", u.username, {"id": wid}); s.commit()
        return {"deleted": True}

    # ---- Notifications: mark read ----
    @app.post("/api/v1/notifications/{nid}/read")
    def mark_read(nid: int, s: Session = Depends(db), u: User = Depends(require("notify.view"))):
        n = s.get(Notification, nid)
        if not n:
            raise HTTPException(404, "notification not found")
        n.is_read = True; s.commit()
        return {"id": nid, "read": True}

    @app.post("/api/v1/notifications/read-all")
    def mark_all_read(s: Session = Depends(db), u: User = Depends(require("notify.view"))):
        rows = s.scalars(select(Notification).where(Notification.is_read == False)).all()  # noqa: E712
        for n in rows:
            n.is_read = True
        s.commit()
        return {"marked": len(rows)}

    # ---- Email: send (real SMTP or simulation outbox) ----
    @app.post("/api/v1/email/send")
    def email_send(b: EmailIn, s: Session = Depends(db), u: User = Depends(require("admin.email"))):
        from .features import email_service
        sent = False
        try:
            sent = email_service.send_email(b.to_addr, b.subject, b.body)
        except Exception as e:  # SMTP failure -> fall back to outbox
            audit(s, "email.send_failed", u.username, {"to": b.to_addr, "error": str(e)[:120]})
        s.add(EmailOutbox(to_addr=b.to_addr, subject=b.subject, body=b.body, sent=sent))
        audit(s, "email.queued" if not sent else "email.sent", u.username, {"to": b.to_addr})
        s.commit()
        return {"to": b.to_addr, "sent": sent, "mode": "smtp" if sent else "simulation"}

    @app.get("/api/v1/email/outbox")
    def email_outbox(s: Session = Depends(db), u: User = Depends(require("admin.email"))):
        return [{"id": e.id, "to": e.to_addr, "subject": e.subject, "sent": e.sent}
                for e in s.scalars(select(EmailOutbox).order_by(EmailOutbox.id.desc())).all()]

    # ---- Evidence renewal chase (uses email path) ----
    @app.post("/api/v1/evidence/{doc_id}/chase")
    def chase_evidence(doc_id: int, s: Session = Depends(db), u: User = Depends(require("lifecycle.evidence"))):
        d = s.get(Document, doc_id)
        if not d:
            raise HTTPException(404, "document not found")
        v = s.get(Vendor, d.vendor_id) if d.vendor_id else None
        to = (v.contact_email if v and v.contact_email else "vendor@example.com")
        from .features import email_service
        sent = False
        try:
            sent = email_service.send_email(to, f"Evidence renewal required: {d.name}",
                                            "Please submit an updated version of this document.")
        except Exception:
            pass
        s.add(EmailOutbox(to_addr=to, subject=f"Renewal: {d.name}", body="renewal chase", sent=sent))
        audit(s, "evidence.chased", u.username, {"document_id": doc_id, "to": to})
        notify(s, f"Renewal chased for '{d.name}'", "business")
        s.commit()
        return {"document_id": doc_id, "chased": True, "mode": "smtp" if sent else "simulation"}

    # ---- Contract gap review ----
    @app.post("/api/v1/contracts/{cid}/gap-review")
    def contract_gap_review(cid: int, s: Session = Depends(db), u: User = Depends(require("intel.contract"))):
        c = s.get(Contract, cid)
        if not c:
            raise HTTPException(404, "contract not found")
        required = json.loads(c.terms_json) if c.terms_json else []
        # deterministic gap review: in absence of a drafted contract, flag all
        # required terms as 'to confirm'; production diffs against uploaded draft.
        gaps = [t for t in required]
        c.gap_review = json.dumps({"missing_or_unconfirmed": gaps, "count": len(gaps)})
        audit(s, "contract.gap_review", u.username, {"contract_id": cid, "gaps": len(gaps)})
        s.commit()
        return {"contract_id": cid, "gap_count": len(gaps), "gaps": gaps}

    # ---- Reassessment: cadence sweep + delta ----
    @app.post("/api/v1/reassessments/run-due")
    def run_due_reassessments(s: Session = Depends(db), u: User = Depends(require("lifecycle.reassess"))):
        # Tier cadence: Tier1 annual, Tier2 biennial, Tier3 triennial.
        cadence = {"Tier 1": 365, "Tier 2": 730, "Tier 3": 1095}
        created = 0
        for e in s.scalars(select(EngagementRow).where(EngagementRow.stage == "monitor")).all():
            v = s.get(Vendor, e.vendor_id)
            days = cadence.get(v.tier if v else "Tier 3", 1095)
            age = (_dt2.utcnow() - e.created_at).days if e.created_at else 0
            if age >= days:
                s.add(Reassessment(engagement_id=e.id, mode="periodic")); created += 1
        audit(s, "reassessment.cadence_run", u.username, {"created": created})
        s.commit()
        return {"created": created}

    # ---- Reporting: register CSV export, audit export ----
    @app.get("/api/v1/reports/register.csv", response_class=PlainTextResponse)
    def register_csv(s: Session = Depends(db), u: User = Depends(require("reg.report"))):
        buf = _io.StringIO(); w = _csv.writer(buf)
        w.writerow(["vendor_id", "name", "tier", "critical", "engagement_id",
                    "title", "stage", "inherent", "residual", "decision"])
        for v in s.scalars(select(Vendor)).all():
            engs = s.scalars(select(EngagementRow).where(EngagementRow.vendor_id == v.id)).all()
            if not engs:
                w.writerow([v.id, v.name, v.tier, v.is_critical, "", "", "", "", "", ""])
            for e in engs:
                w.writerow([v.id, v.name, v.tier, v.is_critical, e.id, e.title,
                            e.stage, e.inherent_band, e.residual_band, e.decision])
        return buf.getvalue()

    @app.get("/api/v1/audit/export.csv", response_class=PlainTextResponse)
    def audit_export(s: Session = Depends(db), u: User = Depends(require("audit.export"))):
        buf = _io.StringIO(); w = _csv.writer(buf)
        w.writerow(["seq", "action", "actor", "timestamp", "hash"])
        for r in s.scalars(select(AuditLog).order_by(AuditLog.seq)).all():
            w.writerow([r.seq, r.action, r.actor,
                        r.created_at.isoformat() if r.created_at else "", r.entry_hash])
        return buf.getvalue()

    # ---- Vendor portal (self-service, scoped) ----
    @app.get("/api/v1/portal/my-status")
    def portal_status(s: Session = Depends(db), u: User = Depends(require("portal.self"))):
        # vendors see a minimal, scoped view (no internal reasoning)
        return {"message": "Vendor portal active",
                "you": u.username,
                "note": "Complete your DDQ and submit evidence via your assigned engagement."}

    # ============================================================
    #  Conversational multi-agent assessment (chat surface)
    # ============================================================
    from .features import agents as _A
    from .features import agent_engine as _AE
    from .features.models_feature import AgentLearning, BackgroundInsight

    @app.get("/api/v1/ai/status")
    def ai_status(u: User = Depends(require("admin.integrations"))):
        from .agents import llm_config
        return llm_config.status()

    @app.get("/api/v1/agent/registry")
    def agent_registry(u: User = Depends(require("engagement.view"))):
        return {"agents": _A.AGENTS,
                "stages": [{"id": s.id, "name": s.name, "short": s.short} for s in _A.STAGES],
                "methodology": _A.METHODOLOGY}

    @app.post("/api/v1/agent/sessions")
    def open_session(b: ChatSessionIn, s: Session = Depends(db),
                     u: User = Depends(require("engagement.view"))):
        sess = ConversationSession(engagement_id=b.engagement_id, actor_role="assessor",
                                   stage=0, active_agent="bro", dossier_json="{}")
        s.add(sess); s.flush()
        opener = ("Bro here — your Risk Oracle. Exposure first. Controls second. Verdict last. "
                  "Drop everything you have on this engagement, or tell me about the supplier and "
                  "we start at intake.")
        s.add(ConversationMessage(session_id=sess.id, role="agent", agent="bro",
                                  stage=0, body=opener))
        audit(s, "agent.session_opened", u.username, {"session_id": sess.id})
        s.commit()
        return {"session_id": sess.id, "stage": 0, "active_agent": "bro"}

    @app.get("/api/v1/agent/sessions/{sid}")
    def get_session(sid: int, s: Session = Depends(db),
                    u: User = Depends(require("engagement.view"))):
        sess = s.get(ConversationSession, sid)
        if not sess:
            raise HTTPException(404, "session not found")
        msgs = s.scalars(select(ConversationMessage)
                         .where(ConversationMessage.session_id == sid)
                         .order_by(ConversationMessage.id)).all()
        insights = s.scalars(select(BackgroundInsight)
                             .where(BackgroundInsight.session_id == sid)
                             .order_by(BackgroundInsight.id.desc())).all()
        learnings = s.scalars(select(AgentLearning).order_by(AgentLearning.id.desc())).all()
        return {
            "session_id": sess.id, "stage": sess.stage, "active_agent": sess.active_agent,
            "dossier": json.loads(sess.dossier_json or "{}"),
            "messages": [{"id": m.id, "role": m.role, "agent": m.agent,
                          "stage": m.stage, "body": m.body} for m in msgs],
            "insights": [{"kind": i.kind, "severity": i.severity, "detail": i.detail} for i in insights],
            "learnings": [{"id": l.id, "text": l.text, "stage": l.stage} for l in learnings],
        }

    @app.post("/api/v1/agent/send")
    def agent_send(b: ChatSendIn, s: Session = Depends(db),
                   u: User = Depends(require("engagement.view"))):
        sess = s.get(ConversationSession, b.session_id)
        if not sess:
            raise HTTPException(404, "session not found")
        dossier = json.loads(sess.dossier_json or "{}")
        learn_texts = [l.text for l in s.scalars(select(AgentLearning)).all()]

        # record the user message
        s.add(ConversationMessage(session_id=sess.id, role="user", stage=sess.stage,
                                  body=b.message))

        # background consistency check (Sara, silent) — persist insights
        for ins in _AE.consistency_check(dossier, b.message, learn_texts):
            detail = ins.get("issue") or ins.get("concern") or ""
            if ins.get("with"):
                detail += f" (↳ {ins['with']})"
            if ins.get("claim"):
                detail += f" (↳ \"{ins['claim']}\")"
            s.add(BackgroundInsight(session_id=sess.id, kind=ins["kind"],
                                    severity=ins.get("severity", "medium"), detail=detail))

        # choose agent: explicit mention > stage owner
        target = b.agent if (b.agent in _A.AGENTS) else _A.route_next_agent(sess.stage)

        # run the agent turn (deterministic-local or live)
        turn = _AE.run_turn(target, sess.stage, dossier, learn_texts, b.message)
        produced = []

        # follow up to two handoffs to keep it bounded
        hops = 0
        while turn.handoff and hops < 2:
            s.add(ConversationMessage(session_id=sess.id, role="agent",
                                      agent=turn.agent_id, stage=sess.stage, body=turn.body))
            produced.append({"agent": turn.agent_id, "body": turn.body})
            target = turn.handoff
            turn = _AE.run_turn(target, sess.stage, dossier, learn_texts, b.message)
            hops += 1

        s.add(ConversationMessage(session_id=sess.id, role="agent",
                                  agent=turn.agent_id, stage=sess.stage, body=turn.body))
        produced.append({"agent": turn.agent_id, "body": turn.body})
        sess.active_agent = turn.agent_id

        advanced = False
        if turn.stage_complete and sess.stage < len(_A.STAGES) - 1:
            sess.stage += 1
            sess.active_agent = _A.route_next_agent(sess.stage)
            advanced = True
            s.add(ConversationMessage(session_id=sess.id, role="system", agent="bro",
                                      stage=sess.stage,
                                      body=f"Stage advanced — {turn.stage_complete} Now at Stage "
                                           f"{sess.stage}: {_A.STAGES[sess.stage].name}."))

        audit(s, "agent.turn", u.username,
              {"session_id": sess.id, "agent": turn.agent_id, "advanced": advanced})
        s.commit()
        return {"session_id": sess.id, "stage": sess.stage,
                "active_agent": sess.active_agent, "advanced": advanced,
                "produced": produced, "stage_complete": turn.stage_complete}

    @app.post("/api/v1/agent/learnings")
    def add_learning(b: LearningIn, s: Session = Depends(db),
                     u: User = Depends(require("engagement.view"))):
        text = _A.synthesize_learning(b.rating, b.agent, b.issue or "", b.note or "", b.stage)
        row = AgentLearning(rating=b.rating, agent=b.agent, stage=b.stage,
                            issue=b.issue, note=b.note, text=text)
        s.add(row); s.flush()
        audit(s, "agent.learning_captured", u.username, {"learning_id": row.id})
        s.commit()
        return {"learning_id": row.id, "text": text}

    @app.get("/api/v1/agent/learnings")
    def list_learnings(s: Session = Depends(db), u: User = Depends(require("engagement.view"))):
        return [{"id": l.id, "text": l.text, "rating": l.rating, "stage": l.stage}
                for l in s.scalars(select(AgentLearning).order_by(AgentLearning.id.desc())).all()]

    @app.delete("/api/v1/agent/learnings/{lid}")
    def delete_learning(lid: int, s: Session = Depends(db),
                        u: User = Depends(require("engagement.view"))):
        row = s.get(AgentLearning, lid)
        if row:
            s.delete(row); s.commit()
        return {"deleted": True}

    # ============================================================
    #  Registry v2 — exhaustive vendor/engagement model + masters
    # ============================================================
    from .features import registry_service as RS
    from .features import financial as FIN
    from .features.registry_models import (
        IndustryMaster, MaterialGroupMaster, VendorGroup, VendorRecord,
        VendorIndustry, ContactRecord, EngagementRecord, AssessmentRecord,
        FindingRecord, RemediationRecord, FourthPartyRecord, FourthPartyVendor,
        ArtefactRecord, IssueRecord,
    )

    # ---- master lists ----
    @app.get("/api/v2/industries")
    def list_industries(s: Session = Depends(db), u: User = Depends(require("vendor.view"))):
        return [{"industry_id": i.industry_id, "sic_code": i.sic_code, "division": i.division}
                for i in s.scalars(select(IndustryMaster).order_by(IndustryMaster.sic_code)).all()]

    @app.get("/api/v2/material-groups")
    def list_material_groups(s: Session = Depends(db), u: User = Depends(require("engagement.view"))):
        return [{"material_group_id": m.material_group_id, "unspsc_code": m.unspsc_code}
                for m in s.scalars(select(MaterialGroupMaster).order_by(MaterialGroupMaster.unspsc_code)).all()]

    # ---- vendors (exhaustive) ----
    @app.post("/api/v2/vendors")
    def v2_create_vendor(b: V2VendorIn, s: Session = Depends(db),
                         u: User = Depends(require("vendor.edit"))):
        v = RS.create_vendor(s, legal_name=b.legal_name, created_via=b.created_via or "button",
                             group_id=b.group_id, parent=b.parent_company,
                             industries=b.industries or [], tier=b.tier or "Tier 3",
                             trading_name=b.trading_name, registration_number=b.registration_number,
                             hq_country=b.hq_country, website=b.website,
                             listing_status=b.listing_status, procurement_ref=b.procurement_ref)
        audit(s, "v2.vendor_created", u.username,
              {"vendor_id": v.vendor_id, "group_id": v.group_id, "via": v.created_via})
        s.commit()
        return {"vendor_id": v.vendor_id, "group_id": v.group_id}

    @app.get("/api/v2/vendors")
    def v2_list_vendors(group_id: Optional[str] = None, s: Session = Depends(db),
                        u: User = Depends(require("vendor.view"))):
        stmt = select(VendorRecord)
        if group_id:
            stmt = stmt.where(VendorRecord.group_id == group_id)
        out = []
        for v in s.scalars(stmt).all():
            inds = [vi.industry_id for vi in s.scalars(select(VendorIndustry).where(
                VendorIndustry.vendor_id == v.vendor_id)).all()]
            out.append({"vendor_id": v.vendor_id, "group_id": v.group_id,
                        "legal_name": v.legal_name, "tier": v.tier, "status": v.status,
                        "is_critical": v.is_critical, "industries": inds,
                        "created_via": v.created_via})
        return out

    @app.get("/api/v2/vendors/{vid}")
    def v2_get_vendor(vid: str, s: Session = Depends(db), u: User = Depends(require("vendor.view"))):
        v = s.scalars(select(VendorRecord).where(VendorRecord.vendor_id == vid)).first()
        if not v:
            raise HTTPException(404, "vendor not found")
        inds = [vi.industry_id for vi in s.scalars(select(VendorIndustry).where(
            VendorIndustry.vendor_id == vid)).all()]
        contacts = [{"id": c.id, "is_primary": c.is_primary, "name": c.name, "email": c.email,
                     "phone": f"{c.phone_country_code or ''} {c.phone_number or ''}".strip(),
                     "designation": c.designation, "country": c.country,
                     "mailing_address": c.mailing_address}
                    for c in s.scalars(select(ContactRecord).where(
                        ContactRecord.owner_type == "vendor", ContactRecord.owner_id == vid)).all()]
        engs = [{"engagement_id": e.engagement_id, "title": e.title, "status": e.status}
                for e in s.scalars(select(EngagementRecord).where(
                    EngagementRecord.vendor_id == vid)).all()]
        return {"vendor_id": v.vendor_id, "group_id": v.group_id, "legal_name": v.legal_name,
                "trading_name": v.trading_name, "tier": v.tier, "status": v.status,
                "hq_country": v.hq_country, "website": v.website,
                "listing_status": v.listing_status, "is_critical": v.is_critical,
                "industries": inds, "contacts": contacts, "engagements": engs,
                "fourth_party_id": v.fourth_party_id}

    @app.post("/api/v2/vendors/{vid}/group")
    def v2_override_group(vid: str, b: GroupOverrideIn, s: Session = Depends(db),
                          u: User = Depends(require("vendor.edit"))):
        v = s.scalars(select(VendorRecord).where(VendorRecord.vendor_id == vid)).first()
        if not v:
            raise HTTPException(404, "vendor not found")
        v.group_id = b.group_id
        audit(s, "v2.vendor_group_override", u.username, {"vendor_id": vid, "group_id": b.group_id})
        s.commit()
        return {"vendor_id": vid, "group_id": b.group_id}

    @app.post("/api/v2/contacts")
    def v2_add_contact(b: V2ContactIn, s: Session = Depends(db),
                       u: User = Depends(require("vendor.edit"))):
        c = RS.add_contact(s, owner_type=b.owner_type, owner_id=b.owner_id, name=b.name,
                           is_primary=b.is_primary, email=b.email,
                           phone_country_code=b.phone_country_code, phone_number=b.phone_number,
                           designation=b.designation, country=b.country,
                           mailing_address=b.mailing_address)
        audit(s, "v2.contact_added", u.username,
              {"owner": b.owner_id, "primary": b.is_primary, "contact_id": c.id})
        s.commit()
        return {"contact_id": c.id, "is_primary": c.is_primary}

    # ---- engagements (exhaustive) ----
    @app.post("/api/v2/engagements")
    def v2_create_engagement(b: V2EngagementIn, s: Session = Depends(db),
                             u: User = Depends(require("engagement.edit"))):
        e = RS.create_engagement(s, vendor_id=b.vendor_id, title=b.title,
                                 owner_user=b.owner_user or u.username,
                                 service_description=b.service_description,
                                 material_group_id=b.material_group_id,
                                 business_unit=b.business_unit,
                                 deployment_model=b.deployment_model,
                                 annual_value=b.annual_value,
                                 currency=b.currency)
        audit(s, "v2.engagement_created", u.username,
              {"engagement_id": e.engagement_id, "vendor_id": b.vendor_id})
        s.commit()
        return {"engagement_id": e.engagement_id}

    @app.get("/api/v2/engagements")
    def v2_list_engagements(vendor_id: Optional[str] = None, status: Optional[str] = None,
                            s: Session = Depends(db), u: User = Depends(require("engagement.view"))):
        stmt = select(EngagementRecord)
        rows = s.scalars(stmt).all()
        out = []
        for e in rows:
            if vendor_id and e.vendor_id != vendor_id:
                continue
            if status and e.status != status:
                continue
            out.append({"engagement_id": e.engagement_id, "vendor_id": e.vendor_id,
                        "title": e.title, "status": e.status, "stage": e.stage,
                        "inherent_band": e.inherent_band, "residual_band": e.residual_band,
                        "open_actions": e.open_actions, "contract_id": e.contract_id,
                        "assessment_id": e.assessment_id, "material_group_id": e.material_group_id})
        return out

    # ---- assessments ----
    @app.post("/api/v2/assessments")
    def v2_create_assessment(b: V2AssessmentIn, s: Session = Depends(db),
                             u: User = Depends(require("engagement.view"))):
        pool = [x.username for x in s.scalars(select(User)).all() if x.is_active]
        rec = RS.create_assessment(s, engagement_id=b.engagement_id, vendor_id=b.vendor_id,
                                   engagement_owner=u.username, session_id=b.session_id,
                                   inherent_band=b.inherent_band, residual_band=b.residual_band,
                                   assessor_pool=pool)
        audit(s, "v2.assessment_created", u.username,
              {"assessment_id": rec.assessment_id, "assessor": rec.assessor_user})
        s.commit()
        return {"assessment_id": rec.assessment_id, "status": rec.status,
                "assessor_user": rec.assessor_user, "spoc_user": rec.spoc_user}

    @app.get("/api/v2/assessments")
    def v2_list_assessments(s: Session = Depends(db), u: User = Depends(require("engagement.view"))):
        out = []
        for a in s.scalars(select(AssessmentRecord)).all():
            if not _can_view_assessment(u, a):
                continue
            out.append({"assessment_id": a.assessment_id, "engagement_id": a.engagement_id,
                        "status": a.status, "inherent_band": a.inherent_band,
                        "outcome": a.outcome, "assessor_user": a.assessor_user,
                        "assessor_signed_off": a.assessor_signed_off, "locked": a.locked,
                        "spoc_user": a.spoc_user})
        return out

    @app.post("/api/v2/assessments/{aid}/signoff")
    def v2_signoff(aid: str, s: Session = Depends(db), u: User = Depends(require("engagement.review"))):
        a = s.scalars(select(AssessmentRecord).where(AssessmentRecord.assessment_id == aid)).first()
        if not a:
            raise HTTPException(404, "assessment not found")
        if a.assessor_user and a.assessor_user != u.username and u.role.key != "admin":
            raise HTTPException(403, "only the assigned assessor may sign off")
        a.assessor_signed_off = True
        audit(s, "v2.assessment_signoff", u.username, {"assessment_id": aid})
        s.commit()
        return {"assessment_id": aid, "assessor_signed_off": True}

    @app.post("/api/v2/assessments/{aid}/approve")
    def v2_approve(aid: str, s: Session = Depends(db), u: User = Depends(require("engagement.review"))):
        try:
            rec = RS.approve_assessment(s, aid)
        except ValueError as e:
            raise HTTPException(400, str(e))
        audit(s, "v2.assessment_approved", u.username, {"assessment_id": aid, "locked": True})
        s.commit()
        return {"assessment_id": aid, "status": rec.status, "locked": rec.locked}

    @app.post("/api/v2/assessments/{aid}/recall")
    def v2_recall(aid: str, s: Session = Depends(db), u: User = Depends(require("engagement.view"))):
        a = s.scalars(select(AssessmentRecord).where(AssessmentRecord.assessment_id == aid)).first()
        if not a:
            raise HTTPException(404, "assessment not found")
        if a.locked:
            raise HTTPException(400, "approved assessments are hard-locked and cannot be recalled")
        a.status = "Recalled"
        audit(s, "v2.assessment_recalled", u.username, {"assessment_id": aid})
        s.commit()
        return {"assessment_id": aid, "status": "Recalled"}

    @app.post("/api/v2/assessments/{aid}/reassign")
    def v2_reassign(aid: str, b: ReassignIn, s: Session = Depends(db),
                    u: User = Depends(require("engagement.review"))):
        a = s.scalars(select(AssessmentRecord).where(AssessmentRecord.assessment_id == aid)).first()
        if not a:
            raise HTTPException(404, "assessment not found")
        if a.locked:
            raise HTTPException(400, "approved assessment is locked")
        a.assessor_user = b.assessor_user
        a.assessor_signed_off = False
        audit(s, "v2.assessor_reassigned", u.username, {"assessment_id": aid, "to": b.assessor_user})
        s.commit()
        return {"assessment_id": aid, "assessor_user": b.assessor_user}

    # ---- findings + remediation ----
    @app.post("/api/v2/findings")
    def v2_create_finding(b: V2FindingIn, s: Session = Depends(db),
                          u: User = Depends(require("finding.manage"))):
        f = RS.create_finding(s, title=b.title, severity=b.severity or "Medium",
                              source=b.source or "Assessor", description=b.description,
                              domain=b.domain, engagement_id=b.engagement_id,
                              vendor_id=b.vendor_id, assessment_id=b.assessment_id,
                              raised_by=u.username, due_date=b.due_date)
        audit(s, "v2.finding_created", u.username,
              {"finding_id": f.finding_id, "severity": f.severity})
        s.commit()
        return {"finding_id": f.finding_id, "severity": f.severity, "status": f.status}

    @app.get("/api/v2/findings")
    def v2_list_findings(engagement_id: Optional[str] = None, s: Session = Depends(db),
                         u: User = Depends(require("finding.view"))):
        rows = s.scalars(select(FindingRecord)).all()
        return [{"finding_id": f.finding_id, "title": f.title, "severity": f.severity,
                 "source": f.source, "status": f.status, "engagement_id": f.engagement_id,
                 "remediation_id": f.remediation_id}
                for f in rows if not engagement_id or f.engagement_id == engagement_id]

    @app.post("/api/v2/remediations")
    def v2_create_remediation(b: V2RemediationIn, s: Session = Depends(db),
                              u: User = Depends(require("finding.manage"))):
        r = RS.create_remediation(s, finding_id=b.finding_id, plan=b.plan,
                                  owner=b.owner, target_date=b.target_date)
        audit(s, "v2.remediation_created", u.username,
              {"remediation_id": r.remediation_id, "finding_id": b.finding_id})
        s.commit()
        return {"remediation_id": r.remediation_id}

    # ---- fourth parties ----
    @app.post("/api/v2/fourth-parties")
    def v2_create_fourth_party(b: V2FourthPartyIn, s: Session = Depends(db),
                               u: User = Depends(require("lifecycle.fourthparty"))):
        fp = RS.create_fourth_party(s, legal_name=b.legal_name, vendor_ids=b.vendor_ids or [],
                                    also_vendor_id=b.vendor_id, service_provided=b.service_provided,
                                    hq_country=b.hq_country)
        audit(s, "v2.fourth_party_created", u.username,
              {"fourth_party_id": fp.fourth_party_id, "concentration": fp.concentration_flag})
        s.commit()
        return {"fourth_party_id": fp.fourth_party_id, "concentration_flag": fp.concentration_flag}

    @app.get("/api/v2/fourth-parties")
    def v2_list_fourth_parties(s: Session = Depends(db), u: User = Depends(require("lifecycle.fourthparty"))):
        out = []
        for fp in s.scalars(select(FourthPartyRecord)).all():
            vlinks = [fv.vendor_id for fv in s.scalars(select(FourthPartyVendor).where(
                FourthPartyVendor.fourth_party_id == fp.fourth_party_id)).all()]
            out.append({"fourth_party_id": fp.fourth_party_id, "legal_name": fp.legal_name,
                        "concentration_flag": fp.concentration_flag, "vendor_id": fp.vendor_id,
                        "supports_vendors": vlinks})
        return out

    # ---- artefacts + revalidation + issues ----
    @app.post("/api/v2/artefacts")
    def v2_create_artefact(b: V2ArtefactIn, s: Session = Depends(db),
                           u: User = Depends(require("lifecycle.documents"))):
        art = RS.create_artefact(s, vendor_id=b.vendor_id, name=b.name,
                                 artefact_type=b.artefact_type or "certificate",
                                 expiry_date=b.expiry_date, received_via=b.received_via or "upload",
                                 supersedes=b.supersedes, issue_date=b.issue_date,
                                 engagement_id=b.engagement_id)
        audit(s, "v2.artefact_created", u.username,
              {"artefact_id": art.artefact_id, "status": art.status})
        s.commit()
        return {"artefact_id": art.artefact_id, "status": art.status,
                "supersedes": art.supersedes}

    @app.get("/api/v2/artefacts")
    def v2_list_artefacts(vendor_id: Optional[str] = None, s: Session = Depends(db),
                          u: User = Depends(require("lifecycle.documents"))):
        rows = s.scalars(select(ArtefactRecord)).all()
        return [{"artefact_id": a.artefact_id, "vendor_id": a.vendor_id, "name": a.name,
                 "type": a.artefact_type, "expiry_date": a.expiry_date, "status": a.status,
                 "is_current": a.is_current, "received_via": a.received_via,
                 "doc_link": a.object_uri}
                for a in rows if not vendor_id or a.vendor_id == vendor_id]

    # ============================================================
    # CR-4/5/12 — DOCUMENT STORE + AI EXTRACTION
    # ============================================================
    @app.post("/api/v2/documents/upload")
    def v2_doc_upload(b: DocUploadIn, s: Session = Depends(db),
                      u: User = Depends(require("lifecycle.documents"))):
        from .features import documents as DOC
        out = []
        for f in b.files:
            try:
                row = DOC.store_document(s, filename=f.filename, content_type=f.content_type or "",
                                         data_b64=f.data_b64, vendor_id=b.vendor_id,
                                         engagement_id=b.engagement_id, uploaded_by=u.username,
                                         purpose=b.purpose)
            except ValueError as e:
                raise HTTPException(422, str(e))
            out.append({"doc_id": row.doc_id, "filename": row.filename, "size": row.size_bytes})
        audit(s, "v2.doc_upload", u.username, {"count": len(out), "purpose": b.purpose})
        s.commit()
        return {"documents": out}

    @app.get("/api/v2/documents/{doc_id}")
    def v2_doc_get(doc_id: str, s: Session = Depends(db),
                   u: User = Depends(require("lifecycle.documents"))):
        from .features import documents as DOC
        import base64 as _b64
        from fastapi import Response
        d = DOC.get_document(s, doc_id)
        if not d:
            raise HTTPException(404, "document not found")
        raw = _b64.b64decode(d.data_b64 or "")
        return Response(content=raw, media_type=d.content_type,
                        headers={"Content-Disposition": f'inline; filename="{d.filename}"'})

    @app.post("/api/v2/certificates/ingest")
    def v2_cert_ingest(b: CertIngestIn, s: Session = Depends(db),
                       u: User = Depends(require("lifecycle.documents"))):
        """CR-5: multi-document certificate ingest. Each document is stored, read by the
        extractor, and a certificate record (ArtefactRecord) is created with the document
        linked for viewing, tagged to the vendor (and engagement where given)."""
        from .features import documents as DOC
        v = s.scalars(select(VendorRecord).where(VendorRecord.vendor_id == b.vendor_id)).first()
        if not v:
            raise HTTPException(404, "vendor not found")
        created = []
        for f in b.files:
            try:
                doc = DOC.store_document(s, filename=f.filename, content_type=f.content_type or "",
                                         data_b64=f.data_b64, vendor_id=b.vendor_id,
                                         engagement_id=b.engagement_id, uploaded_by=u.username,
                                         purpose="certificate")
            except ValueError as e:
                raise HTTPException(422, str(e))
            ext = DOC.extract_certificate(s, doc)
            art = RS.create_artefact(
                s, vendor_id=b.vendor_id, name=ext["name"],
                artefact_type=ext["artefact_type"], expiry_date=ext.get("expiry_date"),
                received_via="upload", issue_date=ext.get("issue_date"),
                engagement_id=b.engagement_id, object_uri=f"/api/v2/documents/{doc.doc_id}")
            created.append({"artefact_id": art.artefact_id, "name": art.name,
                            "type": art.artefact_type, "expiry_date": art.expiry_date,
                            "status": art.status, "doc_id": doc.doc_id,
                            "doc_link": f"/api/v2/documents/{doc.doc_id}",
                            "gaps": ext.get("gaps", [])})
        audit(s, "v2.cert_ingest", u.username,
              {"vendor_id": b.vendor_id, "count": len(created)})
        s.commit()
        return {"certificates": created}

    @app.post("/api/v2/artefacts/revalidate")
    def v2_revalidate(s: Session = Depends(db), u: User = Depends(require("lifecycle.evidence"))):
        result = RS.revalidation_run(s)
        # send 7-day notices via the email path (SMTP or simulation)
        for n in result["notify_7day"]:
            v = s.scalars(select(VendorRecord).where(VendorRecord.vendor_id == n["vendor_id"])).first()
            contact = s.scalars(select(ContactRecord).where(
                ContactRecord.owner_type == "vendor", ContactRecord.owner_id == n["vendor_id"],
                ContactRecord.is_primary == True)).first()  # noqa: E712
            to = contact.email if contact and contact.email else "vendor@example.com"
            s.add(EmailOutbox(to_addr=to, subject=f"Certificate expiring: {n['name']}",
                              body=f"{n['name']} expires {n['expiry']}. Please provide an updated copy.",
                              sent=False))
        audit(s, "v2.revalidation_run", u.username,
              {"checked": result["checked"], "notify": len(result["notify_7day"]),
               "new_issues": len(result["new_issues"])})
        s.commit()
        return result

    @app.get("/api/v2/issues")
    def v2_list_issues(status: Optional[str] = None, s: Session = Depends(db),
                       u: User = Depends(require("finding.view"))):
        rows = s.scalars(select(IssueRecord).order_by(IssueRecord.id.desc())).all()
        return [{"issue_id": i.issue_id, "vendor_id": i.vendor_id, "vendor_name": i.vendor_name,
                 "artefact_id": i.artefact_id, "kind": i.kind, "detail": i.detail,
                 "status": i.status, "closed_reason": i.closed_reason}
                for i in rows if not status or i.status == status]

    # ---- financial DD (deterministic engine) ----
    @app.post("/api/v2/financial-dd")
    def v2_financial_dd(b: FinancialIn, s: Session = Depends(db),
                        u: User = Depends(require("intel.financial"))):
        from .features import master_service as MS
        from .features import entity_resolve as ER
        result = FIN.assess_financials(b.figures, b.flags or {})
        ent = ER.resolve_entity(s, vendor_id=b.vendor_id, other_name=b.other_name)
        persisted = False
        if ent.get("registered"):
            persisted = MS.persist_fdd(s, ent["vendor_id"], result)
            MS.refresh_risk_profile(s, ent["vendor_id"])
        result["entity"] = ent
        result["persisted"] = persisted
        audit(s, "v2.financial_dd", u.username,
              {"banding": result["banding"], "altman_zone": result["altman"]["zone"],
               "entity": ent["vendor_name"], "persisted": persisted})
        s.commit()
        return result

    # ---- reputation & ESG (7-pillar engine) ----
    @app.post("/api/v2/reputation")
    def v2_reputation(b: ReputationIn, s: Session = Depends(db),
                      u: User = Depends(require("intel.reputation"))):
        from .features import reputation as REP
        from .features import entity_resolve as ER
        from .features import master_service as MS
        ent = ER.resolve_entity(s, vendor_id=b.vendor_id, other_name=b.other_name)
        result = REP.assess_reputation(b.events or [], b.customer_facing)
        result["entity"] = ent
        persisted = False
        if ent.get("registered"):
            persisted = MS.persist_reputation(s, ent["vendor_id"], result)
            MS.refresh_risk_profile(s, ent["vendor_id"])
        result["persisted"] = persisted
        audit(s, "v2.reputation", u.username,
              {"overall": result["overall"], "verdict": result["verdict"],
               "entity": ent["vendor_name"], "events": result["event_count"],
               "persisted": persisted})
        s.commit()
        return result

    # ---- contract management (Matt) ----
    @app.post("/api/v2/contracts/terms")
    def v2_contract_terms(b: ContractTermsIn, s: Session = Depends(db),
                          u: User = Depends(require("intel.contract"))):
        from .features import contracts as CON
        from .features import entity_resolve as ER
        ent = ER.resolve_entity(s, vendor_id=b.vendor_id, other_name=b.other_name)
        terms = CON.required_terms(b.inherent_band, b.exposure or {})
        audit(s, "v2.contract_terms", u.username,
              {"inherent": b.inherent_band, "count": len(terms), "entity": ent["vendor_name"]})
        s.commit()
        return {"inherent_band": b.inherent_band, "required_terms": terms,
                "count": len(terms), "entity": ent}

    @app.post("/api/v2/contracts/gap-report")
    def v2_contract_gap(b: ContractGapIn, s: Session = Depends(db),
                        u: User = Depends(require("intel.contract"))):
        from .features import contracts as CON
        rep = CON.gap_report(b.contract_text, b.inherent_band, b.exposure or {})
        audit(s, "v2.contract_gap_report", u.username,
              {"gaps": len(rep["gaps"]), "critical": rep["critical_gaps"]})
        s.commit()
        return rep

    @app.post("/api/v2/contracts/diff")
    def v2_contract_diff(b: ContractDiffIn, s: Session = Depends(db),
                         u: User = Depends(require("intel.contract"))):
        from .features import contracts as CON
        rep = CON.existing_vs_to_add(b.inherent_band, b.exposure or {},
                                     b.prior_contract_texts or [])
        audit(s, "v2.contract_diff", u.username,
              {"existing": len(rep["terms_already_existing"]),
               "to_add": len(rep["terms_to_be_added"])})
        s.commit()
        return rep

    @app.post("/api/v2/contracts/gap-from-document")
    def v2_contract_gap_doc(b: ContractGapDocIn, s: Session = Depends(db),
                            u: User = Depends(require("intel.contract"))):
        """CR-12: upload a contract document; AI extracts terms; gap review runs against
        the required terms for the engagement's inherent band. For a REGISTERED engagement
        the inherent band and exposure are inherited automatically; only an 'Other' vendor
        is prompted for the band."""
        from .features import documents as DOC
        from .features import contracts as CON
        from .features import master_service as MS
        band = b.inherent_band
        exposure = {}
        engagement_id = b.engagement_id
        vendor_id = b.vendor_id
        # inherit from the engagement where registered
        if engagement_id:
            eng = MS.engagement_full(s, engagement_id)
            if not eng:
                raise HTTPException(404, "engagement not found")
            base = eng.get("base", {}); ext = eng.get("ext", {}) or {}
            band = base.get("inherent_band") or band
            vendor_id = base.get("vendor_id") or vendor_id
            # derive exposure flags from engagement risk fields
            exposure = {
                "personal_data": bool(ext.get("personal_data")),
                "cross_border": bool(ext.get("cross_border")),
                "mission_critical": bool(ext.get("mission_critical")),
                "regulated": bool(ext.get("regulated_activity")),
            }
        if not band:
            raise HTTPException(422, "inherent band required for an 'Other' (unregistered) vendor")
        # store + extract
        try:
            doc = DOC.store_document(s, filename=b.file.filename,
                                     content_type=b.file.content_type or "",
                                     data_b64=b.file.data_b64, vendor_id=vendor_id,
                                     engagement_id=engagement_id, uploaded_by=u.username,
                                     purpose="contract")
        except ValueError as e:
            raise HTTPException(422, str(e))
        terms = DOC.extract_contract_terms(s, doc)
        text = DOC._decode_text(doc)
        rep = CON.gap_report(text, band, exposure)
        audit(s, "v2.contract_gap_doc", u.username,
              {"doc_id": doc.doc_id, "engagement_id": engagement_id,
               "gaps": len(rep["gaps"])})
        s.commit()
        return {"doc_id": doc.doc_id, "doc_link": f"/api/v2/documents/{doc.doc_id}",
                "inherited_from_engagement": bool(engagement_id),
                "inherent_band": band, "exposure": exposure,
                "extracted_terms": terms, "gap_report": rep,
                "readable": terms.get("readable", False)}

    # ---- management dashboard + chat (leadership-gated) ----
    @app.get("/api/v2/management/risk-view")
    def v2_risk_view(s: Session = Depends(db), u: User = Depends(require("dashboard.risk"))):
        from .features import management as MGMT
        return MGMT.risk_view(s)

    @app.get("/api/v2/management/ops-view")
    def v2_ops_view(s: Session = Depends(db), u: User = Depends(require("dashboard.ops"))):
        from .features import management as MGMT
        return MGMT.ops_view(s)

    @app.get("/api/v2/management/concentration")
    def v2_concentration(s: Session = Depends(db), u: User = Depends(require("dashboard.risk"))):
        from .features import management as MGMT
        return MGMT.concentration_graph(s)

    @app.get("/api/v2/management/concentration/detail")
    def v2_concentration_detail(node_type: str, key: str, s: Session = Depends(db),
                                u: User = Depends(require("dashboard.risk"))):
        from .features import management as MGMT
        if node_type not in ("location", "fourth_party", "vendor"):
            raise HTTPException(400, "node_type must be location, fourth_party or vendor")
        return MGMT.concentration_node_detail(s, node_type, key)

    @app.post("/api/v2/intelligence/board")
    def v2_board_intelligence(s: Session = Depends(db),
                              u: User = Depends(require("dashboard.exec"))):
        from .features import intelligence as INTEL
        result = INTEL.board_intelligence(s)
        from .agents import llm_config
        if llm_config.is_enabled():
            try:
                import json as _json
                ctx = _json.dumps({"internal": result["internal"],
                                   "external": result["external"],
                                   "observations": result["observations"][:6],
                                   "predictions": result["predictions"]})
                enriched = llm_config.complete(
                    "You are a BCG-grade board adviser on third-party risk. Using ONLY "
                    "the supplied analysis, write a 3-4 sentence executive briefing for the "
                    "board: the single most important matter, the systemic pattern across "
                    "the observations, and the one thing the board must instruct management "
                    "to do first. Direct, no preamble.",
                    f"Analysis: {ctx}", domain="management")
                if enriched:
                    result["executive_briefing"] = enriched
                    result["engine"] = "llm"
            except Exception:
                pass
        audit(s, "v2.board_intelligence", u.username,
              {"engine": result["engine"], "observations": len(result["observations"])})
        s.commit()
        return result

    @app.post("/api/v2/management/chat")
    def v2_management_chat(b: MgmtChatIn, s: Session = Depends(db),
                           u: User = Depends(require("dashboard.exec"))):
        from .features import management as MGMT
        # live LLM enrichment when configured; deterministic resolver otherwise
        result = MGMT.management_answer(s, b.question)
        from .agents import llm_config
        if llm_config.is_enabled():
            try:
                ctx = json.dumps(result["data"])
                enriched = llm_config.complete(
                    "You are a BCG-grade TPRM management consultant. Answer the "
                    "executive's question crisply using ONLY the supplied data. "
                    "Lead with the headline, then the so-what.",
                    f"Question: {b.question}\nData: {ctx}", domain="management")
                if enriched:
                    result["answer"] = enriched
                    result["engine"] = "llm"
            except Exception:
                pass
        audit(s, "v2.management_chat", u.username, {"engine": result["engine"]})
        s.commit()
        return result

    @app.get("/api/v2/management/suggested")
    def v2_management_suggested(u: User = Depends(require("dashboard.exec"))):
        from .features import management as MGMT
        return {"questions": MGMT.SUGGESTED_QUESTIONS}

    # ---- capture a chat session into a structured assessment ----
    @app.post("/api/v2/assessments/from-session")
    def v2_capture_session(b: CaptureIn, s: Session = Depends(db),
                           u: User = Depends(require("engagement.view"))):
        from .features import assessment_capture as CAP
        pool = [x.username for x in s.scalars(select(User)).all() if x.is_active]
        try:
            rec = CAP.capture_session(s, session_id=b.session_id,
                                      engagement_id=b.engagement_id,
                                      vendor_id=b.vendor_id,
                                      engagement_owner=u.username, assessor_pool=pool)
        except ValueError as e:
            raise HTTPException(400, str(e))
        audit(s, "v2.assessment_captured", u.username,
              {"assessment_id": rec.assessment_id, "session_id": b.session_id,
               "status": rec.status})
        s.commit()
        return {"assessment_id": rec.assessment_id, "status": rec.status,
                "inherent_band": rec.inherent_band, "assessor_user": rec.assessor_user}

    @app.get("/api/v2/assessments/{aid}/structured")
    def v2_assessment_structured(aid: str, s: Session = Depends(db),
                                 u: User = Depends(require("engagement.view"))):
        a = s.scalars(select(AssessmentRecord).where(
            AssessmentRecord.assessment_id == aid)).first()
        if not a:
            raise HTTPException(404, "assessment not found")
        if not _can_view_assessment(u, a):
            raise HTTPException(403, "you do not have access to this assessment record")
        return {"assessment_id": a.assessment_id, "engagement_id": a.engagement_id,
                "status": a.status, "locked": a.locked,
                "structured": json.loads(a.structured_json or "{}")}

    @app.get("/api/v2/assessments/{aid}/review")
    def v2_assessment_review(aid: str, s: Session = Depends(db),
                             u: User = Depends(require("engagement.view"))):
        """CR-2: full reviewable detail — scope, inherent risks, controls assessed,
        documents and the final residual recommendation — for a reviewer to scrutinise
        before approving. CR-3 access rule enforced."""
        from .features import master_service as MS
        a = s.scalars(select(AssessmentRecord).where(
            AssessmentRecord.assessment_id == aid)).first()
        if not a:
            raise HTTPException(404, "assessment not found")
        if not _can_view_assessment(u, a):
            raise HTTPException(403, "you do not have access to this assessment record")
        st = json.loads(a.structured_json or "{}")
        eng = MS.engagement_full(s, a.engagement_id) if a.engagement_id else {}
        base = eng.get("base", {})
        # documents/artefacts tagged to this vendor/engagement
        arts = []
        for art in s.scalars(select(ArtefactRecord).where(
                ArtefactRecord.vendor_id == a.vendor_id)).all():
            arts.append({"artefact_id": art.artefact_id, "kind": art.artefact_type,
                         "title": art.name, "status": art.status,
                         "expiry_date": art.expiry_date,
                         "doc_link": getattr(art, "doc_link", None)})
        # controls assessed: DDQ / per-stage controls captured in structured snapshot
        controls = st.get("per_stage", [])
        can_approve = (getattr(u.role, "key", None) in ("admin", "vrm")) and not a.locked
        return {
            "assessment_id": a.assessment_id, "engagement_id": a.engagement_id,
            "vendor_id": a.vendor_id, "status": a.status, "locked": a.locked,
            "outcome": a.outcome, "assessor_signed_off": a.assessor_signed_off,
            "scope": {"title": base.get("title"), "service_description": base.get("service_description"),
                      "data_classification": (eng.get("ext", {}) or {}).get("data_classification"),
                      "is_critical": base.get("is_critical")},
            "inherent": {"band": a.inherent_band, "detail": st.get("inherent_detail"),
                         "risks": st.get("risks", [])},
            "controls_assessed": controls,
            "documents": arts,
            "residual": {"band": a.residual_band, "verdict": st.get("verdict"),
                         "recommendation": st.get("recommendation")},
            "gaps": st.get("gaps", []),
            "transcript_available": bool(st.get("transcript")),
            "can_approve": can_approve,
        }

    @app.post("/api/v2/artefacts/email-intake")
    def v2_email_intake(b: EmailIntakeIn, s: Session = Depends(db),
                        u: User = Depends(require("lifecycle.documents"))):
        from .features import email_intake as EI
        result = EI.process_inbound_email(
            s, sender=b.sender, subject=b.subject or "",
            attachment_name=b.attachment_name or "", attachment_b64=b.attachment_b64,
            body_text=b.body_text or "", vendor_id=b.vendor_id)
        audit(s, "v2.email_intake", u.username,
              {"status": result["status"], "artefact_id": result.get("artefact_id")})
        s.commit()
        return result

    # ---- analysis-section support: sectors, peers, research, monitoring ----
    @app.get("/api/v2/sectors")
    def v2_sectors(u: User = Depends(require("intel.financial"))):
        return FIN.SECTORS

    @app.post("/api/v2/financial-dd/peers")
    def v2_peers(b: PeerBenchmarkIn, s: Session = Depends(db),
                 u: User = Depends(require("intel.financial"))):
        result = FIN.assess_financials(b.figures, b.flags or {})
        peers = FIN.peer_benchmark(result["ratios"], b.sector)
        return {"sector": b.sector, "peers": peers}

    @app.post("/api/v2/financial-dd/research")
    def v2_fin_research(b: FinResearchIn, s: Session = Depends(db),
                        u: User = Depends(require("intel.financial"))):
        from .features import entity_resolve as ER
        res = ER.research_financials(b.company, b.jurisdiction or "UK",
                                     b.identifier or "", b.year or "")
        audit(s, "v2.fin_research", u.username,
              {"company": b.company, "matched": res.get("matched")})
        s.commit()
        return res

    @app.get("/api/v2/fin-monitor")
    def v2_finmon_list(s: Session = Depends(db), u: User = Depends(require("intel.financial"))):
        from .features.registry_models import FinMonitorRecord
        rows = s.scalars(select(FinMonitorRecord).order_by(FinMonitorRecord.id)).all()
        return [{"id": r.id, "vendor_id": r.vendor_id, "entity_name": r.entity_name,
                 "last_signal": r.last_signal, "last_swept": r.last_swept,
                 "last_result": r.last_result} for r in rows]

    @app.post("/api/v2/fin-monitor")
    def v2_finmon_add(b: FinMonitorAddIn, s: Session = Depends(db),
                      u: User = Depends(require("intel.financial"))):
        from .features import entity_resolve as ER
        from .features.registry_models import FinMonitorRecord
        ent = ER.resolve_entity(s, vendor_id=b.vendor_id, other_name=b.other_name)
        if ent["vendor_name"] == "(unspecified)":
            raise HTTPException(400, "provide a vendor_id or other_name")
        row = FinMonitorRecord(vendor_id=ent["vendor_id"], entity_name=ent["vendor_name"])
        s.add(row); s.flush()
        audit(s, "v2.finmon_empanel", u.username, {"entity": ent["vendor_name"], "id": row.id})
        s.commit()
        return {"id": row.id, "vendor_id": row.vendor_id, "entity_name": row.entity_name}

    @app.delete("/api/v2/fin-monitor/{mid}")
    def v2_finmon_remove(mid: int, s: Session = Depends(db),
                         u: User = Depends(require("intel.financial"))):
        from .features.registry_models import FinMonitorRecord
        row = s.get(FinMonitorRecord, mid)
        if row:
            s.delete(row); s.commit()
        return {"deleted": True}

    @app.post("/api/v2/fin-monitor/sweep")
    def v2_finmon_sweep(b: FinMonitorSweepIn, s: Session = Depends(db),
                        u: User = Depends(require("intel.financial"))):
        from .features.registry_models import FinMonitorRecord
        from .agents import llm_config
        import datetime as _dt
        targets = ([s.get(FinMonitorRecord, b.monitor_id)] if b.monitor_id
                   else s.scalars(select(FinMonitorRecord)).all())
        targets = [t for t in targets if t]
        ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        swept = 0
        for t in targets:
            if llm_config.is_enabled():
                text = llm_config.complete(
                    "You are Vera, financial monitor. From authoritative public sources "
                    "(registry filings, regulator notices, rating agencies, official "
                    "releases, reputable press) report concisely: (1) financial-health "
                    "signal, (2) recent disclosures/results, (3) profit warnings, "
                    "(4) credit-rating changes, (5) distress signals. If nothing material, "
                    "say so. Name each source. End with one word on its own line: "
                    "SIGNAL=ok | SIGNAL=watch | SIGNAL=distress.",
                    f"Monitoring sweep for: {t.entity_name}", domain="finance")
                signal = "ok"
                if text:
                    low = text.lower()
                    signal = ("distress" if "signal=distress" in low else
                              "watch" if "signal=watch" in low else "ok")
                t.last_result = text or "No material findings."
                t.last_signal = signal
            else:
                t.last_result = ("Live monitoring needs an AI key. With a key set, Vera "
                                 "sweeps authoritative sources for financial-health signals, "
                                 "profit warnings, rating changes and distress indicators.")
                t.last_signal = "ok"
            t.last_swept = ts
            swept += 1
            # R1: reconcile the panel signal into the attribute time-series + risk profile
            if t.vendor_id:
                from .features import master_service as MS
                MS.persist_monitor_result(s, t.vendor_id, t.last_signal, t.last_result)
                MS.refresh_risk_profile(s, t.vendor_id)
        audit(s, "v2.finmon_sweep", u.username, {"swept": swept})
        s.commit()
        return {"swept": swept, "last_swept": ts,
                "ai_enabled": llm_config.is_enabled()}

    # ============================================================
    # REQ 1 — VENDOR MASTER
    # ============================================================
    @app.get("/api/v2/vendor-master/{vid}")
    def v2_vendor_master_get(vid: str, s: Session = Depends(db),
                             u: User = Depends(require("vendor.view"))):
        from .features import master_service as MS
        # banking visible only to admin or vendor.critical holders
        inc_bank = u.role.key == "admin" or "vendor.critical" in {p.key for p in u.role.permissions}
        data = MS.get_vendor_master(s, vid, include_bank=inc_bank)
        if not data:
            raise HTTPException(404, "vendor not found")
        return data

    @app.put("/api/v2/vendor-master/{vid}")
    def v2_vendor_master_put(vid: str, b: VendorMasterIn, s: Session = Depends(db),
                             u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        v = s.scalars(select(VendorRecord).where(VendorRecord.vendor_id == vid)).first()
        if not v:
            raise HTTPException(404, "vendor not found")
        err = _validate_typed_fields(b.data)
        if err:
            raise HTTPException(422, err)
        inc_bank = b.include_bank and (
            u.role.key == "admin" or "vendor.critical" in {p.key for p in u.role.permissions})
        if b.include_bank and not inc_bank:
            raise HTTPException(403, "banking fields require elevated permission")
        MS.update_vendor_master(s, vid, b.data, include_bank=inc_bank)
        audit(s, "v2.vendor_master_update", u.username, {"vendor_id": vid, "bank": inc_bank})
        s.commit()
        return MS.get_vendor_master(s, vid, include_bank=inc_bank)

    # ============================================================
    # REQ 2 — VENDOR ATTRIBUTE DATABASE
    # ============================================================
    @app.get("/api/v2/vendor-attributes/{vid}")
    def v2_vendor_attributes(vid: str, s: Session = Depends(db),
                             u: User = Depends(require("vendor.view"))):
        from .features import master_service as MS
        v = s.scalars(select(VendorRecord).where(VendorRecord.vendor_id == vid)).first()
        if not v:
            raise HTTPException(404, "vendor not found")
        return MS.vendor_attributes(s, vid)

    @app.post("/api/v2/vendor-attributes/{vid}/screening")
    def v2_attr_screening(vid: str, b: ScreeningIn, s: Session = Depends(db),
                          u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        if b.screen_type not in MS.SCREEN_TYPES:
            raise HTTPException(400, f"screen_type must be one of {MS.SCREEN_TYPES}")
        MS.set_screening(s, vid, b.screen_type, result=b.result, detail=b.detail,
                         screened_date=b.screened_date, next_due=b.next_due)
        audit(s, "v2.screening_update", u.username, {"vendor_id": vid, "type": b.screen_type})
        s.commit()
        return MS.list_screening(s, vid)

    @app.post("/api/v2/vendor-attributes/{vid}/domain/{domain}")
    def v2_attr_domain(vid: str, domain: str, b: AttrDomainIn, s: Session = Depends(db),
                       u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        fn = {"privacy": MS.update_privacy, "cyber": MS.update_cyber,
              "resilience": MS.update_resilience, "esg": MS.update_esg,
              "governance": MS.update_governance}.get(domain)
        if not fn:
            raise HTTPException(404, "unknown attribute domain")
        fn(s, vid, b.data)
        audit(s, "v2.attr_update", u.username, {"vendor_id": vid, "domain": domain})
        s.commit()
        return MS.vendor_attributes(s, vid)

    @app.post("/api/v2/vendor-attributes/{vid}/insurance")
    def v2_attr_insurance(vid: str, b: InsuranceIn, s: Session = Depends(db),
                          u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        MS.add_insurance(s, vid, b.model_dump())
        audit(s, "v2.insurance_add", u.username, {"vendor_id": vid, "type": b.policy_type})
        s.commit()
        return MS.vendor_attributes(s, vid)

    @app.post("/api/v2/vendor-attributes/{vid}/monitor-signal")
    def v2_attr_signal(vid: str, b: MonitorSignalIn, s: Session = Depends(db),
                       u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        MS.add_monitor_signal(s, vid, b.signal_type, b.value, b.source)
        s.commit()
        return {"ok": True}

    @app.post("/api/v2/vendor-attributes/{vid}/refresh-rollups")
    def v2_attr_refresh(vid: str, s: Session = Depends(db),
                        u: User = Depends(require("vendor.view"))):
        from .features import master_service as MS
        MS.refresh_cyber_certs(s, vid)
        rp = MS.refresh_risk_profile(s, vid)
        s.commit()
        return {"refreshed": True, "inherent_band": rp.inherent_band,
                "residual_band": rp.residual_band, "open_findings": rp.open_findings}

    # ============================================================
    # REQ 3 — ENGAGEMENT REGISTER
    # ============================================================
    @app.get("/api/v2/engagement-register/{eid}")
    def v2_eng_full(eid: str, s: Session = Depends(db),
                    u: User = Depends(require("engagement.view"))):
        from .features import master_service as MS
        data = MS.engagement_full(s, eid)
        if not data:
            raise HTTPException(404, "engagement not found")
        return data

    @app.put("/api/v2/engagement-register/{eid}")
    def v2_eng_ext_put(eid: str, b: EngExtIn, s: Session = Depends(db),
                       u: User = Depends(require("engagement.edit"))):
        from .features import master_service as MS
        eng = s.scalars(select(EngagementRecord).where(
            EngagementRecord.engagement_id == eid)).first()
        if not eng:
            raise HTTPException(404, "engagement not found")
        # base-record fields (inherent/residual band) persist to the engagement itself
        data = dict(b.data or {})
        for base_field in ("inherent_band", "residual_band"):
            if base_field in data:
                setattr(eng, base_field, data.pop(base_field))
        MS.update_eng_ext(s, eid, data)
        audit(s, "v2.engagement_update", u.username, {"engagement_id": eid})
        s.commit()
        return MS.engagement_full(s, eid)

    @app.post("/api/v2/engagement-register/{eid}/child")
    def v2_eng_child_add(eid: str, b: EngChildIn, s: Session = Depends(db),
                         u: User = Depends(require("engagement.edit"))):
        from .features import master_service as MS
        if b.kind not in ("deliverable", "milestone", "sla", "obligation", "personnel"):
            raise HTTPException(400, "invalid child kind")
        row = MS.add_eng_child(s, eid, b.kind, b.data)
        audit(s, "v2.engagement_child_add", u.username, {"engagement_id": eid, "kind": b.kind})
        s.commit()
        return {"id": row.id, "kind": b.kind}

    @app.delete("/api/v2/engagement-register/{eid}/child/{kind}/{cid}")
    def v2_eng_child_del(eid: str, kind: str, cid: int, s: Session = Depends(db),
                         u: User = Depends(require("engagement.edit"))):
        from .features import master_ext as MX
        model = {"deliverable": MX.EngagementDeliverable, "milestone": MX.EngagementMilestone,
                 "sla": MX.EngagementSLA, "obligation": MX.EngagementObligation,
                 "personnel": MX.EngagementPersonnel}.get(kind)
        if not model:
            raise HTTPException(400, "invalid child kind")
        row = s.get(model, cid)
        if row and row.engagement_id == eid:
            s.delete(row); s.commit()
        return {"deleted": True}

    @app.get("/api/v2/obligations/overdue")
    def v2_obligations_overdue(s: Session = Depends(db),
                               u: User = Depends(require("engagement.view"))):
        from .features import master_service as MS
        return MS.overdue_obligations(s)

    # ============================================================
    # REQ 2 — CONTRACT ENTITY
    # ============================================================
    @app.post("/api/v2/contracts")
    def v2_contract_create(b: ContractCreateIn, s: Session = Depends(db),
                           u: User = Depends(require("intel.contract"))):
        from .features import master_service as MS
        if not b.vendor_id and not b.engagement_id:
            raise HTTPException(400, "a contract must link to a vendor (MSA) or an engagement (Contract/PO)")
        row = MS.create_contract(s, contract_type=b.contract_type, vendor_id=b.vendor_id,
                                 engagement_id=b.engagement_id, parent_msa=b.parent_msa,
                                 data=b.data or {})
        audit(s, "v2.contract_create", u.username,
              {"contract_id": row.contract_id, "type": row.contract_type,
               "primary": row.primary_link})
        s.commit()
        return {"contract_id": row.contract_id, "primary_link": row.primary_link,
                "vendor_id": row.vendor_id, "engagement_id": row.engagement_id,
                "contract_type": row.contract_type}

    @app.get("/api/v2/contracts")
    def v2_contract_list(vendor_id: Optional[str] = None, engagement_id: Optional[str] = None,
                         s: Session = Depends(db), u: User = Depends(require("intel.contract"))):
        from .features import master_service as MS
        return MS.list_contracts(s, vendor_id=vendor_id, engagement_id=engagement_id)

    @app.put("/api/v2/contracts/{cid}")
    def v2_contract_update(cid: str, b: ContractUpdateIn, s: Session = Depends(db),
                           u: User = Depends(require("intel.contract"))):
        from .features import master_service as MS
        row = MS.update_contract(s, cid, b.data)
        if not row:
            raise HTTPException(404, "contract not found")
        audit(s, "v2.contract_update", u.username, {"contract_id": cid})
        s.commit()
        return {"contract_id": row.contract_id, "status": row.status}

    @app.post("/api/v2/contracts/migrate-v1")
    def v2_contract_migrate(s: Session = Depends(db),
                            u: User = Depends(require("intel.contract"))):
        from .features import master_service as MS
        n = MS.migrate_v1_contracts(s)
        audit(s, "v2.contract_migrate_v1", u.username, {"migrated": n})
        s.commit()
        return {"migrated": n}

    @app.post("/api/v2/engagement-register/{eid}/sync-contract")
    def v2_eng_sync_contract(eid: str, s: Session = Depends(db),
                             u: User = Depends(require("engagement.edit"))):
        from .features import master_service as MS
        row = MS.sync_engagement_contract(s, eid)
        s.commit()
        if not row:
            return {"synced": False, "reason": "no contract_reference on engagement"}
        return {"synced": True, "contract_id": row.contract_id}

    # ============================================================
    # REQ 3 — CRITICAL VENDORS MODULE
    # ============================================================
    @app.put("/api/v2/engagements/{eid}/criticality-inputs")
    def v2_crit_inputs(eid: str, b: CriticalityInputIn, s: Session = Depends(db),
                       u: User = Depends(require("engagement.edit"))):
        from .features import master_service as MS
        if not s.scalars(select(EngagementRecord).where(
                EngagementRecord.engagement_id == eid)).first():
            raise HTTPException(404, "engagement not found")
        MS.set_criticality_inputs(s, eid, b.model_dump())
        res = MS.score_engagement_criticality(s, eid)
        audit(s, "v2.criticality_inputs", u.username, {"engagement_id": eid, "score": res["score"]})
        s.commit()
        return res

    @app.get("/api/v2/engagements/{eid}/criticality")
    def v2_crit_score(eid: str, s: Session = Depends(db),
                      u: User = Depends(require("engagement.view"))):
        from .features import master_service as MS
        res = MS.score_engagement_criticality(s, eid)
        if res.get("exists") is False:
            raise HTTPException(404, "engagement not found")
        return res

    @app.post("/api/v2/critical-vendors/analyse")
    def v2_crit_analyse(b: CriticalAnalysisIn, s: Session = Depends(db),
                        u: User = Depends(require("vendor.critical"))):
        from .features import master_service as MS
        res = MS.run_critical_analysis(s, b.vendor_id)
        audit(s, "v2.critical_analysis", u.username,
              {"analysed": res["analysed"], "critical": len(res["critical_vendors"])})
        s.commit()
        return res

    @app.get("/api/v2/critical-vendors")
    def v2_crit_list(s: Session = Depends(db), u: User = Depends(require("vendor.view"))):
        from .features import master_service as MS
        return MS.list_critical(s)

    @app.post("/api/v2/critical-vendors/{vid}/override")
    def v2_crit_override(vid: str, b: CriticalOverrideIn, s: Session = Depends(db),
                         u: User = Depends(require("vendor.critical"))):
        from .features import master_service as MS
        res = MS.override_vendor_criticality(s, vid, b.is_critical, b.reason, u.username)
        audit(s, "v2.criticality_override", u.username,
              {"vendor_id": vid, "is_critical": b.is_critical})
        s.commit()
        return res

    @app.post("/api/v2/engagements/{eid}/criticality-override")
    def v2_eng_crit_override(eid: str, b: CriticalOverrideIn, s: Session = Depends(db),
                             u: User = Depends(require("engagement.edit"))):
        from .features import master_service as MS
        res = MS.override_engagement_criticality(s, eid, b.is_critical, b.reason or "manual", u.username)
        if res.get("exists") is False:
            raise HTTPException(404, "engagement not found")
        audit(s, "v2.eng_criticality_override", u.username,
              {"engagement_id": eid, "is_critical": b.is_critical})
        s.commit()
        return res

    # ============================================================
    # REQ 4 — VENDOR PERFORMANCE MANAGEMENT (critical vendors)
    # ============================================================
    @app.post("/api/v2/performance/scorecards")
    def v2_perf_create(b: ScorecardCreateIn, s: Session = Depends(db),
                       u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        try:
            sc = MS.create_scorecard(s, b.vendor_id, b.period_label,
                                     period_start=b.period_start, period_end=b.period_end,
                                     cadence=b.cadence)
        except ValueError as e:
            raise HTTPException(409, str(e))
        MS.auto_source_kpis(s, sc.scorecard_id)
        MS.compute_scorecard(s, sc.scorecard_id)
        audit(s, "v2.scorecard_create", u.username,
              {"scorecard_id": sc.scorecard_id, "vendor_id": b.vendor_id})
        s.commit()
        return MS.get_scorecard(s, sc.scorecard_id)

    @app.get("/api/v2/performance/scorecards/{sid}")
    def v2_perf_get(sid: str, s: Session = Depends(db),
                    u: User = Depends(require("vendor.view"))):
        from .features import master_service as MS
        sc = MS.get_scorecard(s, sid)
        if not sc:
            raise HTTPException(404, "scorecard not found")
        return sc

    # CR-11: performance enrolment (any vendor, not only critical)
    @app.get("/api/v2/performance/enrolment")
    def v2_perf_enrolment_list(s: Session = Depends(db),
                               u: User = Depends(require("vendor.view"))):
        from .features import master_service as MS
        return MS.list_perf_enrolment(s)

    @app.post("/api/v2/performance/enrolment")
    def v2_perf_enrol(b: PerfEnrolIn, s: Session = Depends(db),
                      u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        added = []
        for vid in b.vendor_ids:
            MS.enrol_vendor(s, vid, source="manual", user=u.username)
            added.append(vid)
        audit(s, "v2.perf_enrol", u.username, {"vendors": added})
        s.commit()
        return {"enrolled": added}

    @app.delete("/api/v2/performance/enrolment/{vid}")
    def v2_perf_unenrol(vid: str, s: Session = Depends(db),
                        u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        ok = MS.unenrol_vendor(s, vid)
        audit(s, "v2.perf_unenrol", u.username, {"vendor_id": vid})
        s.commit()
        return {"unenrolled": ok}

    @app.get("/api/v2/performance/vendor/{vid}")
    def v2_perf_list(vid: str, s: Session = Depends(db),
                     u: User = Depends(require("vendor.view"))):
        from .features import master_service as MS
        return MS.list_scorecards(s, vid)

    @app.put("/api/v2/performance/kpi/{kpi_id}")
    def v2_perf_kpi(kpi_id: int, b: KPIScoreIn, s: Session = Depends(db),
                    u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        row = MS.set_kpi_score(s, kpi_id, actual=b.actual, score=b.score,
                               excluded=b.excluded, exclude_reason=b.exclude_reason)
        if not row:
            raise HTTPException(404, "kpi not found")
        MS.compute_scorecard(s, row.scorecard_id)
        s.commit()
        return MS.get_scorecard(s, row.scorecard_id)

    @app.post("/api/v2/performance/scorecards/{sid}/recompute")
    def v2_perf_recompute(sid: str, s: Session = Depends(db),
                          u: User = Depends(require("vendor.view"))):
        from .features import master_service as MS
        # recompute only; auto-sourcing happens at creation or via explicit re-source
        res = MS.compute_scorecard(s, sid)
        s.commit()
        return res

    @app.post("/api/v2/performance/scorecards/{sid}/resource")
    def v2_perf_resource(sid: str, s: Session = Depends(db),
                         u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        n = MS.auto_source_kpis(s, sid)
        res = MS.compute_scorecard(s, sid)
        s.commit()
        return {"sourced": n, **res}

    @app.post("/api/v2/performance/scorecards/{sid}/agree")
    def v2_perf_agree(sid: str, b: AgreeIn, s: Session = Depends(db),
                      u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        sc = MS.agree_scorecard(s, sid, b.party)
        if not sc:
            raise HTTPException(404, "scorecard not found")
        audit(s, "v2.scorecard_agree", u.username, {"scorecard_id": sid, "party": b.party})
        s.commit()
        return {"scorecard_id": sid, "status": sc.status, "agreed_with_vendor": True}

    @app.post("/api/v2/performance/scorecards/{sid}/publish")
    def v2_perf_publish(sid: str, s: Session = Depends(db),
                        u: User = Depends(require("vendor.critical"))):
        from .features import master_service as MS
        res = MS.publish_scorecard(s, sid, u.username)
        if not res:
            raise HTTPException(404, "scorecard not found")
        audit(s, "v2.scorecard_publish", u.username,
              {"scorecard_id": sid, "score": res.get("composite_score")})
        s.commit()
        return res

    @app.post("/api/v2/performance/vendor/{vid}/reviews")
    def v2_perf_review_create(vid: str, b: ReviewIn, s: Session = Depends(db),
                              u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        row = MS.create_review(s, vid, b.data)
        audit(s, "v2.perf_review", u.username, {"review_id": row.review_id, "vendor_id": vid})
        s.commit()
        return {"review_id": row.review_id, "review_date": row.review_date}

    @app.post("/api/v2/performance/reviews/{rid}/acknowledge")
    def v2_perf_review_ack(rid: str, s: Session = Depends(db),
                           u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        row = MS.acknowledge_review(s, rid)
        if not row:
            raise HTTPException(404, "review not found")
        s.commit()
        return {"review_id": rid, "vendor_acknowledged": True}

    @app.post("/api/v2/performance/capa")
    def v2_perf_capa(b: PerfCapaIn, s: Session = Depends(db),
                     u: User = Depends(require("vendor.edit"))):
        from .features import master_service as MS
        sc = MS.get_scorecard(s, b.scorecard_id)
        if not sc:
            raise HTTPException(404, "scorecard not found")
        res = MS.raise_performance_capa(s, sc["vendor_id"], b.scorecard_id,
                                        b.gap, b.owner, b.due_date)
        audit(s, "v2.perf_capa", u.username, res)
        s.commit()
        return res

    @app.post("/api/v2/performance/capa/{rid}/verify")
    def v2_perf_capa_verify(rid: str, b: CapaVerifyIn, s: Session = Depends(db),
                            u: User = Depends(require("vendor.critical"))):
        from .features import master_service as MS
        res = MS.verify_performance_capa(s, rid, u.username, b.evidence)
        if not res:
            raise HTTPException(404, "remediation not found")
        audit(s, "v2.perf_capa_verify", u.username, {"remediation_id": rid})
        s.commit()
        return res

    # ============================================================
    # REQ 5 — ProAssess (autonomous assessment)
    # ============================================================
    @app.post("/api/v2/proassess/run")
    def v2_proassess_run(b: ProAssessRunIn, s: Session = Depends(db),
                         u: User = Depends(require("engagement.view"))):
        from .features import master_service as MS
        report = MS.run_proassess(s, vendor_id=b.vendor_id, engagement_id=b.engagement_id,
                                  irq=b.irq, ddq=b.ddq, documents=b.documents,
                                  extracted=b.extracted)
        audit(s, "v2.proassess_run", u.username,
              {"vendor_id": b.vendor_id, "inherent": report["inherent_band"],
               "residual": report["residual_band"], "gaps": report["gap_count"]})
        s.commit()
        return report

    @app.post("/api/v2/proassess/register")
    def v2_proassess_register(b: ProAssessRegisterIn, s: Session = Depends(db),
                              u: User = Depends(require("vendor.critical"))):
        from .features import master_service as MS
        res = MS.register_proassess(s, b.report, u.username)
        audit(s, "v2.proassess_register", u.username, res)
        s.commit()
        return res

    @app.post("/api/v2/proassess/autonomous")
    def v2_proassess_autonomous(b: ProAssessAutoIn, s: Session = Depends(db),
                                u: User = Depends(require("vendor.critical"))):
        """CR-4: single-input, document-aware, autonomous ProAssess. Works for new or
        existing vendors; creates records across the databases when create_records=True."""
        from .features import master_service as MS
        if not b.vendor_id and not b.new_vendor_name:
            raise HTTPException(422, "provide vendor_id or new_vendor_name")
        try:
            report = MS.run_proassess_autonomous(
                s, free_text=b.free_text or "", documents=b.documents,
                vendor_id=b.vendor_id, new_vendor_name=b.new_vendor_name,
                engagement_title=b.engagement_title, ddq=b.ddq,
                user=u.username, create_records=b.create_records)
        except Exception as e:
            s.rollback()
            raise HTTPException(400, f"autonomous assessment failed: {e}")
        if report.get("error"):
            raise HTTPException(422, report["error"])
        audit(s, "v2.proassess_autonomous", u.username,
              {"vendor_id": report.get("vendor_id"), "created_vendor": report.get("created_vendor"),
               "tables_written": report.get("tables_written", [])})
        s.commit()
        return report

    # ============================================================
    # REQ 6 — VENDOR 360 DASHBOARD (compile + correlate)
    # ============================================================
    @app.get("/api/v2/vendor360/portfolio")
    def v2_vendor360_portfolio(s: Session = Depends(db),
                               u: User = Depends(require("vendor.view"))):
        from .features import master_service as MS
        return MS.vendor360_portfolio(s)

    @app.get("/api/v2/vendor360/{vid}")
    def v2_vendor360(vid: str, s: Session = Depends(db),
                     u: User = Depends(require("vendor.view"))):
        from .features import master_service as MS
        data = MS.vendor360(s, vid)
        if not data:
            raise HTTPException(404, "vendor not found")
        s.commit()  # vendor360 refreshes the risk-profile snapshot
        return data

    # ===== mount the web UI =====
    from .web import ui as _ui
    app.include_router(_ui)

    return app


def _count_by(rows, attr):
    out: dict = {}
    for r in rows:
        k = getattr(r, attr) or "none"
        out[k] = out.get(k, 0) + 1
    return out


import os as _os
app = create_app(_os.environ.get("BRO_DB_URL", "sqlite:///bro_unified.db"))
