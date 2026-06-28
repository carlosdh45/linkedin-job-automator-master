"""
Local CSV import service for BD OS companies, prospects, and signals.
No external API calls. All data stays on disk.
"""
import csv
import io
from datetime import date
from typing import List, Tuple

from backend.models.bd import (
    BDCompany, BDProspect, BDSignal,
    BDImportResult, BDImportPreviewRow,
)
from backend.services.bd_company_store import list_companies, create_company
from backend.services.bd_prospect_store import list_prospects, create_prospect
from backend.services.bd_signal_store import list_signals, create_signal
from backend.services.bd_scoring import compute_opportunity_score

MAX_FILE_BYTES = 500_000  # 500 KB

# Signal type normalization
_SIGNAL_TYPE_MAP = {
    "funding": "funding",
    "hiring": "hiring",
    "expansion": "growth",
    "growth": "growth",
    "leadership_change": "leadership_change",
    "leadership change": "leadership_change",
    "technology_change": "tech_change",
    "tech_change": "tech_change",
    "tech change": "tech_change",
    "operational_pain": "pain_point",
    "pain_point": "pain_point",
    "pain point": "pain_point",
    "partnership": "growth",
    "market_event": "other",
    "market event": "other",
    "compliance_pressure": "pain_point",
    "compliance pressure": "pain_point",
    "competitive": "competitive",
    "custom": "other",
    "other": "other",
}

# Seniority normalization
_SENIORITY_MAP = {
    "ceo": "ceo", "chief executive officer": "ceo",
    "founder": "ceo", "co-founder": "ceo", "cofounder": "ceo",
    "cto": "cto", "chief technology officer": "cto",
    "coo": "coo", "chief operating officer": "coo",
    "cfo": "cfo", "cso": "cso", "cmo": "cmo", "cpo": "cpo",
    "vp": "vp", "vice president": "vp", "svp": "vp", "evp": "vp",
    "director": "director", "dir": "director",
    "manager": "manager", "mgr": "manager",
    "head": "head",
    "partner": "partner", "managing partner": "partner",
    "principal": "principal",
    "lead": "lead",
    "senior": "senior", "sr": "senior",
}


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _parse_csv(content: bytes) -> Tuple[List[dict], List[str]]:
    """Decode and parse CSV bytes → list of lowercase-key row dicts + errors."""
    if len(content) > MAX_FILE_BYTES:
        return [], [f"File exceeds {MAX_FILE_BYTES // 1000}KB limit"]
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1", errors="replace")

    reader = csv.DictReader(io.StringIO(text))
    rows: List[dict] = []
    errors: List[str] = []
    if reader.fieldnames is None:
        return [], ["CSV file is empty or has no header row"]
    try:
        for row in reader:
            rows.append({k.strip().lower(): (v or "").strip() for k, v in row.items()})
    except Exception as exc:
        errors.append(f"CSV parse error: {exc}")
    return rows, errors


def _normalize(s: str) -> str:
    return s.strip().lower()


def _check_columns(headers: set, required: set) -> List[str]:
    missing = required - headers
    if missing:
        return [f"Missing required column(s): {', '.join(sorted(missing))}"]
    return []


def _strength_to_score(strength: str) -> int:
    """Convert strength text/number to relevance_score 0-100."""
    s = strength.strip().lower()
    if s.isdigit():
        return max(0, min(100, int(s)))
    return {"critical": 90, "high": 75, "medium": 50, "low": 25}.get(s, 50)


def _get_or_create_company(
    name: str, company_path: str, existing: List[BDCompany]
) -> Tuple[str, List[BDCompany]]:
    """Return (company_id, updated_existing_list). Creates placeholder if not found."""
    norm = _normalize(name)
    for c in existing:
        if _normalize(c.name) == norm:
            return c.id, existing
    # Create minimal placeholder
    score, label, _ = compute_opportunity_score(
        icp_match=False, pain_point_count=0, signal_count=0,
        company_size=None, prospect_seniority=None,
        days_since_last_signal=None, existing_relationship=False,
    )
    new_co = create_company(company_path, {
        "name": name,
        "status": "identified",
        "opportunity_score": score,
        "score_label": label,
    })
    existing.append(new_co)
    return new_co.id, existing


# ── Companies ─────────────────────────────────────────────────────────────────

COMPANY_REQUIRED = {"name"}
COMPANY_OPTIONAL = {"domain", "industry", "size", "region", "description",
                    "website", "linkedin_url", "icp_notes", "tags"}

