import sys
sys.path.insert(0, 'backend')
import uuid
from app.db.session import SessionLocal
from app.db.models import User, Report, VerificationJob
from app.db.repositories.report_repository import ReportRepository
from app.security.authentication import TokenData, get_password_hash
from app.api.history import get_verification_history
from app.api.reports import get_report_endpoint, assert_report_access
from fastapi import HTTPException

db = SessionLocal()
try:
    repo = ReportRepository(db)

    # 1. Create two isolated test users
    uid_a = str(uuid.uuid4())
    uid_b = str(uuid.uuid4())

    user_a = User(id=uid_a, email=f"test_iso_a_{uid_a[:6]}@example.com", username=f"user_a_{uid_a[:6]}", hashed_password=get_password_hash("pass123"), role="user")
    user_b = User(id=uid_b, email=f"test_iso_b_{uid_b[:6]}@example.com", username=f"user_b_{uid_b[:6]}", hashed_password=get_password_hash("pass123"), role="user")
    db.add(user_a)
    db.add(user_b)
    db.commit()

    # 2. Create reports for User A and User B
    job_a = VerificationJob(id=str(uuid.uuid4()), job_type="claim", status="completed", user_id=uid_a)
    job_b = VerificationJob(id=str(uuid.uuid4()), job_type="claim", status="completed", user_id=uid_b)
    db.add(job_a)
    db.add(job_b)
    db.commit()

    report_a = repo.create_report(
        job_id=job_a.id,
        user_id=uid_a,
        title="User A Secret Analysis",
        input_type="claim",
        overall_verdict="SUPPORTED",
        verdict_label="Accuracy Level of Real: 95.0%",
        confidence_score=95.0,
        confidence_level="HIGH",
        summary="User A data",
        explanation="Confidential User A dossier",
        limitations=[],
        checks_performed=[],
        checks_unavailable=[]
    )

    report_b = repo.create_report(
        job_id=job_b.id,
        user_id=uid_b,
        title="User B Secret Analysis",
        input_type="claim",
        overall_verdict="CONTRADICTED",
        verdict_label="Accuracy Level of Real: 5.0%",
        confidence_score=90.0,
        confidence_level="HIGH",
        summary="User B data",
        explanation="Confidential User B dossier",
        limitations=[],
        checks_performed=[],
        checks_unavailable=[]
    )

    # 3. Verify Repository level isolation
    reports_for_a = repo.list_reports(user_id=uid_a)
    reports_for_b = repo.list_reports(user_id=uid_b)

    ids_a = [r.id for r in reports_for_a]
    ids_b = [r.id for r in reports_for_b]

    assert report_a.id in ids_a, "Report A should be visible to User A"
    assert report_b.id not in ids_a, "SECURITY VIOLATION: Report B leaked to User A!"

    assert report_b.id in ids_b, "Report B should be visible to User B"
    assert report_a.id not in ids_b, "SECURITY VIOLATION: Report A leaked to User B!"

    # 4. Verify Route level security and 403 Forbidden check
    token_a = TokenData(username=user_a.email, role="user", uid=user_a.id)
    token_b = TokenData(username=user_b.email, role="user", uid=user_b.id)

    # User A accessing Report A should succeed
    assert_report_access(report_a, token_a, db)

    # User A accessing Report B MUST raise 403 Forbidden
    forbidden = False
    try:
        assert_report_access(report_b, token_a, db)
    except HTTPException as e:
        if e.status_code == 403:
            forbidden = True
    assert forbidden, "SECURITY VIOLATION: User A was able to access User B's report!"

    print("\n>>> ALL USER DATA ISOLATION AND AUTHORIZATION CHECKS PASSED PERFECTLY! <<<")

finally:
    db.close()
