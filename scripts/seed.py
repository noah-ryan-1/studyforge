import os
from studyforge.memory.store import MemoryStore
from studyforge.memory.models import (
	UserProfile, Subject, RecurringBlock, WorkVolunteering, OneOffEvent, 
	PastExperience, MemoryFragment, StudySession, ConversationTurn 
)

# wipe the dev database before seeding
DB_PATH = "dev.db"
if os.path.exists(DB_PATH):
	os.remove(DB_PATH)

store = MemoryStore("dev.db")

store.save_profile(UserProfile(
	name="Alex",
	primary_goal="Become an ML Engineer focused on research and applied AI",
	weekly_hours_target=20, 
	commute_minutes=120, 
))

econ_id = store.add_subject(Subject(
	name="Econometrics",
	current_grade=58, 
	target_grade=80,
	priority=3,
	year_taken="2026",
	status="active",
))

store.add_subject(Subject(
	name="Stochastic Models",
	current_grade=70, 
	target_grade=80,
	priority=2,
	year_taken="2026",
	status="active",
))

store.add_subject(Subject(
	name="Algorithms and Data Structures",
	current_grade=75,
	target_grade=85,
	priority=1,
	year_taken="2026",
	status="active",
))

store.add_recurring_block(RecurringBlock(
	name="COMP20007 Lecture",
	type="lecture",
	day_of_week="Monday",
	start_time="10:00",
	end_time="11:00",
	location="Peter Hall Building",
))

store.add_work_volunteering(WorkVolunteering(
	name="English Language Tutoring",
	type="job",
	day_of_week="Monday",
	start_time="11:00",
	end_time="12:00",
	hours_per_week=1.0,
))

store.add_one_off_event(OneOffEvent(
	name="Schneider Electric Job Interview",
	type="other",
	date="2026/08/14",
	start_time="13:00",
	end_time="14:00",
))

store.add_past_experience(PastExperience(
	category="subject",
	name="Design of Algorithms",
	description="Very similar to current course Algorithms and Data Structures",
	grade=48,
	year=2026,
	relevance="Relevant to Machine Learning through understanding of algorithms",
))

store.log_session(StudySession(
	subject_id=econ_id, hours=2.0, quality=4,
	notes="Finished chapter on Linear Regression"
))

store.add_fragment(MemoryFragment(
	category='health',
	content="Love to go for a hike every second week and to incoporate physical activity into every week to ensure that I have a means of destressing and focusing on something else.",
))

# -- Verify -- 

print("Profile:", store.get_profile())
print("Subjects:", store.get_subjects())
print("Recurring Blocks:", store.get_recurring_blocks())
print("Work/Volunteering:", store.get_work_volunteering())
print("One Off Events:", store.get_one_off_events())
print("Past Experience:", store.get_past_experience())
print("Study Session:", store.get_sessions())

store.close() 


