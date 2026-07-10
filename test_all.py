"""Comprehensive test script for the smart traffic violation system."""
import requests
import json
import sys

BASE = "http://localhost:8001/api/v1"
AI_BASE = "http://localhost:8001/internal/ai"
results = {"pass": 0, "fail": 0, "errors": []}

def test(name, method, url, expected_status, **kwargs):
    """Run a test and check status code."""
    try:
        resp = method(url, **kwargs)
        ok = resp.status_code == expected_status
        status = "PASS" if ok else "FAIL"
        detail = ""
        try:
            body = resp.json()
            if not ok:
                detail = f" body={json.dumps(body, ensure_ascii=False)[:200]}"
        except:
            detail = f" body={resp.text[:200]}"

        if ok:
            results["pass"] += 1
        else:
            results["fail"] += 1
            results["errors"].append(f"{status} {name}: expected {expected_status}, got {resp.status_code}{detail}")

        print(f"{status} {name} -> {resp.status_code}{detail}")
        return resp
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"CRASH {name}: {e}")
        print(f"CRASH {name}: {e}")
        return None

# ============================================================
# STEP 1: Auth Tests
# ============================================================
print("=" * 60)
print("1. AUTH MODULE")
print("=" * 60)

# Login as admin
r = test("Login admin (correct)", requests.post, f"{BASE}/auth/login", 200,
         json={"username": "admin", "password": "admin1234"})
ADMIN_TOKEN = r.json()["access_token"] if r and r.status_code == 200 else None
ADMIN_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

# Login wrong password
test("Login admin (wrong pw)", requests.post, f"{BASE}/auth/login", 401,
     json={"username": "admin", "password": "wrong"})

# Login owner1 (citizen)
r = test("Login citizen (owner1)", requests.post, f"{BASE}/auth/login", 200,
         json={"username": "owner1", "password": "pass1234"})
CITIZEN_TOKEN = r.json()["access_token"] if r and r.status_code == 200 else None
CITIZEN_HEADERS = {"Authorization": f"Bearer {CITIZEN_TOKEN}"}

# Register new user
test("Register new citizen", requests.post, f"{BASE}/auth/register", 200,
     json={"username": "testcitizen2", "password": "test1234", "phone": "13800000002"})

# Register duplicate
test("Register duplicate username", requests.post, f"{BASE}/auth/register", 409,
     json={"username": "admin", "password": "test1234"})

# Get current user
test("GET /auth/me (admin)", requests.get, f"{BASE}/auth/me", 200, headers=ADMIN_HEADERS)

# No token - should fail
test("GET /auth/me (no token)", requests.get, f"{BASE}/auth/me", 401)

# Update profile
test("PUT /auth/profile", requests.put, f"{BASE}/auth/profile", 200,
     headers=ADMIN_HEADERS, json={"phone": "13900000001", "email": "admin@test.com"})

# Change password
test("PUT /auth/password (correct old)", requests.put, f"{BASE}/auth/password", 200,
     headers=ADMIN_HEADERS, json={"old_password": "admin1234", "new_password": "admin1234"})

# Change password with wrong old
test("PUT /auth/password (wrong old)", requests.put, f"{BASE}/auth/password", 400,
     headers=ADMIN_HEADERS, json={"old_password": "wrong", "new_password": "newpass"})

# Get permissions/menus
test("GET /permissions/menus (admin)", requests.get, f"{BASE}/permissions/menus", 200, headers=ADMIN_HEADERS)
test("GET /permissions/menus (citizen)", requests.get, f"{BASE}/permissions/menus", 200, headers=CITIZEN_HEADERS)

# ============================================================
# STEP 2: Intake Tests
# ============================================================
print("\n" + "=" * 60)
print("2. INTAKE MODULE")
print("=" * 60)

# Create a minimal test image
import io
from PIL import Image
img = Image.new('RGB', (100, 100), color='red')
buf = io.BytesIO()
img.save(buf, format='JPEG')
test_img = buf.getvalue()

# Citizen report upload
r = test("POST /intakes/citizen-reports", requests.post, f"{BASE}/intakes/citizen-reports", 200,
         headers=CITIZEN_HEADERS,
         files={"image": ("test.jpg", test_img, "image/jpeg")},
         data={"location_text": "测试路口1号", "captured_at": "2026-07-10T10:00:00"})

# Admin upload
r = test("POST /intakes/admin-uploads", requests.post, f"{BASE}/intakes/admin-uploads", 200,
         headers=ADMIN_HEADERS,
         files={"image": ("admin_test.jpg", test_img, "image/jpeg")},
         data={"location_text": "管理员上传测试", "captured_at": "2026-07-10T11:00:00"})

