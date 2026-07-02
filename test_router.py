from src.studyforge.llm.router import LLMRouter, Provider

router = LLMRouter(
	provider=Provider.DEEPSEEK,
	system_prompt="You are a helpful study coach."
)

response = router.chat("Hello! What's 2+2?")
print("Response:", response)

response2 = router.chat("Now multiply that by 10.")
print("Response:", response2)

print("\nConversation history:")
for msg in router.history:
	print(f"   [{msg.role}]: {msg.content[:60]}...")
