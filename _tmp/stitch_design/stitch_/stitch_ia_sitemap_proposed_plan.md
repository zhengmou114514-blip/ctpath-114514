# Stitch Clinical Workstation - Information Architecture (IA)

## 1. Global Structure (Business Shell)
- **Top Bar**: System status (Demo/MySQL mode), Model health, Current User Profile (Name/Title/Dept), Global notifications, Logout.
- **Side Navigation**: Role-based primary links.
- **Main Content Area**: Mutually exclusive workspaces.

## 2. Role-Based Navigation

### 5.1 Doctor Role
- **Home (Dashboard)**: Patient queue, risk alerts, summary snippets.
- **Patient Management**: Searchable archive of patients.
- **Model Center**:
    - Insight (Patient-specific results)
    - Dashboard (Global performance/monitoring)
- **Data Governance**: Governance dashboard & actions.
- **Medicine Management**: Drug catalog & permission matrix.
- **System Center**: Settings & logs.

### 5.2 Nurse Role
- **Follow-up Workspace**: Task board, contact logs.
- **Process Board**: Workflow visualization.
- **System Center**: Settings.

### 5.3 Archivist Role
- **Patient Archive**: Full records management.
- **Medicine Management**: Drugs & Permissions.
- **Governance Center**: Data quality & conflict resolution.
- **System Center**: Settings.

## 3. Core Page Flows
- **Login Flow**: Login -> Role Detection -> Home Workspace.
- **Main Clinical Flow**: Home -> Select Patient -> Patient Detail -> Run Prediction -> Review Latest Prediction -> Follow-up/Action.
- **Governance Flow**: Governance Center -> Identify Issue -> Perform Action -> Verify Status.

## 4. Key Page Specifications

### Patient Detail (The Hub)
- **Tabs/Sections**: Profile Summary, EHR Summary, Attachment Panel, Patient Timeline, Evidence Summary, AI Prediction & Care Advice, Medication Assessment, Follow-up Access.
- **State States**:
    - *Preloaded*: Static historical data.
    - *Predicting*: Active loading state for API call.
    - *Latest*: Freshly returned AI results.
    - *Failed*: Error handling.