# Camera capture upload - need a valid camera key first (we'll test that later)
# For now, test without key should fail
test("POST /intakes/camera-captures (no key)", requests.post, f"{BASE}/intakes/camera-captures", 401,
     files={"image": ("cam_test.jpg", test_img, "image/jpeg")})

# Duplicate upload (same image hash)
r = test("POST /intakes/citizen-reports (duplicate)", requests.post, f"{BASE}/intakes/citizen-reports", 409,
         headers=CITIZEN_HEADERS,
         files={"image": ("test.jpg", test_img, "image/jpeg")},
         data={"location_text": "测试路口1号", "captured_at": "2026-07-10T10:00:00"})

# Invalid file type
test("POST /intakes/citizen-reports (invalid type)", requests.post, f"{BASE}/intakes/citizen-reports", 400,
     headers=CITIZEN_HEADERS,
     files={"image": ("malicious.txt", b"not an image", "text/plain")},
     data={"location_text": "bad", "captured_at": "2026-07-10T10:00:00"})

# ============================================================
# STEP 3: Case Tests
# ============================================================
print("\n" + "=" * 60)
print("3. CASE MODULE")
print("=" * 60)

# List cases
r = test("GET /cases (admin)", requests.get, f"{BASE}/cases", 200, headers=ADMIN_HEADERS)
cases = r.json()["items"] if r and r.status_code == 200 else []
print(f"   Found {len(cases)} cases")

# Get case detail
if cases:
    case_id = cases[0]["id"]
    test(f"GET /cases/{case_id}", requests.get, f"{BASE}/cases/{case_id}", 200, headers=ADMIN_HEADERS)

# Approve a case
# First find a pending case
pending_cases = [c for c in cases if c.get("status") == "pending_human_review"]
if pending_cases:
    case_id = pending_cases[0]["id"]
    test(f"POST /cases/{case_id}/approve", requests.post, f"{BASE}/cases/{case_id}/approve", 200,
         headers=ADMIN_HEADERS,
         json={"plate_no": "粤A12345", "violation_type": "speeding", "fine_amount": 200, "points": 3})

# Reject a case
uploaded_cases = [c for c in cases if c.get("status") == "uploaded"]
if uploaded_cases:
    case_id = uploaded_cases[0]["id"]
    test(f"POST /cases/{case_id}/reject", requests.post, f"{BASE}/cases/{case_id}/reject", 200,
         headers=ADMIN_HEADERS, json={"review_opinion": "证据不足"})

# Request recheck
uploaded_cases2 = [c for c in cases if c.get("status") == "uploaded"]
if uploaded_cases2:
    case_id = uploaded_cases2[0]["id"]
    test(f"POST /cases/{case_id}/request-recheck", requests.post, f"{BASE}/cases/{case_id}/request-recheck", 202,
         headers=ADMIN_HEADERS)

# Filter cases by status
test("GET /cases?status=uploaded", requests.get, f"{BASE}/cases?status=uploaded", 200, headers=ADMIN_HEADERS)

# ============================================================
# STEP 4: Violation Tests
# ============================================================
print("\n" + "=" * 60)
print("4. VIOLATION MODULE")
print("=" * 60)

r = test("GET /violations", requests.get, f"{BASE}/violations", 200, headers=ADMIN_HEADERS)
violations = r.json()["items"] if r and r.status_code == 200 else []
print(f"   Found {len(violations)} violations")

if violations:
    v_id = violations[0]["id"]
    test(f"GET /violations/{v_id}", requests.get, f"{BASE}/violations/{v_id}", 200, headers=ADMIN_HEADERS)

# Get violations by owner
test("GET /owners/1/violations", requests.get, f"{BASE}/owners/1/violations", 200, headers=ADMIN_HEADERS)

# Citizen getting own violations
test("GET /owners/1/violations (self)", requests.get, f"{BASE}/owners/1/violations", 200, headers=CITIZEN_HEADERS)

# ============================================================
# STEP 5: Statistics Tests
# ============================================================
print("\n" + "=" * 60)
print("5. STATISTICS MODULE")
print("=" * 60)

test("GET /statistics/overview", requests.get, f"{BASE}/statistics/overview", 200, headers=ADMIN_HEADERS)
test("GET /statistics/by-location", requests.get, f"{BASE}/statistics/by-location", 200, headers=ADMIN_HEADERS)
test("GET /statistics/by-type", requests.get, f"{BASE}/statistics/by-type", 200, headers=ADMIN_HEADERS)
test("GET /statistics/by-time", requests.get, f"{BASE}/statistics/by-time", 200, headers=ADMIN_HEADERS)

