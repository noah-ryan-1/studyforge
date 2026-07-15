import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from studyforge.memory.store import MemoryStore
from studyforge.memory.models import UserProfile
from studyforge.core.consultation import SaveRouter, ConsultationEngine
from studyforge.core.chat_loop import ChatLoop


@pytest.fixture
def store():
	with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
		path = f.name
	s = MemoryStore(path)
	yield s
	s.close()
	os.unlink(path)


def test_save_router_parses_profile(store):
	router = SaveRouter(store)
	response = """
	Great let me save your profile.
	<save>
	{"table": "user_profile", "data": {
		"name": "Alex",
		"primary_goal": "ML engineer",
		"weekly_hours_target": 20,
		"commute_minutes": 60
	}}
	</save>
	"""
	saved = router.process(response)
	assert len(saved) == 1
	assert "Alex" in saved[0]
	profile = store.get_profile()
	assert profile is not None
	assert profile.name == "Alex"

def test_save_router_parses_subject(store):
	router = SaveRouter(store)
	response = """
	<save>
	{"table": "subjects", "data": {
		"name":"Econometrics", "status":"active",
		"current_grade": 58.0, "target_grade":80.0,
		"priority":3, "year_taken":"2026"
	}}
	</save>
	"""
	router.process(response)
	subjects = store.get_subjects()

	assert len(subjects) == 1
	assert subjects[0].name == "Econometrics"

def test_save_router_handles_multiple_blocks(store):
	router = SaveRouter(store)
	response = """
	<save>{"table": "memory_fragments", "data":
		{"category": "social", "content": "Enjoys hiking"}}</save>
	<save>{"table": "memory_fragments", "data":
		{"category": "constraint", "content": "Can't focus after 9pm"}}</save>
	"""
	saved = router.process(response)
	
	assert len(saved) == 2
	assert len(store.get_fragments()) == 2

def test_save_router_detects_completion(store):
	router = SaveRouter(store)
	
	assert not router.is_complete("Still chatting...")
	assert router.is_complete("All done! <consultation_complete/>")

def test_save_router_cleans_response(store):
	router = SaveRouter(store)
	raw = 'Here is some text. <save>{"table":"memory_fragments":, "data":{"category":"social", "content":"test"}}</save>More text.'
	cleaned = router.clean_response(raw)

	assert "<save>" not in cleaned
	assert "Here is some text." in cleaned
	assert "More text." in cleaned

def test_save_router_handles_bad_json_gracefully(store):
	router = SaveRouter(store)
	response = "this is not json"
	saved = router.process(response)

	assert saved == []

@patch("studyforge.core.consultation.LLMRouter")
def test_consultation_engine_start(mock_router_class, store):
	mock_router = MagicMock()
	mock_router.chat.return_value = (
		"Hi! I'm StudyForge. What's your name and primary goal?\n"
		'<save>{"table": "user_profile", "data": {'
		'"name": "Test", "primary_goal": "ML_engineer", '
		'"weekly_hours_target": 20, "commute_minutes": 0}}</save>'
	)
	mock_router_class.return_value = mock_router

	engine = ConsultationEngine(store)
	response = engine.start()

	assert mock_router.chat.called
	assert "<save>" not in response
	assert store.get_profile() is not None
	assert store.get_profile().name == "Test"

@patch("studyforge.core.consultation.LLMRouter")
def test_consultation_engine_detecs_completion(mock_router_class, store):
	mock_router = MagicMock()
	mock_router.chat.return_value = (
		"I have everything I need. <consultation_complete/>"
	)
	mock_router_class.return_value = mock_router

	engine = ConsultationEngine(store)
	engine.start()

	assert engine.is_complete

@patch("studyforge.core.chat_loop.LLMRouter")
def test_chat_loop_saves_remember_fragment(mock_router_class, store):
	mock_router = MagicMock()
	mock_router.chat.return_value = (
		"Got it, I'll keep that in mind.\n"
		'<remember>{"category": "constraint", '
		'"content": "Cannot focus after 9pm"}</remember>'
	)
	mock_router_class.return_value = mock_router

	store.save_profile(UserProfile(
		name="Alex", primary_goal="ML engineer",
		weekly_hours_target=20, commute_minutes=60
	))

	loop = ChatLoop(store)
	response = loop.send("I can't focus after 9pm")

	assert "<remember>" not in response
	fragments = store.get_fragments(category="constraint")
	assert len(fragments) == 1
	assert "9pm" in fragments[0].content

@patch("studyforge.core.chat_loop.LLMRouter")
def test_chat_loop_saves_conversation_turns(mock_router_class, store):
	mock_router = MagicMock()
	mock_router.chat.return_value = "Sure here's what I suggest."
	mock_router_class.return_value = mock_router


	store.save_profile(UserProfile(
		name="Alex", primary_goal="ML engineer",
		weekly_hours_target=20, commute_minutes=60
	))

	loop = ChatLoop(store)
	loop.send("When should I study Linear Algebra?")

	turns = store.get_recent_turns()

	assert len(turns) == 2
	assert turns[0].role == "user"
	assert turns[1].role == "assistant" 
