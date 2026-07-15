import re
import json
from studyforge.llm.router import LLMRouter, Provider
from studyforge.memory.store import MemoryStore
from studyforge.memory.models import ConversationTurn, MemoryFragment

CHAT_SYSTEM_PROMPT = """
You are StudyForge, a personal study coach and life organiser.
You know this person well - their full profile is below.

Use this context in every response. Never give generic advice.
Reference their specific subjects, grades, commitments and goals. 

ONGOING MEMORY:
If the user tells you something new worth remembering, emit at the END
of your message:

{{"category":"commitment", "content":"Fortnightly meeting with thesis supervisor, usually Thursdays"}}

This is an example above.

Valid categories: preference, commitment, social, constraint, goal_detail,
personal, health, observation

Omit entirely if nothing new was learned.

YOUR ROLES IN DAILY USE:
- Answer questions about scheduling, priorities, and study stratergy
- Help fit new commitments into the existing schedule realistically
- Provide encouragment that's honest, not hollow 
- Notice when the user seems stressed and acknowledge it
- Flag when they are overcommitting without being preachy
- Suggest rest and social time when the pattern warrants it

When asked to schedule something, think about:
- Commute time eating into available hours
- Energy levels at different times of day (from their profile)
- Upcoming exams or deadlines that need buffer time
- Whether they have had breaks and how many recently

--- USER PROFILE ---
{context}
---
"""

class ChatLoop:
	def __init__(self, store: MemoryStore, provider: Provider = Provider.DEEPSEEK):
		self.store = store
		context = store.get_context_for_llm()
		self.router = LLMRouter(
			provider=provider,
			system_prompt=CHAT_SYSTEM_PROMPT.format(context=context),
			max_tokens=1024,
		)

	def send(self, user_message: str) -> str:
		raw = self.router.chat(user_message)

		fragment = self._extract_remember(raw)
		if fragment:
			self.store.add_fragment(fragment)

		clean = re.sub(r"<remember>.*?</remember>", "", raw, flags=re.DOTALL).strip()

		self.store.add_turn(ConversationTurn(role="user", content=user_message))
		self.store.add_turn(ConversationTurn(role="assistant", content=clean))

		return clean

	def _extract_remember(self, response: str) -> MemoryFragment | None:
		match = re.search(r"<remember>(.*?)</remember>", response, re.DOTALL)
		if not match:
			return None
		try:
			data = json.loads(match.group(1).strip())
			return MemoryFragment(
				category=data["category"],
				content=data["content"],
				source="daily_chat"
			)
		except (json.JSONDecodeError, KeyError):
			return None

	def refresh_context(self):
		""" Call this after adding new data to memory mid-session."""
		context = self.store.get_context_for_llm()
		self.router.system_prompt = CHAT_SYSTEM_PROMPT.format(context=context)
