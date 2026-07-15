import os
from studyforge.memory.store import MemoryStore
from studyforge.core.consultation import ConsultationEngine

if os.path.exists("test_consult.db"):
	os.remove("test_consult.db")

store = MemoryStore("test_consult.db")
engine = ConsultationEngine(store)

print("=== Starting Consultation ===")
opening = engine.start()
print(f"StudyForge: {opening}")

fake_answers = [
	"Hi, my name is Alex.", 
	"I want to become a machine learning engineer, focused on research and building real things. Not just using models but understanding them",
	"I'm in third year",
	"Semester ends in late October and I haven't got my exam schedule which could last until November. Mix of assignments and final exam for most subjects",
	"I'm doing Algorithms and Data Structures, currently at 75 but want to push to 85. Feeling pretty comfortable with it",
	"Also Stochastic models, sitting at 70, targetting 80, it's ok - the probability components connect well with my goal.",
	"And Econometrics. That's my weakest right now at 58%. I want an 80% but honestly feels like a stretch. Mostly assignments and exam.",
	"I have a lecture on Mondays 10-11am at Peter Hall, and a tutorial Wednesday 2-3pm.",
	"I tutor English as a second language on Monday 11-12. Its a regular thing each week.",
	"I have a job interview with TikTok on August 15th at 1pm",
	"I previously failed Design of Algorithms with a 48. I was doing too much that semester, and couldn't commit to any of my subjects.",
	"Commute is about an hour each way by train. I do 5 days a week.",
	"Typical day - up at 7, leave at 8, get to uni by 9, back home around 6-7pm most days. By the evening I am pretty cooked, but I would love to workout.",
	"Mornings are my best time. After about 8pm I can't really focus on anything hard.",
	"Honestly? Maybe 8 to 10 hours of real study a week on top of everything. I've tried more and it falls apart and less is like when I failed that subject.",
	"Sundays are off. Non-negotiable. Family day. I like hiking on Saturdays if I can as well.",
	"No major burnout but I have had period where I just stopped studying for a week or two, and began missing classes. Usually after crunch periods.",
	"12 months from now I want to have job lined up so that I can continue into Masters while working with a clear ML focus. The tiktok interview is part of this",  
]

for answer in fake_answers:
	if engine.is_complete:
		break
	print(f"You: {answer}")
	response = engine.reply(answer)
	print(f"StudyForge: {response}")

print("\n=== Final Memory State ===")
print("Profile:", store.get_profile())
print("Subjects:", store.get_subjects())
print("Blocks:", store.get_recurring_blocks())
print("Work:", store.get_work_volunteering())
print("Events:", store.get_one_off_events())
print("Experience:", store.get_past_experience())
print("Fragments:", store.get_fragments())
store.close()
