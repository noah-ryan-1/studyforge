import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from studyforge.integrations.calendar_client import CalendarClient, CalendarEvent
from studyforge.integrations.calendar_sync import CalendarSync, _classify_type
from studyforge.memory.store import MemoryStore
from studyforge.memory.models import UserProfile


@pytest.fixture
def store():
	with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
		path = f.name
	s = MemoryStore(path)
	s.save_profile(UserProfile(
		name="Jake", primary_goal="clinical Psychologist",
		weekly_hours_target=20, commute_minutes=60,
		commute_days_per_week=5,
	))
	yield s 
	s.close()
	os.unlink(path)

def make_event(title, start_str, end_str, recurring=False):
	start = datetime.fromisoformat(start_str).replace(tzinfo=timezone.utc)
	end = datetime.fromisoformat(end_str).replace(tzinfo=timezone.utc)
	return CalendarEvent(
		id=f"evt_{title[:4]}",
		title=title,
		start=start,
		end=end,
		is_recurring=recurring,
	)

def test_classify_type_lecture():
	assert _classify_type("Anatomy Lecture", {"lecture": ["lecture"]}) == "lecture"

def test_classify_type_exam():
	from studyforge.integrations.calendar_sync import ONE_OFF_TYPES
	assert _classify_type("Psychology Final Exam", ONE_OFF_TYPES) == "exam"

def classify_type_unknown():
	assert _classify_type("Coffee with Alex", {"exam": ["exam"]}) == "other"


@patch("studyforge.integrations.calendar_client.build")
@patch("studyforge.integrations.calendar_client.InstalledAppFlow")
@patch("studyforge.integrations.calendar_client.TOKEN_PATH")
@patch("studyforge.integrations.calendar_client.CREDS_PATH")
def test_sync_recurring_creates_block(mock_creds, mock_token, mock_flow, mock_build, store):
	mock_token.exists.return_value = False
	mock_creds.exists.return_value = True
	mock_creds_obj = MagicMock()
	mock_flow.from_client_secrets_file.return_value.run_local_server.return_value = mock_creds_obj
	mock_creds_obj.to_json.return_value = "{}"
	mock_token.write_text = MagicMock()

	mock_service = MagicMock()
	mock_build.return_value = mock_service
	mock_service.events.return_value.list.return_value.execute.return_value = {"items": []}

	syncer = CalendarSync(store)
	event = make_event(
		"Anatomy Lecture", "2026-07-25T10:00:00",
		"2026-07-25T11:00:00", recurring=True
	)
	syncer._sync_recurring(event)
	blocks = store.get_recurring_blocks()

	assert len(blocks) == 1
	assert blocks[0].name == "Anatomy Lecture"
	assert blocks[0].day_of_week == "Saturday"


@patch("studyforge.integrations.calendar_client.build")
@patch("studyforge.integrations.calendar_client.InstalledAppFlow")
@patch("studyforge.integrations.calendar_client.TOKEN_PATH")
@patch("studyforge.integrations.calendar_client.CREDS_PATH")
def test_sync_one_off_creates_event(mock_creds, mock_token, mock_flow, mock_build, store):
	mock_token.exists.return_value = False
	mock_creds.exists.return_value = True
	mock_flow.from_client_secrets_file.return_value.run_local_server.return_value = MagicMock(to_json=lambda: "{}")
	mock_token.write_text = MagicMock()
	mock_build.return_value = MagicMock()
	mock_build.return_value.events.return_value.list.return_value.execute.return_value = {"items": []}

	syncer = CalendarSync(store)
	event = make_event(
		"Royal Childrens Hospital Interview", "2026-08-15T13:00:00",
		"2026-08-15T14:00:00", recurring=False
	)
	syncer._sync_one_off(event)
	events = store.get_one_off_events()

	assert len(events) == 1
	assert events[0].name == "Royal Childrens Hospital Interview"
	assert events[0].type == "appointment"