# With time filters
test("GET /statistics/overview?start_time=2026-01-01&end_time=2026-12-31", requests.get,
     f"{BASE}/statistics/overview?start_time=2026-01-01T00:00:00&end_time=2026-12-31T23:59:59", 200, headers=ADMIN_HEADERS)

# ============================================================
# STEP 6: Camera CRUD Tests
# ============================================================
print("\n" + "=" * 60)
print("6. CAMERA MODULE")
print("=" * 60)

CAMERA_BASE = f"{BASE}/admin/cameras"

# Create camera
r = test("POST /admin/cameras", requests.post, CAMERA_BASE, 200,
         headers=ADMIN_HEADERS,
         json={"device_code": "CAM-TEST-001", "location_text": "测试路口-中山路"})
camera_id = r.json()["id"] if r and r.status_code == 200 else None

# List cameras
test("GET /admin/cameras", requests.get, CAMERA_BASE, 200, headers=ADMIN_HEADERS)

# Get camera detail
if camera_id:
    test(f"GET /admin/cameras/{camera_id}", requests.get, f"{CAMERA_BASE}/{camera_id}", 200, headers=ADMIN_HEADERS)

# Update camera
if camera_id:
    test(f"PATCH /admin/cameras/{camera_id}", requests.patch, f"{CAMERA_BASE}/{camera_id}", 200,
         headers=ADMIN_HEADERS, json={"location_text": "更新测试路口"})

# Generate API key
if camera_id:
    r = test(f"POST /admin/cameras/{camera_id}/keys", requests.post, f"{CAMERA_BASE}/{camera_id}/keys", 200,
             headers=ADMIN_HEADERS)
    camera_key = r.json().get("raw_key") if r and r.status_code == 200 else None

# List keys
if camera_id:
    test(f"GET /admin/cameras/{camera_id}/keys", requests.get, f"{CAMERA_BASE}/{camera_id}/keys", 200, headers=ADMIN_HEADERS)

# Test camera auth with the key
if camera_key:
    test("POST /intakes/camera-captures (valid key)", requests.post, f"{BASE}/intakes/camera-captures", 200,
         headers={"X-Camera-Key": camera_key},
         files={"image": ("cam_test_valid.jpg", test_img, "image/jpeg")},
         data={"speed": "60.5", "captured_at": "2026-07-10T12:00:00"})

# Revoke key
if camera_id:
    r2 = test(f"GET /admin/cameras/{camera_id}/keys", requests.get, f"{CAMERA_BASE}/{camera_id}/keys", 200, headers=ADMIN_HEADERS)
    keys = r2.json() if r2 and r2.status_code == 200 else []
    if keys:
        key_id = keys[0]["id"]
        test(f"POST .../keys/{key_id}/revoke", requests.post, f"{CAMERA_BASE}/{camera_id}/keys/{key_id}/revoke", 200,
             headers=ADMIN_HEADERS)
        # After revoke, key should fail
        if camera_key:
            test("POST /intakes/camera-captures (revoked key)", requests.post, f"{BASE}/intakes/camera-captures", 401,
                 headers={"X-Camera-Key": camera_key},
                 files={"image": ("cam_revoked.jpg", test_img, "image/jpeg")})

# ============================================================
# STEP 7: User Management Tests
# ============================================================
print("\n" + "=" * 60)
print("7. USER MANAGEMENT MODULE")
print("=" * 60)

USER_BASE = f"{BASE}/admin/users"

# Create user
r = test("POST /admin/users (create)", requests.post, USER_BASE, 200,
         headers=ADMIN_HEADERS,
         json={"username": "testreviewer1", "password": "pass1234", "role_code": "reviewer", "phone": "13800000003"})
new_user_id = r.json()["id"] if r and r.status_code == 200 else None

# List users
test("GET /admin/users", requests.get, USER_BASE, 200, headers=ADMIN_HEADERS)

# Get user
if new_user_id:
    test(f"GET /admin/users/{new_user_id}", requests.get, f"{USER_BASE}/{new_user_id}", 200, headers=ADMIN_HEADERS)

# Update user
if new_user_id:
    test(f"PATCH /admin/users/{new_user_id}", requests.patch, f"{USER_BASE}/{new_user_id}", 200,
         headers=ADMIN_HEADERS, json={"phone": "13900000004", "status": "active"})

# Disable user
if new_user_id:
    test(f"PATCH /admin/users/{new_user_id} (disable)", requests.patch, f"{USER_BASE}/{new_user_id}", 200,
         headers=ADMIN_HEADERS, json={"status": "disabled"})

