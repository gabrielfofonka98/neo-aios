# Design Opinions

> **Philosophy:** Opinionated design creates distinctive products.
> Generic design creates forgettable ones.

---

## The 6 Core Opinions

### 1. Personality Over Polish

**Opinion:** A distinctive UI with rough edges beats a polished generic one.

Users remember products that feel unique. They forget products that look like every other SaaS dashboard.

**Implications:**
- Don't use component libraries out-of-the-box
- Customize every element to match your brand
- Accept imperfection if it serves personality
- Ask: "Would users recognize this UI without the logo?"

### 2. Typography is Identity

**Opinion:** The font is the single most impactful design decision.

Typography establishes voice before users read a word. The wrong font can make excellent content feel mediocre.

**Implications:**
- Choose fonts deliberately, not by default
- Spend time on typographic hierarchy
- Use font weight and size as primary differentiators
- Typography should reflect brand personality

### 3. Color is Emotion

**Opinion:** Color palette should evoke specific feelings, not just look nice.

Colors aren't decorative—they're emotional. Every color choice should answer: "What do I want users to feel?"

**Implications:**
- Define emotional intent before choosing colors
- Use color consistently for meaning
- Dark mode isn't just inverted colors
- Avoid default color palettes from frameworks

### 4. Space is Expensive

**Opinion:** Generous whitespace signals quality; cramped layouts signal desperation.

Whitespace is not empty space—it's breathing room. Products that feel premium have generous margins.

**Implications:**
- Default to more space, not less
- Let content breathe
- Dense information ≠ good UX
- Whitespace is a feature, not waste

### 5. Motion is Meaning

**Opinion:** Every animation must earn its existence with purpose.

Animations without purpose are distracting. Animations with purpose guide attention and create delight.

**Implications:**
- No animation is better than generic animation
- Each motion should answer: "What does this communicate?"
- Duration and easing matter
- Micro-interactions create perceived quality

### 6. Constraints Breed Creativity

**Opinion:** Set strict design constraints early; they force creative solutions.

Unlimited options paralyze designers. Constraints force focus and create cohesive systems.

**Implications:**
- Define your constraints before designing
- Limit color palette strictly
- Limit font choices strictly
- Say no to "one-off" treatments

---

## Anti-Patterns (PROHIBITED)

### Typography Anti-Patterns

❌ **DO NOT USE as primary typefaces:**
- Inter
- Roboto
- Open Sans
- Source Sans Pro
- Lato
- Montserrat (overused)

These fonts are defaults. They say "we didn't make a choice."

✅ **Instead:** Choose fonts that reflect brand personality. Consider:
- Serif fonts for authority/tradition
- Display fonts for personality
- Custom or less-common fonts for distinction

### Color Anti-Patterns

❌ **DO NOT USE:**
- Tailwind default blue (`#3B82F6`)
- Default gradient directions (top-to-bottom)
- Cliché gradients (purple-to-pink, blue-to-purple)
- Black text on white only (`#000` on `#FFF`)

✅ **Instead:**
- Choose a primary color with emotional intent
- Use off-black text (`#1a1a1a` or similar)
- Custom gradients with brand colors
- Consider dark mode from the start

### Layout Anti-Patterns

❌ **DO NOT USE:**
- Hero + 3 feature cards
- Default Bootstrap/Tailwind templates
- "Above the fold" obsession
- Cookie-cutter SaaS layouts

✅ **Instead:**
- Design for your specific content
- Break conventional layouts when appropriate
- Let content dictate structure
- Create memorable page architecture

### Motion Anti-Patterns

❌ **DO NOT USE:**
- `transition: all 300ms ease` everywhere
- `transition: all` (performance killer)
- Animations that don't guide attention
- Bouncy animations for serious products
- Loading spinners as only feedback

✅ **Instead:**
- Specific property transitions
- Duration based on movement distance
- Easing that matches brand (snappy vs smooth)
- Skeleton loading over spinners

---

## Decision Framework

When making any design decision, ask:

1. **Is this distinctive?**
   > Would users recognize this without the logo?

2. **Is this intentional?**
   > Can I explain why this choice was made?

3. **Is this emotional?**
   > What feeling does this evoke?

4. **Is this constrained?**
   > Does this fit within our design system?

If you can't answer yes to all four, reconsider the decision.

---

## Quick Reference

| Element | Question to Ask |
|---------|-----------------|
| Typography | "Does this font match our voice?" |
| Color | "What emotion does this evoke?" |
| Space | "Is there enough room to breathe?" |
| Motion | "What does this animation communicate?" |
| Layout | "Is this template or custom?" |

---

## When to Break These Rules

Rules exist to be broken—but consciously. Break these opinions when:

1. **User research contradicts them** - Data beats opinion
2. **Accessibility requires it** - Inclusion trumps aesthetics
3. **Technical constraints demand it** - Ship beats perfect
4. **Brand strategy calls for it** - Business context matters

But document WHY you broke the rule. Future designers need context.

---

*Design opinions for AIOS products. Version 1.0*
