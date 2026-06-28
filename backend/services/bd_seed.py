"""
BD OS demo seed data. Local only. No external API calls.
"""
from backend.models.bd import (
    BDCompany, BDProspect, BDSignal, BDPainPoint,
    BDOpportunity, BDDealPacket, BDChecklistItem, BDOutreachDraft,
    BDICPConfig,
)
from backend.services import (
    bd_company_store, bd_prospect_store, bd_signal_store,
    bd_pain_point_store, bd_opportunity_store, bd_deal_packet_store,
    bd_outreach_store,
)
from backend.services.bd_icp_store import save_icp_config


_SAFETY_NOTICE = "\n\n---\nPrepared for manual review. DobryBot does not send automatically."


def _make_checklist(*items: str) -> list[BDChecklistItem]:
    return [BDChecklistItem(text=t, done=False) for t in items]


# ── ICP Seed ──────────────────────────────────────────────────────────────────

def seed_icp_demo(icp_config_path: str) -> BDICPConfig:
    """Seed a demo ICP configuration aligned with CorosDev BD OS use cases.
    Local only — no external calls."""
    icp = BDICPConfig(
        target_industries=[
            "SaaS",
            "Financial Services",
            "Private Equity",
            "Logistics",
            "Healthcare Operations",
            "Professional Services",
            "Mid-market Technology",
        ],
        company_size_min=50,
        company_size_max=2000,
        target_roles=[
            "CEO",
            "Founder",
            "COO",
            "CTO",
            "VP Operations",
            "VP Sales",
            "Managing Partner",
            "Head of Business Development",
        ],
        pain_point_priorities=[
            "manual prospecting",
            "low outbound conversion",
            "poor lead qualification",
            "disconnected CRM data",
            "slow deal origination",
            "lack of market signal tracking",
            "offshore execution bottlenecks",
        ],
        signal_priorities=[
            "hiring",
            "leadership_change",
            "pain_point",
            "funding",
            "growth",
        ],
        scoring_weights={
            "icp_match": 30,
            "pain_points": 25,
            "signals": 20,
            "seniority": 15,
            "urgency": 7,
            "existing_relationship": 3,
        },
    )
    return save_icp_config(icp_config_path, icp)


