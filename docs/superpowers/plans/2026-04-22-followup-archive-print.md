# Follow-up, Archive, and Print Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make patient archive, follow-up tasks, contact relationships, disease flow, and printable archive output behave like a real hospital workflow, using existing clinic data and openhis-inspired layouts.

**Architecture:** Keep the clinic workspace split into互斥 sections and let the archive page act as the overview hub. Reuse existing workspace controller data (`selectedPatient`, `followupItems`, `flowBoardItems`, `timeline`, `contactLogs`, `auditLogs`) instead of adding a new store. Add a dedicated printable archive view that renders a document-style layout and can trigger browser print.

**Tech Stack:** Vue 3, TypeScript, Vue Router, Pinia, Element Plus, existing clinic service layer.

---

### Task 1: Make follow-up modules open directly from archive and workspace

**Files:**
- Modify: `frontend/src/composables/useWorkspaceController.ts`
- Modify: `frontend/src/pages/AppWorkspacePage.vue`
- Modify: `frontend/src/pages/PatientArchivePage.vue`

- [ ] **Step 1: Write the failing smoke test**

Add or update a small page-level test that clicks the archive quick links and expects `openFollowupModule()` to be called with the selected section even when no patient is preselected.

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npm test -- src/pages/__tests__/AppWorkspacePage.spec.ts`
Expected: the archive quick-link click does not yet reach the follow-up section with the new direct behavior.

- [ ] **Step 3: Implement the minimal logic**

```ts
async function openFollowupModule(patientId?: string, targetSection: 'tasks' | 'contacts' | 'flow' = 'tasks') {
  if (!canAccessSection(targetSection)) {
    setPermissionError('Current role has no permission to open follow-up workspace.')
    followupFocusPatientId.value = ''
    redirectToHomeSection()
    return
  }

  loadingOpenFollowup.value = true
  followupFocusPatientId.value = patientId || selectedPatientId.value || ''
  section.value = targetSection
  clearMessages()
  updateWindowQuery(targetSection)

  try {
    await loadOperationalBoards()
    archiveSuccess.value = 'Follow-up workspace opened successfully.'
  } finally {
    loadingOpenFollowup.value = false
  }
}
```

- [ ] **Step 4: Update the archive quick links**

```vue
<div class="archive-quick-links">
  <button class="secondary-button" type="button" @click="emit('open-followup', { section: 'tasks' })">随访任务</button>
  <button class="secondary-button" type="button" @click="emit('open-followup', { section: 'contacts' })">联系方式</button>
  <button class="secondary-button" type="button" @click="emit('open-followup', { section: 'flow' })">病情流转</button>
</div>
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd frontend && npm test -- src/pages/__tests__/AppWorkspacePage.spec.ts`
Expected: page-level smoke test passes and direct follow-up entry is wired.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/composables/useWorkspaceController.ts frontend/src/pages/AppWorkspacePage.vue frontend/src/pages/PatientArchivePage.vue
git commit -m "feat: direct follow-up entry from archive"
```

### Task 2: Add printable archive document output

**Files:**
- Create: `frontend/src/pages/PatientArchivePrintPage.vue`
- Modify: `frontend/src/pages/AppWorkspacePage.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/pages/PatientArchivePage.vue`

- [ ] **Step 1: Write the failing smoke test**

Add a test that exercises the archive export action and verifies a printable route/view is opened with the current patient data.

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npm test -- src/pages/__tests__/PatientDetailPage.spec.ts`
Expected: there is no printable archive route yet.

- [ ] **Step 3: Implement a document-style print page**

Render:
- patient identity block
- archive summary
-病程时间线
- contact relationships
- audit trail
- current medications and follow-up snapshot

Add a print trigger so the page behaves like a printable hospital document instead of a generic export blob.

- [ ] **Step 4: Wire the archive export action**

```ts
function handleExportPatients() {
  if (!canManageArchive()) {
    setPermissionError('Current role has no permission to export archive.')
    return
  }

  const dataStr = JSON.stringify(allPatients.value, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `patients_${new Date().toISOString().slice(0, 10)}.json`
  link.click()
  URL.revokeObjectURL(url)

  archiveSuccess.value = `Exported ${allPatients.value.length} patients.`
}
```

Replace the export target with a printable route that opens the document view and lets the browser print it.

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd frontend && npm run build`
Expected: printable archive route compiles without breaking the workspace.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/PatientArchivePrintPage.vue frontend/src/pages/AppWorkspacePage.vue frontend/src/router/index.ts frontend/src/pages/PatientArchivePage.vue
git commit -m "feat: add printable archive output"
```

### Task 3: Rework follow-up board data presentation

**Files:**
- Modify: `frontend/src/components/FollowupWorklistBoard.vue`
- Modify: `frontend/src/pages/FollowupWorkbenchPage.vue`
- Modify: `frontend/src/services/types.ts`

- [ ] **Step 1: Write the failing smoke test**

Add a test that asserts:
- follow-up tasks are grouped by status
- contact history includes the patient/emergency-contact relationship
- flow board shows next action and current flow status

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npm test -- src/pages/__tests__/AppWorkspacePage.spec.ts`
Expected: current board still mixes generic copy and needs more explicit data presentation.

- [ ] **Step 3: Update the board layout**

Use the existing `followupItems` and `flowBoardItems` fields to render:
- left board: pending / in progress / completed task columns
- right panel: contact log form and selected task history
- flow snapshot: patient, disease, stage, risk, next action

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd frontend && npm run build`
Expected: clinic build passes with the updated board presentation.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/FollowupWorklistBoard.vue frontend/src/pages/FollowupWorkbenchPage.vue frontend/src/services/types.ts
git commit -m "feat: present follow-up board with real workflow data"
```

### Task 4: Verification and docs

**Files:**
- Modify: `docs/启动方式.md`
- Modify: `README.md` if needed

- [ ] **Step 1: Update startup notes**

Document which module belongs to clinic workflow and how to open the printable archive document during demonstration.

- [ ] **Step 2: Run the final verification commands**

Run:
- `cd frontend && npm run build`
- `E:\Anaconda3\envs\ctpath\python.exe E:\CTpath-master\test_backend_contracts.py`

Expected:
- clinic build passes
- backend contracts pass
- follow-up/archive workflow remains intact

- [ ] **Step 3: Commit**

```bash
git add docs/启动方式.md README.md
git commit -m "docs: record archive print and follow-up workflow"
```
