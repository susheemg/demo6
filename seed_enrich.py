"""
Comprehensive enrichment of the demonstrator database (bro_demo.db).

Runs AFTER seed_demo.py. Fills every remaining form, table and child collection,
and enforces logical correlation so each data point connects:
  - all engagement-register groups populated (origination..lifecycle)
  - engagement children: deliverables, milestones, SLAs, obligations, personnel
  - vendor contacts + industries
  - full assessment IRQ/DDQ structured data
  - findings -> remediation plans; expired certs -> issues; breaches/adverse media/
    financial distress -> matching findings; SLA breaches -> performance findings
  - notifications, monitoring enrolment, performance-review meetings
Idempotent-ish: safe to re-run on a fresh seed.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BRO_TRUST_HEADER", "1")
os.environ.pop("ANTHROPIC_API_KEY", None)

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

import app.bro_app as ba
from app.features import registry_service as RS
from app.features import master_service as MS
from app.features import master_ext as MX
from app.features import models_feature as MF
from app.features.models_feature import AuditLog
from app.features.bro_engine import chain_hash
from app.features.registry_models import (
    VendorRecord, EngagementRecord, AssessmentRecord, FindingRecord,
    IssueRecord, ArtefactRecord, FinMonitorRecord, RemediationRecord,
    IndustryMaster, VendorIndustry,
)
from app.features.master_data import ID_PREFIX

random.seed(7)
DB = "sqlite:///" + os.path.join(os.path.dirname(os.path.abspath(__file__)), "bro_demo.db")


def off(days):
    from datetime import date, timedelta
    return (date.today() + timedelta(days=days)).isoformat()


def main():
    ba.create_app(DB)
    s = Session(create_engine(DB))

    vendors = list(s.scalars(select(VendorRecord)).all())
    vmap = {v.vendor_id: v for v in vendors}
    engs = list(s.scalars(select(EngagementRecord)).all())
    OWNERS = ["susheem.grover", "hilda.osei", "silvia.romano", "fadi.haddad", "ikenna.okafor", "scott.mercer"]
    ASSESSORS = ["assessor.one", "assessor.two", "assessor.three"]
    industries = [row[0] for row in s.execute(select(IndustryMaster.id)).all()]

    GOV_FORUM = ["Quarterly Service Review", "Monthly Ops Forum", "Exec Steering Committee", "Annual Risk Review"]
    PRICING = ["Fixed fee", "Time & materials", "Consumption-based", "Subscription", "Per-transaction"]
    PAYTERMS = ["Net 30", "Net 45", "Net 60", "Net 90"]
    DATACLASS = ["Public", "Internal", "Confidential", "Restricted", "Highly Restricted"]
    SENT = ["Positive", "Neutral", "Strained", "At risk"]

    crit_vendor_ids = [v.vendor_id for v in vendors if v.is_critical]

    # =====================================================================
    # 1) FULL ENGAGEMENT REGISTER — every group, correlated to inherent band
    # =====================================================================
    sla_breach_engs = set()
    for e in engs:
        band = e.inherent_band or "MODERATE"
        v = vmap.get(e.vendor_id)
        hi = band in ("HIGH", "ELEVATED")
        ext = MS.get_or_create_eng_ext(s, e.engagement_id)
        crit_eng = _is_crit_eng(s, e.engagement_id)
        data = {
            # origination
            "business_justification": f"Procurement of {e.title.split(' #')[0].lower()} to support business operations.",
            "requested_by": random.choice(OWNERS), "procurement_category": v.tier if v else "Tier 3",
            "sourcing_route": random.choice(["Competitive tender", "Direct award", "Framework call-off", "Renewal"]),
            "competitive_flag": random.choice([True, False]),
            "competitive_rationale": "Selected on best value against evaluation criteria.",
            "requisition_ref": f"REQ-{random.randint(10000,99999)}", "business_case_ref": f"BC-{random.randint(1000,9999)}",
            # contract
            "contract_reference": f"CTR-{random.randint(10000,99999)}",
            "agreement_type": "MSA + SOW" if hi else random.choice(["Contract", "Order Form", "SOW"]),
            "signatories": f"{random.choice(OWNERS)} / {(v.legal_name if v else 'Vendor')} authorised signatory",
            "governing_law": random.choice(["England & Wales", "New York", "Ireland", "Singapore"]),
            "governing_language": "English",
            "execution_date": off(-random.randint(120, 900)), "effective_date": off(-random.randint(90, 800)),
            "initial_term": random.choice(["12 months", "24 months", "36 months"]),
            "renewal_type": random.choice(["Auto-renew", "Mutual", "None"]),
            "renewal_window": random.choice(["30 days", "60 days", "90 days"]),
            "notice_period": random.choice(["30 days", "60 days", "90 days"]),
            "termination_rights": "For cause and for convenience with notice.",
            "cure_period": random.choice(["15 days", "30 days"]), "change_of_control": True,
            "assignment_rights": "Not without prior written consent",
            "clause_flags": "Liability cap, audit rights, exit assistance, DP addendum",
            "contract_status": random.choice(["Executed", "Executed", "In renewal", "In negotiation"]),
            "contract_version": f"v{random.randint(1,4)}.0",
            # scope
            "scope_in": f"Provision, support and maintenance of {e.title.split(' #')[0].lower()}.",
            "scope_out": "Hardware procurement; third-party licences not listed.",
            "objectives": "Reliable, secure delivery meeting agreed service levels.",
            "assumptions": "Stable requirements; timely access provided.",
            "dependencies": "Network connectivity; identity provider integration.",
            "change_control_ref": f"CC-{random.randint(100,999)}",
            # service
            "service_type": ext.service_type or e.title.split(" #")[0],
            "supported_function": random.choice(["Trading", "Settlements", "Client Onboarding", "Finance", "HR", "Risk"]),
            "function_criticality": "Critical" if crit_eng else ("Important" if hi else "Standard"),
            "ict_flag": random.choice([True, True, False]),
            "integration_points": random.choice(["API", "SFTP", "SSO/SAML", "Direct DB", "File exchange"]),
            # financial
            "tcv": (e.annual_value or 100000) * random.choice([1, 2, 3]),
            "acv": e.annual_value or 100000, "pricing_model": random.choice(PRICING),
            "rate_card": "Agreed rate card v2", "indexation_terms": "CPI-linked, capped at 4%",
            "payment_terms": random.choice(PAYTERMS), "invoicing_frequency": random.choice(["Monthly", "Quarterly"]),
            "discounts": random.choice(["Volume tier", "Early payment 2%", "None"]),
            "fx_terms": "GBP/USD",
            "budget_allocation": random.choice(["OPEX", "CAPEX"]),
            "po_numbers": f"PO-{random.randint(100000,999999)}",
            "committed_spend": e.annual_value or 100000,
            "actual_spend": int((e.annual_value or 100000) * random.uniform(0.6, 1.05)),
            # governance
            "engagement_owner": e.owner_user or random.choice(OWNERS),
            "vendor_account_manager": f"{(v.legal_name.split()[0] if v else 'Vendor')} Account Team",
            "governance_forum": random.choice(GOV_FORUM),
            "governance_cadence": random.choice(["Monthly", "Quarterly", "Bi-annual"]),
            "escalation_path": "Engagement Owner → VRM Lead → Exec Sponsor",
            "raci": "Owner=A, Vendor=R, VRM=C, Exec=I",
            "relationship_sentiment": random.choice(SENT),
            "performance_reporting_cadence": random.choice(["Monthly", "Quarterly"]),
            # risk
            "data_classification": "Highly Restricted" if crit_eng else random.choice(DATACLASS),
            "data_volume": random.choice(["<10k", "10k-100k", "100k-1m", ">1m"]),
            "personal_data": bool(ext.personal_data) or hi,
            "data_subject_types": random.choice(["Employees", "Customers", "Both", "None"]),
            "system_access": random.choice(["None", "Read", "Read/Write", "Privileged"]),
            "physical_access": random.choice([True, False]),
            "mission_critical": hi, "cross_border": bool(ext.cross_border),
            "regulated_activity": random.choice([True, False]),
            "fourth_party_reliance": random.choice([True, True, False]),
            "concentration_contribution": "High" if crit_eng else random.choice(["Medium", "Low"]),
            # resilience
            "rto": random.choice(["2h", "4h", "8h", "24h"]), "rpo": random.choice(["15m", "1h", "4h"]),
            "bcp_dependency": random.choice(["Critical", "Important", "Standard"]),
            "exit_plan": "Documented and tested" if crit_eng else random.choice(["Documented", "Draft", "Not started"]),
            "exit_plan_tested": crit_eng or random.random() < 0.3,
            "transition_in_status": "Complete", "alternative_provider": random.choice(["Identified", "None", "In discovery"]),
            # compliance
            "dpa_in_place": bool(ext.personal_data) and random.random() < 0.85,
            "audit_rights": True, "audit_last_exercised": off(-random.randint(60, 700)),
            "required_clauses_present": random.choice([True, True, False]),
            "insurance_evidenced": random.random() < 0.8,
            "regulatory_notifications": random.choice(["N/A", "FCA notified", "Pending"]),
            # lifecycle
            "engagement_stage": e.status or "Active",
            "approval_status": random.choice(["Approved", "Approved", "Pending"]),
            "approver": random.choice(OWNERS), "approval_date": off(-random.randint(30, 400)),
            "go_live_date": off(-random.randint(30, 600)),
            "next_review_date": off(random.randint(20, 300)),
            "review_cadence": "Annual" if hi else "Biennial",
            "renewal_decision": random.choice(["Renew", "Renew", "Under review", "Exit"]),
            "end_date": off(random.randint(200, 1000)), "transition_status": "N/A",
            "data_steward": random.choice(OWNERS),
        }
        MS.update_eng_ext(s, e.engagement_id, data)

        # ---- engagement children (richer for critical/high) ----
        n_child = 3 if (crit_eng or hi) else 1
        for i in range(n_child):
            MS.add_eng_child(s, e.engagement_id, "deliverable", {
                "description": random.choice(["Service operational readiness", "Quarterly service report",
                                              "Implementation & integration", "Knowledge transfer pack"]),
                "due_date": off(random.randint(-200, 200)), "acceptance_criteria": "Signed-off by engagement owner",
                "accountable_owner": random.choice(OWNERS),
                "status": random.choice(["Complete", "Complete", "In progress", "Planned"])})
        MS.add_eng_child(s, e.engagement_id, "milestone", {
            "name": "Go-live", "due_date": off(-random.randint(10, 400)),
            "acceptance": "Production acceptance", "payment_trigger": 30.0,
            "status": "Achieved"})
        # SLAs — some breached (drives performance findings)
        breached = (random.random() < 0.22)
        if breached:
            sla_breach_engs.add((e.engagement_id, e.vendor_id))
        MS.add_eng_child(s, e.engagement_id, "sla", {
            "metric": "Availability", "target": "99.9%", "measurement_window": "Monthly",
            "calculation": "Uptime / total time", "credit_penalty": "5% monthly fee per 0.1% below",
            "current_value": "99.6%" if breached else "99.95%", "breach_flag": breached})
        MS.add_eng_child(s, e.engagement_id, "sla", {
            "metric": "P1 response time", "target": "15 min", "measurement_window": "Per incident",
            "calculation": "Time to acknowledge", "credit_penalty": "Service credit",
            "current_value": "12 min", "breach_flag": False})
        MS.add_eng_child(s, e.engagement_id, "obligation", {
            "description": "Provide annual SOC 2 report", "obligated_party": "Vendor",
            "obl_type": "Assurance", "due_date": off(random.randint(30, 300)), "recurrence": "Annual",
            "accountable_owner": random.choice(ASSESSORS), "status": "On track",
            "consequence": "Escalation; potential breach notice", "alert_rule": "30 days before due"})
        if crit_eng or hi:
            MS.add_eng_child(s, e.engagement_id, "obligation", {
                "description": "Notify of material subcontractor changes", "obligated_party": "Vendor",
                "obl_type": "Notification", "recurrence": "As required", "status": "On track",
                "accountable_owner": random.choice(OWNERS)})
        MS.add_eng_child(s, e.engagement_id, "personnel", {
            "name": random.choice(["A. Patel", "J. Murphy", "L. Schmidt", "R. Tan", "C. Rossi"]),
            "role": random.choice(["Service Delivery Manager", "Technical Lead", "Account Director"]),
            "key_personnel": True, "vetting_status": random.choice(["BPSS", "SC", "Completed"]),
            "access_level": random.choice(["Standard", "Privileged"]),
            "location": random.choice(["UK", "India", "US", "Ireland"]), "jml_status": "Active"})
    s.commit()
    print("engagement register + children: done")

    # =====================================================================
    # 2) VENDOR CONTACTS + INDUSTRIES + MONITORING ENROLMENT
    # =====================================================================
    for v in vendors:
        # industries
        if industries:
            s.add(VendorIndustry(vendor_id=v.vendor_id, industry_id=random.choice(industries)))
        # contacts (primary + secondary)
        first = v.legal_name.split()[0]
        RS.add_contact(s, owner_type="vendor", owner_id=v.vendor_id, name=f"{first} Relationship Lead",
                       is_primary=True, email=f"relationship@{_dom(v.legal_name)}",
                       phone_country_code="+1", phone_number=f"{random.randint(2000000000,9999999999)}",
                       designation="Account Director", country="United States")
        RS.add_contact(s, owner_type="vendor", owner_id=v.vendor_id, name=f"{first} Security Contact",
                       is_primary=False, email=f"security@{_dom(v.legal_name)}",
                       designation="CISO Office", country="United States")
        # monitoring enrolment for critical + sample
        if v.is_critical or random.random() < 0.4:
            if not s.scalars(select(FinMonitorRecord).where(FinMonitorRecord.vendor_id == v.vendor_id)).first():
                s.add(FinMonitorRecord(vendor_id=v.vendor_id, entity_name=v.legal_name,
                                       last_result=random.choice(["stable", "stable", "watch"]),
                                       last_signal="financial_health", last_swept=off(-random.randint(1, 30))))
    s.commit()
    print("contacts + industries + monitoring: done")

    # ---- fourth-party detail (service / HQ / website) so the drill-down is complete ----
    from app.features.registry_models import FourthPartyRecord as _FPR
    _FP_DETAIL = {
        "aws": ("Cloud infrastructure (IaaS)", "United States", "aws.amazon.com"),
        "amazon web services": ("Cloud infrastructure (IaaS)", "United States", "aws.amazon.com"),
        "microsoft": ("Cloud platform (Azure)", "United States", "azure.microsoft.com"),
        "azure": ("Cloud platform (Azure)", "United States", "azure.microsoft.com"),
        "google": ("Cloud platform (GCP)", "United States", "cloud.google.com"),
        "equinix": ("Data-centre colocation", "United States", "equinix.com"),
        "twilio": ("Communications API / messaging", "United States", "twilio.com"),
        "cloudflare": ("CDN / edge security", "United States", "cloudflare.com"),
        "okta": ("Identity & access management", "United States", "okta.com"),
        "stripe": ("Payment processing", "United States", "stripe.com"),
    }
    for fp in s.scalars(select(_FPR)).all():
        nm = (fp.legal_name or "").lower()
        svc, hq, web = ("Specialist sub-processor", random.choice(["United States", "Ireland", "United Kingdom", "India"]), None)
        for kfrag, det in _FP_DETAIL.items():
            if kfrag in nm:
                svc, hq, web = det
                break
        fp.service_provided = fp.service_provided or svc
        fp.hq_country = fp.hq_country or hq
        if web and not fp.website:
            fp.website = web
        fp.listing_status = fp.listing_status or random.choice(["Public", "Private"])
    s.commit()
    print("fourth-party detail: done")

    # =====================================================================
    # 3) FULL ASSESSMENT IRQ/DDQ STRUCTURED DATA + assessor/dates
    # =====================================================================
    asmts = list(s.scalars(select(AssessmentRecord)).all())
    for a in asmts:
        band = a.inherent_band or "MODERATE"
        hi = band in ("HIGH", "ELEVATED")
        irq = {
            "Q1_service": "Outsourced service supporting a business function",
            "Q2_dependency": "High" if hi else "Moderate",
            "Q3_data": (["Personal", "Confidential"] + (["Payment Card"] if hi else [])),
            "Q4_volume": ">1,000,000" if hi else "100,000-1,000,000",
            "Q5_system_access": "Yes" if hi else "No",
            "Q6_offshore": random.choice(["Yes", "No"]),
            "Q7_subprocessors": "Yes" if hi else "No",
        }
        ddq = {
            "infosec": {"iso27001": "Yes", "soc2": "Yes" if hi else "Partial", "pentest": "<12 months"},
            "resilience": {"bcp_tested": "Yes" if hi else "Documented", "rto": "4h"},
            "privacy": {"dpa": "Signed", "cross_border": irq["Q6_offshore"]},
        }
        domains = {d: random.randint(2, 4) for d in (["infosec", "resilience", "privacy", "reputation", "compliance"] if hi
                                                     else ["infosec", "privacy"])}
        a.structured_json = json.dumps({
            "source": "assessment", "irq": irq, "ddq": ddq, "domain_scores": domains,
            "recommendation": a.outcome or ("Approve with conditions" if hi else "Approve"),
            "verdict": a.outcome or ("Approve with conditions" if hi else "Approve"),
            "scope_summary": f"{band} inherent engagement; {len(domains)} control domains in scope.",
        })
        a.engagement_owner = a.engagement_owner or random.choice(OWNERS)
        a.spoc_name = "Vendor SPOC"; a.spoc_email = "spoc@vendor.example"
        if hi and not a.assessor_user:
            a.assessor_user = random.choice(ASSESSORS)
        if a.status == "Completed":
            a.assessor_signed_off = True; a.locked = random.random() < 0.6
            a.outcome = a.outcome or random.choice(["Approved", "Approved with findings"])
    s.commit()
    print("assessment IRQ/DDQ: done")

    # =====================================================================
    # 4) CORRELATION PASS — make every signal produce its consequence
    # =====================================================================
    def add_finding(vid, title, sev, dom, eid=None, status="Open"):
        return RS.create_finding(s, title=title, severity=sev, vendor_id=vid,
                                 status=status, source="Correlation", domain=dom,
                                 engagement_id=eid)

    # (a) breach history -> InfoSec finding
    for v in vendors:
        cy = s.scalars(select(MX.VendorCyber).where(MX.VendorCyber.vendor_id == v.vendor_id)).first()
        if cy and cy.breach_history_flag:
            add_finding(v.vendor_id, "Disclosed security breach in vendor history — assurance review required",
                        "High", "infosec")
    # (b) adverse-media / sanctions screening hit -> reputation signal + finding
    for v in vendors:
        for sc in s.scalars(select(MX.VendorScreening).where(MX.VendorScreening.vendor_id == v.vendor_id)).all():
            if (sc.result or "").lower() == "hit":
                dom = "reputation" if "media" in (sc.screen_type or "") else "compliance"
                add_finding(v.vendor_id, f"Screening hit ({sc.screen_type}) requires disposition", "High", dom)
                MS.persist_reputation(s, v.vendor_id, {"verdict": "Adverse", "overall": random.randint(35, 55)})
    # (c) financial distress band -> FDD finding
    for v in vendors:
        mx = s.scalars(select(MX.VendorMasterExt).where(MX.VendorMasterExt.vendor_id == v.vendor_id)).first()
        if mx and (mx.financial_health_band or "") in ("Weak", "Distress", "Caution"):
            add_finding(v.vendor_id, f"Financial health {mx.financial_health_band} — enhanced monitoring", "Medium", "financial")
    # (d) SLA breaches -> performance finding (linked to engagement)
    for eid, vid in sla_breach_engs:
        add_finding(vid, "SLA availability breach in reporting period — service credits due", "Medium", "performance", eid=eid)
    s.commit()
    print("correlation findings: done")

    # =====================================================================
    # 5) EXPIRED CERTIFICATES -> ISSUES (via revalidation), + remediation plans
    # =====================================================================
    # backdate a slice of certificates to expired so the revalidation engine opens issues
    arts = list(s.scalars(select(ArtefactRecord)).all())
    for art in random.sample(arts, min(18, len(arts))):
        art.expiry_date = off(-random.randint(40, 200))
        art.status = "Expired"
    s.commit()
    res = RS.revalidation_run(s)
    s.commit()
    print(f"revalidation: {len(res.get('new_issues', []))} expired-cert issues opened")

    # remediation plans for ~all High + half Medium open findings
    findings = list(s.scalars(select(FindingRecord).where(FindingRecord.status.in_(["Open", "In remediation"]))).all())
    made = 0
    for f in findings:
        if f.remediation_id:
            continue
        if f.severity == "High" or (f.severity == "Medium" and random.random() < 0.5):
            rem = RS.create_remediation(s, finding_id=f.finding_id,
                                        plan=f"Remediate: {f.title[:60]}",
                                        owner=random.choice(OWNERS), target_date=off(random.randint(20, 120)),
                                        status=random.choice(["Open", "In progress", "In progress"]),
                                        progress_pct=random.choice([0, 25, 50, 75]),
                                        milestones_json=json.dumps([
                                            {"m": "Root cause", "done": True},
                                            {"m": "Vendor remediation", "done": random.random() < 0.5},
                                            {"m": "Evidence & verify", "done": False}]))
            f.remediation_id = rem.remediation_id
            f.status = "In remediation"
            made += 1
    s.commit()
    print(f"remediation plans: {made}")

    # =====================================================================
    # 6) PERFORMANCE-REVIEW MEETINGS (tied to scorecards) + NOTIFICATIONS
    # =====================================================================
    scorecards = list(s.scalars(select(MX.VendorScorecard)).all())
    for sc in scorecards:
        if random.random() < 0.7:
            s.add(MX.PerformanceReview(
                review_id=f"PRV-{sc.scorecard_id[-4:]}-{random.randint(100,999)}",
                vendor_id=sc.vendor_id, scorecard_id=sc.scorecard_id,
                review_date=off(-random.randint(10, 200)), cadence="Quarterly",
                attendees="Engagement Owner, VRM Lead, Vendor Account Director",
                summary="Service performing to expectations; minor actions agreed.",
                outcomes="Continue; address open SLA action.", vendor_acknowledged=True,
                vendor_ack_date=off(-random.randint(5, 180)), next_review_date=off(random.randint(30, 120))))
    # notifications: expiry notices, new issues, approvals
    for i in res.get("new_issues", [])[:20]:
        s.add(MF.Notification(audience="vrm", event=f"Issue opened: expired certificate ({i['vendor_id']})", is_read=False))
    for n in res.get("notify_7day", [])[:10]:
        s.add(MF.Notification(audience="vrm", event=f"Certificate expiring within 7 days ({n['vendor_id']})", is_read=False))
    for a in random.sample(asmts, min(15, len(asmts))):
        s.add(MF.Notification(audience="all", event=f"Assessment {a.assessment_id} {a.outcome or 'completed'}", is_read=random.random() < 0.5))
    for v in crit_vendor_ids:
        s.add(MF.Notification(audience="exec", event=f"Critical vendor review due: {vmap[v].legal_name}", is_read=False))
    s.commit()
    print("performance reviews + notifications: done")

    # =====================================================================
    # 7) AUDIT TRAIL — realistic, correctly hash-chained activity log
    # =====================================================================
    import json as _json
    last = s.scalars(select(AuditLog).order_by(AuditLog.seq.desc())).first()
    prev = last.entry_hash if last else "genesis"
    seq = (last.seq + 1) if last else 0
    def _audit(action, actor, detail):
        nonlocal prev, seq
        h = chain_hash(prev, action, actor, detail)
        s.add(AuditLog(seq=seq, action=action, actor=actor,
                       detail=_json.dumps(detail, sort_keys=True), prev_hash=prev, entry_hash=h))
        prev = h; seq += 1
    for v in vendors:
        _audit("vendor.created", "demo-seed", {"vendor_id": v.vendor_id, "name": v.legal_name})
    for v in vendors:
        if v.is_critical:
            _audit("vendor.criticality_override", "susheem.grover",
                   {"vendor_id": v.vendor_id, "is_critical": True})
    for e in engs[:120]:
        _audit("engagement.created", e.owner_user or "susheem.grover",
               {"engagement_id": e.engagement_id, "vendor_id": e.vendor_id})
    for a in asmts:
        _audit("assessment.captured", a.assessor_user or a.engagement_owner or "assessor.one",
               {"assessment_id": a.assessment_id, "inherent": a.inherent_band, "residual": a.residual_band})
        if a.locked:
            _audit("assessment.approved", "ikenna.okafor",
                   {"assessment_id": a.assessment_id, "outcome": a.outcome})
    for art in s.scalars(select(ArtefactRecord)).all():
        _audit("certificate.ingested", "assessor.one",
               {"artefact_id": art.artefact_id, "vendor_id": art.vendor_id, "name": art.name})
    for f in s.scalars(select(FindingRecord)).all():
        _audit("finding.raised", "assessor.two",
               {"finding_id": f.finding_id, "severity": f.severity, "domain": f.domain})
    for i in s.scalars(select(IssueRecord)).all():
        _audit("issue.opened", "system", {"issue_id": i.issue_id, "kind": i.kind})
    s.commit()
    print("audit trail: chained entries written")

    # refresh profiles so Vendor 360 + dashboards reconcile after new findings/signals
    for v in vendors:
        try:
            MS.refresh_risk_profile(s, v.vendor_id)
        except Exception:
            pass
    s.commit()
    s.close()
    print("\nENRICHMENT COMPLETE")


def _dom(name):
    base = "".join(ch for ch in name.lower().split(",")[0].split("(")[0] if ch.isalnum())[:18]
    return f"{base or 'vendor'}.com"


def _is_crit_eng(s, eid):
    rows = s.scalars(select(MX.CriticalityDesignation).where(
        MX.CriticalityDesignation.subject_type == "engagement",
        MX.CriticalityDesignation.subject_id == eid).order_by(MX.CriticalityDesignation.id)).all()
    state = False
    for r in rows:
        state = r.is_critical
    return state


if __name__ == "__main__":
    main()
