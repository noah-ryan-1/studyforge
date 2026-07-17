import os
from datetime import datetime
from studyforge.memory.store import MemoryStore
from studyforge.memory.models import (
	UserProfile, Subject, RecurringBlock, WorkVolunteering,
	StudySession, EventRating
)
from studyforge.core.realism import RealismChecker
from studyforge.core.summary import SummaryEngine
from studyforge.llm.router import Provider


DB = "realism_and_summ.db"
if os.path.exists(DB):
	os.remove(DB)


store = MemoryStore(DB)


store.save_profile(UserProfile(
	name="Alex",
	primary_goal="become an ML engineer focused on research",
	weekly_hours_target=20,
	commute_minutes=60,
))
algo_id = store.add_subject(Subject(
	name="Econometrics", status="active",
	current_grade=58.0, target_grade=80.0,
	priority=3, year_taken="2026", weekly_hours_target=7.0
))
store.add_recurring_block(RecurringBlock(
	name="Econometrics Lecture", type="lecture",
	day_of_week="Monday", start_time="10:00", end_time="11:00"
))
store.add_work_volunteering(WorkVolunteering(
	name="ESL Tutoring", type="job", day_of_week="Monday",
	start_time="11:00", end_time="12:00", hours_per_week=1.0
))
store.log_session(StudySession(
	subject_id=algo_id, hours=1.5, quality=3, notes="Struggled with heteroskedasticity section",
	logged_at=datetime.now().isoformat()
))
store.add_rating(EventRating(
	event_type="study", event_label="econometrics session", rating=4, mood="focused",
	notes="Good session felt productive"
))

print("=== Running realism check ===")
checker = RealismChecker(store, provider=Provider.DEEPSEEK)
result = checker.check()
checker.print_report(result)

print("\n=== Generating daily summary ===")
engine = SummaryEngine(store, provider=Provider.DEEPSEEK)
daily = engine.generate_daily()
print(daily)

print("\n=== Generating weekly summary ===")
weekly = engine.generate_weekly()
print(weekly)

print("\n=== Saved summaries ===")
for s in store.get_summaries():
	print(f" [{s.type}] {s.period_start}: {s.content[:80]}...")

store.close() 
