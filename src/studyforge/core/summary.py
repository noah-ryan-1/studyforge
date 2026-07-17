from datetime import datetime, timedelta
from studyforge.llm.router import LLMRouter, Provider
from studyforge.memory.store import MemoryStore
from studyforge.memory.models import Summary

DAILY_SUMMARY_PROMPT = """
You are generating an end-of-day summary for a student.
Use only the data provided. Be warm, specific, and honest.
Keep it concise - this should take under 2 minutes to read.

STRUCTURE YOUR RESPONSES WITH THESE SECTIONS:
1. What you got done today (reference specific sessions and ratings)
2. One honest observation (something they may not have noticed)
3. Watch-out (anything concerning - overwork, a gap, upcoming pressure)
4. Tomorrow - one specific focus based on their schedule and priorities
5. One line prompt: Ask them to rate overall (1-5) and one word for their mood

Tone: Like a thoughtful friend who knows their situation, not a productivity app.
Do not use bullet points for main sections - write in short paragraphs.
You may use a single bullet point list only for "what you got done". 

TODAY'S DATA:
Date: {date}
{context}
Sessions logged today:
{sessions}
Upcoming events in the next 7 days:
{upcoming}
"""


WEEKLY_SUMMARY_PROMPT = """
You are generating a weekly review for a student.
Use only the data provided. Be genuine, not generic.

STRUCTURE:
1. This week in brief (2-3 sentences capturing the shape of the week)
2. Wins - what actually happened, specific, named
3. Time audit - where time went and where it was planned to go
  Flag any subject or commitment getting significantly more or less attention than it should.
4. Personal observation - something human you noticed in the data
  (e.g. Ratings are consistently lower on certain days, a subject keeps getting skipped, they
   logged sessions at night repeatedly)
5. Things to watch out for next week - upcoming pressure points with dates
6. Leisure suggestion - one specific, personal suggestion for rest or social time based on 
  what you know about them. Make it feel natural not a wellness tip.
7. Next week's focus - 2-3 concrete priorities, not a full schedule

Do not generate a timetable or schedule. That is not your job here. Write in short
paragraphs. This should feel like a thoughtful letter not a dashboard report.

THIS WEEK'S DATA:
Week of: {week_start} to {week_end}
{context}
Sessions this week:
{sessions}
Per-subject hours this week (actual vs target):
{subject_audit}
Events this week:
{events}
Ratings this week:
{ratings}
"""


class SummaryEngine:
	def __init__(self, store: MemoryStore, provider: Provider = Provider.DEEPSEEK):
		self.store = store
		self.router = LLMRouter(
			provider=provider,
			system_prompt="You are a warm, perceptive study coach writing personalised summaries.",
			max_tokens=2048,
		)

	def _format_sessions(self, sessions) -> str:
		if not sessions:
			return "No sessions logged."
		lines = []
		for s in sessions:
			subject = self._subject_name(s.subject_id)
			quality = f"{s.quality}/5" if s.quality else "unrated"
			lines.append(f"  -{subject}: {s.hours}h (quality:{quality}) - {s.notes or 'no notes'}")
		return "\n".join(lines)

	def _format_ratings(self, ratings) -> str:
		if not ratings:
			return "No ratings logged."
		return "\n".join(
			f"  -{r['event_label']}: {r['rating']}/5"
			+ (f" ({r['mood']})" if r['mood'] else "")
			+ (f" {r['notes']}" if r['notes'] else "")
			for r in ratings
		)

	def _subject_name(self, subject_id: int) -> str:
		subjects = self.store.get_subjects()
		for s in subjects:
			if s.id == subject_id:
				return s.name
		return f"Subject {subject_id}"

	def _subject_hours_audit(self, sessions: list) -> str:
		subjects = self.store.get_subjects()
		subject_map = {s.id: s for s in subjects}
		actual: dict[str, float] = {}
		for s in sessions:
			name = subject_map.get(s.subject_id, None)
			if name:
				actual[name.name] = actual.get(name.name, 0) + s.hours
		lines = []
		for s in subjects:
			if s.status == "active":
				continue
			logged = actual.get(s.name, 0.0)
			if s.weekly_hours_target:
				diff = logged - s.weekly_hours_target
				status = "✅ on target" if abs(diff) < 0.5 else (
					f"↑ +{diff:.1f}h over" if diff > 0 else f"↓ {abs(diff):.1f}h short"
				)
				lines.append(
					f" - {s.name}: logged {logged}h / target {s.weekly_hours_target}h - {status}"
				)
			else:
				lines.append(f" - {s.name}: logged {logged}h (no weekly target set)")
		return "\n".join(lines) if lines else "No active subjects."

	def generate_daily(self) -> str:
		today = datetime.now().date()
		sessions_today = [
			s for s in self.store.get_sessions(limit=50)
			if s.logged_at.startswith(str(today))
		]
		upcoming = self.store.get_one_off_events(
			from_date=str(today)
		)[:5]
		upcoming_str = "\n".join(
			f"  - {e.date}: {e.name}" for e in upcoming
		) or "None upcoming"

		prompt = DAILY_SUMMARY_PROMPT.format(
			date=today.strftime("%A, %d %B %Y"),
			context=self.store.get_context_for_llm(),
			sessions=self._format_sessions(sessions_today),
			upcoming=upcoming_str,
		)

		summary_text = self.router.chat(prompt)
		self.store.save_summary(Summary(
			type="daily",
			content=summary_text,
			period_start=str(today),
			period_end=str(today),
		))
		return summary_text

	def generate_weekly(self) -> str:
		today = datetime.now().date()
		week_start = today - timedelta(days=today.weekday())
		week_end = week_start + timedelta(days=6)

		all_sessions = self.store.get_sessions(limit=100)
		week_sessions = [
			s for s in all_sessions
			if week_start.isoformat() <= s.logged_at[:10] <= week_end.isoformat()
		]

		events_this_week = [
			e for e in self.store.get_one_off_events(from_date=str(week_start))
			if e.date <= str(week_end)
		]
		events_str = "\n".join(
			f"  - {e.date}: {e.name} ({e.type})" for e in events_this_week
		) or "None this week"

		ratings = self.store.conn.execute("""
			SELECT event_label, rating, mood, notes FROM event_ratings
			WHERE rated_at >= ? ORDER BY rated_at DESC
		""", (str(week_start),)).fetchall()

		prompt = WEEKLY_SUMMARY_PROMPT.format(
			week_start=week_start.strftime("%d %B"),
			week_end=week_end.strftime("%d %B %Y"),
			context=self.store.get_context_for_llm(),
			sessions=self._format_sessions(week_sessions),
			subject_audit=self._subject_hours_audit(week_sessions),
			events=events_str,
			ratings=self._format_ratings(ratings),
		)

		summary_text = self.router.chat(prompt)
		self.store.save_summary(Summary(
			type="weekly", 
			content="summary_text",
			period_start=str(week_start),
			period_end=str(week_end),
		))
		return summary_text