# ============================================================
# STEP 8: Vehicle Management Tests
# ============================================================
print("\n" + "=" * 60)
print("8. VEHICLE MODULE")
print("=" * 60)

VEHICLE_BASE = f"{BASE}/admin/vehicles"

# Create vehicle
r = test("POST /admin/vehicles", requests.post, VEHICLE_BASE, 200,
         headers=ADMIN_HEADERS,
         json={"plate_no": "粤C99999", "owner_id": 2, "vehicle_type": "sedan", "color": "white"})
vehicle_id = r.json()["id"] if r and r.status_code == 200 else None

# List vehicles
test("GET /admin/vehicles", requests.get, VEHICLE_BASE, 200, headers=ADMIN_HEADERS)

# Get vehicle
if vehicle_id:
    test(f"GET /admin/vehicles/{vehicle_id}", requests.get, f"{VEHICLE_BASE}/{vehicle_id}", 200, headers=ADMIN_HEADERS)

# Update vehicle
if vehicle_id:
    test(f"PATCH /admin/vehicles/{vehicle_id}", requests.patch, f"{VEHICLE_BASE}/{vehicle_id}", 200,
         headers=ADMIN_HEADERS, json={"color": "black"})

# Duplicate plate
test("POST /admin/vehicles (duplicate plate)", requests.post, VEHICLE_BASE, 409,
     headers=ADMIN_HEADERS,
     json={"plate_no": "粤C99999", "owner_id": 2, "vehicle_type": "suv", "color": "red"})

# ============================================================
# STEP 9: Violation Rules Tests
# ============================================================
print("\n" + "=" * 60)
print("9. VIOLATION RULES MODULE")
print("=" * 60)

RULES_BASE = f"{BASE}/admin/rules"

r = test("POST /admin/rules", requests.post, RULES_BASE, 200,
         headers=ADMIN_HEADERS,
         json={"rule_code": "SPEED-LIMIT-60", "violation_type": "speeding", "rule_type": "speed",
               "params": {"limit": 60}, "description": "限速60km/h"})
rule_id = r.json()["id"] if r and r.status_code == 200 else None

test("GET /admin/rules", requests.get, RULES_BASE, 200, headers=ADMIN_HEADERS)

if rule_id:
    test(f"GET /admin/rules/{rule_id}", requests.get, f"{RULES_BASE}/{rule_id}", 200, headers=ADMIN_HEADERS)
    test(f"PATCH /admin/rules/{rule_id}", requests.patch, f"{RULES_BASE}/{rule_id}", 200,
         headers=ADMIN_HEADERS, json={"is_active": False})

# ============================================================
# STEP 10: Rewards Tests
# ============================================================
print("\n" + "=" * 60)
print("10. REWARDS MODULE")
print("=" * 60)

test("GET /admin/rewards", requests.get, f"{BASE}/admin/rewards", 200, headers=ADMIN_HEADERS)

# ============================================================
# STEP 11: Audit Logs Tests
# ============================================================
print("\n" + "=" * 60)
print("11. AUDIT LOGS MODULE")
print("=" * 60)

test("GET /admin/audit-logs", requests.get, f"{BASE}/admin/audit-logs", 200, headers=ADMIN_HEADERS)

# ============================================================
# STEP 12: Analysis / Report Tests
# ============================================================
print("\n" + "=" * 60)
print("12. ANALYSIS / REPORT MODULE")
print("=" * 60)

test("POST /analysis/reports", requests.post, f"{BASE}/analysis/reports", 200,
     headers=ADMIN_HEADERS, json={"report_type": "weekly", "start_time": "2026-07-01T00:00:00", "end_time": "2026-07-10T23:59:59"})

# ============================================================
# STEP 13: Internal AI Tests
# ============================================================
print("\n" + "=" * 60)
print("13. INTERNAL AI MODULE")
print("=" * 60)

# YOLO detect
r = test("POST /internal/ai/yolo/detect", requests.post, f"{AI_BASE}/yolo/detect", 200,
         headers=ADMIN_HEADERS,
         files={"image": ("ai_test.jpg", test_img, "image/jpeg")})
if r and r.status_code == 200:
    detections = r.json()
    print(f"   YOLO returned {len(detections)} objects")

# OCR
test("POST /internal/ai/ocr/plate", requests.post, f"{AI_BASE}/ocr/plate", 200,
     headers=ADMIN_HEADERS,
     files={"image": ("plate_test.jpg", test_img, "image/jpeg")})

