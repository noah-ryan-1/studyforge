import sqlite3
from pathlib import Path
from studyforge.memory.models import (
	UserProfile, Subject, StudySession, ConversationTurn, MemoryFragment,
	PastExperience, OneOffEvent, WorkVolunteering, RecurringBlock
)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"



class MemoryStore:
	def __init__(self, db_path: str = "studyforge.db"):
		self.db_path = db_path
		self.conn = sqlite3.connect(db_path)
		self.conn.row_factory = sqlite3.Row
		self.apply_schema()

	def apply_schema(self):
		schema = SCHEMA_PATH.read_text()
		self.conn.executescript(schema)
		self.conn.commit()
	
	def close(self):
		self.conn.close()


	# -- User Profile --
	def save_profile(self, profile: UserProfile):
		existing = self.get_profile()
		if existing is None:
			self.conn.execute("""
				INSERT INTO user_profile (id, name, primary_goal, weekly_hours_target, commute_minutes)
				VALUES (1, ?, ?, ?, ?)
				ON CONFLICT(id) DO UPDATE SET
					name=excluded.name,
					primary_goal=excluded.primary_goal,
					weekly_hours_target=excluded.weekly_hours_target,
					commute_minutes=excluded.commute_minutes,
					updated_at=datetime('now')
			""", (profile.name, profile.primary_goal, profile.weekly_hours_target, profile.commute_minutes))
		else:
			# only update fields that were actually provided
			updated_name = profile.name or existing.name
			updated_goal = profile.primary_goal or existing.primary_goal
			updated_hours = profile.weekly_hours_target or existing.weekly_hours_target
			updated_commute = profile.commute_minutes if profile.commute_minutes != 0 else existing.commute_minutes
			self.conn.execute("""
				UPDATE user_profile SET
					name = ?,
					primary_goal = ?,
					weekly_hours_target = ?,
					commute_minutes = ?,
					updated_at = datetime('now')
				WHERE id = 1
			""", (updated_name, updated_goal, updated_hours, updated_commute))
		self.conn.commit()
	
	def get_profile(self) -> UserProfile | None:
		row = self.conn.execute("SELECT * FROM user_profile WHERE id=1").fetchone()
		if not row:
			return None
		return UserProfile(
			id=row["id"], name=row["name"], primary_goal=row["primary_goal"],
			weekly_hours_target=row["weekly_hours_target"], 
			commute_minutes=row["commute_minutes"]
		)
	
	
	# -- Subjects --
	def add_subject(self, subject: Subject) -> int:
		cur = self.conn.execute("""
			INSERT INTO subjects ( name, current_grade, target_grade, final_grade, priority, notes,
				status, year_taken)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)
		""", (subject.name, subject.current_grade, subject.target_grade, subject.final_grade, subject.priority,
			 subject.notes ,subject.status, subject.year_taken))
		self.conn.commit()
		return cur.lastrowid

	def get_subjects(self) -> list[Subject]:
		rows = self.conn.execute("SELECT * FROM subjects ORDER BY priority").fetchall()
		return [Subject(id=r["id"], name=r["name"], current_grade=r['current_grade'], 
			target_grade=r['target_grade'], final_grade=r['final_grade'],  priority=r['priority'], 
			notes=r['notes'], status=r['status'], year_taken=r['year_taken']) for r in rows]


	# -- recurring blocks (lectures, tutorials, labs) -- 
	def add_recurring_block(self, block: RecurringBlock) -> int:
		curr = self.conn.execute("""
			INSERT INTO recurring_blocks(name, type, day_of_week, start_time, end_time, location, notes)
			VALUES (?, ?, ?, ?, ?, ?, ?)
		""", (block.name, block.type, block.day_of_week, block.start_time, block.end_time, 
			block.location, block.notes))
		self.conn.commit()
		return curr.lastrowid

	def get_recurring_blocks(self) -> list[RecurringBlock]:
		rows = self.conn.execute(
			"SELECT * FROM recurring_blocks ORDER BY day_of_week, start_time"
		).fetchall()
		return [RecurringBlock(id=r["id"], name=r["name"], type=r["type"],
			day_of_week=r["day_of_week"], start_time=r["start_time"],
			end_time=r["end_time"], location=r["location"],
			notes=r["notes"]) for r in rows]

	# -- work and volunteering -- 
	def add_work_volunteering(self, entry: WorkVolunteering) -> int:
		cur = self.conn.execute("""
			INSERT INTO work_volunteering
			(name, type, day_of_week, start_time, end_time, is_recurring, hours_per_week, notes)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)
		""", (entry.name, entry.type, entry.day_of_week, entry.start_time,
			entry.end_time, int(entry.is_recurring), entry.hours_per_week, entry.notes))
		self.conn.commit()
		return cur.lastrowid  

	def get_work_volunteering(self) -> list[WorkVolunteering]:
		rows = self.conn.execute("SELECT * FROM work_volunteering").fetchall()
		return [WorkVolunteering(id=r["id"], name=r["name"], type=r["type"],
			day_of_week=r["day_of_week"], start_time=r["start_time"],
			end_time=r["end_time"], is_recurring=bool(r["is_recurring"]),
			hours_per_week=r["hours_per_week"], notes=r["notes"]) for r in rows]
	


	# -- one-off events --
	def add_one_off_event(self, event: OneOffEvent) -> int:
		curr = self.conn.execute("""
			INSERT INTO one_off_events (name, type, date, start_time, end_time, notes)
			VALUES (?, ?, ?, ?, ?, ?)
		""", (event.name, event.type, event.date, event.start_time, event.end_time, event.notes))
		self.conn.commit()
		return curr.lastrowid

	def get_one_off_events(self, from_date: str | None = None) -> list[OneOffEvent]:
		if from_date:
			rows = self.conn.execute(
				"SELECT * FROM one_off_events WHERE date >= ? ORDER BY date, start_time",
				(from_date,)
			).fetchall()
		else:
			rows = self.conn.execute(
                		"SELECT * FROM one_off_events ORDER BY date, start_time",
			).fetchall()
		return [OneOffEvent(id=r["id"], name=r["name"], type=r["type"], date=r["date"], start_time=r["start_time"],
			end_time=r["end_time"], notes=r["notes"]) for r in rows]

 
	# -- past experience --
	def add_past_experience(self, exp: PastExperience) -> int:
		cur = self.conn.execute("""
			INSERT INTO past_experience (category, name, description, grade, year, relevance)
			VALUES (?, ?, ?, ?, ?, ?)
		""", (exp.category, exp.name, exp.description, exp.grade, exp.year, exp.relevance))
		self.conn.commit()
		return cur.lastrowid

	def get_past_experience(self) -> list[PastExperience]:
		rows = self.conn.execute(
			"SELECT * FROM past_experience ORDER BY category, year DESC"
		).fetchall()
		return [PastExperience(id=r["id"], category=r["category"], name=r["name"],
			description=r["description"], grade=r["grade"],
			year=r["year"], relevance=r["relevance"]) for r in rows] 


	# -- memory fragments --
	def add_fragment(self, fragment: MemoryFragment) -> int:
		cur = self.conn.execute("""
			INSERT INTO memory_fragments (category, content, source)
			VALUES (?, ?, ?)
		""", (fragment.category, fragment.content, fragment.source))
		self.conn.commit()
		return cur.lastrowid

	def get_fragments(self, category: str | None = None, limit: int = 40) -> list[MemoryFragment]:
		if category:
			rows = self.conn.execute(
				"SELECT * FROM memory_fragments WHERE category = ? ORDER BY created_at DESC LIMIT ?",
				(category, limit)
			).fetchall()
		else:
			rows = self.conn.execute(
				"SELECT * FROM memory_fragments ORDER BY created_at DESC LIMIT ?",
				(limit,)
			).fetchall()
		return [
			MemoryFragment(id=r["id"], category=r["category"], content=r["content"], source=r["source"])
			for r in rows
		]
 
	# -- study sessions -- 
	def log_session(self, session: StudySession) -> int:
		cur = self.conn.execute("""
			INSERT INTO study_sessions (subject_id, hours, quality, notes, logged_at)
			VALUES (?, ?, ?, ?, ?)
		""", (session.subject_id, session.hours, session.quality, session.notes, session.logged_at))
		self.conn.commit()
		return cur.lastrowid

	def get_sessions(self, limit: int = 50) -> list[StudySession]:
		rows = self.conn.execute(
			"SELECT * FROM study_sessions ORDER BY logged_at DESC LIMIT ?", (limit,)
		).fetchall()
		return [StudySession(id=r["id"], subject_id=r["subject_id"], hours=r["hours"], quality=r["quality"],
				notes=r["notes"], logged_at=r["logged_at"]) for r in rows]

	# -- conversation history -- 
	def add_turn(self, turn: ConversationTurn) -> int:
		cur = self.conn.execute("""
			INSERT INTO conversation_turns (role, content, context_tag)
			VALUES (?, ?, ?)
		""", (turn.role, turn.content, turn.context_tag))
		self.conn.commit()
		return cur.lastrowid

	def get_recent_turns(self, limit: int = 20, context_tag: str = "general") -> list[ConversationTurn]:
		rows = self.conn.execute("""
			SELECT * FROM (
				SELECT * FROM conversation_turns
				WHERE context_tag=?
				ORDER BY created_at DESC LIMIT ?
			) ORDER BY created_at ASC
		""", (context_tag, limit)).fetchall()
		return [ConversationTurn(id=r["id"], role=r["role"], content=r["content"], context_tag=r["context_tag"])
				for r in rows]


	def get_context_for_llm(self) -> str:
		from datetime import datetime

		profile = self.get_profile()
	
		all_subjects = self.get_subjects()
		active_subjects = [s for s in all_subjects if s.status == "active"]
		past_subjects = [s for s in all_subjects if s.status == "past"]

		recurring = self.get_recurring_blocks()
		work = self.get_work_volunteering()
		upcoming = self.get_one_off_events(
			from_date=datetime.now().date().isoformat()
		)
		experience = self.get_past_experience()
		fragments = self.get_fragments(limit=40)
		recent_ratings = self.conn.execute(
			"""SELECT event_label, rating, mood, notes
			FROM event_ratings ORDER BY rated_at DESC LIMIT 10"""
		).fetchall()

		parts = []

		if profile:
			parts.append(
				f"Name: {profile.name}\n"
				f"Goal: {profile.primary_goal}\n"
				f"Weekly study target: {profile.weekly_hours_target}h\n"
				f"Commute: {profile.commute_minutes} min each way "
				f"({round(profile.commute_minutes / 60 * 2, 1)}h a day lost to travel)"
			)

		if active_subjects:
			parts.append("Current subjects:\n" + "\n".join(
				f" - {s.name} | now: {s.current_grade} -> target: {s.target_grade}"
				f" | priority {s.priority}"
				+ (f" | note: {s.notes}" if s.notes else "")
				for s in active_subjects
			))

		if past_subjects:
			parts.append("Completed subjects:\n" + "\n".join(
				f" - {s.name} | final: {s.final_grade} | {s.year_taken}"
				for s in past_subjects
			))

		if experience:
			parts.append("Background and past experience:\n" + "\n".join(
				f"  [{e.category}] {e.name} ({e.year}) - {e.description}"
				+ (f"\n Relevance: {e.relevance}" if relevance else "")
				for e in experience
			))

		if recurring:
			parts.append("Fixed weekly timetable:\n" + "\n".join(
				f" - {b.name} ({b.type}): {b.day_of_week} {b.start_time}-{b.end_time}"
				+ (f" @ {b.location}" if b.location else "")
				for b in recurring
			))

		if work:
			parts.append("Work and Volunteering:\n" + "\n".join(
				f" - {w.name} ({w.type}): "
				+ (f"{w.day_of_week} {w.start_time}-{w.end_time}" if w.day_of_week else "variable schedule")
				+ (f" ~{w.hours_per_week}h/week" if w.hours_per_week else "")
				for w in work
			))

		if upcoming:
			parts.append("Upcoming one-off events:\n" + "\n".join(
				f"  - {e.date} {e.start_time or ''}: {e.name} ({e.type})"
				+ (f" - {e.notes}" if notes else "")
				for e in upcoming
			))

		if fragments:
			by_category: dict[str, list[str]] = {}
			for f in fragments:
				by_category.setdefault(f.category, []).append(f.content)
			frag_lines = []
			for cat, items in by_category.items():
				for item in items:
					frag_lines.append(f" [{cat}] {item}")
			parts.append("Personal context:\n" + "\n".join(frag_lines))

		if recent_ratings:
			parts.append("Recent event feedback:\n" + "\n".join(
				f"  -{r['event_label']}: {r['rating']}/5"
				+ (f" ({r['mood']})" if r['mood'] else "")
				+ (f" - {r['notes']}" if r['notes'] else "")
				for r in recent_ratings
			))

		return "\n\n".join(parts)   
