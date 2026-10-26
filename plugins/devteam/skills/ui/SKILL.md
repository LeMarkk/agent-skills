---
name: ui
description: Build user interfaces that are accessible, responsive and consistent with the project's design system, with every state handled and the result checked in a real browser. Use when building or changing screens, components or forms.
---

# ui

A screen is done when it works for every user, at every size, in every state, and looks like it belongs in the product.

## Before building

1. Find the project's design system: tokens, theme, component library, an existing screen to match. Reuse components before writing new ones.
2. List the states the screen can be in: loading, empty, error, success, partial data, no permission, offline if it applies. Each one gets a design.

## Components

- **Small and single-purpose.** A component either fetches or presents; split one that does both.
- **State lives as low as it can**, lifted only when siblings need it. Server data goes through the project's data layer (React Query, SWR, loaders); don't copy it into local state.
- **Props are the interface.** Keep them few and named for intent (`variant="danger"`), not appearance (`red`).
- **Forms:** label every field, validate on submit and on blur, show errors next to the field in words that say how to fix it, keep what the user typed.

## Accessibility (WCAG 2.1 AA)

- Use the right element first: `<button>` for actions, `<a>` for navigation, real `<label>`s, headings in order. ARIA only when no native element fits.
- Everything works with a keyboard: visible focus, logical tab order, `Esc` closes dialogs, focus moves into a dialog and returns when it closes.
- Text contrast at least 4.5:1 (3:1 for large text and UI parts). Don't use color alone to carry meaning.
- Images have alt text; decorative ones have `alt=""`.
- Announce changes that matter (form errors, toasts) to screen readers with a live region.

## Layout

- Mobile first. Check at 320, 768, 1024 and 1440 px wide: no horizontal scroll, no clipped text, touch targets at least 44 px.
- Use the design system's spacing and type scale. Avoid one-off pixel values.
- Avoid the generic AI look: no default gradients, no emoji as icons, no centered-everything hero unless the design calls for it. Match the product.
- Reserve space for loading content (skeletons, fixed image sizes) so the page doesn't jump.

## Check it in a browser

Run the app and look at the actual result, not just the code:

- [ ] No console errors or warnings
- [ ] Each state renders (force empty, error and slow responses)
- [ ] Tab through the whole flow with the keyboard
- [ ] The four widths above look right
- [ ] An accessibility check (axe, Lighthouse) shows no violations

If a browser tool (Chrome DevTools MCP, Playwright) is available, use it for screenshots and console checks. Otherwise, say which checks you couldn't do so a person can.
