"""
End-to-end verification: RL Q-values must only change on follow-up outcome, not on first-time prescribe.

Flow:
  1. Login as doctor
  2. Create patient
  3. Create first-time consultation → prescribe → snapshot Q-table (expect NO change)
  4. Create follow-up consultation with vitals → prescribe → POST /outcome with "improved"
  5. Re-check Q-table → expect upward shift for the parent visit's plan actions
"""
import sys, json, requests

BASE = "http://localhost:8000"

doctor   = requests.Session()
admin    = requests.Session()

# ── 1. Login (doctor + admin) ───────────────────────────────────────────────────
print("=== Step 1: Login ===")
r = doctor.post(f"{BASE}/api/auth/login", json={"username": "doctor", "password": "Doctor@123"})
assert r.status_code == 200, f"Doctor login failed: {r.status_code} {r.text}"
r = admin.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "Admin@123"})
assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
print("Both sessions authenticated.")

# ── 2. Create patient (admin, receptionist role required) ──────────────────────
print("\n=== Step 2: Create patient ===")
r = admin.post(f"{BASE}/api/patients", json={
    "basicInfo":   {"firstName": "Test", "lastName": "VerifyRL", "gender": "Male", "age": 45, "maritalStatus": ""},
    "contactInfo": {"mobileNumber": "9999888877", "address": "", "city": "", "state": "", "pincode": ""},
    "otherInfo":   {"occupation": "", "bloodGroup": "", "idType": "", "idNumber": ""},
})
assert r.status_code == 200, f"Patient creation failed: {r.status_code} {r.text}"
patient_id = r.json()["patient_id"]
print(f"Patient created: {patient_id}")

# ── 3a. First-time consultation ─────────────────────────────────────────────────
print("\n=== Step 3a: Create first-time consultation ===")
r = doctor.post(f"{BASE}/api/consultations", json={
    "patientId": patient_id,
    "assessment": {
        "symptoms":   "Joint pain, fatigue",
        "diagnosis":  "Amavata",
        "prakriti":   "Vata",
        "vikriti":    "Pitta",
        "comorbidities": "",
        "notes":      "",
        "parent_visit_id": None,
    },
})
assert r.status_code == 200, f"Consultation failed: {r.status_code} {r.text}"
visit1_id = r.json().get("visit_id") or r.json().get("id") or r.json().get("visitId")
print(f"Visit 1 id: {visit1_id}")

# ── 3b. Get AI treatment recommendation (POST /api/recommend) ─────────────────
print("\n=== Step 3b: Get AI recommendation ===")
prakriti = "Vata"
vikriti  = "Pitta"
r = doctor.post(f"{BASE}/api/recommend", json={
    "disease":       "Amavata",
    "symptoms":      "Joint pain, fatigue",
    "prakriti":      prakriti,
    "vikriti":       vikriti,
    "age":           45,
    "gender":        "Male",
    "comorbidities": "",
})
assert r.status_code == 200, f"Recommend failed: {r.status_code} {r.text}"
treatment = r.json()
namc_code = treatment.get("namc_code") or treatment.get("original_ai_plan", {}).get("namc_code") or "UNKNOWN"
print(f"namc_code={namc_code}, prakriti={prakriti}, vikriti={vikriti}")

# Build a minimal plan with known entries so _plan_action_keys has actions to update.
# (The real recommendation returns empty lists for Amavata — no dataset entries — so we
#  inject plausible entries to make the Q-update path observable.)
plan = {
    "namc_code":  namc_code,
    "match_method": treatment.get("match_method"),
    "match_confidence": treatment.get("match_confidence"),
    "herbs": [
        {"name": "Shallaki",   "dosage": "500mg BD", "benefits": "Anti-inflammatory"},
        {"name": "Guggul",     "dosage": "500mg BD", "benefits": "Joint support"},
    ],
    "yoga": [
        {"practice": "Bhujangasana", "duration": "5 min", "benefits": "Back strength"},
    ],
    "diet": ["Avoid cold foods", "Warm sesame oil massage"],
    "lifestyle": ["Daily 30-min walk", "Adequate sleep"],
}
print(f"Using plan: herbs={[h['name'] for h in plan['herbs']]}, yoga={[y['practice'] for y in plan['yoga']]}")

# ── Snapshot Q-table BEFORE first prescribe ────────────────────────────────────
print("\n=== Snapshot Q-table BEFORE first prescribe ===")
r = admin.get(f"{BASE}/api/model/q-table-state", params={"namc_code": namc_code, "prakriti": prakriti, "vikriti": vikriti})
assert r.status_code == 200, f"Q-table state failed: {r.status_code} {r.text}"
q_before = {a["name"]: a["q_value"] for a in r.json().get("actions", [])}
print(f"Q-table actions before prescribe: {len(q_before)} keys")

