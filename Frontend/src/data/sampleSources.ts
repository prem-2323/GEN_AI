export interface SampleSourceDoc {
  id: string;
  name: string;
  type: 'PDF' | 'DOCX' | 'TXT';
  size: string;
  category: string;
  summary: string;
  content: string;
}

export const SAMPLE_SOURCES: SampleSourceDoc[] = [
  {
    id: 'sample-sec-cve',
    name: 'Threat_Intelligence_Advisory_Q3_2026.docx',
    type: 'DOCX',
    size: '1.4 MB',
    category: 'Cybersecurity',
    summary: 'Critical vulnerability CVE-2026-8891 analysis & zero-trust remediation roadmap',
    content: `Threat Intelligence Advisory Q3 2026: Critical Ingress Gateway Vulnerability
Author: Global Cybersecurity Operations & Defense Unit
Publication Date: September 24, 2026
Classification: TLP:AMBER / Restricted Internal Executive & Technical Distribution

1. EXECUTIVE SUMMARY & URGENCY
Over the past 90 days, the Security Operations Center (SOC) observed a 340% increase in coordinated ransomware-as-a-service (RaaS) campaigns targeting containerized hybrid-cloud environments. An active zero-day vulnerability (designated CVE-2026-8891, CVSS Score 9.8 Critical) in widely deployed cloud ingress controllers has been weaponized by advanced persistent threat group 'VortexShadow'. Immediate remediation is mandated across all enterprise Kubernetes clusters.

2. TECHNICAL TELEMETRY & INCIDENT FINDINGS
- Vulnerability Identifier: CVE-2026-8891 (Remote Unauthenticated Memory Corruption via Crafted HTTP/2 Frames)
- Impact Scope: 142 enterprise nodes across 18 regional data centers detected anomalous privilege escalation attempts.
- Infiltration Vector: Polymorphic TLS handshakes bypassing traditional Web Application Firewall (WAF) rule engines.
- Detection & Containment: Mean Time to Detect (MTTD) was reduced from 4.2 hours to 18 minutes following deployment of automated eBPF runtime sensors. Zero confirmed customer data exfiltrations have occurred to date.

3. STRATEGIC REMEDIATION ROADMAP & MANDATES
- Phase 1 (Immediate / Next 24 Hours): Patch all cluster ingress controllers with emergency hotfix build v1.24.9-sec. Revoke and rotate all cluster service account JWT tokens and administrative SSH certificates.
- Phase 2 (Within 7 Days): Enforce Zero Trust Network Access (ZTNA) policies restricting inter-pod egress exclusively to cryptographically signed microservice endpoints.
- Phase 3 (Ongoing / 30 Days): Implement kernel-level attestation (IMA) and mandate hardware-backed FIDO2 multi-factor authentication for all continuous deployment pipelines.

4. COMPLIANCE & STAKEHOLDER COMMUNICATION
All business unit leads must submit signed remediation confirmation logs to the Chief Information Security Officer (CISO) by Friday 17:00 UTC. Regular status briefings will be provided to the Audit & Risk Committee.`
  },
  {
    id: 'sample-ai-strategy',
    name: 'Enterprise_AI_Transformation_Framework.pdf',
    type: 'PDF',
    size: '2.1 MB',
    category: 'AI & Strategy',
    summary: 'Canonical knowledge graphs, zero-hallucination guardrails & multi-agent synthesis',
    content: `Enterprise AI Transformation Strategy & Responsible Governance 2026-2028
Published by: Office of the Chief Technology Officer (OCTO) & AI Ethics Board
Target Audience: Executive Leadership, Business Unit Heads, and AI Engineering Teams

1. EXECUTIVE OVERVIEW
As organizations accelerate the adoption of generative AI and autonomous agentic workflows, establishing robust governance, factual verification, and unified knowledge architectures is paramount. This strategic framework establishes our core pillars for deploying production-grade AI applications across 45 business units without risking hallucinations or data leakage.

2. CORE STRATEGIC PILLARS
- Unified Canonical Knowledge Representation (UCKR): Implementing a centralized knowledge graph engine that extracts, cross-references, and validates factual assertions across all source documents prior to synthesis.
- Zero-Hallucination Guardrails: Autonomous verification pipelines cross-auditing model deliverables against verified entity-event-metric graphs with a strict minimum 95% grounding threshold.
- Omnichannel Transformation: Transforming single source knowledge assets into multi-stakeholder formats (Executive Summaries, Technical Advisories, Social Syntheses, and Multimedia Decks) in under 60 seconds.

3. TARGET MILESTONES & PERFORMANCE METRICS
- Q4 2026: 100% compliance across all customer-facing AI agents with EU AI Act and ISO/IEC 42001 standards.
- Q1 2027: 4.8x reduction in content transformation turnaround time, saving an estimated 12,000 engineering hours annually.
- Budget Allocation: $14.5M dedicated towards verifiable multi-agent infrastructure and automated quality auditing.

4. ORGANIZATIONAL ROADMAP
The AI Center of Excellence (CoE) will provide standardized SDKs, validation harnesses, and automated deliverable templates starting next quarter.`
  },
  {
    id: 'sample-cloud-migration',
    name: 'Cloud_Infrastructure_Modernization_Report.txt',
    type: 'TXT',
    size: '480 KB',
    category: 'Engineering',
    summary: 'Zero-downtime database migration results, latency gains & 42% cost reduction',
    content: `Engineering Post-Mortem: Core Database Modernization & Multi-Region Migration
Published by: Platform Engineering & Cloud Infrastructure Team
Date: September 2026

1. EXECUTIVE SUMMARY
Over the past 6 months, the Platform Engineering organization successfully executed a zero-downtime migration of our primary transaction datastore to a globally distributed cloud-native architecture. The project encompassed 8.2 terabytes of active production data across 45 million customer accounts.

2. KEY PERFORMANCE OUTCOMES
- Latency Reduction: 95th-percentile (p95) API response times decreased from 142ms to 38ms globally.
- Infrastructure Cost Optimization: Cloud compute and storage spend decreased by 42%, yielding an annualized run-rate savings of $1.85M.
- Availability & Resilience: Achieved five-nines (99.999%) uptime during the cutover window with zero data inconsistency or lost transactions.
- Automated Failover: Multi-region active-active failover time improved from 12 minutes to sub-4 seconds.

3. LESSONS LEARNED & ARCHITECTURAL BEST PRACTICES
- Dual-write synchronization with asynchronous reconciliation logs prevented silent data drift.
- Canary traffic routing with synthetic load testing detected 3 critical deadlock edge cases prior to full production cutover.
- Next Steps: Roll out automated self-healing partition rebalancing across all secondary caching clusters by Q4.`
  }
];
