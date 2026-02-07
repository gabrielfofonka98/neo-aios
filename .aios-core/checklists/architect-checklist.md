# Architect Checklist

> **Purpose:** Validate system architecture documentation completeness and quality
> **Agent:** Architect (Aria)
> **Version:** 1.0.0

---

## Required Artifacts

Before starting validation, gather:
- System architecture document (e.g., `docs/architecture/system-architecture.md`)
- Technical stack documentation
- Architectural Decision Records (ADRs)
- System diagrams (if available)

---

## Validation Instructions

For each section below:
1. Read the requirement carefully
2. Look for evidence in the architecture documentation
3. Mark as:
   - ✅ **PASS**: Requirement clearly met
   - ❌ **FAIL**: Requirement not met or insufficient
   - ⚠️ **PARTIAL**: Some coverage but needs improvement
   - **N/A**: Not applicable to this project

---

## Section 1: System Overview

- [ ] Project purpose and goals clearly stated
- [ ] Target users and use cases identified
- [ ] System boundaries defined (what's in scope, what's not)
- [ ] High-level architecture diagram present
- [ ] Technology stack documented (languages, frameworks, databases)

---

## Section 2: Component Architecture

- [ ] All major components/modules identified
- [ ] Component responsibilities clearly defined
- [ ] Component boundaries and interfaces documented
- [ ] Component dependencies mapped
- [ ] Data flow between components explained

---

## Section 3: Technical Decisions

- [ ] Key architectural patterns documented (MVC, microservices, etc.)
- [ ] Technology choices justified (why this stack?)
- [ ] Trade-offs and alternatives considered
- [ ] Scalability approach defined
- [ ] Performance considerations documented

---

## Section 4: Infrastructure & Deployment

- [ ] Deployment architecture documented
- [ ] Infrastructure requirements specified
- [ ] Environment strategy defined (dev, staging, prod)
- [ ] CI/CD pipeline approach outlined
- [ ] Monitoring and observability strategy

---

## Section 5: Security & Compliance

- [ ] Authentication/authorization strategy defined
- [ ] Data protection approach documented
- [ ] Security best practices identified
- [ ] Compliance requirements addressed (if applicable)
- [ ] Security testing strategy outlined

---

## Section 6: Data Architecture

- [ ] Data models documented
- [ ] Database schema approach defined
- [ ] Data storage strategy explained
- [ ] Data migration plan (if applicable)
- [ ] Backup and recovery strategy

---

## Section 7: Quality & Testing

- [ ] Testing strategy defined (unit, integration, e2e)
- [ ] Code quality standards documented
- [ ] Performance benchmarks identified
- [ ] Error handling approach defined
- [ ] Logging strategy documented

---

## Section 8: Technical Debt

- [ ] Known technical debt identified
- [ ] Technical debt prioritized (critical/high/medium/low)
- [ ] Refactoring opportunities documented
- [ ] Legacy system integration challenges noted
- [ ] Mitigation strategies proposed

---

## Final Report Template

```markdown
# Architecture Validation Report

## Summary
- **Status**: [APPROVED / NEEDS WORK]
- **Pass Rate**: [X/Y items passed]
- **Critical Issues**: [count]

## Findings by Section
[List sections with pass/fail/partial status]

## Critical Issues
[List any critical gaps or problems]

## Recommendations
[Specific improvements needed]

## Approval Status
- [ ] Architecture documentation is complete
- [ ] Ready for development phase
```

---

## Pass/Fail Criteria

- **APPROVED**: 90%+ items pass, no critical issues
- **NEEDS WORK**: <90% pass rate OR any critical issues present
- **BLOCKED**: Missing required artifacts

---

**Version:** 1.0.0
**Last Updated:** 2026-02-07
**Owner:** Architect (Aria)