COMPANIES_TEMPLATE = (
    "name,domain,industry,size,region,description,website,linkedin_url,icp_notes,tags\n"
    "Acme Corp,acme.com,SaaS,100-500,US,Enterprise workflow automation,"
    "https://acme.com,https://linkedin.com/company/acme,Strong ICP match,automation;workflow\n"
    "Bright Logistics,brightlogistics.io,Logistics,50-200,US,Last-mile delivery operations,"
    "https://brightlogistics.io,,Logistics ops pain,logistics;operations\n"
)


def import_companies_csv(
    content: bytes, company_path: str, *, dry_run: bool = True
) -> BDImportResult:
    rows, parse_errors = _parse_csv(content)
    if parse_errors:
        return BDImportResult(
            import_type="companies", dry_run=dry_run,
            imported_count=0, skipped_count=0, duplicate_count=0,
            error_count=len(parse_errors), errors=parse_errors,
        )

    if not rows:
        return BDImportResult(
            import_type="companies", dry_run=dry_run,
            imported_count=0, skipped_count=0, duplicate_count=0,
            error_count=1, errors=["CSV has no data rows"],
        )

    col_errors = _check_columns(set(rows[0].keys()), COMPANY_REQUIRED)
    if col_errors:
        return BDImportResult(
            import_type="companies", dry_run=dry_run,
            imported_count=0, skipped_count=0, duplicate_count=0,
            error_count=len(col_errors), errors=col_errors,
        )

    existing = list_companies(company_path)
    existing_names = {_normalize(c.name) for c in existing}
    existing_domains = {_normalize(c.domain) for c in existing if c.domain}

    imported = skipped = duplicates = 0
    errors: List[str] = []
    preview: List[BDImportPreviewRow] = []

    for i, row in enumerate(rows, start=2):
        name = row.get("name", "")
        if not name:
            msg = f"Row {i}: name is required"
            errors.append(msg)
            skipped += 1
            preview.append(BDImportPreviewRow(row=i, data=row, status="error", message=msg))
            continue

        domain = row.get("domain", "")
        norm_name = _normalize(name)
        norm_domain = _normalize(domain) if domain else ""

        if norm_name in existing_names or (norm_domain and norm_domain in existing_domains):
            duplicates += 1
            preview.append(BDImportPreviewRow(
                row=i, data=row, status="duplicate",
                message=f"Company '{name}' already exists (matched by name or domain)",
            ))
            continue

        # Build notes from rich columns
        notes_parts = []
        if row.get("description"):
            notes_parts.append(row["description"])
        if row.get("region"):
            notes_parts.append(f"Region: {row['region']}")
        if row.get("website"):
            notes_parts.append(f"Website: {row['website']}")
        if row.get("linkedin_url"):
            notes_parts.append(f"LinkedIn: {row['linkedin_url']}")
        if row.get("icp_notes"):
            notes_parts.append(f"ICP notes: {row['icp_notes']}")
        if row.get("tags"):
            notes_parts.append(f"Tags: {row['tags']}")

        score, label, _ = compute_opportunity_score(
            icp_match=False, pain_point_count=0, signal_count=0,
            company_size=row.get("size") or None,
            prospect_seniority=None, days_since_last_signal=None,
            existing_relationship=False,
        )
        data = {
            "name": name,
            "domain": domain or None,
            "industry": row.get("industry") or None,
            "size_estimate": row.get("size") or None,
            "pain_points": [],
            "tech_signals": [],
            "icp_match": False,
            "status": "identified",
            "notes": "\n".join(notes_parts),
            "opportunity_score": score,
            "score_label": label,
            "source": "imported",
        }

        if not dry_run:
            create_company(company_path, data)
            existing_names.add(norm_name)
            if norm_domain:
                existing_domains.add(norm_domain)

        imported += 1
        preview.append(BDImportPreviewRow(
            row=i, data=row, status="ok",
            message=f"{'Would import' if dry_run else 'Imported'}: {name}",
        ))

    return BDImportResult(
        import_type="companies", dry_run=dry_run,
        imported_count=imported, skipped_count=skipped,
        duplicate_count=duplicates, error_count=len(errors),
        errors=errors, preview_rows=preview,
    )


# ── Prospects ─────────────────────────────────────────────────────────────────

PROSPECT_REQUIRED = {"full_name", "company_name", "role"}
PROSPECT_OPTIONAL = {"seniority", "email", "linkedin_url",
                     "company_id", "department", "region", "notes", "relationship_status"}

