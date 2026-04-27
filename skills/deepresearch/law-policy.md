# Law & Policy Research Mode

Used when the topic involves laws, regulations, compliance obligations, regulator guidance, statutory requirements, retention periods, legal applicability, country comparisons, audit/recordkeeping rules, or vendor/product fit against policy requirements.

This mode is for rigorous policy research, not legal advice. Every legal conclusion must distinguish binding law from proposed rules, regulator guidance, standards, secondary interpretation, and implementation best practice.

---

## 5-Part Structure

### Part 1: Legal Source Mapping
- Identify authoritative statutes, regulations, official gazettes, regulator guidance, ministry publications, consultation papers, and official standards.
- Establish legal status: binding law, implementing regulation, regulator guidance, draft/proposed rule, consultation paper, industry standard, or secondary summary.
- Note publication dates, effective dates, amendment history, current status, and whether translations are official.
- Prefer official sources; use law-firm or vendor summaries only as secondary support.

### Part 2: Applicability & Covered Entities
- Determine who is regulated: ordinary enterprises, service providers, ISPs, hosting providers, cloud providers, public Wi-Fi operators, critical infrastructure, financial institutions, data controllers/processors, licensees, or electronic system operators.
- Identify trigger conditions: business role, sector, service type, user location, data type, incident, regulator notice, company size, or public availability.
- Separate clearly covered, conditionally covered, likely not covered, and unresolved/local-counsel-needed cases.
- Do not assume a company is covered just because it owns relevant technology.

### Part 3: Obligation Extraction
- Extract concrete duties: record, retain, disclose, protect, delete, audit, report, notify, localize, encrypt, sign, timestamp, or preserve.
- Capture retention periods, required fields/content, formats, integrity controls, access controls, production deadlines, penalties, and exceptions.
- Distinguish continuous obligations from event-triggered, notice-triggered, incident-triggered, or sector-triggered obligations.
- For log/compliance topics, normalize requirements into retention period, required content, integrity, availability, privacy limits, and security controls.

### Part 4: Comparative Analysis & Practical Interpretation
- Compare jurisdictions, sectors, or regimes in tables.
- Translate legal language into operational requirements while labeling certainty levels.
- Distinguish explicit legal obligations from practical evidence-chain requirements and best practices.
- Identify conflicts, especially retention vs. privacy/data minimization, local storage vs. cloud processing, and regulator access vs. confidentiality.
- Include capacity, cost, implementation, or process modeling when the user asks for operational planning.

### Part 5: Vendor / Product / Operational Fit
- Evaluate whether relevant products, services, or architectures can satisfy the requirements.
- Use official product documentation first.
- Compare retention, export, archive, compression, integrity, timestamping, signing, audit trails, local/cloud storage, data residency, and country-specific support.
- Classify fit as native support, partial support, requires external system, unsupported, or unclear.
- Do not treat vendor "compliance" marketing as legal compliance unless mapped to specific requirements.

---

## Research Plan Guidelines

Before writing `RESEARCH_PLAN.md`:
- Confirm the jurisdiction scope, subject matter, regulated activities, and entity types to test.
- Identify known regulators, ministries, legal portals, official gazettes, and standards bodies.
- Gather search terms in English and local languages.
- Confirm whether vendor/product fit, storage/cost modeling, implementation architecture, or legal-only analysis is in scope.
- If the user asks for a country comparison, define the comparison dimensions before launching agents.

`RESEARCH_PLAN.md` must include:
- Problem statement and jurisdiction scope.
- Regulated activities and entity types to test.
- Research questions per part.
- Known starting points: legal portals, regulator URLs, statute names, consultation papers, standards, vendor docs.
- Source-quality hierarchy and how unofficial translations will be labeled.
- Expected output tables: source table, applicability matrix, obligation table, retention table, required-fields table, vendor/solution matrix if relevant.
- "What NOT to assume before research" section.

---

## Agent Prompt Scaffolding

### Agent 1 — Legal Source Mapping
```
Research authoritative legal and policy sources for this topic.
Fetch and read official statutes, regulations, official gazettes, regulator pages, consultation papers, and official guidance.
Distinguish binding law, draft/proposed rules, regulator guidance, standards, and secondary summaries.
Starting URLs: [official legal portals/regulators from the plan]
Searches to perform: [local-language and English searches]
Save to: {folder}/raw_research/01_legal_source_mapping.md
Target: 2000+ words with source tables, dates, legal status, and URLs.
```

