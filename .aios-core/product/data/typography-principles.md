# Typography Principles

> Typography is voice made visible.

---

## Core Principle

**Typography establishes trust and personality before users read a single word.**

A product with thoughtful typography feels professional. A product with default typography feels rushed.

---

## Type Scale

Use a consistent scale based on a modular ratio.

### Recommended Scale (1.25 ratio)

| Name | Size | Use |
|------|------|-----|
| `xs` | 12px | Captions, metadata, legal |
| `sm` | 14px | Secondary text, labels |
| `base` | 16px | Body text (default) |
| `lg` | 20px | Subheadings, emphasis |
| `xl` | 25px | Section headings |
| `2xl` | 31px | Page titles |
| `3xl` | 39px | Hero text |
| `4xl` | 49px | Display, marketing |

**Rule:** Never use arbitrary sizes. Stick to the scale.

---

## Font Selection

### Categories and Personality

| Category | Personality | Use When |
|----------|-------------|----------|
| **Serif** | Authority, tradition, elegance | Finance, legal, luxury |
| **Sans-serif** | Modern, clean, neutral | Tech, SaaS, productivity |
| **Display** | Bold, distinctive, memorable | Headlines, marketing |
| **Mono** | Technical, code, data | Developer tools, terminals |

### Pairing Rules

1. **One family for UI** - Consistency over variety
2. **Max 2 families per product** - Headings + body
3. **Contrast in pairings** - Serif + sans, not sans + sans
4. **Test at all sizes** - Some fonts fail at small sizes

### Fonts to Avoid (as primaries)

- Inter, Roboto, Open Sans (too default)
- System fonts without fallbacks
- Decorative fonts for body text
- Free fonts with incomplete character sets

---

## Hierarchy

### Visual Hierarchy Rules

1. **Size** - Larger = more important
2. **Weight** - Bolder = more important
3. **Color** - Higher contrast = more important
4. **Space** - More space = more important

### Standard Hierarchy

```
Page Title     →  2xl, bold, high contrast
Section Head   →  xl, semibold
Subsection     →  lg, medium
Body           →  base, regular
Caption        →  sm, regular, lower contrast
```

### Never Do

- ❌ All caps for body text
- ❌ Bold for long paragraphs
- ❌ Italic for more than a sentence
- ❌ Underline for non-links

---

## Line Length

### Optimal Reading Width

| Context | Characters | Reason |
|---------|------------|--------|
| Body text | 50-75 chars | Optimal for reading |
| Captions | 40-60 chars | Shorter = easier scan |
| Headlines | 20-35 chars | Impact over comfort |

**Rule:** If a line is too long, users' eyes get lost returning to the next line.

### Implementation

```css
/* Body text container */
.prose {
  max-width: 65ch; /* ch = character width */
}
```

---

## Line Height

### Context-Based Line Height

| Size | Line Height | Reason |
|------|-------------|--------|
| Body (16px) | 1.5 - 1.6 | Comfortable reading |
| Large (24px+) | 1.2 - 1.3 | Headlines need less |
| Small (12px) | 1.4 - 1.5 | Small text needs air |

**Rule:** Larger text needs less line height. Smaller text needs more.

---

## Letter Spacing

### When to Adjust

| Scenario | Adjustment |
|----------|------------|
| ALL CAPS | +0.05em to +0.1em |
| Large display | -0.01em to -0.02em |
| Body text | None (trust the font) |
| Tight headlines | -0.02em max |

**Rule:** Only adjust when the font demands it. Trust type designers.

---

## Weights

### Standard Weight Usage

| Weight | Use |
|--------|-----|
| 300 (Light) | Large display text only |
| 400 (Regular) | Body text, default |
| 500 (Medium) | Subtle emphasis, labels |
| 600 (Semibold) | Headings, buttons |
| 700 (Bold) | Strong emphasis, titles |

**Rule:** If using more than 3-4 weights, your hierarchy is unclear.

---

## Responsive Typography

### Mobile Considerations

- Minimum 16px for body text (avoids zoom on iOS)
- Increase line height slightly on mobile
- Reduce heading sizes proportionally
- Test thumb-scrolling readability

### Fluid Typography (Optional)

```css
/* Scales from 16px at 320px to 20px at 1920px */
font-size: clamp(1rem, 0.5rem + 1vw, 1.25rem);
```

---

## Accessibility

### Requirements

- [ ] Body text minimum 16px
- [ ] Color contrast ratio ≥ 4.5:1 (AA) or ≥ 7:1 (AAA)
- [ ] Don't rely on color alone for meaning
- [ ] Allow user font scaling
- [ ] Test with screen readers

### Common Mistakes

- ❌ Light gray text on white (#999 on #FFF)
- ❌ Placeholder text as labels
- ❌ Fixed font sizes (use rem, not px)
- ❌ Preventing zoom on mobile

---

## Checklist

Before shipping, verify:

- [ ] Type scale is consistent
- [ ] Max 2 font families used
- [ ] Hierarchy is clear without reading
- [ ] Line length is controlled
- [ ] Contrast meets accessibility standards
- [ ] Responsive behavior tested
- [ ] No default/system fonts without intent

---

*Typography principles for AIOS products. Version 1.0*
