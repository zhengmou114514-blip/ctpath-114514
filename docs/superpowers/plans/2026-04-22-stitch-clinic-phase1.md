# Stitch Clinic Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the clinic-side presentation and navigation to match the Stitch prototype more closely while keeping the current login, patient detail, prediction, follow-up, and logout closure stable.

**Architecture:** Keep the current clinic frontend entry on `frontend/src`, but tighten the clinic-only route boundary, replace the most visible mojibake and placeholder copy with final Chinese product copy, and reshape the login/dashboard/detail shell to follow the Stitch archive/login/dashboard proportions. Preserve existing composables and APIs instead of introducing a new state layer.

**Tech Stack:** Vue 3, TypeScript, Vue Router, Pinia, Element Plus, Vite

---

### Task 1: Lock the clinic-only navigation boundary

**Files:**
- Modify: `E:\CTpath-master\frontend\src\pages\AppWorkspacePage.vue`
- Modify: `E:\CTpath-master\frontend\src\config\workspaceMenu.ts`

- [ ] Remove stale model route sync entries from the clinic shell.
- [ ] Keep only existing clinic routes in `splitRouteSections`, `sectionToRouteName`, and `isSplitWorkspaceRoute`.
- [ ] Replace all remaining mojibake menu labels and descriptions with final Chinese labels.

### Task 2: Rebuild the login experience against Stitch `_3` and `_5`

**Files:**
- Modify: `E:\CTpath-master\frontend\src\components\LoginScreen.vue`

- [ ] Keep current login/register behavior and emitted events.
- [ ] Adjust the page structure to match the Stitch split layout: left brand panel on desktop, right auth panel, professional medical messaging, bottom trust strip.
- [ ] Replace placeholder and mojibake copy with final graduation-project wording.

### Task 3: Rebuild the doctor dashboard against Stitch `_4`

**Files:**
- Modify: `E:\CTpath-master\frontend\src\pages\DoctorDashboardPage.vue`

- [ ] Keep current patient open/open-detail/open-archive/open-followup events.
- [ ] Retain the main three-part structure: top status region, center queue table, right alert/focus column.
- [ ] Remove mojibake and align labels, CTAs, and section hierarchy with the Stitch design.

### Task 4: Stabilize the clinic sidebar against the Stitch navigation

**Files:**
- Modify: `E:\CTpath-master\frontend\src\components\AppSidebar.vue`

- [ ] Keep the existing role-based menu source.
- [ ] Remove unused model menu icon handling from the clinic sidebar display.
- [ ] Align brand, user meta, counts, and logout CTA with the Stitch left navigation.

### Task 5: Repair the patient detail page into a demo-ready clinical view

**Files:**
- Modify: `E:\CTpath-master\frontend\src\pages\PatientDetailPage.vue`
- Test: `E:\CTpath-master\frontend\src\pages\__tests__\PatientDetailPage.spec.ts`

- [ ] Keep the real prediction trigger and follow-up navigation logic untouched.
- [ ] Replace all mojibake and ambiguous state text with clear Chinese product copy.
- [ ] Preserve the distinction between preloaded summary, predicting, latest prediction, and prediction failed.
- [ ] Update the affected test expectation strings if needed.

### Task 6: Verify the clinic closure still works

**Files:**
- Test: `E:\CTpath-master\frontend\src\pages\__tests__\AppBootstrap.spec.ts`
- Test: `E:\CTpath-master\frontend\src\pages\__tests__\AppWorkspacePage.spec.ts`

- [ ] Run `cmd /c npm run build` under `E:\CTpath-master\frontend`.
- [ ] Run `cmd /c npm test -- src/pages/__tests__/AppBootstrap.spec.ts src/pages/__tests__/PatientDetailPage.spec.ts src/pages/__tests__/AppWorkspacePage.spec.ts` under `E:\CTpath-master\frontend`.
- [ ] Record any remaining phase-2 blockers separately rather than widening the scope in this pass.
