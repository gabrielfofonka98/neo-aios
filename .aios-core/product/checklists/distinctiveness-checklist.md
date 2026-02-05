# Distinctiveness Checklist

> Use this checklist to validate that your UI is distinctive, not generic.

---

## Quick Test

**Could users recognize your product without the logo?**

- [ ] **Yes** → You might be distinctive
- [ ] **No** → Your design is probably generic

---

## Typography Check

### Font Selection

- [ ] Primary font is NOT Inter, Roboto, or Open Sans
- [ ] Font choice reflects brand personality
- [ ] Font pairing is intentional (if using 2 fonts)
- [ ] Typography creates recognizable voice

### Hierarchy

- [ ] Type scale is custom (not default Tailwind)
- [ ] Headings have distinctive treatment
- [ ] Weight usage is intentional and consistent

**🚨 Red Flags:**
- Using system fonts without customization
- Default framework typography
- Same font as competitors

---

## Color Check

### Primary Colors

- [ ] Primary color is NOT Tailwind blue-500 (`#3B82F6`)
- [ ] Colors have documented emotional intent
- [ ] Palette is customized, not framework default

### Gradients

- [ ] No purple-to-pink gradients (unless brand-specific)
- [ ] No blue-to-cyan gradients
- [ ] Gradient direction is intentional

### Neutrals

- [ ] Using off-black, not pure `#000000`
- [ ] Using off-white, not pure `#FFFFFF`
- [ ] Neutrals have brand undertone (warm/cool)

**🚨 Red Flags:**
- Tailwind default color palette
- Competitor-similar color scheme
- Trendy gradients without brand purpose

---

## Layout Check

### Structure

- [ ] Homepage is NOT "Hero + 3 feature cards"
- [ ] Layout serves content, not template
- [ ] Section arrangement is thoughtful

### Components

- [ ] Card designs are customized
- [ ] Buttons have distinct style
- [ ] Forms have personality
- [ ] Navigation is memorable

**🚨 Red Flags:**
- Bootstrap/Tailwind template feeling
- "Every SaaS looks like this" vibe
- Copy-paste component library

---

## Motion Check

### Animation Purpose

- [ ] Every animation communicates something
- [ ] No `transition: all 300ms ease` everywhere
- [ ] Motion reflects brand (snappy vs smooth)

### Timing

- [ ] Duration varies by context (not uniform)
- [ ] Easing is intentional (not default ease)
- [ ] Micro-interactions feel polished

**🚨 Red Flags:**
- Generic 300ms on everything
- Linear easing on UI elements
- Animation for decoration only

---

## Distinctiveness Score

Count your checkmarks:

| Score | Assessment |
|-------|------------|
| 0-5 | ⛔ Generic - Major redesign needed |
| 6-10 | ⚠️ Forgettable - Needs distinctive elements |
| 11-15 | ✅ Distinctive - Minor polish needed |
| 16-18 | 🌟 Memorable - Ship with confidence |

---

## Action Items (If Generic)

### Quick Wins (30 min)
1. Change primary font
2. Customize primary color
3. Adjust neutral undertone
4. Update button style

### Medium Effort (2-4 hours)
1. Create custom type scale
2. Design custom card component
3. Define animation personality
4. Redesign key interaction

### Major Investment (1+ day)
1. Complete color system redesign
2. Custom layout for key pages
3. Motion design language
4. Component library customization

---

## Competitor Check

Before shipping, compare to competitors:

1. **Screenshot your UI**
2. **Screenshot 3 competitors**
3. **Show to stranger**
4. **Ask: "Which is different?"**

If they can't tell yours apart → not distinctive enough.

---

## Final Approval

### Sign-off Requirements

- [ ] All red flag items addressed
- [ ] Distinctiveness score ≥ 11
- [ ] Competitor check passed
- [ ] Designer approved
- [ ] Stakeholder approved

### Documentation

Record your distinctive elements:

| Element | How It's Distinctive |
|---------|---------------------|
| Font | [e.g., "Using Söhne for modern tech feel"] |
| Color | [e.g., "Deep purple for premium positioning"] |
| Layout | [e.g., "Asymmetric hero with floating cards"] |
| Motion | [e.g., "Snappy 150ms with expo easing"] |

---

*Distinctiveness checklist for AIOS products. Version 1.0*
