"""
Registry models — the exhaustive data model for the TPRM platform.

New entities (all with human-readable auto-IDs):
  IdCounter          per-entity sequence source
  IndustryMaster     SIC-based industry list (Industry ID = name)
  MaterialGroupMaster UNSPSC-based material groups
  VendorGroup        group/parent company (GRP-xxxxx)
  VendorRecord       exhaustive vendor (VEN-xxxxxx) — many per group
  VendorIndustry     vendor <-> industry tags (many-to-many)
  ContactRecord      contacts for vendor/engagement (primary + backups)
  EngagementRecord   exhaustive engagement (ENG-xxxxxx) — many per vendor
  AssessmentRecord   assessment (ASM-xxxxxx) — mapped to engagement
  FindingRecord      finding (FND-xxxxxx)
  RemediationRecord  remediation plan (RMD-xxxxxx)
  FourthPartyRecord  fourth party (F4P-xxxxxx) — mirrors vendor, many-vendor link
  FourthPartyVendor  fourth-party <-> vendor link (many-to-many)
  ArtefactRecord     dated evidence / certificate (ART-xxxxxx)
  IssueRecord        issues log (ISS-xxxxxx)

These complement the original lightweight Vendor/EngagementRow (kept for the
existing tested endpoints); new endpoints use these richer records.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .models_db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IdCounter(Base):
    __tablename__ = "id_counters"
    entity: Mapped[str] = mapped_column(String, primary_key=True)
    last_seq: Mapped[int] = mapped_column(Integer, default=0)


class IndustryMaster(Base):
    __tablename__ = "industry_master"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    industry_id: Mapped[str] = mapped_column(String, unique=True)  # the name
    sic_code: Mapped[str] = mapped_column(String)
    division: Mapped[Optional[str]] = mapped_column(String, default=None)


class MaterialGroupMaster(Base):
    __tablename__ = "material_group_master"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_group_id: Mapped[str] = mapped_column(String, unique=True)  # the name
    unspsc_code: Mapped[str] = mapped_column(String)


class VendorGroup(Base):
    __tablename__ = "vendor_groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[str] = mapped_column(String, unique=True)   # GRP-xxxxx
    name: Mapped[str] = mapped_column(String)
    parent_company: Mapped[Optional[str]] = mapped_column(String, default=None)
    ai_assigned: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class VendorRecord(Base):
    __tablename__ = "vendor_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String, unique=True)   # VEN-xxxxxx (PK semantics)
    group_id: Mapped[Optional[str]] = mapped_column(String, default=None)  # GRP-xxxxx
    # identity
    legal_name: Mapped[str] = mapped_column(String)
    trading_name: Mapped[Optional[str]] = mapped_column(String, default=None)
    registration_number: Mapped[Optional[str]] = mapped_column(String, default=None)
    tax_id: Mapped[Optional[str]] = mapped_column(String, default=None)
    duns: Mapped[Optional[str]] = mapped_column(String, default=None)
    lei: Mapped[Optional[str]] = mapped_column(String, default=None)
    website: Mapped[Optional[str]] = mapped_column(String, default=None)
    # corporate
    incorporation_country: Mapped[Optional[str]] = mapped_column(String, default=None)
    incorporation_date: Mapped[Optional[str]] = mapped_column(String, default=None)
    legal_form: Mapped[Optional[str]] = mapped_column(String, default=None)
    listing_status: Mapped[Optional[str]] = mapped_column(String, default=None)  # public/private
    ticker: Mapped[Optional[str]] = mapped_column(String, default=None)
    ultimate_parent: Mapped[Optional[str]] = mapped_column(String, default=None)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    annual_revenue: Mapped[Optional[float]] = mapped_column(Float, default=None)
    revenue_currency: Mapped[Optional[str]] = mapped_column(String, default=None)
    # addresses
    hq_address: Mapped[Optional[str]] = mapped_column(Text, default=None)
    hq_country: Mapped[Optional[str]] = mapped_column(String, default=None)
    operating_countries: Mapped[Optional[str]] = mapped_column(Text, default=None)  # csv
    # classification / risk
    tier: Mapped[str] = mapped_column(String, default="Tier 3")
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    criticality_reason: Mapped[Optional[str]] = mapped_column(Text, default=None)
    # banking / tax
    bank_name: Mapped[Optional[str]] = mapped_column(String, default=None)
    bank_account: Mapped[Optional[str]] = mapped_column(String, default=None)
    payment_terms: Mapped[Optional[str]] = mapped_column(String, default=None)
    # lifecycle / status
    status: Mapped[str] = mapped_column(String, default="Active")  # Active/Inactive/Onboarding/Offboarded
    onboarded_date: Mapped[Optional[str]] = mapped_column(String, default=None)
    # procurement link
    procurement_ref: Mapped[Optional[str]] = mapped_column(String, default=None)
    source_system: Mapped[Optional[str]] = mapped_column(String, default=None)
    # cross-link if this vendor is also catalogued as a fourth party
    fourth_party_id: Mapped[Optional[str]] = mapped_column(String, default=None)
    created_via: Mapped[str] = mapped_column(String, default="button")  # button/chat/procurement
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class VendorIndustry(Base):
    __tablename__ = "vendor_industries"
    __table_args__ = (UniqueConstraint("vendor_id", "industry_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String)
    industry_id: Mapped[str] = mapped_column(String)  # name from IndustryMaster


class ContactRecord(Base):
    __tablename__ = "contact_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_type: Mapped[str] = mapped_column(String)   # vendor / engagement / fourth_party
    owner_id: Mapped[str] = mapped_column(String)     # VEN-/ENG-/F4P-
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String, default=None)
    phone_country_code: Mapped[Optional[str]] = mapped_column(String, default=None)  # +44
    phone_number: Mapped[Optional[str]] = mapped_column(String, default=None)
    designation: Mapped[Optional[str]] = mapped_column(String, default=None)
    country: Mapped[Optional[str]] = mapped_column(String, default=None)
    mailing_address: Mapped[Optional[str]] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class EngagementRecord(Base):
    __tablename__ = "engagement_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String, unique=True)  # ENG-xxxxxx
    vendor_id: Mapped[str] = mapped_column(String)                   # many per vendor
    title: Mapped[str] = mapped_column(String)
    service_description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    material_group_id: Mapped[Optional[str]] = mapped_column(String, default=None)  # UNSPSC name
    deployment_model: Mapped[Optional[str]] = mapped_column(String, default=None)
    business_unit: Mapped[Optional[str]] = mapped_column(String, default=None)
    contract_id: Mapped[Optional[str]] = mapped_column(String, default=None)        # CON-xxxxxx
    assessment_id: Mapped[Optional[str]] = mapped_column(String, default=None)      # ASM-xxxxxx (latest)
    annual_value: Mapped[Optional[float]] = mapped_column(Float, default=None)
    currency: Mapped[Optional[str]] = mapped_column(String, default=None)
    start_date: Mapped[Optional[str]] = mapped_column(String, default=None)
    end_date: Mapped[Optional[str]] = mapped_column(String, default=None)
    # risk rollups
    inherent_band: Mapped[Optional[str]] = mapped_column(String, default=None)
    inherent_score: Mapped[Optional[float]] = mapped_column(Float, default=None)
    residual_band: Mapped[Optional[str]] = mapped_column(String, default=None)
    residual_score: Mapped[Optional[float]] = mapped_column(Float, default=None)
    open_actions: Mapped[int] = mapped_column(Integer, default=0)  # derived rollup
    # status
    status: Mapped[str] = mapped_column(String, default="Active")  # Active/Inactive/Overdue
    stage: Mapped[str] = mapped_column(String, default="sourcing")
    owner_user: Mapped[Optional[str]] = mapped_column(String, default=None)  # engagement owner
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AssessmentRecord(Base):
    __tablename__ = "assessment_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[str] = mapped_column(String, unique=True)  # ASM-xxxxxx
    engagement_id: Mapped[str] = mapped_column(String)               # mapped to engagement
    vendor_id: Mapped[Optional[str]] = mapped_column(String, default=None)
    session_id: Mapped[Optional[int]] = mapped_column(Integer, default=None)  # chat session
    status: Mapped[str] = mapped_column(String, default="Drafted")  # Drafted/In-Progress/Completed/Approved/Recalled
    # structured capture
    inherent_band: Mapped[Optional[str]] = mapped_column(String, default=None)
    residual_band: Mapped[Optional[str]] = mapped_column(String, default=None)
    outcome: Mapped[Optional[str]] = mapped_column(String, default=None)  # Approved / Approved with findings
    structured_json: Mapped[str] = mapped_column(Text, default="{}")      # per-stage structured data
    # ownership / access
    engagement_owner: Mapped[Optional[str]] = mapped_column(String, default=None)
    spoc_name: Mapped[Optional[str]] = mapped_column(String, default=None)
    spoc_email: Mapped[Optional[str]] = mapped_column(String, default=None)
    spoc_office: Mapped[Optional[str]] = mapped_column(String, default=None)
    spoc_user: Mapped[Optional[str]] = mapped_column(String, default=None)  # username for access
    # assessor (high inherent)
    assessor_user: Mapped[Optional[str]] = mapped_column(String, default=None)
    assessor_signed_off: Mapped[bool] = mapped_column(Boolean, default=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)  # hard-lock on Approved
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class FindingRecord(Base):
    __tablename__ = "finding_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    finding_id: Mapped[str] = mapped_column(String, unique=True)  # FND-xxxxxx
    assessment_id: Mapped[Optional[str]] = mapped_column(String, default=None)
    engagement_id: Mapped[Optional[str]] = mapped_column(String, default=None)
    vendor_id: Mapped[Optional[str]] = mapped_column(String, default=None)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    domain: Mapped[Optional[str]] = mapped_column(String, default=None)
    severity: Mapped[str] = mapped_column(String, default="Medium")  # Critical/High/Medium/Low
    source: Mapped[str] = mapped_column(String, default="Assessor")   # AI / Assessor
    status: Mapped[str] = mapped_column(String, default="Open")       # Open/In Remediation/Closed
    raised_by: Mapped[Optional[str]] = mapped_column(String, default=None)
    due_date: Mapped[Optional[str]] = mapped_column(String, default=None)
    remediation_id: Mapped[Optional[str]] = mapped_column(String, default=None)
    closed_date: Mapped[Optional[str]] = mapped_column(String, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class RemediationRecord(Base):
    __tablename__ = "remediation_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    remediation_id: Mapped[str] = mapped_column(String, unique=True)  # RMD-xxxxxx
    finding_id: Mapped[str] = mapped_column(String)
    plan: Mapped[str] = mapped_column(Text)
    owner: Mapped[Optional[str]] = mapped_column(String, default=None)
    target_date: Mapped[Optional[str]] = mapped_column(String, default=None)
    milestones_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String, default="Planned")  # Planned/In Progress/Complete/Verified
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    evidence: Mapped[Optional[str]] = mapped_column(Text, default=None)
    completed_date: Mapped[Optional[str]] = mapped_column(String, default=None)
    verified_by: Mapped[Optional[str]] = mapped_column(String, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class FourthPartyRecord(Base):
    __tablename__ = "fourth_party_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fourth_party_id: Mapped[str] = mapped_column(String, unique=True)  # F4P-xxxxxx
    legal_name: Mapped[str] = mapped_column(String)
    service_provided: Mapped[Optional[str]] = mapped_column(String, default=None)
    hq_country: Mapped[Optional[str]] = mapped_column(String, default=None)
    registration_number: Mapped[Optional[str]] = mapped_column(String, default=None)
    website: Mapped[Optional[str]] = mapped_column(String, default=None)
    listing_status: Mapped[Optional[str]] = mapped_column(String, default=None)
    concentration_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    # if this fourth party is ALSO a vendor in our system:
    vendor_id: Mapped[Optional[str]] = mapped_column(String, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class FourthPartyVendor(Base):
    __tablename__ = "fourth_party_vendors"
    __table_args__ = (UniqueConstraint("fourth_party_id", "vendor_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fourth_party_id: Mapped[str] = mapped_column(String)
    vendor_id: Mapped[str] = mapped_column(String)


class ArtefactRecord(Base):
    __tablename__ = "artefact_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artefact_id: Mapped[str] = mapped_column(String, unique=True)  # ART-xxxxxx
    vendor_id: Mapped[str] = mapped_column(String)                 # mapped to vendor
    engagement_id: Mapped[Optional[str]] = mapped_column(String, default=None)
    name: Mapped[str] = mapped_column(String)
    artefact_type: Mapped[str] = mapped_column(String, default="certificate")  # soc2/iso/cert/other
    is_dated: Mapped[bool] = mapped_column(Boolean, default=True)  # carries validity
    issue_date: Mapped[Optional[str]] = mapped_column(String, default=None)
    expiry_date: Mapped[Optional[str]] = mapped_column(String, default=None)
    status: Mapped[str] = mapped_column(String, default="Valid")  # Valid/Expiring/Expired
    object_uri: Mapped[Optional[str]] = mapped_column(String, default=None)
    supersedes: Mapped[Optional[str]] = mapped_column(String, default=None)  # prior artefact_id
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    received_via: Mapped[str] = mapped_column(String, default="upload")  # upload/chat/email
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class IssueRecord(Base):
    __tablename__ = "issue_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[str] = mapped_column(String, unique=True)  # ISS-xxxxxx
    vendor_id: Mapped[str] = mapped_column(String)
    vendor_name: Mapped[str] = mapped_column(String)
    artefact_id: Mapped[Optional[str]] = mapped_column(String, default=None)
    kind: Mapped[str] = mapped_column(String, default="expired_certificate")
    detail: Mapped[Optional[str]] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String, default="Open")  # Open/Closed
    closed_reason: Mapped[Optional[str]] = mapped_column(String, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)


class FinMonitorRecord(Base):
    """A vendor empanelled for periodic financial-health monitoring sweeps."""
    __tablename__ = "fin_monitor_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[Optional[str]] = mapped_column(String, default=None)  # VEN- or None for "Other"
    entity_name: Mapped[str] = mapped_column(String)
    last_result: Mapped[Optional[str]] = mapped_column(Text, default=None)
    last_signal: Mapped[Optional[str]] = mapped_column(String, default=None)  # ok/watch/distress
    last_swept: Mapped[Optional[str]] = mapped_column(String, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
