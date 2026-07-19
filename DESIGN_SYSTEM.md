# Dott Health — Design System

Source of truth for the visual language and reusable UI components implemented in this repo (`templates/index.html`, `static/css/styles.css`, `static/js/script.js`). This file replaces `HANDOFF_register_flow.md` — that file described a React (`app/`) → `legacy-static/` port that doesn't match this repo's actual structure (see `CLAUDE.md`); everything below reflects what's actually built and running here.

Full brand reference (colors, type scale, spacing, imagery, voice) lives in **`Dott Health Brand Guidelines.html`** at the repo root — a large exported reference doc. Treat it as the canonical brand source; the tokens below are the subset actually wired into code today via `static/css/styles.css`'s `:root` block. If the two ever disagree, the brand guidelines file wins for *new* work — update `:root` to match rather than the other way around.

---

## 1. Brand tokens (as implemented)

All defined in `static/css/styles.css` `:root`:

| Token | Value | Use |
|---|---|---|
| `--plum` | `#430A4D` | Primary brand color — page background, headings, primary text on light modals, focus rings |
| `--mist` | `#F7C8FF` | Accent (currently unused in compiled CSS beyond token definition) |
| `--periwinkle` | `#94A4E6` | Hover border on profession picker cards |
| `--tangerine` | `#FF6A32` | CTA button background (`.btn-primary`) |
| `--tangerine-hover` | `#FF7F4D` | CTA hover state |
| `--success` | `#19855D` | Success checkmark circle fill |
| `--amber` / `--pgreen` / `--pyellow` | `#ECC03C` / `#B2E7CC` / `#FAE89E` | Reserved palette tokens, not yet used in compiled CSS |
| `--ink` | `#2E282F` | Primary text on light backgrounds |
| `--ink-2` | `#655B67` | Secondary/muted text, placeholders |
| `--line` | `#ECE9ED` | Default border color for inputs, dropdowns, cards |
| `--white` | `#FFFFFF` | Modal backgrounds, button text |

Fonts:
- `--font-display`: `'Parkinsans', sans-serif` — headings, buttons, section titles
- `--font-body`: `'Figtree', sans-serif` — body text, inputs

Loaded via Google Fonts in `templates/index.html:10` (weights 500/600/700 for Parkinsans, 400/500/600 for Figtree).

The brand guidelines HTML file also documents additional palette entries (error/warning reds, deeper greens, a monospace font `'JetBrains Mono'`, and an `'Inter'` fallback) not yet consumed by `styles.css` — check there before introducing new colors rather than picking an arbitrary hex.

---

## 2. Layout primitives

