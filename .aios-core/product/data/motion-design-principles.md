# Motion Design Principles

> Animation without purpose is distraction. Animation with purpose is magic.

---

## Core Principle

**Every animation must earn its existence by communicating something.**

If you can't explain what an animation communicates, delete it.

---

## Purpose Categories

### What Animations Should Do

| Purpose | Example |
|---------|---------|
| **Guide attention** | New element fades in |
| **Show causality** | Button press → action result |
| **Indicate state** | Loading, success, error |
| **Create continuity** | Page transitions |
| **Provide feedback** | Hover, click responses |
| **Establish hierarchy** | Staggered reveals |

### What Animations Should NOT Do

- ❌ Decorate without meaning
- ❌ Delay user actions
- ❌ Distract from content
- ❌ Show off technical skill
- ❌ Create motion sickness

---

## Duration Guidelines

### Duration by Distance/Importance

| Movement | Duration | Examples |
|----------|----------|----------|
| Micro (subtle) | 100-150ms | Button hover, checkbox |
| Small | 150-200ms | Dropdown open, tooltip |
| Medium | 200-300ms | Modal open, accordion |
| Large | 300-500ms | Page transition, drawer |
| Emphasis | 500-800ms | Success celebration |

### Rules

1. **Larger movements need more time** - Eye needs to track
2. **Frequent animations should be faster** - Don't annoy users
3. **Important animations can be slower** - Draw attention
4. **Never exceed 800ms** - Feels sluggish

---

## Easing Functions

### Standard Easings

| Easing | Feel | Use For |
|--------|------|---------|
| `ease-out` | Snappy, responsive | Most UI animations |
| `ease-in-out` | Smooth, natural | Position changes |
| `ease-in` | Accelerating | Elements leaving |
| `linear` | Mechanical | Progress bars only |

### Custom Curves (Recommended)

```css
/* Snappy entrance */
--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);

/* Smooth movement */
--ease-in-out-cubic: cubic-bezier(0.65, 0, 0.35, 1);

/* Bouncy (use sparingly) */
--ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
```

### Never Use

- ❌ `linear` for UI movement (feels robotic)
- ❌ Bouncy easing for professional tools
- ❌ Same easing for everything

---

## Common Patterns

### Fade In

```css
.fade-in {
  animation: fadeIn 200ms ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

### Slide Up (Modals, Toasts)

```css
.slide-up {
  animation: slideUp 300ms ease-out forwards;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### Scale In (Buttons, Cards)

```css
.scale-in {
  animation: scaleIn 200ms ease-out forwards;
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

### Staggered Reveal

```css
.stagger-item {
  animation: fadeIn 200ms ease-out forwards;
  animation-delay: calc(var(--index) * 50ms);
}
```

---

## Interaction Feedback

### Hover States

- **Duration:** 100-150ms
- **Effect:** Subtle color/scale change
- **Rule:** Faster = more responsive feel

```css
.button {
  transition: background-color 150ms ease-out;
}
```

### Click/Press States

- **Duration:** 50-100ms
- **Effect:** Scale down slightly
- **Rule:** Immediate = tactile feel

```css
.button:active {
  transform: scale(0.98);
  transition: transform 50ms ease-out;
}
```

### Focus States

- **Duration:** 150ms
- **Effect:** Ring or outline
- **Rule:** Must be visible for accessibility

```css
.button:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
  transition: outline 150ms ease-out;
}
```

---

## Loading States

### Hierarchy of Feedback

1. **Immediate** - Button disabled state
2. **Short wait** - Spinner or progress
3. **Long wait** - Skeleton + message
4. **Error** - Clear feedback + retry

### Skeleton Loading (Preferred)

Better than spinners because:
- Shows content structure
- Reduces perceived wait time
- Feels more polished

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--neutral-100) 25%,
    var(--neutral-200) 50%,
    var(--neutral-100) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```

---

## Anti-Patterns (PROHIBITED)

### ❌ `transition: all`

```css
/* NEVER */
.element {
  transition: all 300ms ease;
}

/* ALWAYS specify properties */
.element {
  transition:
    background-color 150ms ease-out,
    transform 200ms ease-out;
}
```

**Why:** Performance killer, unexpected behaviors.

### ❌ Same Duration Everywhere

```css
/* NEVER */
* { transition-duration: 300ms; }
```

**Why:** Different movements need different timing.

### ❌ Animation for Animation's Sake

If you can't explain what it communicates, delete it.

### ❌ Blocking Animations

Animations that prevent user action are hostile UX.

---

## Performance

### Rules

1. **Only animate transform and opacity** - GPU accelerated
2. **Avoid animating layout properties** - Width, height, margin
3. **Use will-change sparingly** - Only when needed
4. **Test on low-end devices** - 60fps or don't ship

### Safe to Animate

- ✅ `transform` (translate, scale, rotate)
- ✅ `opacity`
- ⚠️ `filter` (can be expensive)
- ❌ `width`, `height`, `margin`, `padding`

---

## Accessibility

### Respect Motion Preferences

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Requirements

- [ ] All animations can be disabled
- [ ] No flashing/strobing effects
- [ ] Autoplay animations have controls
- [ ] Motion doesn't cause disorientation

---

## Checklist

Before shipping motion:

- [ ] Every animation has documented purpose
- [ ] Duration matches movement size
- [ ] Easing is intentional (not default)
- [ ] Performance tested (60fps)
- [ ] Reduced motion is respected
- [ ] No `transition: all` in codebase
- [ ] Loading states use skeletons

---

*Motion design principles for AIOS products. Version 1.0*
