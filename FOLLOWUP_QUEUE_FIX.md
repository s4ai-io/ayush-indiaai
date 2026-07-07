# Follow-up Visits & the Doctor's Pending Queue — Bug Fix

## The bug

The doctor dashboard's **Pending Queue** tab (and the **Completed** tab) filtered
patients by `Patient.diagnosis_done` — a single boolean on the *patient* row,
set to `True` the first time any prescription was ever saved for them, and
never reset.

That's patient-level state being used to answer a per-visit question. Once a
patient had one completed diagnosis, `diagnosis_done` stayed `True` forever —
so:

- Any **follow-up visit** created for that patient (`parent_visit_id` set, no
  prescription yet) never showed up in Pending Queue. It also showed up
  *immediately* in the Completed tab, before the doctor had done anything with
  it, because Completed was `Patient.diagnosis_done == True` too — matched by
  every visit belonging to that patient, prescribed or not.
- Only a patient's very first-ever visit could ever appear as "pending"; a
  second unprescribed visit for the same patient (follow-up or otherwise) was
  invisible.

This was already affecting the real database before this fix — 10 visits sat
with an empty prescription (`{}`) while their patients had long since flipped
to `diagnosis_done = True` from an earlier visit, including one real follow-up
visit for "Back Pain" that had no way of ever reaching a doctor.

## The fix

Pending vs. completed is now a **per-visit** question, answered from the
`medical_records.prescription` column itself:

- **Pending**: `prescription IS NULL OR prescription = '' OR prescription = '{}'`
- **Completed**: anything else (a real prescription was saved)

`Patient.diagnosis_done` is untouched and still used elsewhere (e.g. the
"Visited" badge in the patient directory) — this fix only changes what feeds
the doctor's two queue tabs.

The Pending Queue now returns **one entry per thing needing doctor
attention**, not one per patient:

- A pending visit (first-time or follow-up) — clicking "Consult" **resumes
  that exact visit** (`/doctor/treatment/{record_id}`), no new consultation is
  created. Previously, clicking "Consult" on a pending-queue card always
  created a *brand-new* consultation, silently orphaning whatever visit had
  actually been queued (e.g. a receptionist's follow-up pick).
- A patient with **zero** visits yet — same as before, "Consult" creates the
  first consultation on click.

Follow-up entries carry an `is_followup` flag and show a purple "Follow-up:
{condition}" badge on the queue card; completed follow-ups get the same badge
in the Completed tab.

### Receptionist follow-up menu

Receptionists can now also flag a queued visit as a follow-up. Previously the
New-vs-Follow-up dialog (`FollowupChoiceDialog`, on `/patients`) was
doctor/admin-only, gated on the same endpoint that returns a patient's full
clinical history (`/api/patients/{id}/diagnoses` — symptoms, notes,
prescriptions, vitals), which receptionists are correctly not allowed to see.

A new endpoint, **`GET /api/patients/{id}/conditions`**, returns *only* the
distinct diagnosis names + visit id/date for a patient — nothing clinical.
It needs no RBAC change: it doesn't match the `history|diagnoses` pattern
reserved for doctor/admin, so it falls through to the existing "shared
patient directory" rule and is available to every authenticated role.
`FollowupChoiceDialog` now uses this endpoint, so the same dialog works for
receptionists on `/patients` — pick "Follow-up" + a condition, and the queued
visit shows up in the doctor's Pending Queue tagged accordingly.

## Is a DB migration required?

**No.** Every column this fix relies on (`prescription`, `parent_visit_id`)
already exists — `parent_visit_id` was added in the prior follow-up-visits
change (`scripts/add_followup_and_vitals_columns.py`, already run). This fix
is a pure query-logic change in `backend/services/csv_service.py` and
`backend/main.py`. If you're setting up a fresh environment, just make sure
that earlier migration has been run:

```bash
cd backend
./venv/bin/python scripts/add_followup_and_vitals_columns.py
```

## Seeding demo follow-up visits

To see the fix working with real follow-up entries in the queue (rather than
waiting for real patients to be re-queued):

```bash
cd backend
./venv/bin/python scripts/generate_followup_visits.py
# or, for a different count:
FOLLOWUP_SEED_COUNT=10 ./venv/bin/python scripts/generate_followup_visits.py
```

This picks up to `FOLLOWUP_SEED_COUNT` (default 5) already-diagnosed patients,
clones their most recent visit (diagnosis/symptoms/prakriti/vikriti/
comorbidities) into a new pending `medical_records` row linked via
`parent_visit_id`, and leaves it unprescribed. It's idempotent-ish in effect
(each run adds another round of follow-ups) but safe to run — it never
touches existing rows, only inserts new ones.

## What changed, file by file

| File | Change |
|---|---|
| `backend/services/csv_service.py` | `_visit_queue()` shared helper (prescription-based filter); `get_pending_visit_queue()` (pending visits + never-consulted patients); `get_completed_diagnoses_summary()` rewritten on the same filter; new `get_patient_conditions()`; removed the now-dead `get_patients_by_status()`. |
| `backend/main.py` | `GET /api/patients?status=pending\|completed` now calls the visit-based queries; new `GET /api/patients/{id}/conditions`. |
| `backend/scripts/generate_followup_visits.py` | New — seeds demo follow-up visits (see above). |
| `src/types/clinical.ts` | New `PendingQueueEntry`, `PatientCondition` types; `CompletedDiagnosis` gained `parent_visit_id` / `is_followup`. |
| `src/components/consultation/FollowupChoiceDialog.tsx` | Switched from `/diagnoses` (doctor/admin-only, heavy) to `/conditions` (all roles, minimal). |
| `src/app/patients/page.tsx` | Follow-up dialog now available to every role (was doctor/admin-only), driven by the lightweight condition list. |
| `src/app/doctor/page.tsx` | Pending tab rewritten around `PendingQueueEntry`; `QueueCard` resumes an existing pending visit directly instead of always creating a new one; follow-up badges on both tabs. |
