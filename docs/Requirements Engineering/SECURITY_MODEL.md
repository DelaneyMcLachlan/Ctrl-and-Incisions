# Security model

> **Project context:** A lab workstation application that fuses **NDI tracker 6‑DoF pose** with **live ultrasound/webcam image** in a single UI. Early testing may use **phone accelerometers + webcam**; production lab use will connect to actual **NDI hardware** and ultrasound. Real subject data **may** be captured; controls below reflect that.

## 1) Roles

### Scope & assumptions
- Hardware: NDI tracker connected **via USB/serial** (e.g., Aurora/Polaris common API), plus ultrasound capture (USB frame‑grabber) or webcam.
- Runtime: Single **lab workstation**; **no server** or cloud dependency.
- Connectivity: **Local USB/serial** between tracking hardware and the app (no IP networking). If a network stream is added later, see the Compliance checklist note on TLS.
- Testing path: Phase 1 uses **phone accelerometer** + **webcam**; Phase 2 uses **NDI hardware** + ultrasound.
- Non‑functional requirement tags used: **SEC‑A (Authentication)**, **SEC‑Z (Authorization)**, **SEC‑D (Data protection)**, **SEC‑L (Logging/Audit)**, **SEC‑O (Operational safety/accuracy)**.

### Roles — **SEC‑Z**
- **User (Lab Member)** — run the app in **Live Mode** without login; view pose + image; perform calibration; record sessions; add annotations.
- **Supervisor (Faculty/PI)** — access **Saved Mode** (load/review/export saved sessions) using **university SSO**; can approve exports for coursework/publication. *(No separate Admin role; user management is handled by the university SSO itself.)*

### Authentication — **SEC‑A (minimal by design)**
- **Live Mode (no login):** Anyone at the workstation can open the app, connect devices, and visualize data.
- **Saved Mode (login required):** Viewing/exporting **saved sessions** requires **university SSO** login (students/faculty). No MFA required.
- **Session timeouts:** Saved‑mode sessions auto‑lock after **20 minutes idle**; re‑authenticate to continue.

### Authorization — **SEC‑Z**
- **User (Lab Member):** create and save sessions, add annotations; cannot export raw data unless logged in with SSO.
- **Supervisor:** load any saved session; export raw or derived data for research/assessment.
- **Data scoping:** Saved sessions are labeled by random **SessionID** (no names in filenames). If subject identifiers are ever captured, they are stored in a small separate JSON file that is **not** required for pose/image loading.

### Data protection — **SEC‑D / SEC‑L / SEC‑O**
- **In transit:** Device links are **USB/serial** on the same machine; **TLS is not applicable**. 
- **At rest:** Enable workstation **full‑disk encryption** (BitLocker/FileVault; XTS‑AES). Optionally encrypt each saved session file using an app‑level key (e.g., AES‑GCM) if storing beyond the lab.
- **File layout:** Store **pose**, **image frames**, and **metadata** under `data/<SessionID>/`; keep any identifiers in `data/<SessionID>/identifiers.json` (restricted by Saved‑Mode auth).
- **Logging:** Keep a simple CSV/JSON log: app start/stop, device connect/disconnect, save/load/export events, and SSO username for Saved‑Mode operations. Retain **90 days** (capstone scope).
- **Operational safety/accuracy:** Provide a **pre‑session calibration check** (probe/tool registration + image overlay sanity check) and warn if environmental conditions (e.g., metal near EM tracker) could degrade accuracy.

---

## 2) Compliance checklist

| Requirement | How Met | Evidence/Notes |
|---|---|---|
| **Use with real data** | SessionID‑based file layout; identifiers isolated in a separate file; Saved‑Mode login required to open/export | Folder structure screenshot; example `identifiers.json` redacted |
| **Access control (minimal)** | No login for Live Mode; **SSO required** to open/export saved sessions; Supervisor can mark sessions as restricted | SSO login screen; role summary in README |
| **“TLS vs USB” clarity** | NDI tracker uses **USB/serial**; **no TLS** required on‑device. If network streaming is added later, enforce **TLS 1.2+** | Connection diagram; note in README |
| **Encryption at rest** | Workstation **full‑disk encryption** (BitLocker/FileVault, XTS‑AES); optional per‑session encryption if data leaves the lab | OS security settings screenshot; optional app key config |
| **Logging & audit (capstone)** | Log save/load/export + SSO user; retain 90 days | Sample log file; retention note |
| **Calibration & accuracy** | Pre‑session calibration checklist; warning if EM interference likely; document tracker accuracy class from vendor | `calibration_checklist.md`; in‑app warning screen |
| **Data retention (capstone)** | Keep sessions only for project term; delete or archive securely after grading/publication | Retention policy section in README |
| **Subject consent** | If real subjects are used, store consent form copy alongside SessionID; restrict loading to Saved‑Mode | Consent template; folder example |