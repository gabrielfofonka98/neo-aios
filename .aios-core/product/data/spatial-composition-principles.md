# Spatial Composition Principles

> Whitespace is not empty space. It's the pause between notes that makes music.

---

## Core Principle

**Space communicates hierarchy, relationship, and quality.**

Cramped layouts feel desperate. Generous layouts feel confident.

---

## The Whitespace Mindset

### Why Space Matters

| More Space | Less Space |
|------------|------------|
| Premium feel | Cluttered feel |
| Clear hierarchy | Confusing hierarchy |
| Focused attention | Scattered attention |
| Calm, confident | Anxious, busy |

### The Rule

**When in doubt, add more space.**

It's easier to reduce space than to realize you need more.

---

## Spacing Scale

### Consistent Scale (Base 4)

| Token | Size | Use |
|-------|------|-----|
| `1` | 4px | Tight grouping, icons |
| `2` | 8px | Related elements |
| `3` | 12px | Small gaps |
| `4` | 16px | Standard spacing |
| `5` | 20px | Medium separation |
| `6` | 24px | Section padding |
| `8` | 32px | Component separation |
| `10` | 40px | Section separation |
| `12` | 48px | Large gaps |
| `16` | 64px | Page sections |
| `20` | 80px | Hero spacing |
| `24` | 96px | Maximum breathing room |

### Implementation

```css
:root {
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-4: 1rem;     /* 16px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-12: 3rem;    /* 48px */
  --space-16: 4rem;    /* 64px */
}
```

---

## Grouping & Proximity

### The Proximity Principle

**Elements that are related should be close together.**
**Elements that are unrelated should be far apart.**

### Visual Example

```
WRONG:                    RIGHT:
┌─────────────────┐      ┌─────────────────┐
│ Label           │      │ Label           │
│                 │      │ Input           │
│                 │      │                 │
│ Input           │      │ Label           │
│                 │      │ Input           │
│                 │      │                 │
│ Label           │      │ Label           │
│                 │      │ Input           │
│ Input           │      └─────────────────┘
└─────────────────┘
(equal spacing)          (grouped by relation)
```

### Spacing Ratios

- Within a group: `space-2` to `space-4`
- Between groups: `space-6` to `space-8`
- Between sections: `space-12` to `space-16`

---

## Grid System

### Standard Grid

| Screen Size | Columns | Gutter | Margin |
|-------------|---------|--------|--------|
| Mobile (<640px) | 4 | 16px | 16px |
| Tablet (640-1024px) | 8 | 24px | 32px |
| Desktop (>1024px) | 12 | 24px | 48px+ |

### Container Widths

| Name | Width | Use |
|------|-------|-----|
| `sm` | 640px | Narrow content (forms) |
| `md` | 768px | Reading content |
| `lg` | 1024px | Standard apps |
| `xl` | 1280px | Wide apps |
| `2xl` | 1536px | Maximum |

### Rule

**Content should rarely span full width on large screens.**

Reading becomes difficult. Use max-width containers.

---

## Component Spacing

### Internal Padding

| Component | Padding |
|-----------|---------|
| Button | `8px 16px` (small) / `12px 24px` (default) |
| Card | `16px` to `24px` |
| Modal | `24px` to `32px` |
| Input | `8px 12px` |
| Navigation | `16px` horizontal |

### External Margins

| Context | Margin |
|---------|--------|
| Between form fields | `16px` to `24px` |
| Between cards | `16px` to `24px` |
| Between sections | `48px` to `96px` |
| Page top/bottom | `48px` minimum |

---

## Responsive Spacing

### Scaling Strategy

Space should breathe with viewport size.

```css
/* Mobile-first with responsive increases */
.section {
  padding: var(--space-6);  /* 24px on mobile */
}

@media (min-width: 768px) {
  .section {
    padding: var(--space-12); /* 48px on tablet */
  }
}

@media (min-width: 1024px) {
  .section {
    padding: var(--space-16); /* 64px on desktop */
  }
}
```

### Never Do

- ❌ Same spacing across all breakpoints
- ❌ Reduce spacing on larger screens
- ❌ Arbitrary responsive values

---

## Visual Hierarchy with Space

### Hierarchy Rules

1. **More important = more space around it**
2. **Titles get more space than body**
3. **CTAs get more space than secondary actions**
4. **Headers need space below, not above**

### Example: Page Header

```
├─ 64px top margin
│
│  HEADING          ←  Large, prominent
│
├─ 24px gap
│
│  Subtext          ←  Secondary info
│
├─ 32px gap
│
│  [CTA Button]     ←  Clear action
│
├─ 48px to content
```

---

## Alignment

### Principles

1. **Left-align text** (in LTR languages)
2. **Align to grid** (not arbitrary positions)
3. **Consistent alignment** within sections
4. **Center sparingly** (for emphasis only)

### Common Mistakes

- ❌ Centered body text (hard to read)
- ❌ Right-aligned forms (unexpected)
- ❌ Misaligned elements in a group
- ❌ Centered everything (loses hierarchy)

---

## Layout Anti-Patterns

### ❌ Wall of Content

No spacing, no grouping, no breathing room.

**Fix:** Add generous padding, group related items.

### ❌ False Economy

"We need to fit more above the fold!"

**Fix:** Let users scroll. Cluttered above-fold is worse than clean below-fold.

### ❌ Inconsistent Spacing

8px here, 13px there, 20px somewhere else.

**Fix:** Use spacing scale consistently.

### ❌ Edge-to-Edge on Desktop

Content stretching full width on 1920px screens.

**Fix:** Max-width containers with generous margins.

---

## Tools & Techniques

### Squint Test

Squint at your design:
- Can you see the groups?
- Is the hierarchy clear?
- Are the spaces consistent?

If not, your spacing needs work.

### The Newspaper Test

Would this pass as a well-designed newspaper?
- Clear sections
- Obvious hierarchy
- Generous margins
- Comfortable reading

### 8-Point Grid

Round everything to multiples of 8:
- `8, 16, 24, 32, 40, 48, 56, 64...`
- Creates natural consistency
- Easy to maintain scale

---

## Checklist

Before shipping:

- [ ] Spacing uses consistent scale (not arbitrary values)
- [ ] Related elements are closer than unrelated
- [ ] Page sections have generous separation
- [ ] Content has max-width containers
- [ ] Responsive spacing increases with viewport
- [ ] Alignment is consistent within groups
- [ ] Squint test passes

---

*Spatial composition principles for AIOS products. Version 1.0*