PROSPECTS_TEMPLATE = (
    "full_name,company_name,role,seniority,email,linkedin_url,department,region,notes,relationship_status\n"
    "Alex Rivera,Acme Corp,VP of Engineering,vp,alex@acme.com,"
    "https://linkedin.com/in/alexrivera,Engineering,US,Met at SaaStr 2024,warm\n"
    "Morgan Chen,Bright Logistics,COO,coo,morgan@brightlogistics.io,"
    "https://linkedin.com/in/morganchen,Operations,US,,cold\n"
)


def import_prospects_csv(
    content: bytes, prospect_path: str, company_path: str, *, dry_run: bool = True
) -> BDImportResult:
    rows, parse_errors = _parse_csv(content)
    if parse_errors:
        return BDImportResult(
            import_type="prospects", dry_run=dry_run,
            imported_count=0, skipped_count=0, duplicate_count=0,
            error_count=len(parse_errors), errors=parse_errors,
        )

    if not rows:
        return BDImportResult(
            import_type="prospects", dry_run=dry_run,
            imported_count=0, skipped_count=0, duplicate_count=0,
            error_count=1, errors=["CSV has no data rows"],
        )

    col_errors = _check_columns(set(rows[0].keys()), PROSPECT_REQUIRED)
    if col_errors:
        return BDImportResult(
            import_type="prospects", dry_run=dry_run,
            imported_count=0, skipped_count=0, duplicate_count=0,
            error_count=len(col_errors), errors=col_errors,
        )

    existing_prospects = list_prospects(prospect_path)
    existing_companies = list_companies(company_path)

    # Duplicate key: (norm_name, norm_company_name)
    existing_keys = {
        (_normalize(p.name), _normalize(p.company_name))
        for p in existing_prospects
    }

    imported = skipped = duplicates = 0
    errors: List[str] = []
    preview: List[BDImportPreviewRow] = []

    for i, row in enumerate(rows, start=2):
        full_name = row.get("full_name", "")
        company_name = row.get("company_name", "")
        role = row.get("role", "")

        if not full_name or not company_name:
            msg = f"Row {i}: full_name and company_name are required"
            errors.append(msg)
            skipped += 1
            preview.append(BDImportPreviewRow(row=i, data=row, status="error", message=msg))
            continue

        key = (_normalize(full_name), _normalize(company_name))
        if key in existing_keys:
            duplicates += 1
            preview.append(BDImportPreviewRow(
                row=i, data=row, status="duplicate",
                message=f"Prospect '{full_name}' at '{company_name}' already exists",
            ))
            continue

        # Seniority normalization
        raw_seniority = row.get("seniority", "").strip().lower()
        seniority = _SENIORITY_MAP.get(raw_seniority, raw_seniority or None)

        # Build notes
        notes_parts = []
        if row.get("email"):
            notes_parts.append(f"Email: {row['email']}")
        if row.get("department"):
            notes_parts.append(f"Department: {row['department']}")
        if row.get("region"):
            notes_parts.append(f"Region: {row['region']}")
        if row.get("relationship_status"):
            notes_parts.append(f"Relationship: {row['relationship_status']}")
        if row.get("notes"):
            notes_parts.append(row["notes"])

        # Get or create company
        company_id = row.get("company_id", "").strip()
        if not company_id:
            if not dry_run:
                company_id, existing_companies = _get_or_create_company(
                    company_name, company_path, existing_companies
                )
            else:
                # For dry run: find company or use placeholder
                norm_co = _normalize(company_name)
                match = next(
                    (c for c in existing_companies if _normalize(c.name) == norm_co), None
                )
                company_id = match.id if match else f"placeholder-{norm_co}"

        data = {
            "company_id": company_id,
            "company_name": company_name,
            "name": full_name,
            "title": role or None,
            "seniority": seniority,
            "linkedin_url": row.get("linkedin_url") or None,
            "pain_point_count": 0,
            "signal_count": 0,
            "status": "identified",
            "notes": "\n".join(notes_parts),
            "source": "imported",
        }

        if not dry_run:
            create_prospect(prospect_path, data)
            existing_keys.add(key)

        imported += 1
        preview.append(BDImportPreviewRow(
            row=i, data=row, status="ok",
            message=f"{'Would import' if dry_run else 'Imported'}: {full_name} @ {company_name}",
        ))

    return BDImportResult(
        import_type="prospects", dry_run=dry_run,
        imported_count=imported, skipped_count=skipped,
        duplicate_count=duplicates, error_count=len(errors),
        errors=errors, preview_rows=preview,
    )


# ── Signals ───────────────────────────────────────────────────────────────────

SIGNAL_REQUIRED = {"company_name", "signal_type", "description"}
SIGNAL_OPTIONAL = {"company_id", "title", "strength", "source", "observed_at", "url", "urgency", "notes"}

