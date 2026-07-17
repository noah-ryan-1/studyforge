import pytest
import tempfile
import os
import json
from unittest.mock import MagicMock, patch
from datetime import datetime
from studyforge.memory.store import MemoryStore
from studyforge.memory.models import (
	UserProfile, Subject, StudySession, EventRating, Summary
)
from studyforge.core.realism import RealismChecker
from studyforge.core.summary import SummaryEngine
from studyforge.llm.router import Provider



@pytest.fixture
def store():
	with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
		path=f.name
	s = MemoryStore(path)
	s.save_profile(UserProfile(
		name="Alex", primary_goal="ML engineer",
		weekly_hours_target=20, commute_minutes=60
	))
	subj_id = s.add_subject(Subject(
		name="Algorithms", status="active",
		current_grade=75.0, target_grade=85.0, 
		weekly_hours_target=10.0, priority=1, year_taken="2026"
	))
	s.log_session(StudySession(
		subject_id=subj_id, hours=2.0, quality=4, 
		notes="Good session", logged_at=datetime.now().isoformat()
	))
	yield s, subj_id
	s.close()
	os.unlink(path)

@patch("studyforge.core.realism.LLMRouter")
def test_realism_checker_parses_valid_json(mock_router_class, store):
	s,_ = store
	mock_router = MagicMock()
	mock_router.chat.return_value = json.dumps({
		"fixed_commitment_hours": 3.0,
		"commute_hours_per_week": 10.0,
		"work_hours_per_week": 1.0,
		"estimated_free_hours": 20.0,
		"stated_target_hours": 20,
		"target_is_realistic": False,
		"reccomended_target_hours": 12,
		"pinch_points": ["Monday is fully blocked"],
		"suggestion": "Study Tuesday and Thursday mornings",
		"summary": "Your target is ambitious given your commute."
	})
	mock_router_class.return_value = mock_router

	checker = RealismChecker(s, provider=Provider.DEEPSEEK)
	result = checker.check()

	assert result["target_is_realistic"] is False
	assert result["reccomended_target_hours"] == 12
	assert len(result["pinch_points"]) == 1

@patch("studyforge.core.realism.LLMRouter")
def test_realism_checker_handles_bad_json(mock_router_class, store):
	s,_ = store
	mock_router = MagicMock()
	mock_router.chat.return_value = "Sorry I can't do that now."
	mock_router_class.return_value = mock_router

	checker = RealismChecker(s, provider=Provider.DEEPSEEK)
	result = checker.check()

	assert "error" in result

@patch("studyforge.core.summary.LLMRouter")
def test_daily_summary_is_saved(mock_router_class, store):
	s,_ = store
	mock_router = MagicMock()
	mock_router.chat.return_value = "Good day today. You studied Well."
	mock_router_class.return_value = mock_router

	engine = SummaryEngine(s, provider=Provider.DEEPSEEK)
	result = engine.generate_daily()

	assert result == "Good day today. You studied Well."
	summaries = s.get_summaries(type="daily")

	assert len(summaries) == 1
	assert summaries[0].type == "daily"

@patch("studyforge.core.summary.LLMRouter")
def test_weekly_summary_is_saved(mock_router_class, store):
	s,_ = store
	mock_router = MagicMock()
	mock_router.chat.return_value = "Solid week overall."
	mock_router_class.return_value = mock_router

	engine = SummaryEngine(s, provider=Provider.DEEPSEEK)
	result = engine.generate_weekly()

	summaries = s.get_summaries(type="weekly")
	assert len(summaries) == 1
	assert summaries[0].period_start is not None

def test_save_and_get_rating(store):
	s,_ = store
	s.add_rating(EventRating(
		event_type="study", event_label="Algorithms session",
		rating=4, mood="focused", notes="Productive"
	))
	ratings = s.get_ratings()
	assert len(ratings) == 1
	assert ratings[0].rating == 4
	assert ratings[0].mood == "focused"

def test_save_and_get_summary(store):
	s,_ = store
	s.save_summary(Summary(
		type="daily", content="Good day.",
		period_start="2026-07-16", period_end="2026-07-16",
	))
	results = s.get_summaries(type="daily")
	assert len(results) == 1
	assert results[0].content == "Good day."
