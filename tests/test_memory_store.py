import pytest
import tempfile
import os
from studyforge.memory.store import MemoryStore
from studyforge.memory.models import (
	UserProfile, Subject, RecurringBlock, WorkVolunteering,
	OneOffEvent, PastExperience, StudySession, ConversationTurn, MemoryFragment
)

@pytest.fixture
def store():
	with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
		db_path = f.name
	s = MemoryStore(db_path)
	yield s 
	s.close()
	os.unlink(db_path)


def test_save_and_get_profile(store):
	profile = UserProfile(name="Alex", primary_goal="ML engineer", weekly_hours_target=20)
	store.save_profile(profile)
	result = store.get_profile()

	assert result.name == "Alex"
	assert result.weekly_hours_target == 20


def test_profile_upsert(store):
	store.save_profile(UserProfile(name="Alex", primary_goal="ML engineer"))
	store.save_profile(UserProfile(name="Alex Updated", primary_goal="Senior ML engineer"))
	result = store.get_profile()

	assert result.name == "Alex Updated"
	assert result.primary_goal == "Senior ML engineer"


def test_add_and_get_subjects(store):
	store.add_subject(Subject(name="Advanced Calculus", priority=2, status="active", year_taken="2026"))
	store.add_subject(Subject(name="Linear Algebra", priority=1, status="active", final_grade=80.1, year_taken="2026"))
	subjects = store.get_subjects()
	
	assert len(subjects) == 2
	assert subjects[0].name == "Linear Algebra" # subjects should be ordered by priority
	assert subjects[1].status == "active"
	assert subjects[1].year_taken == "2026"
	assert subjects[0].final_grade == 80.1 


def test_recurring_block(store):
	store.add_recurring_block(RecurringBlock(name="Linear Algebra Lecture", type="lecture", day_of_week="Monday",
		start_time="10:00", end_time="11:00"))
	recurring_blocks = store.get_recurring_blocks()

	assert len(recurring_blocks) == 1
	assert recurring_blocks[0].name == "Linear Algebra Lecture"


def test_work_volunteering(store):
	store.add_work_volunteering(WorkVolunteering(name="Math Tutoring", type="job"))
	work_volunteering = store.get_work_volunteering()
	
	assert len(work_volunteering) == 1
	assert work_volunteering[0].type == "job" 


def test_one_off_event(store):
	store.add_one_off_event(OneOffEvent(name="Linear Algebra Exam", type="exam", date="2026/08/14"))
	one_off_event = store.get_one_off_events()
	
	assert len(one_off_event) == 1
	assert one_off_event[0].date == "2026/08/14"


def test_past_experience(store):
	store.add_past_experience(PastExperience(category="job", name="Retail Assistant Coles"))
	past_experience = store.get_past_experience()

	assert len(past_experience) == 1
	assert past_experience[0].name == "Retail Assistant Coles"

def test_add_and_get_fragment(store):
	store.add_fragment(MemoryFragment(category="social", content="Enjoys hiking on the weekends", source="daily chat"))
	store.add_fragment(MemoryFragment(category="constraint", content="Cannot focus after 9pm"))
	all_fragments = store.get_fragments()

	assert len(all_fragments) == 2
	assert all_fragments[0].category == "social"
	assert all_fragments[1].source == "consultation" # default
	assert all_fragments[0].source == "daily chat" # checks that source is saved

def test_log_and_retrieve_session(store):
	subj_id = store.add_subject(Subject(name="PyTorch", priority=1, status="past", year_taken="2025"))
	store.log_session(StudySession(subject_id=subj_id, hours=2.5, quality=4))
	sessions = store.get_sessions()
	
	assert len(sessions) == 1
	assert sessions[0].hours == 2.5

def test_conversation_turns_order(store):
	store.add_turn(ConversationTurn(role="user", content="Hello :)"))
	store.add_turn(ConversationTurn(role="assistant", content="Hello There! :)"))
	turns = store.get_recent_turns()

	assert turns[0].role == "user" # original DESC to return latest items but then flipped to read naturally
	assert turns[1].role == "assistant" 

def test_empty_db_returns_none_profile(store):
	assert store.get_profile() is None

def test_get_context_includes_profile(store):
	store.save_profile(UserProfile(
		name="Alex", primary_goal="ML engineer",
		weekly_hours_target=20, commute_minutes=40
	))
	ctx = store.get_context_for_llm()

	assert "Alex" in ctx
	assert "ML engineer" in ctx
	assert "commute" in ctx.lower()

def test_get_context_includes_fragments(store):
	store.add_fragment(MemoryFragment(
		category="social", content="Enjoys hiking on weekends"
	))
	ctx = store.get_context_for_llm()

	assert "hiking" in ctx
	assert "[social]" in ctx
