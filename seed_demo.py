"""
Demonstrator seed — builds a realistic, fully-populated BRO Risk Oracle database.

Targets: 100 vendors (well-known real companies), 275 engagements,
5 critical vendors, 7 critical engagements, with realistic data populated across
every feature: vendor master, risk attributes (screening/privacy/cyber/resilience/
ESG/insurance), criticality, contracts, certificates (document-backed), assessments,
performance scorecards, findings, fourth parties, delivery/receiving locations.

Run:  python seed_demo.py            -> writes ./bro_demo.db
Vendor facts (HQ, sector, listing) reflect public, well-established information.
"""
import base64
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BRO_TRUST_HEADER", "1")
os.environ.pop("ANTHROPIC_API_KEY", None)

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.bro_app import create_app  # ensures models import + tables register
from app.features import registry_service as RS
from app.features import master_service as MS
from app.features import documents as DOC
from app.features.models_db import Base

random.seed(42)

DB = "sqlite:///" + os.path.join(os.path.dirname(os.path.abspath(__file__)), "bro_demo.db")

# (legal_name, hq_country, sector, listing, ticker, exchange)
# Well-known third parties typical of a global financial institution's estate.
VENDORS = [
    ("Amazon Web Services, Inc.", "United States", "Cloud infrastructure", "Listed", "AMZN", "NASDAQ"),
    ("Microsoft Corporation", "United States", "Cloud & software", "Listed", "MSFT", "NASDAQ"),
    ("Google Cloud (Google LLC)", "United States", "Cloud infrastructure", "Listed", "GOOGL", "NASDAQ"),
    ("Oracle Corporation", "United States", "Database & cloud", "Listed", "ORCL", "NYSE"),
    ("SAP SE", "Germany", "Enterprise software", "Listed", "SAP", "XETRA"),
    ("Salesforce, Inc.", "United States", "CRM SaaS", "Listed", "CRM", "NYSE"),
    ("Workday, Inc.", "United States", "HCM & finance SaaS", "Listed", "WDAY", "NASDAQ"),
    ("ServiceNow, Inc.", "United States", "ITSM SaaS", "Listed", "NOW", "NYSE"),
    ("Adobe Inc.", "United States", "Creative & document SaaS", "Listed", "ADBE", "NASDAQ"),
    ("Snowflake Inc.", "United States", "Data cloud", "Listed", "SNOW", "NYSE"),
    ("Databricks, Inc.", "United States", "Data & AI platform", "Private", None, None),
    ("Atlassian Corporation", "Australia", "Dev collaboration SaaS", "Listed", "TEAM", "NASDAQ"),
    ("Datadog, Inc.", "United States", "Observability SaaS", "Listed", "DDOG", "NASDAQ"),
    ("Cloudflare, Inc.", "United States", "Edge network & security", "Listed", "NET", "NYSE"),
    ("Okta, Inc.", "United States", "Identity & access", "Listed", "OKTA", "NASDAQ"),
    ("CrowdStrike Holdings, Inc.", "United States", "Endpoint security", "Listed", "CRWD", "NASDAQ"),
    ("Palo Alto Networks, Inc.", "United States", "Network security", "Listed", "PANW", "NASDAQ"),
    ("Zscaler, Inc.", "United States", "Zero-trust security", "Listed", "ZS", "NASDAQ"),
    ("Fortinet, Inc.", "United States", "Network security", "Listed", "FTNT", "NASDAQ"),
    ("Splunk LLC", "United States", "SIEM & observability", "Listed", "CSCO", "NASDAQ"),
    ("Twilio Inc.", "United States", "Communications API", "Listed", "TWLO", "NYSE"),
    ("DocuSign, Inc.", "United States", "E-signature SaaS", "Listed", "DOCU", "NASDAQ"),
    ("Zoom Communications Inc.", "United States", "Video conferencing", "Listed", "ZM", "NASDAQ"),
    ("Slack (Salesforce)", "United States", "Team messaging", "Listed", "CRM", "NYSE"),
    ("MongoDB, Inc.", "United States", "Database platform", "Listed", "MDB", "NASDAQ"),
    ("Confluent, Inc.", "United States", "Data streaming", "Listed", "CFLT", "NASDAQ"),
    ("HashiCorp (IBM)", "United States", "Infrastructure automation", "Listed", "IBM", "NYSE"),
    ("GitHub, Inc. (Microsoft)", "United States", "Source control SaaS", "Listed", "MSFT", "NASDAQ"),
    ("Bloomberg L.P.", "United States", "Market data & analytics", "Private", None, None),
    ("London Stock Exchange Group plc", "United Kingdom", "Market data (Refinitiv)", "Listed", "LSEG", "LSE"),
    ("S&P Global Inc.", "United States", "Ratings & market data", "Listed", "SPGI", "NYSE"),
    ("Moody's Corporation", "United States", "Credit ratings", "Listed", "MCO", "NYSE"),
    ("MSCI Inc.", "United States", "Indices & analytics", "Listed", "MSCI", "NYSE"),
    ("FactSet Research Systems Inc.", "United States", "Financial data", "Listed", "FDS", "NYSE"),
    ("Intercontinental Exchange, Inc.", "United States", "Exchanges & data", "Listed", "ICE", "NYSE"),
    ("Fitch Ratings, Inc.", "United States", "Credit ratings", "Private", None, None),
    ("Visa Inc.", "United States", "Card network", "Listed", "V", "NYSE"),
    ("Mastercard Incorporated", "United States", "Card network", "Listed", "MA", "NYSE"),
    ("PayPal Holdings, Inc.", "United States", "Payments", "Listed", "PYPL", "NASDAQ"),
    ("Stripe, Inc.", "United States", "Payments platform", "Private", None, None),
    ("Adyen N.V.", "Netherlands", "Payments platform", "Listed", "ADYEN", "Euronext"),
    ("Fiserv, Inc.", "United States", "Payments & banking tech", "Listed", "FI", "NYSE"),
    ("Fidelity National Information Services (FIS)", "United States", "Banking technology", "Listed", "FIS", "NYSE"),
    ("Global Payments Inc.", "United States", "Merchant payments", "Listed", "GPN", "NYSE"),
    ("Worldpay (GTCR)", "United States", "Merchant acquiring", "Private", None, None),
    ("Temenos AG", "Switzerland", "Core banking software", "Listed", "TEMN", "SIX"),
    ("Finastra Group Holdings", "United Kingdom", "Financial software", "Private", None, None),
    ("Murex S.A.S.", "France", "Trading & risk software", "Private", None, None),
    ("Broadridge Financial Solutions", "United States", "Investor comms & tech", "Listed", "BR", "NYSE"),
    ("SS&C Technologies Holdings", "United States", "Fund admin & software", "Listed", "SSNC", "NASDAQ"),
    ("State Street Corporation", "United States", "Custody & admin", "Listed", "STT", "NYSE"),
    ("The Bank of New York Mellon", "United States", "Custody & admin", "Listed", "BK", "NYSE"),
    ("Northern Trust Corporation", "United States", "Asset servicing", "Listed", "NTRS", "NASDAQ"),
    ("Euroclear SA/NV", "Belgium", "Securities settlement", "Private", None, None),
    ("Clearstream (Deutsche Borse)", "Germany", "Securities settlement", "Listed", "DB1", "XETRA"),
    ("SWIFT SC", "Belgium", "Payments messaging", "Private", None, None),
    ("Accenture plc", "Ireland", "Consulting & IT services", "Listed", "ACN", "NYSE"),
    ("Deloitte Touche Tohmatsu Limited", "United Kingdom", "Audit & consulting", "Private", None, None),
    ("PricewaterhouseCoopers LLP", "United Kingdom", "Audit & consulting", "Private", None, None),
    ("Ernst & Young Global Limited", "United Kingdom", "Audit & consulting", "Private", None, None),
    ("KPMG International Limited", "Netherlands", "Audit & consulting", "Private", None, None),
    ("McKinsey & Company", "United States", "Management consulting", "Private", None, None),
    ("Boston Consulting Group", "United States", "Management consulting", "Private", None, None),
    ("Tata Consultancy Services Limited", "India", "IT services", "Listed", "TCS", "NSE"),
    ("Infosys Limited", "India", "IT services", "Listed", "INFY", "NSE"),
    ("Wipro Limited", "India", "IT services", "Listed", "WIPRO", "NSE"),
    ("Cognizant Technology Solutions", "United States", "IT services", "Listed", "CTSH", "NASDAQ"),
    ("Capgemini SE", "France", "Consulting & IT services", "Listed", "CAP", "Euronext"),
    ("Genpact Limited", "United States", "Business process services", "Listed", "G", "NYSE"),
    ("HCLTech (HCL Technologies)", "India", "IT services", "Listed", "HCLTECH", "NSE"),
    ("IBM Corporation", "United States", "IT services & software", "Listed", "IBM", "NYSE"),
    ("Equinix, Inc.", "United States", "Data centres", "Listed", "EQIX", "NASDAQ"),
    ("Digital Realty Trust, Inc.", "United States", "Data centres", "Listed", "DLR", "NYSE"),
    ("BT Group plc", "United Kingdom", "Telecommunications", "Listed", "BT.A", "LSE"),
    ("Vodafone Group Plc", "United Kingdom", "Telecommunications", "Listed", "VOD", "LSE"),
    ("Verizon Communications Inc.", "United States", "Telecommunications", "Listed", "VZ", "NYSE"),
    ("AT&T Inc.", "United States", "Telecommunications", "Listed", "T", "NYSE"),
    ("Colt Technology Services", "United Kingdom", "Network services", "Private", None, None),
    ("Orange Business (Orange S.A.)", "France", "Network services", "Listed", "ORA", "Euronext"),
    ("Automatic Data Processing (ADP)", "United States", "Payroll & HR", "Listed", "ADP", "NASDAQ"),
    ("Ceridian (Dayforce, Inc.)", "United States", "Payroll & HR", "Listed", "DAY", "NYSE"),
    ("SailPoint Technologies", "United States", "Identity governance", "Private", None, None),
    ("CyberArk Software Ltd.", "Israel", "Privileged access security", "Listed", "CYBR", "NASDAQ"),
    ("Proofpoint, Inc.", "United States", "Email security", "Private", None, None),
    ("Mimecast Limited", "United Kingdom", "Email security", "Private", None, None),
    ("Qualys, Inc.", "United States", "Vulnerability management", "Listed", "QLYS", "NASDAQ"),
    ("Tenable Holdings, Inc.", "United States", "Exposure management", "Listed", "TENB", "NASDAQ"),
    ("Veeam Software", "Switzerland", "Backup & recovery", "Private", None, None),
    ("ServiceTitan", "United States", "Field service SaaS", "Listed", "TTAN", "NASDAQ"),
    ("Refinitiv (LSEG)", "United Kingdom", "Market data", "Listed", "LSEG", "LSE"),
    ("Dun & Bradstreet Holdings", "United States", "Business data", "Listed", "DNB", "NYSE"),
    ("LexisNexis Risk Solutions (RELX)", "United Kingdom", "Risk data & screening", "Listed", "REL", "LSE"),
    ("Refinitiv World-Check (LSEG)", "United Kingdom", "Screening data", "Listed", "LSEG", "LSE"),
    ("ComplyAdvantage", "United Kingdom", "AML screening", "Private", None, None),
    ("Onfido (Entrust)", "United Kingdom", "Identity verification", "Private", None, None),
    ("Jumio Corporation", "United States", "Identity verification", "Private", None, None),
    ("DXC Technology Company", "United States", "IT services", "Listed", "DXC", "NYSE"),
    ("NTT DATA Group", "Japan", "IT services", "Listed", "9613", "TSE"),
    ("Fujitsu Limited", "Japan", "IT services", "Listed", "6702", "TSE"),
    ("Sopra Steria Group", "France", "IT services", "Listed", "SOP", "Euronext"),
    ("Nasdaq, Inc.", "United States", "Exchange technology", "Listed", "NDAQ", "NASDAQ"),
    ("Iron Mountain Incorporated", "United States", "Records management", "Listed", "IRM", "NYSE"),
    ("Thomson Reuters Corporation", "Canada", "Information services", "Listed", "TRI", "NYSE"),
    ("Genesys Cloud Services", "United States", "Contact centre SaaS", "Private", None, None),
    ("Pegasystems Inc.", "United States", "BPM & CRM software", "Listed", "PEGA", "NASDAQ"),
]

