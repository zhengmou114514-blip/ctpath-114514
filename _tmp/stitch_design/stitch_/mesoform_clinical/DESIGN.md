# Design System Strategy: The Precision Ledger

## 1. Overview & Creative North Star
### The Creative North Star: "The Precision Ledger"
In the high-stakes environment of chronic disease management, the interface must act as a silent, authoritative partner. We are moving away from the "SaaS Template" look—characterized by heavy borders and generic spacing—and moving toward **The Precision Ledger**. 

This system is an editorial take on clinical data. It treats the screen as a high-fidelity document where information hierarchy is dictated by **tonal depth and typographic weight** rather than structural boxes. We aim for a "quiet" UI: a low-fatigue, high-trust environment that feels like a custom-built workstation for specialists. By utilizing intentional asymmetry in data density and layered surfaces, we create a signature aesthetic that feels permanent, stable, and meticulously curated.

---

## 2. Colors: Tonal Architecture
The palette is built on a foundation of "Healthcare Teals" and "Stabilizing Grays." We prioritize ocular comfort for clinicians who spend 8+ hours on these screens.

### The "No-Line" Rule
**Explicit Instruction:** You are prohibited from using 1px solid borders to define sections or containers. Boundaries must be established through color shifts. 
- Use `surface_container_low` (#f1f4f5) for the main workspace.
- Use `surface_container_lowest` (#ffffff) for active cards or data entry modules.
- The shift in tone creates a "soft edge" that reduces visual noise and cognitive load.

### Surface Hierarchy & Nesting
Treat the UI as physical layers of "Digital Vellum." 
- **Base Layer:** `surface` (#f7fafb) is the desk.
- **Secondary Layer:** `surface_container` (#ebeeef) defines major navigation or sidebar zones.
- **Action Layer:** `surface_container_highest` (#e0e3e4) is reserved for "pop-over" utility panels or transient states.

### The "Glass & Gradient" Rule
While we avoid marketing-style "fluff," we use technical glassmorphism to maintain clinical context. Floating panels (like AI prediction details) should use a semi-transparent `surface` color with a 20px backdrop-blur. 
- **Signature Texture:** Use a subtle vertical gradient from `primary` (#004347) to `primary_container` (#005c61) for high-level primary actions. This adds a "weighted" feel to buttons, making them feel like physical switches rather than flat shapes.

---

## 3. Typography: Editorial Authority
We utilize a dual-typeface system to balance institutional authority with technical precision.

- **Display & Headlines (Public Sans):** This face provides an architectural, stable feel. Use `display-md` (2.75rem) sparingly for patient names or critical metrics. The wide aperture of Public Sans ensures "8s" and "Bs" are never confused—a clinical necessity.
- **Body & Labels (Inter):** Inter is our technical workhorse. Use `label-md` (0.75rem) for data headers, set in All Caps with 5% letter spacing to create an "organized ledger" look.
- **Hierarchy as Brand:** Use `title-lg` (Inter, 1.375rem) for section headers. By pairing a large, bold `headline-sm` with a tiny, high-contrast `label-sm`, we create an editorial rhythm that guides the eye to critical data first.

---

## 4. Elevation & Depth
Depth is achieved through **Tonal Layering**, not shadows. 

- **The Layering Principle:** To lift a component, change its token. A `surface_container_lowest` card sitting on a `surface_container_low` background provides enough contrast to be "interactive" without needing a border.
- **Ambient Shadows:** Only for elements that physically "float" (modals, tooltips). Use: `box-shadow: 0 12px 32px -4px rgba(24, 28, 29, 0.06)`. This creates a soft, natural lift using the `on_surface` color as the shadow tint.
- **The "Ghost Border" Fallback:** For high-density data tables where boundaries are essential, use `outline_variant` (#bec8c9) at 20% opacity. It should be felt, not seen.

---

## 5. Components: Clinical Primitives

### AI Status Indicators (The Pulse)
Predictions must be distinct and non-distracting.
- **Preloaded:** `secondary_container` (#cfe6f2) background with `on_secondary_container` text.
- **Predicting:** A subtle pulse animation on the `surface_tint` (#19686d).
- **Latest:** Solid `primary` (#004347) with `on_primary` (#ffffff) text.
- **Failed:** `error_container` (#ffdad6) with `on_error_container` (#93000a) text.

### Buttons
- **Primary:** Gradient `primary` to `primary_container`. Corner radius `md` (0.375rem).
- **Secondary:** Transparent background, `outline` (#6f797a) at 30% opacity. 
- **Tertiary:** Pure text using `primary` color, used for low-priority "Cancel" or "Back" actions.

### Data Tables (The Ledger)
- **Rule:** Forbid divider lines. 
- **Style:** Use `body-md` for row data. Every second row should use a `surface_container_low` background for readability. 
- **Header:** Use `label-sm` in `on_surface_variant` (#3f4849).

### Input Fields
- Avoid the "boxed" look. Use a `surface_container_highest` bottom-only highlight or a very faint `outline_variant` at 15% opacity. Focus state transitions smoothly to `primary` with a 2px thickness—no "glow" effects.

### Risk Chips
- **High Risk:** `error` (#ba1a1a) text on `error_container`.
- **Medium Risk:** `tertiary` (#5e2f0e) text on `tertiary_container`.
- **Low Risk:** `primary` (#004347) text on `primary_fixed`.

---

## 6. Do's and Don'ts

### Do
- **Do** use whitespace as a separator. If two sections feel cluttered, increase the margin rather than adding a line.
- **Do** align data points vertically. Use tabular numerals for patient vitals to ensure numbers align perfectly for easy scanning.
- **Do** use `surface_bright` to highlight active "New Data" alerts.

### Don't
- **Don't** use pure black (#000000) for text. Always use `on_surface` (#181c1d) to maintain the soft, clinical aesthetic.
- **Don't** use standard "SaaS Blue." Always lean toward the "Teal/Forest" spectrum of our `primary` (#004347) for a more professional, sophisticated feel.
- **Don't** use rounded corners larger than `lg` (0.5rem) for functional components. We want the workstation to feel "structured," not "bubbly."