- **Page shell**: `.page-bg` (fixed, textured DNA-gif background at 18% opacity + a glowing circle overlay) sits behind `.page` (`z-index: 1`, flex column, `min-height: 100dvh`). The plum solid color lives on `<body>`, not a wrapper — moving it to a wrapper div repaints above the negative-z-index texture layer and hides it (see `CLAUDE.md`).
- **Header** (`.site-header`): flex row, `justify-content: space-between`. Logo, then `.site-nav` (flex, `align-items: center` — required so the bordered `.btn-register` button doesn't stretch taller than the plain text links via default `stretch`), then a mobile `.menu-toggle` hamburger (hidden ≥560px).
- **Responsive breakpoint**: single breakpoint at `max-width: 560px` — mobile nav becomes an absolutely-positioned dropdown panel toggled by `.site-nav.open`.

---

## 3. Modal system

Three modal families, all sharing `.modal-overlay` (fixed, centered, dark backdrop, `z-index: 100`) and `.modal-close` (32px circle button, `#F2F0F3` bg):

### 3.1 Standard modal (Waitlist)
`.modal-card` — white rounded card (`border-radius: 24px`), centered via the overlay's flex centering, `max-width: 460px`.

### 3.2 Light modal (Our Vision / Contact Us)
`.vision-wrap` + `.vision-card` — a light-lavender/cream backdrop (`#vision-overlay` / `#contact-overlay` background colors) with a decorative vertical image strip beside the card. Both modals share `.vision-wrap`'s fixed `height: 78vh` so they're always the same size regardless of content length. Opening either swaps the header into a dark-on-light theme via `body.light-modal-active` (logo swap, nav text color, reparents `<header>` in the DOM so it renders above the light backdrop — `openModal()`/`closeModal()` in `script.js` do the reparenting).

**Gotcha hit while building this**: `.vision-card`/`.vision-scroll` need explicit `min-height: 0` in the flex chain, or the scroll container never actually constrains itself — it just grows to fit content and the parent's `max-height` silently clips whatever overflows (map iframe, form fields) instead of making it scrollable.

### 3.3 Register modal (`#register-overlay`)
`.register-card` — taller (`max-height: 85vh`), does **not** close on backdrop click (explicitly skipped in `script.js`'s overlay-click-to-close wiring — Escape and the × button still work). Structure:
- `.register-header-text` → `.register-title-row` (flex, title block + close button side-by-side, `align-items: flex-start` so the × aligns with the title line, not the vertical center of the whole header+subtext block)
- `.register-body` — the scrollable region. Has a **top-only** fade overlay (`.register-body-fade-top`, `position: sticky`, toggled via a `visible` class driven by real scroll-position checks in JS, not pure CSS — see §6). A bottom fade was tried and removed; it washed out the Submit button at scroll-end once content height became variable across Doctor/Nurse forms.

---

## 4. Form components

All form-field CSS is scoped under `#register-form` (an **id** selector — see gotcha below) plus the shared `.multi-select-trigger` class.

### 4.1 Text inputs
`input[type="text"|"tel"|"email"]` inside `#register-form`: 44px height, `border-radius: 10px`, `1px solid var(--line)`, focus ring via `border-color: var(--plum)`.

### 4.2 Custom checkbox (`.checkbox-box`)
Used by both `.register-checkbox` (plain checklists, e.g. "This number has WhatsApp") and `.multi-select-item` (checkbox rows inside multi-select panels). Markup pattern:
```html
<label class="register-checkbox"><input type="checkbox" name="..." value="..."><span class="checkbox-box"></span> Label text</label>
```
The real `<input>` is invisible (`opacity: 0`, absolutely positioned over the visible box) so it stays keyboard/screen-reader accessible; `.checkbox-box` is the visible rounded square, filled `var(--plum)` with a white checkmark drawn via `::after` when the sibling input is `:checked`.

**Gotcha hit while building this**: a checkmark drawn with `::after` directly on the `<input>` itself doesn't reliably get a sized box in Chromium — `<input>` is a replaced element and generated-content pseudo-elements on replaced elements have unreliable box-model support (the checkmark's `width`/`height` computed as `0px` even though `content` and other properties applied fine). Fix: never put `::after` directly on the checkbox input — always use a sibling `<span class="checkbox-box">` and target `input:checked ~ .checkbox-box::after`.

**Second gotcha**: the checked-state selector must explicitly list every parent class it needs to work under (`.multi-select-item input:checked ~ .checkbox-box`, `.register-checkbox input:checked ~ .checkbox-box`). Forgetting to add a new parent class here means the checkbox will *toggle correctly in the DOM* (JS `checked` is `true`) but show **no visual change at all** — an easy bug to miss because nothing throws and the underlying state is correct.

### 4.3 Single-select dropdown (`.single-select`)
Button-based, single-choice replacement for native `<select>` (native selects can't be restyled — the closed box can look custom but the native OS options popup can't, so this repo doesn't use `<select>` at all in the register form). Markup:
```html
<div class="single-select" id="reg-X">
  <input type="hidden" name="X" id="reg-X-value" value="">
  <button type="button" class="multi-select-trigger" id="reg-X-trigger" data-placeholder="true">
    <span class="multi-select-trigger-text">Placeholder</span>
    <svg>...chevron...</svg>
  </button>
  <div class="multi-select-panel" hidden>
    <button type="button" class="multi-select-item" data-value="...">Label</button>
    ...
  </div>
</div>
```
Wired generically in `script.js` — any `.single-select` on the page is auto-discovered (`document.querySelectorAll('.single-select')`), no per-field JS needed. Selecting an item replaces the hidden input's value (exclusive choice), updates the trigger label, and closes the panel. Used for: State, Specialty, Years of experience (both professions), Qualification (Nurse), Preferred consultation mode, Available days, Preferred Shift, Willing to Travel.

### 4.4 Multi-select dropdown (`.multi-select`)
Same trigger/panel shell as `.single-select`, but panel items are `.checkbox-box`-style checkboxes (not buttons), so multiple values accumulate into a comma-joined hidden input. Also auto-discovered generically in `script.js`. Used for: Languages known, Preferred nursing services.

**Trigger label truncation**: once more than 2 items are selected, the trigger shows only the first 2 plus a `+N` count (e.g. `"Home Nursing Care, Elderly Care +6"`), not the full joined list — a full-length join was overflowing the fixed-height trigger box and wrapping onto the section heading above it. The complete list is still in the hidden input (for submission) and in a `title` attribute (for hover/accessibility).

### 4.5 Dropdown panel positioning (`positionDropdownPanel()`)
Shared by both single- and multi-select. On open, measures space above/below the trigger *within the scrollable `.register-body`* (not the viewport) and:
1. Flips the panel above the trigger (`.flip-up` class) if there's more room above than below and the panel doesn't fit below.
2. Dynamically caps the panel's `max-height` to whichever side was chosen — never a fixed 240px regardless of actual space. Options that still don't fit scroll within the panel via its own `overflow-y: auto`.

**Gotcha hit while building this**: measuring `panel.scrollHeight` *before* removing the `hidden` attribute reads `0` — always toggle `hidden` off first, then measure, or the flip/height decision is made against a phantom zero-height panel.

### 4.6 Profession picker (`.profession-options` / `.profession-option`)
Two-button grid (Doctor / Nurse). Selecting one adds `.selected`, sets `licenseLabels`-driven placeholder text (see §5), and expands `.register-expand` (a `grid-template-rows: 0fr → 1fr` CSS-only accordion animation) to reveal the rest of the form.

---

## 5. Register form field inventory

The form (`#register-form`) has one shared "1. Basic Information" block (Full name, Mobile, WhatsApp checkbox, Email, City, State), then **branches by profession** into two mutually-exclusive wrapper divs, then rejoins for Languages Known + Submit.

**Gotcha hit while building this — twice**: `#doctor-only-fields`/`#nurse-only-fields` are toggled via the `hidden` attribute. Giving either wrapper `display: flex` in CSS (needed for internal spacing — see below) silently **overrides the `hidden` attribute's implicit `display: none`**, since author CSS wins over the UA stylesheet rule. Result: both profession's fields render simultaneously regardless of selection, with only JS state (`el.hidden === true`) looking correct — the bug is invisible unless you actually screenshot the page. Any element toggled via the `hidden` attribute that also needs `display: flex`/`grid` for its visible state **must** have a matching `#id[hidden] { display: none }` (or `.class[hidden]`) override. This bit twice in this build: once for `.form-success`, once for these wrappers.

### Doctor path (`#doctor-only-fields`)
1. Registration number, Qualification (free text), Specialty (single-select), Years of experience (single-select), Current hospital/clinic
2. Interested Services — plain `.register-checkbox` list (DOTT Second Opinion, DOTT Homespital, Online/Home Consultation, ICU at Home, Medical Advisory Panel)
3. Consultation Preferences — Preferred consultation mode (single-select: online/home/both), Available days (single-select)

### Nurse path (`#nurse-only-fields`)
1. Registration number, Qualification (single-select: ANM / GNM / B.Sc. Nursing / Post Basic B.Sc. / M.Sc. Nursing / Nurse Practitioner / Other), Years of experience (single-select), Current employer
2. Preferred Nursing Services — multi-select dropdown, 14 options (Home Nursing Care, Elderly Care, ICU at Home, Post-Operative Care, Palliative Care, Mother & Baby Care, Newborn Care, Wound Care & Dressing, Injection & IV Therapy, Catheter Care, Physiotherapy Assistance, Routine Health Check-up, Tele-Nursing, Patient Education & Counselling)
3. Work Preferences — Preferred Working Area (free text), Preferred District/City (free text — deliberately not a cascading state→district→city picker; this is a static site with no backend to source that data from), Preferred Shift (single-select: Full-time/Part-time/Day Shift/Night Shift/On-call), Willing to Travel (single-select: Yes/No)

Both paths end with **Languages Known** (multi-select: English, Malayalam, Hindi, Tamil, Telugu, Kannada, Other) and the Submit button — these live outside both wrapper divs since they're shared.

### Required-field handling
Since both field blocks exist in the DOM simultaneously (one just `hidden`), `required` attributes are managed in JS (`requiredByProfession` map in `script.js`), not hardcoded in HTML — a hidden-but-`required` field silently blocks form submission with a native validation popup the user can't see or reach, since the browser refuses to focus a display:none field. Only the currently-visible profession's key fields (`reg-license`/`reg-qualification` for Doctor, `reg-license-nurse` for Nurse) get `required` toggled on when that profession is picked.

---

## 6. JS architecture notes (`static/js/script.js`)

- Single IIFE, no framework, no build step — plain vanilla JS matching the rest of the site.
- `.single-select` and `.multi-select` are each wired by one generic `document.querySelectorAll(...).forEach(...)` loop — adding a new dropdown of either kind requires **zero new JS**, just matching markup with the right class + a `.multi-select-trigger` / `.multi-select-panel` / hidden `<input>` shape.
- `resetRegisterModal()` runs on a 200ms delay after close (`setTimeout`) so the form doesn't visibly snap back to blank mid-close-animation. It must stay in sync with every stateful piece added to the form: profession selection, both field-block `hidden` flags, every `multiSelects`/`singleSelects` entry, and the mobile-number sanitizer state.
- Scroll-fade visibility (`updateRegisterFades`) is intentionally **not** pure-CSS `position: sticky` — an earlier version relied only on sticky positioning and the bottom fade permanently overlapped the Submit button at true scroll-end, because sticky elements have no native way to detect "no more content below." Fixed by checking actual `scrollTop`/`scrollHeight` in JS and toggling a `.visible` class.

---

## 7. Known non-goals / deferred items

- No backend — `/join-waitlist` and the register form's "submission" are both client-side-only success states; nothing is persisted or emailed (see `CLAUDE.md`).
- Preferred District/City is free text, not a state-aware cascading picker (no data source to back it in a static site).
- `static/js/styles.css` is a stray, unlinked duplicate of `static/css/styles.css` — don't edit it expecting effect.
