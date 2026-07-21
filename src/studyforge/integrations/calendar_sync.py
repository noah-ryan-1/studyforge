from studyforge.integrations.calendar_client import CalendarClient, CalendarEvent
from studyforge.memory.store import MemoryStore
from studyforge.memory.models import RecurringBlock, OneOffEvent

RECURRING_KEYWORDS = {
	"lecture": ["lecture", "lec", "class", "tutorial", "tut", "lab", "workshop"],
	"job": ["work", "shift", "job", "tutoring", "volunteering", "volunteer"],
}

ONE_OFF_TYPES = {
	"exam": ["exam", "test", "midsem", "final", "midterm"],
	"assignment_due": ["assignment", "due", "submit", "submission", "deadline"],
	"appointment": ["appointment", "interview", "meeting", "consult"],
}



def _classify_type(title: str, mapping: dict) -> str:
	lower = title.lower()
	for type_name, keywords in mapping.items():
		if any(k in lower for k in keywords):
			return type_name
	return "other"


class CalendarSync:
	def __init__(self, store: MemoryStore):
		self.store = store
		self.client = CalendarClient()

	def sync_week(self) -> dict[str, int]:
		"""Pull this week's calendar events and store them.
		Returns counts of what was synced."""
		events = self.client.get_events_this_week()
		counts = {"recurring": 0, "one_off": 0, "skipped": 0}

		for event in events:
			if event.is_recurring:
				self._sync_recurring(event)
				counts["recurring"] += 1
			else:
				self._sync_one_off(event)
				counts["one_off"] += 1
		return counts

	def sync_upcoming(self, days: int = 30) -> dict[str, int]:
		"""Pull upcoming one-off events (exams, assignments, interviews, etc.)"""
		events = self.client.get_upcoming_events(days=days)
		counts = {"one_off": 0, "skipped": 0}

		for event in events:
			if not event.is_recurring:
				self._sync_one_off(event)
				counts["one_off"] += 1

		return counts

	def _sync_recurring(self, event: CalendarEvent):
		block_type = _classify_type(event.title, RECURRING_KEYWORDS)
		self.store.add_recurring_block(RecurringBlock(
			name=event.title,
			type=block_type if block_type in ("lecture", "tutorial", "lab") else "other",
			day_of_week=event.start.strftime("%A"),
			start_time=event.start.strftime("%H:%M"),
			end_time=event.end.strftime("%H:%M"),
			location="",
		))

	def _sync_one_off(self, event: CalendarEvent):
		event_type = _classify_type(event.title, ONE_OFF_TYPES)
		self.store.add_one_off_event(OneOffEvent(
			name=event.title,
			type=event_type,
			date=event.start.strftime("%Y-%m-%d"),
			start_time=event.start.strftime("%H:%M"),
			end_time=event.end.strftime("%H:%M")
		)) 
	
