import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from studyforge.cli import app
from studyforge.memory.store import MemoryStore
from studyforge.memory.models import UserProfile, Subject

runner = CliRunner()

@pytest.fixture
def tmp_db(tmp_path):
	db = str(tmp_path / "test.db")
	store = MemoryStore(db)
	store.save_profile(UserProfile(
		name="Alex", primary_goal="ML engineer",
		weekly_hours_target=20, commute_minutes=60,
		commute_days_per_week=5,
	))
	store.add_subject(Subject(
		name="Psychology", status="active",
		current_grade=58.0, target_grade=80.0,
		priority=1, year_taken="2026", weekly_hours_target=6.0,
	))
	store.close()
	return db

@patch("studyforge.cli.DB_PATH")
@patch("studyforge.cli.get_store")
def test_status_command(mock_get_store, mock_db_path, tmp_db):
	store = MemoryStore(tmp_db)
	mock_get_store.return_value = store

	result = runner.invoke(app, ["status"])
	print(result.output)
	print(result.exception)
	assert result.exit_code == 0
	assert "Alex" in result.output
	assert "Psychology" in result.output
	store.close()

@patch("studyforge.cli.get_store")
def test_log_matches_subject(mock_get_store, tmp_db):
	store = MemoryStore(tmp_db)
	mock_get_store.return_value = store

	result = runner.invoke(app, [
		"log", "psych", "--hours", "2.0", "--quality", "4"
	])

	assert result.exit_code == 0
	assert "Psychology" in result.output
	
	# repoen database after CLI closed it
	store = MemoryStore(tmp_db)
	sessions = store.get_sessions()
	assert len(sessions) == 1
	assert sessions[0].hours == 2
	store.close()

@patch("studyforge.cli.get_store")
def test_log_unknown_subject(mock_get_store, tmp_db):
	store = MemoryStore(tmp_db)
	mock_get_store.return_value = store

	result = runner.invoke(app, [
		"log", "physics", "--hours", "1.0", "--quality", "3"
	])

	assert result.exit_code == 1
	assert "No subject matching" in result.output
	store.close()

@patch("studyforge.cli.get_store")
def test_rate_command(mock_get_store, tmp_db):
	store = MemoryStore(tmp_db)
	mock_get_store.return_value = store

	result = runner.invoke(app, [
		"rate", "Pyschology Study Session",
		"--score", "4", "--mood", "focused"
	])

	assert result.exit_code == 0
	assert "Pyschology Study Session" in result.output
	
	# repoeon after CLI closed it 
	store = MemoryStore(tmp_db)
	ratings = store.get_ratings()
	assert len(ratings) == 1
	assert ratings[0].rating == 4
	assert ratings[0].mood == "focused"
	store.close()

@patch("studyforge.cli.get_store")
def test_no_profile_exists_with_message(mock_get_store, tmp_path):
	empty_store = MemoryStore(str(tmp_path / "empty.db"))
	mock_get_store.return_value = empty_store

	result = runner.invoke(app, ["status"])

	assert result.exit_code == 1
	assert "studyforge onboard" in result.output
	empty_store.close()

@patch("studyforge.core.summary.LLMRouter")
@patch("studyforge.cli.get_store")
def test_daily_command(mock_get_store, mock_router_class, tmp_db):
	store = MemoryStore(tmp_db)
	mock_get_store.return_value = store
	mock_router = MagicMock()
	mock_router.chat.return_value = "Good day, Alex!"
	mock_router_class.return_value = mock_router

	result = runner.invoke(app, ["daily", "--provider", "deepseek"])

	assert result.exit_code == 0
	assert "Good day" in result.output
	store.close()