# Rule evaluation
test("POST /internal/ai/rules/evaluate", requests.post, f"{AI_BASE}/rules/evaluate", 200,
     headers=ADMIN_HEADERS,
     json={
         "detection": {"objects": [{"class": "car", "bbox": [100, 200, 300, 350], "confidence": 0.92}]},
         "ocr": {"plate_no": "京A12345"},
         "intake_event": {"speed": 80.0},
         "rule": {"rule_code": "SPEED-60", "rule_type": "speed", "params": {"limit": 60}}
     })

# AI review
test("POST /internal/ai/review/text", requests.post, f"{AI_BASE}/review/text", 200,
     headers=ADMIN_HEADERS,
     json={
         "detection": {"objects": [{"class": "car", "bbox": [100, 200, 300, 350], "confidence": 0.92}]},
         "ocr": {"plate_no": "京A12345"},
         "rule_evaluation": {"match": True, "evidence": "车速80，限速60", "rule_code": "SPEED-60"},
         "intake_event": {"speed": 80.0, "location_text": "中山路"}
     })

# Auth check - citizen can't access AI
test("POST /internal/ai/yolo/detect (citizen)", requests.post, f"{AI_BASE}/yolo/detect", 403,
     headers=CITIZEN_HEADERS,
     files={"image": ("test.jpg", test_img, "image/jpeg")})

# ============================================================
# STEP 14: Role-based Access Tests
# ============================================================
print("\n" + "=" * 60)
print("14. ROLE-BASED ACCESS CONTROL")
print("=" * 60)

# Citizen can't access admin endpoints
test("GET /admin/users (citizen)", requests.get, f"{BASE}/admin/users", 403, headers=CITIZEN_HEADERS)
test("GET /admin/cameras (citizen)", requests.get, f"{BASE}/admin/cameras", 403, headers=CITIZEN_HEADERS)
test("GET /admin/vehicles (citizen)", requests.get, f"{BASE}/admin/vehicles", 403, headers=CITIZEN_HEADERS)
test("GET /admin/rules (citizen)", requests.get, f"{BASE}/admin/rules", 403, headers=CITIZEN_HEADERS)
test("GET /admin/rewards (citizen)", requests.get, f"{BASE}/admin/rewards", 403, headers=CITIZEN_HEADERS)
test("GET /admin/audit-logs (citizen)", requests.get, f"{BASE}/admin/audit-logs", 403, headers=CITIZEN_HEADERS)

# Citizen can't access reviewer endpoints
test("GET /violations (citizen)", requests.get, f"{BASE}/violations", 403, headers=CITIZEN_HEADERS)

# Citizen can't approve/reject cases
if cases:
    test("POST cases/approve (citizen)", requests.post, f"{BASE}/cases/{cases[0]['id']}/approve", 403,
         headers=CITIZEN_HEADERS, json={"plate_no": "test", "violation_type": "speeding"})

# ============================================================
# STEP 15: Edge Cases
# ============================================================
print("\n" + "=" * 60)
print("15. EDGE CASES")
print("=" * 60)

# Pagination
test("GET /cases?page=1&page_size=5", requests.get, f"{BASE}/cases?page=1&page_size=5", 200, headers=ADMIN_HEADERS)
test("GET /cases?page=999&page_size=10", requests.get, f"{BASE}/cases?page=999&page_size=10", 200, headers=ADMIN_HEADERS)

# Non-existent IDs
test("GET /cases/99999", requests.get, f"{BASE}/cases/99999", 404, headers=ADMIN_HEADERS)
test("GET /violations/99999", requests.get, f"{BASE}/violations/99999", 404, headers=ADMIN_HEADERS)
test("GET /admin/cameras/99999", requests.get, f"{BASE}/admin/cameras/99999", 404, headers=ADMIN_HEADERS)
test("GET /admin/users/99999", requests.get, f"{BASE}/admin/users/99999", 404, headers=ADMIN_HEADERS)
test("GET /admin/vehicles/99999", requests.get, f"{BASE}/admin/vehicles/99999", 404, headers=ADMIN_HEADERS)

# Empty body on approve
if cases:
    test("POST cases/approve (empty body)", requests.post, f"{BASE}/cases/{cases[0]['id']}/approve", 422,
         headers=ADMIN_HEADERS, json={})

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
total = results["pass"] + results["fail"]
print(f"Total: {total} | PASS: {results['pass']} | FAIL: {results['fail']}")
if results["errors"]:
    print(f"\nFailed tests ({len(results['errors'])}):")
    for e in results["errors"]:
        print(f"  {e}")
print(f"\nPass rate: {results['pass']/total*100:.1f}%" if total > 0 else "No tests run")