# ── BD Data Seed ──────────────────────────────────────────────────────────────

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
            industry="Financial Services / FinTech",
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
            industry="Infrastructure / SaaS",
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
            industry="Healthcare Operations",
            size_estimate="50–150",
            tech_signals=["AWS", "HIPAA tooling"],
            pain_points=["HIPAA audit prep", "Legacy system integrations"],
            opportunity_score=65,
            score_label="warm",
            icp_match=True,
            status="identified",
        ),
        BDCompany(
            name="Summit Ventures",
            domain="summitvc.io",
            industry="Private Equity",
            size_estimate="50–150",
            tech_signals=["Salesforce", "Excel", "Notion"],
            pain_points=["Slow deal origination", "Manual portfolio prospecting", "Disconnected CRM data"],
            opportunity_score=68,
            score_label="warm",
            icp_match=True,
            status="researched",
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
    ]
    for item in companies:
        item.source = "demo"
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
            recommended_angle="Deployment automation — they posted 3 DevOps roles last month, signaling velocity pressure",
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
            recommended_angle="Compliance reporting automation — new CTO in first 90 days, multiple pain point signals in job postings",
            status="identified",
        ),
        BDProspect(
            company_id=co_by_name["Stratos Engineering"].id,
            company_name="Stratos Engineering",
            name="Jamie Okafor",
            title="COO",
            seniority="coo",
            pain_point_count=2,
            signal_count=2,
            opportunity_score=71,
            score_label="warm",
            recommended_angle="Tech debt reduction and developer onboarding — COO-level mandate after leadership change 6 weeks ago",
            status="identified",
        ),
        BDProspect(
            company_id=co_by_name["Nexus Health"].id,
            company_name="Nexus Health",
            name="Sam Torres",
            title="CEO",
            seniority="ceo",
            pain_point_count=1,
            signal_count=2,
            opportunity_score=65,
            score_label="warm",
            recommended_angle="HIPAA audit prep — annual audit cycle approaching based on company age and recent headcount growth",
            status="researched",
        ),
        BDProspect(
            company_id=co_by_name["Summit Ventures"].id,
            company_name="Summit Ventures",
            name="Taylor Brooks",
            title="COO",
            seniority="coo",
            pain_point_count=3,
            signal_count=2,
            opportunity_score=68,
            score_label="warm",
            recommended_angle="Deal origination intelligence — Fund IV just closed, need scalable BD process for portfolio sourcing",
            status="identified",
        ),
        BDProspect(
            company_id=co_by_name["Prism Analytics"].id,
            company_name="Prism Analytics",
            name="Drew Kim",
            title="CTO",
            seniority="cto",
            pain_point_count=1,
            signal_count=1,
            opportunity_score=52,
            score_label="cold",
            recommended_angle="Data pipeline reliability — mentioned in engineering blog, needs validation before outreach",
            status="identified",
        ),
    ]
    for item in prospects:
        item.source = "demo"
    bd_prospect_store.replace_all(prospect_path, prospects)

    # ── Signals ───────────────────────────────────────────────────────────────
    signals = [
        BDSignal(
            company_id=co_by_name["Meridian Labs"].id,
            company_name="Meridian Labs",
            signal_type="hiring",
            summary="Posting 3 senior DevOps / platform engineering roles — signals scaling initiative or infrastructure pain around deployment velocity",
            source="Job board",
            relevance_score=92,
            detected_at="2026-06-24",
        ),
        BDSignal(
            company_id=co_by_name["Vantage Capital"].id,
            company_name="Vantage Capital",
            signal_type="leadership_change",
            summary="New CTO appointed 6 weeks ago — incoming technical leadership often re-evaluates vendor relationships in first 90 days",
            source="LinkedIn",
            relevance_score=88,
            detected_at="2026-06-20",
            reviewed=True,
        ),
        BDSignal(
            company_id=co_by_name["Vantage Capital"].id,
            company_name="Vantage Capital",
            signal_type="pain_point",
            summary='Compliance Engineer JD explicitly mentions "manual reporting burden" and "spreadsheet-heavy workflows" — confirmed operational pain',
            source="Job board",
            relevance_score=85,
            detected_at="2026-06-22",
        ),
        BDSignal(
            company_id=co_by_name["Stratos Engineering"].id,
            company_name="Stratos Engineering",
            signal_type="tech_change",
            summary="Engineering blog references migrating from Jenkins to GitHub Actions — active toolchain transition, potential support need",
            source="Blog",
            relevance_score=71,
            detected_at="2026-06-18",
        ),
        BDSignal(
            company_id=co_by_name["Nexus Health"].id,
            company_name="Nexus Health",
            signal_type="growth",
            summary="Headcount grew 40% YoY per LinkedIn — rapid scaling often triggers compliance and infrastructure gaps at this stage",
            source="LinkedIn",
            relevance_score=68,
            detected_at="2026-06-15",
            reviewed=True,
        ),
        BDSignal(
            company_id=co_by_name["Summit Ventures"].id,
            company_name="Summit Ventures",
            signal_type="funding",
            summary="Summit Ventures announced $250M Fund IV close — new fund requires accelerated deal origination and portfolio BD process at scale",
            source="TechCrunch",
            relevance_score=78,
            detected_at="2026-06-21",
        ),
        BDSignal(
            company_id=co_by_name["Prism Analytics"].id,
            company_name="Prism Analytics",
            signal_type="competitive",
            summary="Competitor Lumos Analytics raised Series B — Prism may be under pressure to accelerate product velocity and partner BD",
            source="TechCrunch",
            relevance_score=55,
            detected_at="2026-06-10",
        ),
    ]
    for item in signals:
        item.data_source = "demo"
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
            recommended_angle="CI/CD automation reducing deployment cycle time by 60–80%",
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
            recommended_angle="Real-time data reconciliation pipeline reducing settlement errors",
        ),
        BDPainPoint(
            company_id=co_by_name["Vantage Capital"].id,
            company_name="Vantage Capital",
            description="Manual audit prep",
            category="Compliance",
            signal_source="Job board",
            confidence=85,
            recommended_angle="One-click audit package generation with evidence collection",
        ),
        BDPainPoint(
            company_id=co_by_name["Stratos Engineering"].id,
            company_name="Stratos Engineering",
            description="Developer onboarding velocity",
            category="Engineering",
            signal_source="Blog",
            confidence=70,
            recommended_angle="Standardized developer environments cutting onboarding from 2 weeks to 2 days",
        ),
        BDPainPoint(
            company_id=co_by_name["Nexus Health"].id,
            company_name="Nexus Health",
            description="HIPAA audit prep",
            category="Compliance",
            signal_source="LinkedIn",
            confidence=78,
            recommended_angle="HIPAA-ready infrastructure and audit documentation package",
        ),
        BDPainPoint(
            company_id=co_by_name["Summit Ventures"].id,
            company_name="Summit Ventures",
            description="Slow deal origination",
            category="Business Development",
            signal_source="TechCrunch",
            confidence=82,
            recommended_angle="BD intelligence system to surface qualified deals from market signals without manual research overhead",
        ),
        BDPainPoint(
            company_id=co_by_name["Summit Ventures"].id,
            company_name="Summit Ventures",
            description="Manual portfolio prospecting",
            category="Business Development",
            signal_source="TechCrunch",
            confidence=76,
            recommended_angle="Automated signal monitoring for portfolio company BD without adding headcount",
        ),
        BDPainPoint(
            company_id=co_by_name["Prism Analytics"].id,
            company_name="Prism Analytics",
            description="Data pipeline reliability",
            category="Data engineering",
            signal_source="Blog",
            confidence=65,
            recommended_angle="Pipeline observability and error recovery frameworks reducing incident MTTR by 40%",
        ),
    ]
    for item in pain_points:
        item.source = "demo"
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
            recommended_action="Reach out via mutual connection — reference the 3 open DevOps roles as context",
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
            recommended_action="New CTO 6 weeks in — ideal window for intro. Send compliance angle one-pager",
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
            recommended_action="Follow up on Jenkins → GitHub Actions migration blog post — offer migration support angle",
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
            recommended_action="First touch — connect via LinkedIn with healthcare compliance angle before annual audit window",
        ),
        BDOpportunity(
            company_id=co_by_name["Summit Ventures"].id,
            company_name="Summit Ventures",
            contact_name="Taylor Brooks",
            score=68,
            score_label="warm",
            stage="researched",
            pain_points=["Slow deal origination", "Manual portfolio prospecting", "Disconnected CRM data"],
            value_proposition="BD intelligence system that surfaces qualified opportunities from market signals — designed for PE deal sourcing at fund scale.",
            recommended_action="Fund IV announcement is the hook — congratulate and pitch deal origination intelligence for the new fund cycle",
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
            recommended_action="Identify right contact — likely CTO Drew Kim. Validate pain before first outreach",
        ),
    ]
    for item in opportunities:
        item.source = "demo"
    bd_opportunity_store.replace_all(opportunity_path, opportunities)

    # ── Deal Packets ──────────────────────────────────────────────────────────
    meridian_packet = BDDealPacket(
        company_id=co_by_name["Meridian Labs"].id,
        company_name="Meridian Labs",
        contact_name="Alex Rivera",
        contact_role="VP of Engineering",
        engagement_type="New Business",
        company_summary="Meridian Labs is a DevTools / SaaS company (50–200 employees) actively scaling their platform engineering team. Multiple hiring signals and public blog posts indicate infrastructure pain around deployment velocity and release cycle speed.",
        pain_points=["Manual deployment pipeline", "Slow release cycles"],
        value_proposition="CI/CD automation reducing deployment cycle time by 60–80%, delivered in 6–8 weeks without disrupting existing workflows.",
        talking_points=[
            "Address manual deployment pipeline: walk through how similar DevTools companies automated with 6-week implementation",
            "Address slow release cycles: show before/after cycle time metrics from comparable engineering teams",
            "Discuss current toolchain and integration path (GitHub Actions already in use — minimal migration lift)",
            "Understand team size, release cadence, and the business impact of current deployment delays",
            "Clarify decision timeline and whether budget is attached to the open DevOps headcount",
        ],
        outreach_draft=f"""Hi Alex,

I've been following Meridian Labs' engineering work — impressive scaling. I noticed you're posting for 3 senior DevOps roles, which often signals pressure around deployment velocity rather than just headcount.

We've helped similar DevTools teams reduce deployment cycle time by 60–80% in 6–8 weeks without a major migration — starting with what's already there.

Would a 20-minute call to share what's worked for comparable teams be worth your time?

[Your name]{_SAFETY_NOTICE}""",
        checklist=_make_checklist(
            "Review Meridian Labs recent job postings to confirm pain point framing",
            "Identify mutual connections for warm intro path",
            "Review and customize outreach draft for Alex Rivera specifically",
            "Validate 60–80% cycle time claim with relevant reference data",
            "Approve draft in Review Queue before sending",
            "Log outreach attempt and response in Activity Log",
        ),
        status="draft",
    )

    vantage_packet = BDDealPacket(
        company_id=co_by_name["Vantage Capital"].id,
        company_name="Vantage Capital",
        contact_name="Morgan Chen",
        contact_role="CTO",
        engagement_type="New Business",
        company_summary="Vantage Capital is a Financial Services / FinTech firm (200–500 employees) with a recently appointed CTO. Compliance reporting and manual audit prep are confirmed pain points from multiple job descriptions — including an explicit reference to 'spreadsheet-heavy workflows'.",
        pain_points=["Compliance reporting overhead", "Manual audit prep", "Data reconciliation delays"],
        value_proposition="Automated compliance reporting with one-click audit packages for FinTech regulatory requirements — reducing audit prep from weeks to hours.",
        talking_points=[
            "Address compliance reporting overhead: show automated regulatory reporting with evidence collection built in",
            "Address manual audit prep: demo one-click audit package generation for SOC2 / PCI frameworks",
            "New CTO angle: first 90 days is when new technical leadership reassesses vendor landscape — ideal entry window",
            "Understand current compliance stack: what tools are in use, where the bottlenecks are, and upcoming audit obligations",
            "Validate: SOC2 Type II, PCI DSS, or GDPR? Each has different reporting cadence and prep complexity",
        ],
        outreach_draft=f"""Hi Morgan,

Congratulations on joining Vantage Capital as CTO — it's an exciting time for the firm.

I noticed from recent job postings that compliance reporting overhead is a priority challenge for your team. We've helped FinTech CTOs reduce audit prep time from weeks to hours with automated reporting and one-click evidence packages.

As you assess the current stack in your first 90 days, would a brief conversation about what's worked for similar FinTech teams be valuable?

[Your name]{_SAFETY_NOTICE}""",
        checklist=_make_checklist(
            "Confirm Morgan Chen's correct contact information and LinkedIn URL",
            "Research Vantage Capital's regulatory obligations (SOC2, PCI DSS, GDPR)",
            "Tailor outreach draft for new CTO context — reference specific regulatory framework",
            "Identify 2–3 comparable FinTech case studies with measurable outcomes",
            "Approve draft in Review Queue before sending",
        ),
        status="review",
    )

    summit_packet = BDDealPacket(
        company_id=co_by_name["Summit Ventures"].id,
        company_name="Summit Ventures",
        contact_name="Taylor Brooks",
        contact_role="COO",
        engagement_type="New Business",
        company_summary="Summit Ventures is a private equity firm (50–150 employees) that just closed a $250M Fund IV. New fund cycles require accelerated deal origination at scale — exactly when BD process gaps become acute. Manual prospecting and disconnected CRM data are confirmed pain points.",
        pain_points=["Slow deal origination", "Manual portfolio prospecting", "Disconnected CRM data"],
        value_proposition="BD intelligence system that surfaces qualified deal opportunities from market signals — designed for PE deal sourcing without adding BD headcount.",
        talking_points=[
            "Fund IV hook: new fund requires deploying capital on a timeline — slow deal origination directly impacts fund performance",
            "Manual prospecting pain: current process relies on relationship mining and manual research — inefficient at fund scale",
            "Disconnected CRM data: without unified signal tracking, high-value leads fall through the cracks between portfolio reviews",
            "Differentiate: this is not mass outreach automation — it's intelligence-first BD that respects the relationship-driven PE model",
            "Next step: brief product walkthrough using PE-relevant signal types (leadership changes, earnings signals, portfolio adjacency)",
        ],
        outreach_draft=f"""Hi Taylor,

Congratulations on closing Fund IV — $250M is a significant milestone.

New fund cycles are exciting but they also put real pressure on deal origination. We've worked with PE and growth-equity teams to build systematic signal monitoring that surfaces qualified opportunities before they appear on everyone else's radar — without the noise of mass outreach tools.

Given the timeline pressure that comes with a new fund, would a 20-minute conversation about how similar firms have approached this be useful?

[Your name]{_SAFETY_NOTICE}""",
        checklist=_make_checklist(
            "Verify Taylor Brooks' role and confirm COO is the right BD contact at Summit Ventures",
            "Research Fund IV thesis to tailor value proposition to their specific sector focus",
            "Review and customize outreach draft — reference Fund IV specifically",
            "Identify 1–2 PE or growth-equity references with similar BD challenges",
            "Approve draft in Review Queue before sending",
        ),
        status="draft",
    )

    deal_packets = [meridian_packet, vantage_packet, summit_packet]
    for item in deal_packets:
        item.source = "demo"
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
            angle="CI/CD automation and deployment velocity",
            personalization_score=71,
            spam_risk_score=12,
            ai_sounding_score=18,
            quality_status="draft",
            status="draft",
        ),
        BDOutreachDraft(
            company_name="Summit Ventures",
            contact_name="Taylor Brooks",
            contact_role="COO",
            message_type="email",
            subject="Deal origination intelligence for Summit Ventures Fund IV",
            body=summit_packet.outreach_draft,
            tone="executive",
            angle="BD intelligence for PE deal sourcing",
            personalization_score=79,
            spam_risk_score=9,
            ai_sounding_score=15,
            quality_status="draft",
            status="draft",
        ),
    ]
    for item in outreach_drafts:
        item.source = "demo"
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
