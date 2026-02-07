# Component Quality Checklist

> **Purpose:** Validate frontend component quality, UX patterns, and design system adherence
> **Agent:** UX Expert (Pixel)
> **Version:** 1.0.0

---

## Required Artifacts

Before starting validation, gather:
- Frontend specification (e.g., `docs/frontend/frontend-spec.md`)
- Component library or source code
- Design system documentation (if available)
- UI/UX wireframes or mockups (if available)
- Access to running application (if available)

---

## Validation Instructions

For each section below:
1. Read the requirement carefully
2. Look for evidence in frontend documentation or inspect code directly
3. Mark as:
   - ✅ **PASS**: Requirement clearly met
   - ❌ **FAIL**: Requirement not met or insufficient
   - ⚠️ **PARTIAL**: Some coverage but needs improvement
   - **N/A**: Not applicable to this project

---

## Section 1: Component Architecture

- [ ] Component hierarchy clearly defined
- [ ] Component naming follows consistent convention
- [ ] Atomic design methodology followed (atoms, molecules, organisms)
- [ ] Component responsibilities are single-purpose
- [ ] Component reusability considered
- [ ] Component composition patterns documented
- [ ] Shared components properly abstracted

---

## Section 2: Design System

- [ ] Design tokens defined (colors, spacing, typography)
- [ ] Color palette documented and consistent
- [ ] Typography scale defined
- [ ] Spacing system defined (4px/8px grid typical)
- [ ] Breakpoints for responsive design defined
- [ ] Icon system documented
- [ ] Design system usage enforced in components

---

## Section 3: Component Quality

- [ ] Components have clear props/API documentation
- [ ] PropTypes or TypeScript types defined
- [ ] Default props/values set where appropriate
- [ ] Component states handled (loading, error, empty, success)
- [ ] Error boundaries implemented for error handling
- [ ] Component variants documented (primary, secondary, etc.)
- [ ] Storybook or component showcase exists

---

## Section 4: User Experience

- [ ] Loading states provide feedback to users
- [ ] Error messages are user-friendly
- [ ] Empty states designed and implemented
- [ ] Success states provide clear confirmation
- [ ] Interactive elements have hover/focus/active states
- [ ] Feedback for user actions (clicks, submissions)
- [ ] Skeleton loaders or spinners for async operations

---

## Section 5: Accessibility (a11y)

- [ ] Semantic HTML used (header, nav, main, footer)
- [ ] ARIA labels on interactive elements
- [ ] Keyboard navigation supported (Tab, Enter, Esc)
- [ ] Focus indicators visible
- [ ] Color contrast meets WCAG AA standards
- [ ] Screen reader support considered
- [ ] Form labels associated with inputs
- [ ] Alt text on images

---

## Section 6: Responsiveness

- [ ] Mobile-first approach or mobile breakpoints defined
- [ ] Layouts adapt to different screen sizes
- [ ] Touch targets appropriately sized (44px minimum)
- [ ] Responsive images (srcset or CSS)
- [ ] No horizontal scroll on mobile
- [ ] Typography scales responsively
- [ ] Navigation adapts for mobile (hamburger menu, etc.)

---

## Section 7: Performance

- [ ] Components lazy-loaded where appropriate
- [ ] Images optimized (WebP, responsive, lazy-loaded)
- [ ] Unnecessary re-renders minimized (React.memo, useMemo)
- [ ] Large lists virtualized (if applicable)
- [ ] Bundle size optimized (code splitting)
- [ ] CSS-in-JS or CSS Modules prevent style leaks
- [ ] No performance anti-patterns (inline function props, etc.)

---

## Section 8: Code Quality

- [ ] Components follow linting rules (ESLint, Prettier)
- [ ] No console.log or debug code in production
- [ ] No unused imports or variables
- [ ] No hardcoded strings (i18n considered)
- [ ] Component file structure consistent
- [ ] Tests exist for critical components
- [ ] Code follows project conventions

---

## Section 9: Pattern Consistency

- [ ] Button styles consistent across app
- [ ] Form input styles consistent
- [ ] Card/panel styles consistent
- [ ] Modal/dialog patterns consistent
- [ ] Navigation patterns consistent
- [ ] No duplicate/redundant components
- [ ] Design patterns documented

---

## Section 10: Technical Debt

- [ ] Component redundancy identified (duplicate buttons, etc.)
- [ ] Inconsistent styling identified
- [ ] Missing accessibility features identified
- [ ] Performance bottlenecks identified
- [ ] Refactoring opportunities documented
- [ ] Legacy patterns flagged for modernization

---

## Final Report Template

```markdown
# Component Quality Validation Report

## Summary
- **Status**: [APPROVED / NEEDS WORK / BLOCKED]
- **Pass Rate**: [X/Y items passed]
- **Critical Issues**: [count]
- **Accessibility Issues**: [count]
- **UX Issues**: [count]

## Findings by Section
| Section | Status | Pass Rate |
|---------|--------|-----------|
| Component Architecture | ✅/⚠️/❌ | X/Y |
| Design System | ✅/⚠️/❌ | X/Y |
| Accessibility | ✅/⚠️/❌ | X/Y |
| ... | ... | ... |

## Critical Issues
[List any critical gaps in UX, accessibility, or quality]

## Accessibility Gaps
[List missing ARIA labels, keyboard nav issues, contrast issues]

## UX Issues
[List confusing flows, missing feedback, poor error handling]

## Performance Issues
[List bundle size issues, render performance, image optimization]

## Design Consistency Issues
[List pattern redundancy, style inconsistencies]

## Recommendations
[Specific improvements needed, prioritized]

## Technical Debt Summary
- Duplicate components: [count]
- Accessibility gaps: [count]
- Missing responsive breakpoints: [count]
- Performance optimizations needed: [count]

## Approval Status
- [ ] No critical accessibility issues
- [ ] Design system documented and enforced
- [ ] Component quality meets standards
- [ ] UX patterns consistent and user-friendly
- [ ] Frontend is production-ready
```

---

## Pass/Fail Criteria

- **APPROVED**: 90%+ items pass, no critical accessibility/UX issues
- **NEEDS WORK**: <90% pass rate OR any critical issues present
- **BLOCKED**: Missing accessibility (keyboard nav, ARIA) OR no design system

---

## Common Issues Checklist

| Issue | Severity | Check |
|-------|----------|-------|
| Missing keyboard navigation | 🚨 CRITICAL | All interactive elements |
| Color contrast < WCAG AA | 🚨 CRITICAL | All text/backgrounds |
| No loading/error states | ⚠️ HIGH | Async components |
| Missing alt text on images | ⚠️ HIGH | All images |
| Duplicate button styles | ⚠️ MEDIUM | All buttons |
| No responsive breakpoints | ⚠️ HIGH | All layouts |
| Hardcoded strings (no i18n) | ⚠️ MEDIUM | All text |

---

**Version:** 1.0.0
**Last Updated:** 2026-02-07
**Owner:** UX Expert (Pixel)
