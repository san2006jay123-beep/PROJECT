"""
ClassOS Database Cleaner & Reset Script
- Deletes all fake / un-enrolled students.
- Preserves genuine students with enrolled face embeddings (e.g., SANJAY).
- Ensures exactly ONE classroom (CSE-101) exists.
- Resets attendance sessions and initializes active session where students start ABSENT (awaiting camera).
- Resets smart appliances to OFF (0W Eco).
"""

import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'classos', 'backend')))

from app.core.database import SessionLocal
from app.models.student import Student, FaceEmbedding
from app.models.institutional import Teacher, Classroom, Course, ClassSession, Device
from app.models.appliances import ClassroomAppliance, ApplianceStatus, AutomationMode
from app.models.attendance import (
    AttendanceSession,
    AttendanceRecord,
    AttendanceSessionStatus,
    AttendanceClassification,
)
from app.models.student_activity import StudentActivityLog, ActivityType
from app.models.audit_log import AuditLog

db = SessionLocal()

print("=== STEP 1: REMOVING FAKE STUDENTS ===")
for s in db.query(Student).all():
    embed_count = db.query(FaceEmbedding).filter(FaceEmbedding.student_id == s.id).count()
    if embed_count > 0:
        print(f"  [KEEP] Enrolled Student: ID={s.id}, Name={s.name}, Roll={s.roll_number}, Embeddings={embed_count}")
    else:
        print(f"  [DELETE] Fake Student: ID={s.id}, Name={s.name}, Roll={s.roll_number}")
        db.query(AttendanceRecord).filter(AttendanceRecord.student_id == s.id).delete()
        db.query(StudentActivityLog).filter(StudentActivityLog.student_id == s.id).delete()
        db.delete(s)

db.commit()

print("\n=== STEP 2: ENSURING ONLY ONE CLASSROOM (CSE-101) ===")
classrooms = db.query(Classroom).all()
c1 = None
for c in classrooms:
    if c.name == "CSE-101":
        c1 = c
    else:
        print(f"  [DELETE] Extra classroom: {c.name}")
        db.query(ClassSession).filter(ClassSession.classroom_id == c.id).delete()
        db.query(ClassroomAppliance).filter(ClassroomAppliance.classroom_id == c.id).delete()
        db.query(Device).filter(Device.classroom_id == c.id).delete()
        db.delete(c)

if not c1:
    c1 = Classroom(name="CSE-101", building="Turing Block", capacity=60, device_id="LAPTOP-DEV-001")
    db.add(c1)
    db.commit()

print(f"  [ACTIVE CLASSROOM] ID={c1.id}, Name={c1.name}, Building={c1.building}")

print("\n=== STEP 3: ENSURING ONE COURSE & CLASS SESSION ===")
courses = db.query(Course).all()
course1 = None
for cr in courses:
    if cr.code == "CS301":
        course1 = cr
    else:
        print(f"  [DELETE] Extra course: {cr.code}")
        db.query(ClassSession).filter(ClassSession.course_id == cr.id).delete()
        db.delete(cr)

t1 = db.query(Teacher).first()
if not course1:
    course1 = Course(
        code="CS301",
        title="Smart Classroom Systems & Architecture",
        department="Computer Science",
        teacher_id=t1.id if t1 else None,
    )
    db.add(course1)
    db.commit()

db.query(ClassSession).delete()
today_str = datetime.now().strftime("%Y-%m-%d")
cs1 = ClassSession(
    course_id=course1.id,
    classroom_id=c1.id,
    teacher_id=t1.id if t1 else 1,
    session_date=today_str,
    start_time="09:00 AM",
    end_time="10:00 AM",
    status="ACTIVE",
)
db.add(cs1)
db.commit()

print("\n=== STEP 4: RESET APPLIANCES & ATTENDANCE SESSIONS ===")
db.query(AttendanceRecord).delete()
db.query(StudentActivityLog).delete()
db.query(AttendanceSession).delete()
db.commit()

appliance = db.query(ClassroomAppliance).filter(ClassroomAppliance.classroom_id == c1.id).first()
if not appliance:
    appliance = ClassroomAppliance(
        classroom_id=c1.id,
        light_status=ApplianceStatus.OFF,
        fan_status=ApplianceStatus.OFF,
        control_mode=AutomationMode.AUTO_AI,
        occupancy_count=0,
        active_power_watts=0.0,
        energy_saved_kwh=3.20,
    )
    db.add(appliance)
else:
    appliance.light_status = ApplianceStatus.OFF
    appliance.fan_status = ApplianceStatus.OFF
    appliance.occupancy_count = 0
    appliance.active_power_watts = 0.0
    db.add(appliance)

now_utc = datetime.now(timezone.utc)
new_att = AttendanceSession(
    class_session_id=cs1.id,
    session_code=f"session_{now_utc.strftime('%Y%m%d_%H%M%S')}",
    started_at=now_utc,
    started_by=1,
    status=AttendanceSessionStatus.ACTIVE,
    total_frames=1,
    capture_duration_seconds=3.0,
)
db.add(new_att)
db.commit()

active_students = db.query(Student).all()
for s in active_students:
    rec = AttendanceRecord(
        attendance_session_id=new_att.id,
        student_id=s.id,
        ai_status=AttendanceClassification.ABSENT_CANDIDATE,
        final_status=AttendanceClassification.ABSENT,
        confidence=0.0,
        frames_detected=0,
        total_frames=1,
        teacher_override=False,
        current_activity=ActivityType.ATTENTIVE,
        activity_confidence=0.95,
        activity_notes="Awaiting camera verification",
    )
    db.add(rec)

summary_payload = {
    "total_students": len(active_students),
    "present_count": 0,
    "review_count": 0,
    "absent_count": len(active_students),
    "unknown_detections": 0,
    "total_faces_detected": 0,
    "avg_faces_per_frame": 0.0,
}
new_att.summary_stats = json.dumps(summary_payload)
db.add(new_att)
db.commit()

print(f"\n=======================================================")
print(f"DATABASE RESET COMPLETE & CLEANED SUCCESSFULLY")
print(f"Classrooms Count : {db.query(Classroom).count()} ({c1.name})")
print(f"Courses Count    : {db.query(Course).count()} ({course1.code} - {course1.title})")
print(f"Active Students  : {db.query(Student).count()} enrolled students")
for s in db.query(Student).all():
    print(f"   • Roll {s.roll_number} - {s.name} ({s.department})")
print(f"Active Session ID: {new_att.id} ({new_att.session_code})")
print(f"=======================================================")
db.close()