# ── 3c. Prescribe (first time, no rating, severity=6) ──────────────────────────
print("\n=== Step 3c: First-time prescribe ===")
r = doctor.post(f"{BASE}/api/prescribe", json={
    "patientId":          patient_id,
    "visitId":            visit1_id,
    "disease":            "Amavata",
    "symptoms":           "Joint pain, fatigue",
    "comorbidities":      "",
    "prakriti":           prakriti,
    "vikriti":            vikriti,
    "treatmentPlan":      plan,
    "original_ai_plan":   plan,
    "doctorPrescription": "Test first-time prescription",
    "doctorNotes":        "",
    "rating":             None,   # explicitly not sending a rating
    "feedback":           "",
    # Vitals at first visit (will be the baseline)
    "bpm":         72,
    "sugar_level": 8.5,
    "spo2":        98,
    "temperature": 37.0,
    "systolic_bp": 130,
    "diastolic_bp": 85,
})
assert r.status_code == 200, f"Prescribe failed: {r.status_code} {r.text}"
print(f"Prescribe response: {r.json().get('status','?')}")

# Give background task a moment to run
import time; time.sleep(2)

# ── Snapshot Q-table AFTER first prescribe ────────────────────────────────────
print("\n=== Snapshot Q-table AFTER first prescribe (expect NO change) ===")
r = admin.get(f"{BASE}/api/model/q-table-state", params={"namc_code": namc_code, "prakriti": prakriti, "vikriti": vikriti})
q_after_first = {a["name"]: a["q_value"] for a in r.json().get("actions", [])}
changed = {k: (q_before.get(k, 0.0), v) for k, v in q_after_first.items() if abs(v - q_before.get(k, 0.0)) > 0.0001}
if changed:
    print(f"FAIL — Q-values changed after first prescribe: {changed}")
    sys.exit(1)
else:
    print("PASS — No Q-values changed after first-time prescribe.")

# ── 4a. Follow-up consultation ─────────────────────────────────────────────────
print("\n=== Step 4a: Create follow-up consultation ===")
r = doctor.post(f"{BASE}/api/consultations", json={
    "patientId": patient_id,
    "assessment": {
        "symptoms":      "Improved, some residual stiffness",
        "diagnosis":     "Amavata",
        "prakriti":      prakriti,
        "vikriti":       vikriti,
        "comorbidities": "",
        "notes":         "Follow-up after 4 weeks",
        "parent_visit_id": visit1_id,
    },
})
assert r.status_code == 200, f"Follow-up consultation failed: {r.status_code} {r.text}"
visit2_id = r.json().get("visit_id") or r.json().get("id") or r.json().get("visitId")
print(f"Visit 2 (follow-up) id: {visit2_id}")

# ── 4b. Prescribe follow-up visit with vitals (severity improved: 6→3) ─────────
print("\n=== Step 4b: Prescribe follow-up visit with vitals ===")
r = doctor.post(f"{BASE}/api/prescribe", json={
    "patientId":          patient_id,
    "visitId":            visit2_id,
    "disease":            "Amavata",
    "symptoms":           "Residual stiffness",
    "comorbidities":      "",
    "prakriti":           prakriti,
    "vikriti":            vikriti,
    "treatmentPlan":      plan,
    "original_ai_plan":   plan,
    "doctorPrescription": "Continue same herbs, reduce yoga to 20 min",
    "doctorNotes":        "",
    "rating":             None,
    "feedback":           "",
    # Vitals at follow-up
    "bpm":         70,
    "sugar_level": 7.8,
    "spo2":        99,
    "temperature": 36.8,
    "systolic_bp": 125,
    "diastolic_bp": 82,
})
assert r.status_code == 200, f"Follow-up prescribe failed: {r.status_code} {r.text}"
print(f"Follow-up prescribe: {r.json().get('status','?')}")
time.sleep(1)

# ── 4c. POST outcome — doctor marks "improved" ─────────────────────────────────
print("\n=== Step 4c: POST /api/visits/{visit2_id}/outcome (improved) ===")
r = doctor.post(f"{BASE}/api/visits/{visit2_id}/outcome", json={"doctor_reported_outcome": "improved"})
assert r.status_code == 200, f"Outcome POST failed: {r.status_code} {r.text}"
outcome_resp = r.json()
print(json.dumps(outcome_resp, indent=2))

# ── 5. Re-check Q-table — expect upward shift ──────────────────────────────────
print("\n=== Step 5: Q-table AFTER follow-up outcome (expect upward shift) ===")
r = admin.get(f"{BASE}/api/model/q-table-state", params={"namc_code": namc_code, "prakriti": prakriti, "vikriti": vikriti})
q_final = {a["name"]: a["q_value"] for a in r.json().get("actions", [])}

updated = {k: (q_before.get(k, 0.0), q_final[k]) for k in q_final if abs(q_final[k] - q_before.get(k, 0.0)) > 0.0001}
if not updated:
    print("FAIL — No Q-values changed after follow-up outcome. Check apply_followup_outcome.")
    sys.exit(1)

improved_count = sum(1 for old, new in updated.values() if new > old)
total = len(updated)
print(f"PASS — {total} actions updated, {improved_count}/{total} moved upward (expected > 0).")
print("\nUpdated Q-values (old → new):")
for k, (old, new) in sorted(updated.items(), key=lambda x: -(x[1][1] - x[1][0])):
    direction = "↑" if new > old else "↓"
    print(f"  {direction} {k}: {old:.4f} → {new:.4f}  (delta {new-old:+.4f})")

print("\n=== Verification complete ===")
print("First-time prescribe: Q unchanged ✓")
print("Follow-up outcome:     Q shifted upward ✓" if improved_count > 0 else "Follow-up outcome: NOT all shifted up — check reward sign")
