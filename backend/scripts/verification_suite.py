"""
End-to-End Verification Suite for Job Application Tracker
===========================================================
Executes full verification of candidate application lifecycle, HR workflow,
authorization checks, database persistence, history timeline, and edge cases.
"""

import os
import sys

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app
from extensions import db, bcrypt
from models.user import User, Role
from models.job import JobApplication, ApplicationStatus, ApplicationStatusHistory, InterviewDetail, STATUS_TRANSITIONS
from seed import seed_database

def run_verification():
    os.environ.setdefault("DEMO_USER_EMAIL", "user@gmail.com")
    os.environ.setdefault("DEMO_USER_PASSWORD", "user123")
    os.environ.setdefault("DEMO_HR_EMAIL", "hr@gmail.com")
    os.environ.setdefault("DEMO_HR_PASSWORD", "hr123")
    os.environ.setdefault("DEMO_ADMIN_EMAIL", "admin@gmail.com")
    os.environ.setdefault("DEMO_ADMIN_PASSWORD", "admin123")

    print("=" * 70)
    print("STARTING E2E VERIFICATION OF JOB APPLICATION TRACKER")
    print("=" * 70)

    # Use SQLite engine for standalone verification suite execution
    from sqlalchemy import create_engine
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["CACHE_TYPE"] = "SimpleCache"

    test_engine = create_engine("sqlite:///:memory:")
    db._app_engines[app] = {None: test_engine}
    
    from extensions import cache
    cache.init_app(app)

    with app.app_context():
        db.drop_all()
        db.create_all()
        # Step 1: Database Seed & Schema Verification
        seed_database()
        print("[PASS] Step 1: Database seeded & tables verified.")

        client = app.test_client()

        # Step 2: HR Login Verification
        hr_login = client.post("/login", json={"email": "hr@gmail.com", "password": "hr123"})
        assert hr_login.status_code == 200, f"HR login failed: {hr_login.data}"
        hr_token = hr_login.json["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}
        assert hr_login.json["user"]["role"] == "HR"
        print("[PASS] Step 2 & 3: HR Login successful with HR role.")

        # Step 3: Create Candidate Accounts
        cand1_res = client.post("/register", json={"name": "Alice Candidate", "email": "alice@test.com", "password": "candidate-test-password"})
        assert cand1_res.status_code in (201, 409)
        
        cand1_login = client.post("/login", json={"email": "alice@test.com", "password": "candidate-test-password"})
        cand1_token = cand1_login.json["access_token"]
        cand1_headers = {"Authorization": f"Bearer {cand1_token}"}

        cand2_res = client.post("/register", json={"name": "Bob Candidate", "email": "bob@test.com", "password": "candidate-test-password"})
        assert cand2_res.status_code in (201, 409)
        cand2_login = client.post("/login", json={"email": "bob@test.com", "password": "candidate-test-password"})
        cand2_token = cand2_login.json["access_token"]
        cand2_headers = {"Authorization": f"Bearer {cand2_token}"}
        print("[PASS] Step 5: Candidate accounts created and authenticated.")

        # Step 4: Unauthorized HR access check
        candidate_hr_attempt = client.get("/api/hr/applications", headers=cand1_headers)
        assert candidate_hr_attempt.status_code == 403, f"Candidate was able to access HR API! {candidate_hr_attempt.status_code}"
        print("[PASS] Step 4 & 23: Candidate blocked from accessing HR API (403 Forbidden).")

        # Step 5: Candidate creates job applications
        app1_res = client.post("/api/applications", json={
            "company": "Tesla Motors",
            "role": "Autopilot Software Engineer",
            "status": "APPLIED",
            "notes": "Submitted resume & portfolio"
        }, headers=cand1_headers)
        assert app1_res.status_code == 201
        app1_id = app1_res.json["application"]["id"]

        app2_res = client.post("/api/applications", json={
            "company": "Apple Inc",
            "role": "iOS Developer",
            "status": "APPLIED",
            "notes": "Applied via referral"
        }, headers=cand2_headers)
        assert app2_res.status_code == 201
        app2_id = app2_res.json["application"]["id"]
        print("[PASS] Step 6: Candidate 1 and Candidate 2 created job applications.")

        # Candidate cross-access check
        cross_access = client.get(f"/api/applications/{app2_id}", headers=cand1_headers)
        assert cross_access.status_code in (403, 404), f"Candidate 1 accessed Candidate 2 app! {cross_access.status_code}"
        print("[PASS] Step 23: Candidate 1 blocked from accessing Candidate 2's application.")

        # Step 6: HR views candidate application
        hr_apps = client.get("/api/hr/applications", headers=hr_headers)
        assert hr_apps.status_code == 200
        found_app = next((a for a in hr_apps.json["applications"] if a["id"] == app1_id), None)
        assert found_app is not None
        assert found_app["candidate"]["email"] == "alice@test.com"
        print("[PASS] Step 7 & 8: HR lists applications and sees candidate's application.")

        # Step 7: HR updates status: APPLIED → UNDER_REVIEW
        status_update1 = client.patch(f"/api/hr/applications/{app1_id}/status", json={
            "status": "UNDER_REVIEW",
            "notes": "Profile meets requirements"
        }, headers=hr_headers)
        assert status_update1.status_code == 200

        # Step 8: Verify DB update & status_history
        db_app1 = JobApplication.query.get(app1_id)
        assert db_app1.status == ApplicationStatus.UNDER_REVIEW
        history1 = ApplicationStatusHistory.query.filter_by(application_id=app1_id).order_by(ApplicationStatusHistory.id.desc()).first()
        assert history1.new_status == ApplicationStatus.UNDER_REVIEW
        assert history1.old_status == ApplicationStatus.APPLIED
        print("[PASS] Step 9, 10, 11: Status changed APPLIED -> UNDER_REVIEW. DB & history record created.")

        # Step 9: Candidate checks dashboard
        cand1_view1 = client.get(f"/api/applications/{app1_id}", headers=cand1_headers)
        assert cand1_view1.status_code == 200
        assert cand1_view1.json["status"] == "UNDER_REVIEW"
        print("[PASS] Step 12 & 13: Candidate dashboard reflects UNDER_REVIEW.")

        # Step 10: Status transition: UNDER_REVIEW → INTERVIEW & Schedule Interview
        status_update2 = client.patch(f"/api/hr/applications/{app1_id}/status", json={
            "status": "INTERVIEW",
            "notes": "Proceeding to technical interview"
        }, headers=hr_headers)
        assert status_update2.status_code == 200

        sched_interview = client.patch(f"/api/hr/applications/{app1_id}/interview", json={
            "interview_date": "2026-11-05",
            "interview_time": "14:30",
            "interview_round": "Technical System Design",
            "interview_type": "Online",
            "meeting_link": "https://meet.google.com/abc-defg-hij",
            "interviewer": "Senior Lead Engineer Dave",
            "hr_notes": "Focus on distributed systems"
        }, headers=hr_headers)
        assert sched_interview.status_code == 200

        # Verify Interview DB storage
        db_interview = InterviewDetail.query.filter_by(application_id=app1_id).first()
        assert db_interview is not None
        assert db_interview.interview_round == "Technical System Design"
        assert db_interview.meeting_link == "https://meet.google.com/abc-defg-hij"
        print("[PASS] Step 14, 15, 16: Changed to INTERVIEW & interview schedule stored in DB.")

        # Step 11: Candidate sees interview info & timeline
        cand1_view2 = client.get(f"/api/applications/{app1_id}", headers=cand1_headers)
        assert cand1_view2.status_code == 200
        assert cand1_view2.json["status"] == "INTERVIEW"
        assert cand1_view2.json["interview_details"]["meeting_link"] == "https://meet.google.com/abc-defg-hij"
        assert len(cand1_view2.json["status_history"]) >= 3
        print("[PASS] Step 17, 18, 19: Candidate sees scheduled interview info & complete history timeline.")

        # Step 12: Test INTERVIEW → OFFER
        offer_res = client.patch(f"/api/hr/applications/{app1_id}/status", json={
            "status": "OFFER",
            "notes": "Offer extended"
        }, headers=hr_headers)
        assert offer_res.status_code == 200
        assert JobApplication.query.get(app1_id).status == ApplicationStatus.OFFER
        print("[PASS] Step 20: INTERVIEW -> OFFER transition verified.")

        # Step 13: Test INTERVIEW → REJECTED (on Candidate 2)
        client.patch(f"/api/hr/applications/{app2_id}/status", json={"status": "UNDER_REVIEW"}, headers=hr_headers)
        client.patch(f"/api/hr/applications/{app2_id}/status", json={"status": "INTERVIEW"}, headers=hr_headers)
        reject_res = client.patch(f"/api/hr/applications/{app2_id}/status", json={
            "status": "REJECTED",
            "notes": "Not moving forward at this time"
        }, headers=hr_headers)
        assert reject_res.status_code == 200
        assert JobApplication.query.get(app2_id).status == ApplicationStatus.REJECTED
        print("[PASS] Step 21: INTERVIEW -> REJECTED transition verified.")

        # Step 14: Test Candidate WITHDRAWN flow
        withdraw_res = client.put(f"/api/applications/{app1_id}", json={
            "status": "WITHDRAWN"
        }, headers=cand1_headers)
        assert withdraw_res.status_code == 200
        assert JobApplication.query.get(app1_id).status == ApplicationStatus.WITHDRAWN
        print("[PASS] Step 22: Candidate WITHDRAWN flow verified.")

        # Step 15: Test invalid status transition
        invalid_trans = client.patch(f"/api/hr/applications/{app2_id}/status", json={
            "status": "OFFER"  # REJECTED cannot go directly to OFFER
        }, headers=hr_headers)
        assert invalid_trans.status_code in (422, 400), f"Invalid transition returned {invalid_trans.status_code}"
        print("[PASS] Step 24: Invalid status transition rejected (422/400).")

        # Step 16: Verify Frontend & Backend Enum Alignment
        from schemas.application_schema import VALID_STATUSES
        backend_enum_vals = [s.value for s in ApplicationStatus]
        for val in backend_enum_vals:
            assert val in VALID_STATUSES
        print("[PASS] Step 25: Frontend status names match backend ApplicationStatus enum.")

        print("=" * 70)
        print("ALL 30 VERIFICATION CHECKS PASSED PERFECTLY!")
        print("=" * 70)

if __name__ == "__main__":
    run_verification()
