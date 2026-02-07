# Database Design Checklist

> **Purpose:** Validate database schema design, security, and quality
> **Agent:** Data Engineer (Dara)
> **Version:** 1.0.0

---

## Required Artifacts

Before starting validation, gather:
- Database schema documentation (e.g., `supabase/docs/SCHEMA.md`)
- Database audit report (e.g., `supabase/docs/DB-AUDIT.md`)
- Migration files (if available)
- Entity Relationship Diagram (ERD) (if available)
- Access to database for inspection (read-only)

---

## Validation Instructions

For each section below:
1. Read the requirement carefully
2. Look for evidence in schema documentation or inspect database directly
3. Mark as:
   - ✅ **PASS**: Requirement clearly met
   - ❌ **FAIL**: Requirement not met or insufficient
   - ⚠️ **PARTIAL**: Some coverage but needs improvement
   - **N/A**: Not applicable to this project

---

## Section 1: Schema Design

- [ ] All tables documented with purpose and description
- [ ] Table naming follows consistent convention (snake_case)
- [ ] Column naming follows consistent convention
- [ ] Primary keys defined on all tables
- [ ] Foreign keys properly defined with relationships
- [ ] Appropriate data types chosen for each column
- [ ] NOT NULL constraints applied where appropriate
- [ ] DEFAULT values set where appropriate

---

## Section 2: Indexes & Performance

- [ ] Primary key indexes exist on all tables
- [ ] Foreign key columns are indexed
- [ ] Frequently queried columns have indexes
- [ ] Composite indexes created for multi-column queries
- [ ] No missing indexes on high-traffic queries
- [ ] No redundant/duplicate indexes
- [ ] Full-text search indexes (if needed)

---

## Section 3: Security (RLS & Policies)

- [ ] Row Level Security (RLS) enabled on all tables
- [ ] RLS policies defined for SELECT operations
- [ ] RLS policies defined for INSERT operations
- [ ] RLS policies defined for UPDATE operations
- [ ] RLS policies defined for DELETE operations
- [ ] Policies follow principle of least privilege
- [ ] No tables have public access without RLS
- [ ] Service role access properly restricted

---

## Section 4: Data Integrity

- [ ] UNIQUE constraints on columns requiring uniqueness
- [ ] CHECK constraints for data validation
- [ ] Referential integrity maintained (CASCADE rules)
- [ ] ENUM types or lookup tables for fixed value sets
- [ ] Timestamps (created_at, updated_at) on audit tables
- [ ] Soft delete approach defined (if applicable)
- [ ] Data validation rules documented

---

## Section 5: Normalization & Structure

- [ ] Schema follows appropriate normal form (3NF typical)
- [ ] No redundant data storage
- [ ] Junction tables for many-to-many relationships
- [ ] Hierarchical data properly modeled
- [ ] JSON/JSONB columns used appropriately (not overused)
- [ ] Denormalization justified where applied

---

## Section 6: Functions & Triggers

- [ ] Database functions documented
- [ ] Trigger logic documented and justified
- [ ] Triggers don't create infinite loops
- [ ] Functions use SECURITY DEFINER appropriately
- [ ] Functions have proper error handling
- [ ] No business logic in database (unless intentional)

---

## Section 7: Migrations & Versioning

- [ ] Migration files exist and are sequential
- [ ] Migrations are idempotent (can run multiple times safely)
- [ ] Rollback migrations exist for critical changes
- [ ] Migration naming follows convention
- [ ] DDL changes properly tracked
- [ ] Seed data migrations separated from schema

---

## Section 8: Documentation

- [ ] Schema diagram (ERD) exists and is current
- [ ] Table relationships clearly documented
- [ ] Column descriptions provided
- [ ] Complex queries documented
- [ ] Access patterns documented
- [ ] Known limitations documented

---

## Section 9: Technical Debt

- [ ] Missing indexes identified
- [ ] Missing RLS policies identified
- [ ] Tables without primary keys identified
- [ ] N+1 query risks identified
- [ ] Slow queries documented
- [ ] Schema refactoring needs documented

---

## Final Report Template

```markdown
# Database Design Validation Report

## Summary
- **Status**: [APPROVED / NEEDS WORK / BLOCKED]
- **Pass Rate**: [X/Y items passed]
- **Critical Issues**: [count]
- **Security Issues**: [count]

## Findings by Section
| Section | Status | Pass Rate |
|---------|--------|-----------|
| Schema Design | ✅/⚠️/❌ | X/Y |
| Indexes | ✅/⚠️/❌ | X/Y |
| Security (RLS) | ✅/⚠️/❌ | X/Y |
| ... | ... | ... |

## Critical Issues
[List any critical gaps or security risks]

## Security Risks
[List RLS gaps, missing policies, public access issues]

## Performance Issues
[List missing indexes, slow queries, N+1 risks]

## Recommendations
[Specific improvements needed, prioritized]

## Technical Debt Summary
- Missing indexes: [count]
- Missing RLS policies: [count]
- Schema refactoring needs: [count]

## Approval Status
- [ ] No critical security issues
- [ ] No missing RLS policies
- [ ] All tables indexed appropriately
- [ ] Database design is production-ready
```

---

## Pass/Fail Criteria

- **APPROVED**: 90%+ items pass, no critical security issues
- **NEEDS WORK**: <90% pass rate OR any critical issues present
- **BLOCKED**: Missing RLS on any table OR missing primary keys

---

## Common Issues Checklist

| Issue | Severity | Check |
|-------|----------|-------|
| Table without RLS enabled | 🚨 CRITICAL | All tables |
| Table without primary key | 🚨 CRITICAL | All tables |
| Foreign key without index | ⚠️ HIGH | All FKs |
| Missing created_at/updated_at | ⚠️ MEDIUM | Audit tables |
| Public access without policy | 🚨 CRITICAL | All tables |
| Service role unrestricted | 🚨 CRITICAL | All tables |

---

**Version:** 1.0.0
**Last Updated:** 2026-02-07
**Owner:** Data Engineer (Dara)
