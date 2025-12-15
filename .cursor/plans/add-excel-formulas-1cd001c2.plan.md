---
name: "UI Redesign: Clean Professional Eindafrekening"
overview: ""
todos: []
---

# UI Redesign: Clean Professional Eindafrekening

## Overview

Transform both OnePager and Detail templates into modern, clean, professional settlement documents with positive framing, perfect print support, and RyanRent brand identity.

## Design Principles

- Modern & minimal aesthetic (inspired by Tack/Delisas examples)
- Centered layout (max-width 850px) for better readability
- Positive psychology: green for returns, neutral grey/black for charges (no red)
- Flat icon system instead of emojis
- Perfect print output with @media print styles
- RyanRent brand colors from logo

## Changes to template_onepager.html

### 1. Update CSS Variables (Brand Colors)

Replace color system in `:root`:

```css
:root {
    /* RyanRent Brand Colors - from logo */
    --color-brand-green: #8BC34A;  /* Primary green from logo */
    --color-brand-orange: #FF9800; /* Accent orange from logo */
    --color-brand-dark: #2C3E50;   /* Dark text */
    
    /* Semantic Colors - Positive Framing */
    --color-positive: #4CAF50;     /* Returns/refunds */
    --color-positive-bg: #E8F5E9;
    --color-neutral: #546E7A;      /* Charges - NEUTRAL not red */
    --color-neutral-bg: #F5F5F5;
    --color-info: #FF9800;         /* Highlights */
    --color-info-bg: #FFF3E0;
    
    /* Remove --color-error usage */
    
    /* Bar Colors - Refined */
    --color-bar-prepaid: #A5D6A7;  /* Green for prepaid */
    --color-bar-used: #FFE082;     /* Soft yellow for used */
    --color-bar-return: #81C784;   /* Darker green for return */
    --color-bar-charge: #BDBDBD;   /* Neutral grey for extra charges */
    
    /* Layout - Centered Design */
    --max-content-width: 850px;
    --spacing-xs: 6px;
    --spacing-sm: 12px;
    --spacing-md: 20px;
    --spacing-lg: 32px;
    --spacing-xl: 48px;
}
```

### 2. Add Container Wrapper

Wrap entire body content in centered container:

```html
<body>
    <div class="page-container">
        <!-- All existing content here -->
    </div>
</body>
```

Add CSS:

```css
.page-container {
    max-width: var(--max-content-width);
    margin: 0 auto;
    padding: var(--spacing-lg);
    background: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

@media print {
    .page-container {
        max-width: 100%;
        box-shadow: none;
        padding: 0;
    }
}
```

### 3. Replace Emojis with Flat SVG Icons

Remove emojis (🔒, ⚡, 🧹) and add inline SVG icons.

For deposit (line 712):

```html
<td>
    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
    Borg
</td>
```

For GWE (line 721):

```html
<td>
    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
    </svg>
    G/W/E
</td>
```

For Cleaning (line 730):

```html
<td>
    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M3 12h18M3 6h18M3 18h18"/>
    </svg>
    Schoonmaak
</td>
```

Add icon CSS:

```css
.icon {
    width: 16px;
    height: 16px;
    display: inline-block;
    vertical-align: middle;
    margin-right: 6px;
    stroke-width: 2;
    color: var(--color-brand-green);
}
```

### 4. Reframe Negative Values to Neutral

Change all `text-neg` styling and logic:

Replace CSS:

```css
/* OLD: .text-neg { color: var(--color-error); } */
.text-charge {
    color: var(--color-neutral);
    font-weight: 600;
}

.text-return {
    color: var(--color-positive);
    font-weight: 600;
}
```

Update template logic (example for line 715-717):

```html
<!-- OLD -->
<td class="{{ 'text-pos' if financial.borg.terug >= 0 else 'text-neg' }}">
    {{ "€%.2f terug"|format(financial.borg.terug) if financial.borg.terug >= 0 else "€%.2f bijbetalen"|format(abs(financial.borg.terug)) }}
</td>

<!-- NEW -->
<td class="{{ 'text-return' if financial.borg.terug >= 0 else 'text-charge' }}">
    {{ "+€%.2f"|format(financial.borg.terug) if financial.borg.terug >= 0 else "€%.2f"|format(abs(financial.borg.terug)) }}
</td>
```

