# Color System Principles

> Color is not decoration. Color is emotion.

---

## Core Principle

**Every color must answer: "What do I want users to feel?"**

Color choices that can't be explained shouldn't exist in your palette.

---

## Color Psychology

### Primary Emotions

| Color | Emotion | Use For |
|-------|---------|---------|
| **Blue** | Trust, calm, professional | Finance, B2B, reliability |
| **Green** | Growth, success, nature | Health, money, environment |
| **Red** | Urgency, danger, passion | Alerts, actions, food |
| **Orange** | Energy, warmth, creativity | CTAs, entertainment |
| **Purple** | Luxury, wisdom, creativity | Premium, creative tools |
| **Yellow** | Optimism, caution, warmth | Warnings, happiness |
| **Black** | Sophistication, power | Luxury, authority |
| **White** | Clean, minimal, space | Breathing room, purity |

### Important Nuances

- Saturation affects intensity (vibrant vs muted)
- Brightness affects mood (light = positive, dark = serious)
- Cultural context matters (white = mourning in some cultures)

---

## Palette Structure

### Recommended Structure

```
Primary      →  Brand color (1)
Secondary    →  Complement (1)
Accent       →  Attention/CTA (1)
Neutrals     →  Grays (5-7 shades)
Semantic     →  Success, Warning, Error, Info
```

### Total Colors

| Type | Count |
|------|-------|
| Brand colors | 2-3 |
| Neutrals | 5-7 |
| Semantic | 4 |
| **Total** | ~15 max |

**Rule:** If you need more colors, your design system is unclear.

---

## Neutral Scale

### Building Neutrals

Don't use pure grays. Add warmth or coolness to match brand.

| Shade | Lightness | Use |
|-------|-----------|-----|
| 50 | 97% | Background, hover states |
| 100 | 93% | Subtle backgrounds |
| 200 | 85% | Borders, dividers |
| 300 | 75% | Disabled states |
| 400 | 60% | Placeholder text |
| 500 | 45% | Secondary text |
| 600 | 35% | Primary text (light bg) |
| 700 | 25% | Headings |
| 800 | 15% | Primary text (always works) |
| 900 | 8% | Darkest elements |

### Warm vs Cool

```css
/* Cool neutral (blue undertone) */
--neutral-500: hsl(210, 5%, 45%);

/* Warm neutral (yellow undertone) */
--neutral-500: hsl(35, 5%, 45%);
```

---

## Semantic Colors

### Standard Meanings

| Semantic | Color | Use |
|----------|-------|-----|
| **Success** | Green | Completed, positive |
| **Warning** | Yellow/Orange | Caution, attention |
| **Error** | Red | Failed, danger |
| **Info** | Blue | Informational |

### Each Semantic Needs

```
Base       →  Primary semantic color
Light      →  Background for banners
Dark       →  Hover/pressed states
Text       →  Accessible text on light bg
```

---

## Contrast & Accessibility

### WCAG Requirements

| Level | Ratio | For |
|-------|-------|-----|
| AA | 4.5:1 | Normal text |
| AA | 3:1 | Large text (18px+) |
| AAA | 7:1 | Enhanced readability |

### Testing Tools

- [Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Who Can Use](https://whocanuse.com/)
- Browser DevTools color contrast inspection

### Common Mistakes

- ❌ Light gray text (#999) on white
- ❌ Low contrast placeholder text
- ❌ Relying on color alone for status
- ❌ Colorblind-unfriendly green/red combos

---

## Dark Mode

### Not Just Inverted

Dark mode isn't swapping white and black. It's a complete palette shift.

### Dark Mode Rules

1. **Use off-black backgrounds** - Pure black (#000) is harsh
2. **Reduce contrast slightly** - White on dark is more intense
3. **Desaturate colors** - Bright colors strain eyes in dark
4. **Elevate with lightness** - Higher surfaces = lighter color
5. **Test colored text** - Many colors fail on dark backgrounds

### Elevation in Dark Mode

| Elevation | Background |
|-----------|------------|
| Base | `#121212` |
| Level 1 | `#1E1E1E` |
| Level 2 | `#252525` |
| Level 3 | `#2D2D2D` |

---

## Anti-Patterns (PROHIBITED)

### Colors to Avoid

❌ **Tailwind defaults without customization:**
- `#3B82F6` (blue-500) as primary
- `#EF4444` (red-500) for all errors
- Default gradients

❌ **Generic palettes:**
- Pure black `#000000`
- Pure white `#FFFFFF` (prefer off-white)
- Equal saturation across all colors

❌ **Trendy but tired:**
- Purple-to-pink gradients
- Blue-to-cyan gradients
- Rainbow gradients

### Instead

✅ Choose colors with brand intent
✅ Customize framework colors
✅ Use off-black/off-white
✅ Match saturation to brand energy

---

## Implementation

### CSS Custom Properties

```css
:root {
  /* Brand */
  --color-primary: hsl(220, 70%, 50%);
  --color-secondary: hsl(280, 60%, 50%);

  /* Neutrals */
  --color-neutral-100: hsl(220, 10%, 95%);
  --color-neutral-800: hsl(220, 10%, 15%);

  /* Semantic */
  --color-success: hsl(142, 70%, 45%);
  --color-warning: hsl(38, 95%, 50%);
  --color-error: hsl(0, 70%, 55%);
}

[data-theme="dark"] {
  --color-neutral-100: hsl(220, 10%, 12%);
  --color-neutral-800: hsl(220, 10%, 90%);
  /* ... adjust all colors */
}
```

---

## Checklist

Before shipping, verify:

- [ ] Primary color has emotional intent documented
- [ ] Neutral scale has brand undertone
- [ ] All text passes contrast requirements
- [ ] Semantic colors are consistent
- [ ] Dark mode is properly designed (not inverted)
- [ ] No Tailwind defaults used without customization
- [ ] Color is never the only indicator of status

---

*Color system principles for AIOS products. Version 1.0*
