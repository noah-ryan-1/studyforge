from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserProfile:
	name: str = ""
	primary_goal: str = ""
	weekly_hours_target: int = 20
	commute_minutes: int = 0
	commute_days_per_week: int = 5
	id: int = 1


@dataclass
class Subject:
	name: str
	status: str
	year_taken: str
	current_grade: float | None = None
	target_grade: float | None = None
	final_grade: float | None = None
	priority: int = 1 
	weekly_hours_target: float | None = None
	notes: str = ""
	id: int | None = None


@dataclass
class RecurringBlock:
	name: str
	type: str
	day_of_week: str
	start_time: str
	end_time: str
	location: str = ""
	notes: str = ""
	id: int | None = None 


@dataclass
class WorkVolunteering:
	name: str
	type: str
	day_of_week: str | None = None
	start_time: str | None = None
	end_time: str | None = None
	is_recurring: bool = True
	hours_per_week: float | None = None
	notes: str = ""
	id: int | None = None


@dataclass
class OneOffEvent:
	name: str
	type: str
	date: str
	start_time: str | None = None
	end_time: str | None = None
	notes: str = ""
	id: int | None = None


@dataclass
class PastExperience:
	category: str
	name: str 
	description: str = ""
	grade: float | None = None
	year: str | None = None
	relevance: str = ""
	id: int | None = None


@dataclass
class MemoryFragment:
	category: str
	content: str
	source: str = "consultation"
	id: int | None = None


@dataclass
class StudySession:
	subject_id: int
	hours: float
	quality: int
	notes: str = ""
	logged_at: str = field(default_factory=lambda: datetime.now().isoformat())
	id: int | None = None


@dataclass
class ConversationTurn:
	role: str
	content: str
	context_tag: str = "general"
	id: int | None = None


@dataclass
class Summary:
	type: str
	content: str
	period_start: str
	period_end: str
	id: int | None = None
	created_at: str | None = None


@dataclass
class EventRating:
	event_type: str
	event_label: str
	rating: int
	mood: str = ""
	notes: str = ""
	id: int | None = None