Apply same pattern to lines 724, 733, 740 (remove "terug/bijbetalen" language, use +/- symbols).

### 5. Refine Bar Visualizations

Update bar segment colors:

```css
.segment.extra {
    background: var(--color-bar-charge); /* Grey instead of red */
    color: var(--color-neutral);
    border: 1px solid #9E9E9E;
    /* Remove striped pattern for cleaner look */
}
```

### 6. Tighten Spacing & Typography

Update main grid spacing:

```css
.main-grid {
    grid-template-columns: 240px 1px 1fr 1px 100px;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
}

.grid-cell {
    padding: var(--spacing-sm) 0;
}
```

Reduce excessive padding in settlement table:

```css
.settlement-table td {
    padding: var(--spacing-sm) var(--spacing-md);
}
```

### 7. Add Comprehensive Print Styles

Add at end of `<style>`:

```css
@media print {
    @page {
        size: A4 portrait;
        margin: 12mm;
    }
    
    body {
        print-color-adjust: exact;
        -webkit-print-color-adjust: exact;
    }
    
    .page-container {
        box-shadow: none;
        padding: 0;
    }
    
    /* Ensure colors print */
    .segment.used,
    .segment.return,
    .segment.extra,
    .bar-fixed {
        print-color-adjust: exact;
        -webkit-print-color-adjust: exact;
    }
    
    /* Prevent page breaks inside critical sections */
    .main-grid,
    .detail-card,
    .settlement-table {
        page-break-inside: avoid;
    }
    
    /* Hide potential print buttons if added */
    .no-print {
        display: none;
    }
}
```

### 8. Refine Header Layout

Update header for better balance:

```css
.header {
    display: flex;
    justify-content: space-between;
    align-items: center; /* Changed from flex-start */
    margin-bottom: var(--spacing-lg);
    padding-bottom: var(--spacing-md);
    border-bottom: 2px solid var(--color-brand-green);
}

.brand-info h1 {
    font-size: 22px;
    color: var(--color-brand-dark);
}

.guest-name {
    font-size: 20px;
    color: var(--color-brand-dark);
}
```

### 9. Improve Intro Card

Make more prominent and informative:

```css
.intro-card {
    background: linear-gradient(135deg, #E8F5E9 0%, #F1F8E9 100%);
    border-left: 4px solid var(--color-brand-green);
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: var(--radius-sm);
    margin-bottom: var(--spacing-lg);
}

.intro-card p {
    font-size: 15px;
    line-height: 1.6;
    color: var(--color-brand-dark);
    margin: 0;
}
```

Update intro text to be more positive:

```html
<!-- OLD -->
<p>Hieronder ziet u precies wat u vooraf betaalde, hoe dit is gebruikt, en wat het financial.totals.totaal_eindafrekening resultaat is.</p>

<!-- NEW -->
<p>Bedankt voor uw verblijf! Hieronder vindt u een duidelijk overzicht van uw voorschotten en de afrekening.</p>
```

### 10. Settlement Table Refinement

Better visual hierarchy for final total:

```css
.row-total {
    border-top: 2px solid var(--color-border);
    background: var(--color-brand-green);
    color: white;
    font-weight: 700;
}

.row-total td {
    padding: var(--spacing-md);
    font-size: 16px;
}
```

## Changes to template_detail.html

Apply same principles:

1. Centered layout with page-container wrapper
2. Replace any emojis with SVG icons
3. Update color variables to match onepager
4. Use neutral colors for charges
5. Add print styles
6. Tighten spacing throughout

Key sections to update:

- CSS variables (match onepager)
- Container wrapper
- Icon replacements if any emojis present
- Print styles for detailed tables
- Color framing (neutral for charges)

## Testing Plan

After implementation:

1. Generate test PDF with `input_template_filled.xlsx`
2. Verify in browser (check layout, colors, spacing)
3. Test print preview (Cmd+P / Ctrl+P)
4. Print to PDF and verify colors appear correctly
5. Check both OnePager and Detail outputs
6. Test with different data scenarios (all refunds, all charges, mixed)

## Expected Improvements

Before → After:

- Full width → Centered 850px (professional document feel)
- Emoji icons → Flat SVG icons (modern, scalable)
- Red charges → Neutral grey charges (positive psychology)
- Loose spacing → Compact efficient spacing
- Missing colors on print → Perfect print output with colors
- Generic layout → RyanRent branded design