SECTORS_CAT = {  # supplier_category by broad type
    "Cloud infrastructure": "Strategic", "Cloud & software": "Strategic",
    "Market data & analytics": "Strategic", "Card network": "Strategic",
    "Core banking software": "Strategic", "Banking technology": "Strategic",
    "Custody & admin": "Strategic", "Securities settlement": "Strategic",
    "Payments messaging": "Strategic",
}
COUNTRIES_OPS = ["United Kingdom", "United States", "India", "Ireland", "Germany",
                 "Singapore", "Poland", "Philippines", "Netherlands", "Spain"]

OWNERS = ["susheem.grover", "hilda.osei", "silvia.romano", "fadi.haddad",
          "ikenna.okafor", "scott.mercer"]
ASSESSORS = ["assessor.one", "assessor.two", "assessor.three"]


def _today_offset(days):
    from datetime import date, timedelta
    return (date.today() + timedelta(days=days)).isoformat()


def main():
    if os.path.exists("bro_demo.db"):
        os.remove("bro_demo.db")
    # create_app seeds rbac + tables on the given URL
    create_app(DB)
    engine = create_engine(DB)
    s = Session(engine)

    # users for ownership / access demos
    from app.features.models_db import User, Role
    from app.features.models_db import hash_password
    roles = {r.key: r for r in s.query(Role).all()}
    def ensure_user(uname, rolekey):
        u = s.query(User).filter_by(username=uname).first()
        if not u and rolekey in roles:
            u = User(username=uname, password_hash=hash_password("demo"),
                     role_id=roles[rolekey].id, is_active=True)
            s.add(u)
    for o in OWNERS:
        ensure_user(o, "buyer")
    for a in ASSESSORS:
        ensure_user(a, "vrm")
    s.flush()

    # ---- build 100 vendors ----
    catalogue = list(VENDORS)
    while len(catalogue) < 100:
        catalogue.append(catalogue[len(catalogue) % len(VENDORS)])
    catalogue = catalogue[:100]

    # designate the 5 critical vendors (the most systemic dependencies)
    CRITICAL_NAMES = {"Amazon Web Services, Inc.", "Microsoft Corporation",
                      "Bloomberg L.P.", "Visa Inc.", "SWIFT SC"}

    vendor_ids = []
    crit_vendor_ids = []
    for i, (name, hq, sector, listing, ticker, exch) in enumerate(catalogue):
        tier = "Tier 1" if name in CRITICAL_NAMES else random.choice(
            ["Tier 1", "Tier 2", "Tier 2", "Tier 3", "Tier 3", "Tier 4"])
        cat = SECTORS_CAT.get(sector, random.choice(
            ["Strategic", "Operational", "Operational", "Tactical", "Commodity"]))
        v = RS.create_vendor(s, legal_name=name, tier=tier, created_via="demo-seed")
        vid = v.vendor_id
        vendor_ids.append(vid)
        spend = random.choice([45000, 120000, 380000, 950000, 2400000, 6800000, 14500000])
        spend_band = ("<£10k" if spend < 10000 else "£10k–£50k" if spend < 50000 else
                      "£50k–£250k" if spend < 250000 else "£250k–£1m" if spend < 1_000_000 else
                      "£1m–£5m" if spend < 5_000_000 else ">£5m")
        seg = ("Strategic partner" if name in CRITICAL_NAMES else
               random.choice(["Preferred", "Approved", "Approved", "Transactional"]))
        sub = ("Sole source / no alternative" if name in CRITICAL_NAMES else
               random.choice(["Hard to substitute", "Substitutable with effort",
                              "Substitutable with effort", "Easily substitutable"]))
        MS.update_vendor_master(s, vid, {
            "incorporation_country": hq, "operating_status": "Active",
            "legal_form": "Corporation", "listing_status": listing,
            "ticker": ticker or "", "exchange": exch or "",
            "supplier_category": cat, "segmentation": seg, "spend_band": spend_band,
            "substitutability": sub, "annual_spend": spend,
            "relationship_owner": random.choice(OWNERS),
            "sponsoring_bu": random.choice(["Markets Technology", "Operations", "Corporate Functions",
                                            "Data & Analytics", "Payments", "Risk & Compliance"]),
            "strategic_importance": "High" if name in CRITICAL_NAMES else random.choice(["High", "Medium", "Low"]),
            "service_countries": hq,
        }, include_bank=False)

        # ---- risk attributes across all domains ----
        # cyber
        certs = random.sample(["ISO 27001", "SOC 2 Type II", "PCI DSS", "Cyber Essentials Plus"],
                              k=random.randint(1, 3))
        MS.update_cyber(s, vid, {
            "certifications_json": __import__("json").dumps(certs),
            "assurance_status": random.choice(["Assured", "Assured", "In progress", "Gap identified"]),
            "external_rating": random.choice(["A", "A", "B", "B", "C"]),
            "external_rating_date": _today_offset(-random.randint(20, 200)),
            "pentest_recency": random.choice(["<6 months", "6-12 months", ">12 months"]),
            "breach_history_flag": random.random() < 0.12,
        })
        MS.update_privacy(s, vid, {
            "data_processing_role": random.choice(["Processor", "Processor", "Controller", "Joint controller"]),
            "dpa_status": random.choice(["Signed", "Signed", "In negotiation", "Not required"]),
            "cross_border": random.random() < 0.5,
        })
        MS.update_resilience(s, vid, {
            "bcp_status": random.choice(["Tested", "Tested", "Documented", "Not provided"]),
            "exit_plan_status": random.choice(["Documented", "Tested", "Not started"]),
            "rto": random.choice(["2h", "4h", "8h", "24h"]),
            "rpo": random.choice(["15m", "1h", "4h"]),
        })
        MS.update_esg(s, vid, {
            "esg_rating": random.choice(["AA", "A", "A", "BBB", "BB"]),
            "modern_slavery_status": random.choice(["Statement published", "Statement published", "Not applicable"]),
            "net_zero_commitment": random.random() < 0.6,
        })
        for stype in ("sanctions", "adverse_media", "pep"):
            hit = random.random() < (0.18 if stype == "adverse_media" else 0.05)
            MS.set_screening(s, vid, stype,
                             result="hit" if hit else "clear",
                             detail="Flagged for review" if hit else "No match",
                             screened_date=_today_offset(-random.randint(5, 120)),
                             next_due=_today_offset(random.randint(90, 300)))
        if random.random() < 0.7:
            MS.add_insurance(s, vid, {
                "policy_type": random.choice(["Cyber", "Professional indemnity", "Public liability"]),
                "coverage_limit": random.choice([5_000_000, 10_000_000, 25_000_000, 50_000_000]),
                "currency": "GBP", "insurer": random.choice(["AIG", "Allianz", "Chubb", "Zurich", "Beazley"]),
                "certificate_expiry": _today_offset(random.randint(30, 320)),
            })

        # reputation signal for some
        if random.random() < 0.25:
            MS.persist_reputation(s, vid, {"verdict": random.choice(["Watch", "Adverse", "Clear"]),
                                           "overall": random.randint(40, 90)})

        if name in CRITICAL_NAMES:
            crit_vendor_ids.append(vid)
    s.commit()

    # ---- 275 engagements distributed across vendors ----
    SERVICES = [
        ("Cloud hosting & compute", "ELEVATED"), ("Market data feed", "HIGH"),
        ("Payment processing", "HIGH"), ("Core banking platform", "HIGH"),
        ("Identity & access management", "ELEVATED"), ("Endpoint security", "ELEVATED"),
        ("Payroll & HR services", "ELEVATED"), ("E-signature", "MODERATE"),
        ("Collaboration & messaging", "MODERATE"), ("Data analytics platform", "ELEVATED"),
        ("Audit & assurance services", "MODERATE"), ("Managed IT services", "ELEVATED"),
        ("Network connectivity", "ELEVATED"), ("Data centre colocation", "HIGH"),
        ("AML/sanctions screening", "HIGH"), ("Custody & settlement", "HIGH"),
        ("Records management", "LOW"), ("Contact centre platform", "MODERATE"),
        ("Observability & monitoring", "MODERATE"), ("Consulting engagement", "LOW"),
    ]
    eng_ids = []
    crit_eng_targets = 7
    eng_per_vendor = {}
    # ensure each critical vendor gets several engagements
    for n in range(275):
        if n < len(crit_vendor_ids) * 3:
            vid = crit_vendor_ids[n % len(crit_vendor_ids)]
        else:
            vid = random.choice(vendor_ids)
        eng_per_vendor[vid] = eng_per_vendor.get(vid, 0) + 1
        svc, band = random.choice(SERVICES)
        title = f"{svc} #{eng_per_vendor[vid]}"
        owner = random.choice(OWNERS)
        e = RS.create_engagement(s, vendor_id=vid, title=title, owner_user=owner)
        eid = e.engagement_id
        e.inherent_band = band
        # residual usually one notch better unless no mitigation
        order = ["LOW", "MODERATE", "ELEVATED", "HIGH"]
        ri = max(0, order.index(band) - (1 if random.random() < 0.6 else 0))
        e.residual_band = order[ri]
        e.annual_value = random.choice([40000, 120000, 350000, 900000, 2200000, 5500000])
        e.currency = "GBP"
        e.status = random.choice(["Active", "Active", "Active", "Onboarding", "Renewal"])
        eng_ids.append((eid, vid, band))
        # delivery / receiving locations (geographic concentration: skew to a few hubs)
        MS.update_eng_ext(s, eid, {
            "delivery_location": random.choice(
                ["India", "India", "United States", "United States", "United Kingdom",
                 "Ireland", "Singapore", "Poland", "Philippines", "Germany"]),
            "receiving_location": "United Kingdom",
            "service_type": svc,
            "personal_data": random.random() < 0.5,
            "cross_border": random.random() < 0.5,
            "mission_critical": band in ("HIGH", "ELEVATED"),
        })
    s.commit()

    # ---- 7 critical engagements (designate via override) ----
    # Choose them from the 5 critical vendors' own engagements so the upward
    # escalation (critical engagement -> critical vendor) does NOT create new
    # critical vendors beyond the designated 5.
    crit_vendor_set = set(crit_vendor_ids)
    cand = [e for e in eng_ids if e[1] in crit_vendor_set]
    # prefer HIGH-band ones for realism, then fill from remaining critical-vendor engagements
    cand.sort(key=lambda e: 0 if e[2] == "HIGH" else 1)
    for eid, vid, band in cand[:crit_eng_targets]:
        MS.override_engagement_criticality(s, eid, True, "Business-critical service to the firm", "susheem.grover")
    s.commit()

    # ensure the 5 critical vendors carry the authoritative flag
    for vid in crit_vendor_ids:
        MS.override_vendor_criticality(s, vid, True, "Systemic dependency — designated critical", "susheem.grover")
    s.commit()

    # ---- contracts (MSA per critical + sample call-offs) ----
    for vid in crit_vendor_ids:
        msa = MS.create_contract(s, contract_type="MSA", vendor_id=vid,
                                 data={"title": "Master Services Agreement",
                                       "governing_law": "England & Wales"})
    for eid, vid, band in eng_ids[:120]:
        if random.random() < 0.6:
            MS.create_contract(s, contract_type="Contract", engagement_id=eid,
                               data={"title": "Service Agreement",
                                     "governing_law": random.choice(["England & Wales", "New York", "Ireland"])})
    s.commit()

    # ---- certificates (document-backed) for a realistic subset ----
    cert_bodies = {
        "ISO 27001": b"Certificate of Registration ISO 27001:2022 Issued by: BSI Group Valid 2024-04-01 to 2027-03-31 Scope: information security management",
        "SOC 2 Type II": b"SOC 2 Type II Report 2024-01-01 to 2024-12-31 Trust Services Criteria: Security, Availability, Confidentiality",
        "PCI DSS": b"PCI DSS Attestation of Compliance v4.0 Valid 2024-06-01 to 2025-05-31 Level 1 Service Provider",
        "Cyber Essentials Plus": b"Cyber Essentials Plus Certificate Valid 2024-09-01 to 2025-08-31 IASME certification body",
    }
    for vid in vendor_ids[:60]:
        for label in random.sample(list(cert_bodies), k=random.randint(1, 2)):
            raw = cert_bodies[label]
            doc = DOC.store_document(s, filename=f"{label.replace(' ', '_')}.txt",
                                     content_type="text/plain",
                                     data_b64=base64.b64encode(raw).decode(),
                                     vendor_id=vid, uploaded_by="assessor.one", purpose="certificate")
            ext = DOC.extract_certificate(s, doc)
            RS.create_artefact(s, vendor_id=vid, name=ext["name"], artefact_type=ext["artefact_type"],
                               expiry_date=ext.get("expiry_date"), received_via="upload",
                               issue_date=ext.get("issue_date"),
                               object_uri=f"/api/v2/documents/{doc.doc_id}")
    s.commit()

    # ---- assessments for a realistic subset of engagements ----
    n_asmt = 0
    for eid, vid, band in eng_ids:
        if random.random() < 0.45:
            order = ["LOW", "MODERATE", "ELEVATED", "HIGH"]
            ri = max(0, order.index(band) - (1 if random.random() < 0.6 else 0))
            rec = RS.create_assessment(s, engagement_id=eid, vendor_id=vid,
                                       engagement_owner=random.choice(OWNERS),
                                       inherent_band=band, residual_band=order[ri])
            rec.status = random.choice(["Completed", "Completed", "In-Progress", "Drafted"])
            if band in ("HIGH", "ELEVATED"):
                rec.assessor_user = random.choice(ASSESSORS)
            if rec.status == "Completed" and random.random() < 0.5:
                rec.outcome = random.choice(["Approved", "Approved with findings"])
            n_asmt += 1
    s.commit()

    # ---- performance scorecards (critical + a sample of others) ----
    perf_vendors = list(crit_vendor_ids) + random.sample(vendor_ids, 12)
    for vid in perf_vendors:
        for q in ("2025-Q3", "2025-Q4", "2026-Q1"):
            sc = MS.create_scorecard(s, vid, q)
            # set KPI scores
            from app.features import master_ext as MX
            from sqlalchemy import select as _sel
            for k in s.scalars(_sel(MX.ScorecardKPI).where(MX.ScorecardKPI.scorecard_id == sc.scorecard_id)).all():
                k.score = random.randint(2, 5)
            MS.compute_scorecard(s, sc.scorecard_id)
    s.commit()

    # ---- findings across vendors ----
    FIND = [
        ("Expired ISO 27001 certificate not yet renewed", "High", "cyber"),
        ("DPA outstanding for cross-border transfer", "Medium", "privacy"),
        ("BCP test overdue (>12 months)", "Medium", "resilience"),
        ("Adverse media match requires disposition", "High", "reputation"),
        ("SLA breaches in last quarter exceeded threshold", "Medium", "performance"),
        ("Sub-processor list not provided", "Low", "fourth_party"),
        ("Penetration test report older than 12 months", "Medium", "cyber"),
        ("Concentration risk: shared data centre region", "High", "concentration"),
    ]
    for vid in random.sample(vendor_ids, 40):
        title, sev, dom = random.choice(FIND)
        RS.create_finding(s, title=title, severity=sev, vendor_id=vid,
                          status=random.choice(["Open", "Open", "In remediation", "Closed"]),
                          source="Assessment", domain=dom)
    s.commit()

    # ---- fourth parties (shared dependencies => concentration hubs) ----
    SHARED_4P = [
        ("Amazon Web Services (eu-west-1)", 0.55),
        ("Microsoft Azure (West Europe)", 0.4),
        ("Akamai CDN", 0.25),
        ("Twilio messaging", 0.2),
        ("Equinix LD5 data centre", 0.3),
    ]
    for name, frac in SHARED_4P:
        users = random.sample(vendor_ids, int(len(vendor_ids) * frac))
        fp = RS.create_fourth_party(s, legal_name=name, vendor_ids=users)
        fp.concentration_flag = len(users) >= 20
    s.commit()

    # refresh risk profiles so Vendor 360 + management reconcile
    for vid in vendor_ids:
        try:
            MS.refresh_risk_profile(s, vid)
        except Exception:
            pass
    s.commit()

    # ---- report ----
    from app.features.registry_models import VendorRecord, EngagementRecord, AssessmentRecord, ArtefactRecord
    from app.features.master_ext import VendorScorecard
    nv = s.query(VendorRecord).count()
    ne = s.query(EngagementRecord).count()
    ncv = s.query(VendorRecord).filter(VendorRecord.is_critical == True).count()  # noqa: E712
    from app.features.master_ext import CriticalityDesignation
    from sqlalchemy import select as _sel2
    # latest designation per engagement
    crit_engs = set()
    for d in s.scalars(_sel2(CriticalityDesignation).where(
            CriticalityDesignation.subject_type == "engagement").order_by(
            CriticalityDesignation.id)).all():
        if d.is_critical:
            crit_engs.add(d.subject_id)
        else:
            crit_engs.discard(d.subject_id)
    nce = len(crit_engs)
    na = s.query(AssessmentRecord).count()
    nart = s.query(ArtefactRecord).count()
    nsc = s.query(VendorScorecard).count()
    print(f"Vendors: {nv} | Engagements: {ne} | Critical vendors: {ncv} | Critical engagements: {nce}")
    print(f"Assessments: {na} | Certificates: {nart} | Scorecards: {nsc}")
    s.close()


if __name__ == "__main__":
    main()
