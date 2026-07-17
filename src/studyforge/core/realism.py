from datetime import datetime
from studyforge.llm.router import LLMRouter, Provider
from studyforge.memory.store import MemoryStore

REALISM_PROMPT = """
You are analysing whether a student's weekly study target is realistic
given their actual commitments. Be honest and direct - not hard but not 
falsely encouraging either. 

Use only the data below. Do not assume anything not being stated. 

YOUR ANALYSIS MUST COVER:
1. Total fixed hours per week (lectures + tutorials + labs + other fixed commitments)
2. Total commute hours per week (commute_minutes x 2 x days_attending)
3. Total work/volunteering hours per week
4. Estimated sleep (7-8h per night = 49/56 a week)
5. Waking hours remained after all those above
6. Whether the stated weekly_hours_target is achievable in that remainder
7. A reccomended realistic target if the stated one is not achievable
8. Any specific pinch points (e.g. Mondays are completely packed)
9. One concrete suggestion for where sutdy time could realistically fit

FORMAT YOUR RESPONSE AS JSON ONLY - no prose, no markdown:
{{
	"fixed_commitment_hours": ,
	"commute_hours_per_week": ,
	"work_hours_per_week": ,
	"estimated_free_hours": ,
	"stated_target_hours": ,
	"target_is_realistic": ,
	"recommended_target_hours": ,
	"pinch_points": [,...],
	"suggestion": ,
	"summary":
}}

USER DATA:
{context}
"""


class RealismChecker:
	def __init__(self, store: MemoryStore, provider: Provider = Provider.DEEPSEEK):
		self.store = store
		self.router = LLMRouter(
			provider=provider,
			system_prompt="You are a precise scheduling analyst. Return only valid JSON.",
			max_tokens=1024,
		)

	def check(self) -> dict:
		context = self.store.get_context_for_llm()
		raw = self.router.chat(REALISM_PROMPT.format(context= context))
		return self._parse(raw)

	def _parse(self, raw: str) -> dict:
		import re, json
		# strip markdown code fences is present
		cleaned = re.sub(r"```(?:json)?\s*|```", "", raw).strip()
		try:
			return json.loads(cleaned)
		except json.JSONDecodeError:
			return {"error": "Failed to parse realism check", "raw": raw}

	def print_report(self, result: dict):
		if "error" in result:
			print(f"Realism check failed: {result['error']}")
			return
		print("\n=== Realism Check ===")
		print(f"Fixed commitments: {result.get('fixed_commitment_hours')}h/week")
		print(f"Commute:           {result.get('commute_hours_per_week')}h/week")
		print(f"Work/Volunteering: {result.get('work_hours_per_week')}h/week")
		print(f"Estimated free:    {result.get('estimated_free_hours')}h/week")
		print(f"Study target:      {result.get('stated_target_hours')}h/week")
		print(f"Realistic:         {result.get('target_is_realistic')}")
		print(f"Recommended time:  {result.get('recommended_target_hours')}h/week")
		print(f"Pinch Points:")
		for p in result.get('pinch_points', []):
			print(f" - {p}")
		print(f"Suggestion:        {result.get('suggestion')}")
		print(f"{result.get('summary')}")   