### Agent 2 — Applicability & Covered Entities
```
Research who is covered and when the obligations apply.
Analyze entity types, sector scope, territorial scope, trigger conditions, exemptions, and edge cases.
Classify ordinary enterprises, service providers, public access providers, data controllers/processors, critical infrastructure, licensees, and other relevant entities.
Starting URLs: [statutes/regulator guidance from the plan]
Save to: {folder}/raw_research/02_applicability.md
Target: 2000+ words with applicability matrix and source URLs.
```

### Agent 3 — Obligation Extraction
```
Extract concrete obligations from the applicable laws and policies.
Capture retention periods, required records/data fields, audit trail requirements, disclosure duties, security controls, integrity requirements, deletion limits, reporting deadlines, and penalties.
Quote or paraphrase article/section numbers and label legal certainty.
Starting URLs: [primary legal texts from the plan]
Save to: {folder}/raw_research/03_obligation_extraction.md
Target: 2000+ words with obligation tables and source URLs.
```

### Agent 4 — Comparative & Practical Analysis
```
Build jurisdiction-by-jurisdiction or regime-by-regime comparison tables.
Interpret what the obligations mean in practice, separating mandatory requirements from recommended controls and operational evidence-chain needs.
Identify conflicts, ambiguities, privacy/minimization constraints, and implementation implications.
If relevant, include sizing/capacity/cost formulas and assumptions.
Save to: {folder}/raw_research/04_comparative_analysis.md
Target: 2000+ words with tables, assumptions, formulas if applicable, and source URLs.
```

### Agent 5 — Vendor / Product / Operational Fit
```
Research whether relevant vendors, products, services, or architectures can satisfy the obligations.
Use official product documentation first.
Compare retention, export, archive, compression, integrity, timestamping, signing, audit, local/cloud storage, data residency, and country-specific support.
Classify fit as native support, partial support, requires external system, unsupported, or unclear.
Save to: {folder}/raw_research/05_vendor_operational_fit.md
Target: 2000+ words with vendor/solution matrix and source URLs.
```

---

## Output Requirements

Use this file structure:

```
{topic}_{YYYYMM}/
├── RESEARCH_PLAN.md
├── RESEARCH_REPORT.md
├── report.html            # optional, if HTML requested
└── raw_research/
    ├── 01_legal_source_mapping.md
    ├── 02_applicability.md
    ├── 03_obligation_extraction.md
    ├── 04_comparative_analysis.md
    └── 05_vendor_operational_fit.md
```

The final report should include:
- Executive conclusion.
- Source table with legal status.
- Applicability matrix.
- Obligation comparison table.
- Retention-period table.
- Required-fields/content table.
- Practical implementation interpretation.
- Vendor/product fit matrix if relevant.
- Capacity/cost model if relevant.
- Caveats and unresolved legal questions.
- Source list with official URLs.

---

## Common Pitfalls

1. **Assuming every enterprise is covered.** Many laws apply only to service providers, licensees, public access providers, data controllers, critical infrastructure, or electronic system operators.
2. **Treating proposed rules as current law.** Consultation papers and draft rules must be labeled as proposed or pending.
3. **Confusing metadata with content.** Traffic data, communications data, access records, and content may have different legal treatment.
4. **Equating logs with compliance.** A firewall log alone may not prove user identity without DHCP, NAT, VPN, directory, Wi-Fi, or authentication logs.
5. **Ignoring privacy/minimization duties.** Long retention can conflict with data protection principles unless purpose, access control, deletion, and security are defined.
6. **Over-reading vendor claims.** Vendor reports or compliance templates are not legal compliance unless mapped to specific statutory requirements.
7. **Missing local-language sources.** For non-English jurisdictions, search in local language and verify against official gazette/regulator pages.
8. **Not separating legal certainty levels.** Label findings as confirmed binding, regulator guidance, proposed, secondary interpretation, implementation best practice, or unresolved.

---

## Lessons Learned

1. **Applicability first.** In policy research, subject status often matters more than technology. Determine whether the user is a provider, operator, controller, licensee, public access provider, or ordinary enterprise before extracting duties.
2. **Legal status must be explicit.** Draft rules, consultation papers, unofficial translations, vendor summaries, and regulator guidance must never be mixed with binding statutory obligations.
3. **Operational evidence chains matter.** A regulation may say "traffic data" or "audit trail" but implementation may require identity, DHCP, NAT, VPN, time sync, admin audit, and integrity logs together.
4. **Retention is not always maximization.** Data protection laws may require minimization, purpose limitation, and deletion even when cybersecurity teams prefer longer logging.
5. **Vendor fit is usually architectural.** Product features often satisfy parts of a requirement, but local timestamping, WORM, legal hold, data residency, or official export formats may require external systems.