SIGNALS_TEMPLATE = (
    "company_name,signal_type,description,strength,source,observed_at,title,url,notes\n"
    "Acme Corp,hiring,Posting 3 senior DevOps roles — signals deployment velocity pressure,"
    "75,Job board,2026-06-25,DevOps hiring spike,https://acme.com/jobs,\n"
    "Bright Logistics,leadership_change,New COO appointed after founder transition,"
    "80,LinkedIn,2026-06-20,COO leadership change,,First 90 days — good entry window\n"
)


def import_signals_csv(
    content: bytes, signal_path: str, company_path: str, *, dry_run: bool = True
) -> BDImportResult:
    rows, parse_errors = _parse_csv(content)
    if parse_errors:
        return BDImportResult(
            import_type="signals", dry_run=dry_run,
            imported_count=0, skipped_count=0, duplicate_count=0,
            error_count=len(parse_errors), errors=parse_errors,
        )

    if not rows:
        return BDImportResult(
            import_type="signals", dry_run=dry_run,
            imported_count=0, skipped_count=0, duplicate_count=0,
            error_count=1, errors=["CSV has no data rows"],
        )

    col_errors = _check_columns(set(rows[0].keys()), SIGNAL_REQUIRED)
    if col_errors:
        return BDImportResult(
            import_type="signals", dry_run=dry_run,
            imported_count=0, skipped_count=0, duplicate_count=0,
            error_count=len(col_errors), errors=col_errors,
        )

    existing_signals = list_signals(signal_path)
    existing_companies = list_companies(company_path)

    # Duplicate key: (norm_company_name, norm_signal_type, detected_at)
    existing_keys = {
        (_normalize(s.company_name), s.signal_type, s.detected_at)
        for s in existing_signals
    }

    imported = skipped = duplicates = 0
    errors: List[str] = []
    preview: List[BDImportPreviewRow] = []

    for i, row in enumerate(rows, start=2):
        company_name = row.get("company_name", "")
        signal_type_raw = row.get("signal_type", "")
        description = row.get("description", "")

        if not company_name or not signal_type_raw or not description:
            msg = f"Row {i}: company_name, signal_type, and description are required"
            errors.append(msg)
            skipped += 1
            preview.append(BDImportPreviewRow(row=i, data=row, status="error", message=msg))
            continue

        signal_type = _SIGNAL_TYPE_MAP.get(_normalize(signal_type_raw), "other")
        detected_at = row.get("observed_at", "").strip() or date.today().isoformat()

        key = (_normalize(company_name), signal_type, detected_at or "")
        if key in existing_keys:
            duplicates += 1
            preview.append(BDImportPreviewRow(
                row=i, data=row, status="duplicate",
                message=f"Signal for '{company_name}' ({signal_type}) on {detected_at} already exists",
            ))
            continue

        # Build summary from title + description
        title = row.get("title", "").strip()
        summary_parts = []
        if title:
            summary_parts.append(title)
        summary_parts.append(description)
        if row.get("notes"):
            summary_parts.append(row["notes"])
        summary = " — ".join(summary_parts) if title else description

        source = row.get("source", "").strip()
        if row.get("url"):
            source = f"{source} ({row['url']})" if source else row["url"]

        relevance_score = _strength_to_score(row.get("strength", "50"))

        # Get or create company
        company_id = row.get("company_id", "").strip()
        if not company_id:
            if not dry_run:
                company_id, existing_companies = _get_or_create_company(
                    company_name, company_path, existing_companies
                )
            else:
                norm_co = _normalize(company_name)
                match = next(
                    (c for c in existing_companies if _normalize(c.name) == norm_co), None
                )
                company_id = match.id if match else f"placeholder-{norm_co}"

        data = {
            "company_id": company_id,
            "company_name": company_name,
            "signal_type": signal_type,
            "summary": summary,
            "source": source or None,
            "relevance_score": relevance_score,
            "detected_at": detected_at,
            "reviewed": False,
            "data_source": "imported",
        }

        if not dry_run:
            create_signal(signal_path, data)
            existing_keys.add(key)

        imported += 1
        preview.append(BDImportPreviewRow(
            row=i, data=row, status="ok",
            message=f"{'Would import' if dry_run else 'Imported'}: {signal_type} signal for {company_name}",
        ))

    return BDImportResult(
        import_type="signals", dry_run=dry_run,
        imported_count=imported, skipped_count=skipped,
        duplicate_count=duplicates, error_count=len(errors),
        errors=errors, preview_rows=preview,
    )
