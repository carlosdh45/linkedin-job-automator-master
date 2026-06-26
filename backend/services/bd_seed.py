"""
BD OS demo seed data. Local only. No external API calls.
"""
from backend.models.bd import (
    BDCompany, BDProspect, BDSignal, BDPainPoint,
    BDOpportunity, BDDealPacket, BDChecklistItem, BDOutreachDraft,
)
from backend.services import (
    bd_company_store, bd_prospect_store, bd_signal_store,
    bd_pain_point_store, bd_opportunity_store, bd_deal_packet_store,
    bd_outreach_store,
)
from backend.services.bd_scoring import compute_opportunity_score


_SAFETY_NOTICE = "\n\n---\nPrepared for manual review. DobryBot does not send automatically."


def _make_checklist(*items: str) -> list[BDChecklistItem]:
    return [BDChecklistItem(text=t, done=False) for t in items]


def seed_bd_demo(
    company_path: str,
    prospect_path: str,
    signal_path: str,
    pain_point_path: str,
    opportunity_path: str,
    deal_packet_path: str,
    outreach_path: str,
) -> dict:
    # ── Companies ─────────────────────────────────────────────────────────────
    companies = [
        BDCompany(
            name="Meridian Labs",
            domain="meridianlabs.io",
            industry="DevTools / SaaS",
            size_estimate="50–200",
            tech_signals=["GitHub Actions", "Kubernetes", "Python"],
            pain_points=["Manual deployment pipeline", "Slow release cycles"],
            opportunity_score=87,
            score_label="hot",
            icp_match=True,
            status="researched",
        ),
        BDCompany(
            name="Vantage Capital",
            domain="vantagecap.com",
            industry="FinTech",
            size_estimate="200–500",
            tech_signals=["AWS", "Postgres", "Python"],
            pain_points=["Compliance reporting overhead", "Data reconciliation delays", "Manual audit prep"],
            opportunity_score=80,
            score_label="hot",
            icp_match=True,
            status="qualified",
        ),
        BDCompany(
            name="Stratos Engineering",
            domain="stratos.build",
            industry="Infrastructure",
            size_estimate="100–300",
            tech_signals=["Jenkins", "GitHub Actions", "Terraform"],
            pain_points=["Developer onboarding velocity", "Tech debt accumulation"],
            opportunity_score=71,
            score_label="warm",
            icp_match=True,
            status="researched",
        ),
        BDCompany(
            name="Nexus Health",
            domain="nexushealth.co",
            industry="HealthTech",
            size_estimate="50–150",
            tech_signals=["AWS", "HIPAA tooling"],
            pain_points=["HIPAA audit prep", "Legacy system integrations"],
            opportunity_score=65,
            score_label="warm",
            icp_match=True,
            status="identified",
        ),
        BDCompany(
            name="Prism Analytics",
            domain="prismanalytics.io",
            industry="Data / Analytics",
            size_estimate="20–80",
            tech_signals=["Airflow", "dbt", "Snowflake"],
            pain_points=["Data pipeline reliability"],
            opportunity_score=52,
            score_label="cold",
            icp_match=False,
            status="identified",
        ),
        BDCompany(
            name="Cascade Retail",
            domain="cascaderetail.com",
            industry="E-commerce",
            size_estimate="500+",
            tech_signals=["Shopify", "Node.js"],
            pain_points=["Inventory sync delays", "Cart abandonment analytics"],
            opportunity_score=44,
            score_label="cold",
            icp_match=False,
            status="identified",
        ),
    ]
    bd_company_store.replace_all(company_path, companies)

    co_by_name = {c.name: c for c in companies}

    # ── Prospects ─────────────────────────────────────────────────────────────
    prospects = [
        BDProspect(
            company_id=co_by_name["Meridian Labs"].id,
            company_name="Meridian Labs",
            name="Alex Rivera",
            title="VP of Engineering",
            seniority="vp",
            pain_point_count=2,
            signal_count=4,
            opportunity_score=87,
            score_label="hot",
            recommended_angle="Deployment automation — they posted 3 DevOps roles last month",
            status="researched",
        ),
        BDProspect(
            company_id=co_by_name["Vantage Capital"].id,
            company_name="Vantage Capital",
            name="Morgan Chen",
            title="CTO",
            seniority="cto",
            pain_point_count=3,
            signal_count=3,
            opportunity_score=80,
            score_label="hot",
            recommended_angle="Compliance reporting — multiple pain point mentions in recent job postings",
            status="identified",
        ),
        BDProspect(
            company_id=co_by_name["Stratos Engineering"].id,
            company_name="Stratos Engineering",
            name="Jamie Okafor",
            title="Head of Platform",
            seniority="head of",
            pain_point_count=2,
            signal_count=2,
            opportunity_score=71,
            score_label="warm",
            recommended_angle="Tech debt reduction — leadership change 6 weeks ago signals new priorities",
            status="identified",
        ),
        BDProspect(
            company_id=co_by_name["Nexus Health"].id,
            company_name="Nexus Health",
            name="Sam Torres",
            title="VP Product",
            seniority="vp",
            pain_point_count=1,
            signal_count=2,
            opportunity_score=65,
            score_label="warm",
            recommended_angle="HIPAA audit prep — annual audit cycle approaching based on company age",
            status="researched",
        ),
        BDProspect(
            company_id=co_by_name["Prism Analytics"].id,
            company_name="Prism Analytics",
            name="Drew Kim",
            title="Director of Engineering",
            seniority="director",
            pain_point_count=1,
            signal_count=1,
            opportunity_score=52,
            score_label="cold",
            recommended_angle="Data pipeline reliability — mentioned in engineering blog post",
            status="identified",
        ),
    ]
    bd_prospect_store.replace_all(prospect_path, prospects)

    # ── Signals ───────────────────────────────────────────────────────────────
    signals = [
        BDSignal(
            company_id=co_by_name["Meridian Labs"].id,
            company_name="Meridian Labs",
            signal_type="hiring",
            summary="Posting 3 senior DevOps / platform engineering roles — signals scaling initiative or infrastructure pain",
            source="Job board",
            relevance_score=92,
            detected_at="2026-06-24",
        ),
        BDSignal(
            company_id=co_by_name["Vantage Capital"].id,
            company_name="Vantage Capital",
            signal_type="leadership_change",
            summary="New CTO appointed 6 weeks ago — incoming technical leadership often re-evaluates vendor relationships",
            source="LinkedIn",
            relevance_score=88,
            detected_at="2026-06-20",
            reviewed=True,
        ),
        BDSignal(
            company_id=co_by_name["Vantage Capital"].id,
            company_name="Vantage Capital",
            signal_type="pain_point",
            summary='Job description for Compliance Engineer mentions "manual reporting burden" and "spreadsheet-heavy workflows"',
            source="Job board",
            relevance_score=85,
            detected_at="2026-06-22",
        ),
        BDSignal(
            company_id=co_by_name["Stratos Engineering"].id,
            company_name="Stratos Engineering",
            signal_type="tech_change",
            summary="Engineering blog post references migrating from Jenkins to GitHub Actions — potential toolchain transition support need",
            source="Blog",
            relevance_score=71,
            detected_at="2026-06-18",
        ),
        BDSignal(
            company_id=co_by_name["Nexus Health"].id,
            company_name="Nexus Health",
            signal_type="growth",
            summary="Headcount grew 40% YoY per LinkedIn — signals scaling challenges and possible new budget for infrastructure",
            source="LinkedIn",
            relevance_score=68,
            detected_at="2026-06-15",
            reviewed=True,
        ),
        BDSignal(
            company_id=co_by_name["Prism Analytics"].id,
            company_name="Prism Analytics",
            signal_type="competitive",
            summary="Competitor Lumos Analytics raised Series B — Prism may be under pressure to accelerate product velocity",
            source="TechCrunch",
            relevance_score=55,
            detected_at="2026-06-10",
        ),
    ]
    bd_signal_store.replace_all(signal_path, signals)

    # ── Pain Points ───────────────────────────────────────────────────────────
    pain_points = [
        BDPainPoint(
            company_id=co_by_name["Meridian Labs"].id,
            company_name="Meridian Labs",
            description="Manual deployment pipeline",
            category="DevOps",
            signal_source="Job board",
            confidence=90,
            recommended_angle="CI/CD automation reducing cycle time by 60–80%",
        ),
        BDPainPoint(
            company_id=co_by_name["Meridian Labs"].id,
            company_name="Meridian Labs",
            description="Slow release cycles",
            category="Engineering velocity",
            signal_source="Job board",
            confidence=82,
            recommended_angle="Release velocity improvements without disrupting existing workflows",
        ),
        BDPainPoint(
            company_id=co_by_name["Vantage Capital"].id,
            company_name="Vantage Capital",
            description="Compliance reporting overhead",
            category="Compliance",
            signal_source="Job board",
            confidence=88,
            recommended_angle="Automated compliance reporting with audit-ready outputs",
        ),
        BDPainPoint(
            company_id=co_by_name["Vantage Capital"].id,
            company_name="Vantage Capital",
            description="Data reconciliation delays",
            category="Data quality",
            signal_source="Job board",
            confidence=75,
            recommended_angle="Real-time data reconciliation pipeline",
        ),
        BDPainPoint(
            company_id=co_by_name["Vantage Capital"].id,
            company_name="Vantage Capital",
            description="Manual audit prep",
            category="Compliance",
            signal_source="Job board",
            confidence=85,
            recommended_angle="One-click audit package generation",
        ),
        BDPainPoint(
            company_id=co_by_name["Stratos Engineering"].id,
            company_name="Stratos Engineering",
            description="Developer onboarding velocity",
            category="Engineering",
            signal_source="Blog",
            confidence=70,
            recommended_angle="Standardized developer environments and runbooks",
        ),
        BDPainPoint(
            company_id=co_by_name["Nexus Health"].id,
            company_name="Nexus Health",
            description="HIPAA audit prep",
            category="Compliance",
            signal_source="LinkedIn",
            confidence=78,
            recommended_angle="HIPAA-ready infrastructure and audit documentation",
        ),
        BDPainPoint(
            company_id=co_by_name["Prism Analytics"].id,
            company_name="Prism Analytics",
            description="Data pipeline reliability",
            category="Data engineering",
            signal_source="Blog",
            confidence=65,
            recommended_angle="Pipeline observability and error recovery frameworks",
        ),
    ]
    bd_pain_point_store.replace_all(pain_point_path, pain_points)

    # ── Opportunities ─────────────────────────────────────────────────────────
    opportunities = [
        BDOpportunity(
            company_id=co_by_name["Meridian Labs"].id,
            company_name="Meridian Labs",
            contact_name="Alex Rivera",
            score=87,
            score_label="hot",
            stage="researched",
            pain_points=["Manual deployment pipeline", "Slow release cycles"],
            value_proposition="CI/CD automation reducing deployment cycle time by 60–80%, delivered in 6–8 weeks.",
            recommended_action="Reach out via mutual connection — Morgan at Acme introduced us",
        ),
        BDOpportunity(
            company_id=co_by_name["Vantage Capital"].id,
            company_name="Vantage Capital",
            contact_name="Morgan Chen",
            score=80,
            score_label="hot",
            stage="qualified",
            pain_points=["Compliance reporting overhead", "Manual audit prep"],
            value_proposition="Automated compliance reporting with one-click audit packages for FinTech regulatory requirements.",
            recommended_action="New CTO 6 weeks in — send intro + compliance angle deck",
        ),
        BDOpportunity(
            company_id=co_by_name["Stratos Engineering"].id,
            company_name="Stratos Engineering",
            contact_name="Jamie Okafor",
            score=71,
            score_label="warm",
            stage="researched",
            pain_points=["Developer onboarding velocity", "Tech debt accumulation"],
            value_proposition="Standardized developer environments cutting onboarding from 2 weeks to 2 days.",
            recommended_action="Follow up on tech change signal — Jenkins → GitHub Actions migration",
        ),
        BDOpportunity(
            company_id=co_by_name["Nexus Health"].id,
            company_name="Nexus Health",
            contact_name="Sam Torres",
            score=65,
            score_label="warm",
            stage="identified",
            pain_points=["HIPAA audit prep"],
            value_proposition="HIPAA-ready infrastructure audit with documentation package delivered in 3 weeks.",
            recommended_action="First touch — connect on LinkedIn with healthcare compliance angle",
        ),
        BDOpportunity(
            company_id=co_by_name["Prism Analytics"].id,
            company_name="Prism Analytics",
            contact_name=None,
            score=52,
            score_label="cold",
            stage="identified",
            pain_points=["Data pipeline reliability"],
            value_proposition="Pipeline observability reducing incident MTTR by 40%.",
            recommended_action="Identify right contact — likely VP Engineering or CTO",
        ),
    ]
    bd_opportunity_store.replace_all(opportunity_path, opportunities)

    # ── Deal Packets ──────────────────────────────────────────────────────────
    meridian_packet = BDDealPacket(
        company_id=co_by_name["Meridian Labs"].id,
        company_name="Meridian Labs",
        contact_name="Alex Rivera",
        contact_role="VP of Engineering",
        engagement_type="New Business",
        company_summary="Meridian Labs is a DevTools / SaaS company (50–200 employees) actively scaling their platform engineering team. Multiple hiring signals and public blog posts indicate infrastructure pain around deployment velocity.",
        pain_points=["Manual deployment pipeline", "Slow release cycles"],
        value_proposition="CI/CD automation reducing deployment cycle time by 60–80%, delivered in 6–8 weeks without disrupting existing workflows.",
        talking_points=[
            "Address manual deployment pipeline: walk through how similar DevTools companies automated with 6-week implementation",
            "Address slow release cycles: show before/after cycle time metrics from comparable teams",
            "Discuss current toolchain and integration path (GitHub Actions already in use)",
            "Understand team size, release cadence, and blocker severity",
            "Discuss timeline and decision-making process",
        ],
        outreach_draft=f"""Hi Alex,

I've been following Meridian Labs' engineering work — impressive scaling. I noticed you're posting for senior DevOps roles, which often signals pressure around deployment velocity.

We've helped similar DevTools teams reduce deployment cycle time by 60–80% in 6–8 weeks without a major migration.

Would a 20-minute call to share what's worked for comparable teams be worth your time?

[Your name]{_SAFETY_NOTICE}""",
        checklist=_make_checklist(
            "Review Meridian Labs recent job postings for pain point confirmation",
            "Identify mutual connections for warm intro",
            "Review and customize outreach draft for Alex Rivera",
            "Validate value proposition numbers with relevant case studies",
            "Approve draft in Review Queue before sending",
            "Log outreach attempt and response in Activity",
        ),
        status="draft",
    )

    vantage_packet = BDDealPacket(
        company_id=co_by_name["Vantage Capital"].id,
        company_name="Vantage Capital",
        contact_name="Morgan Chen",
        contact_role="CTO",
        engagement_type="New Business",
        company_summary="Vantage Capital is a FinTech firm (200–500 employees) with a recently appointed CTO. Compliance reporting and manual audit prep are confirmed pain points from job descriptions.",
        pain_points=["Compliance reporting overhead", "Manual audit prep", "Data reconciliation delays"],
        value_proposition="Automated compliance reporting with one-click audit packages for FinTech regulatory requirements — reducing audit prep from weeks to hours.",
        talking_points=[
            "Address compliance reporting overhead: automated reporting with regulatory-ready outputs",
            "Address manual audit prep: one-click audit package generation with evidence collection",
            "New CTO angle: new technical leadership typically reassesses vendor landscape in first 90 days",
            "Discuss current compliance stack and gaps",
            "Understand regulatory obligations (SOC2, PCI, etc.) and audit frequency",
        ],
        outreach_draft=f"""Hi Morgan,

Congratulations on joining Vantage Capital as CTO — it's an exciting time for the firm.

I noticed from recent job postings that compliance reporting overhead is a priority challenge for your team. We've helped FinTech CTOs like you reduce audit prep time from weeks to hours with automated reporting and one-click evidence packages.

As you settle into your new role, would a brief conversation about what's working for similar FinTech teams be valuable?

[Your name]{_SAFETY_NOTICE}""",
        checklist=_make_checklist(
            "Confirm Morgan Chen's LinkedIn and correct contact info",
            "Research Vantage Capital's regulatory obligations (SOC2, PCI, GDPR)",
            "Review and tailor outreach draft for new CTO context",
            "Identify 2–3 comparable FinTech case studies",
            "Approve draft in Review Queue before sending",
        ),
        status="review",
    )

    deal_packets = [meridian_packet, vantage_packet]
    bd_deal_packet_store.replace_all(deal_packet_path, deal_packets)

    # ── Outreach Drafts ───────────────────────────────────────────────────────
    outreach_drafts = [
        BDOutreachDraft(
            company_name="Vantage Capital",
            contact_name="Morgan Chen",
            contact_role="CTO",
            message_type="email",
            subject="Reducing compliance reporting overhead at Vantage Capital",
            body=vantage_packet.outreach_draft,
            tone="executive",
            angle="Compliance reporting automation",
            personalization_score=84,
            spam_risk_score=8,
            ai_sounding_score=12,
            quality_status="review",
            status="review",
        ),
        BDOutreachDraft(
            company_name="Meridian Labs",
            contact_name="Alex Rivera",
            contact_role="VP of Engineering",
            message_type="linkedin",
            subject=None,
            body=meridian_packet.outreach_draft,
            tone="warm",
            angle="CI/CD automation",
            personalization_score=71,
            spam_risk_score=12,
            ai_sounding_score=18,
            quality_status="draft",
            status="draft",
        ),
    ]
    bd_outreach_store.replace_all(outreach_path, outreach_drafts)

    return {
        "companies": len(companies),
        "prospects": len(prospects),
        "signals": len(signals),
        "pain_points": len(pain_points),
        "opportunities": len(opportunities),
        "deal_packets": len(deal_packets),
        "outreach_drafts": len(outreach_drafts),
    }


def clear_bd_demo(
    company_path: str,
    prospect_path: str,
    signal_path: str,
    pain_point_path: str,
    opportunity_path: str,
    deal_packet_path: str,
    outreach_path: str,
) -> None:
    bd_company_store.clear_companies(company_path)
    bd_prospect_store.clear_prospects(prospect_path)
    bd_signal_store.clear_signals(signal_path)
    bd_pain_point_store.clear_pain_points(pain_point_path)
    bd_opportunity_store.clear_opportunities(opportunity_path)
    bd_deal_packet_store.clear_deal_packets(deal_packet_path)
    bd_outreach_store.clear_drafts(outreach_path)
