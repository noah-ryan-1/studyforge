from enum import Enum
from dataclasses import dataclass, field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class Provider(Enum):
	CLAUDE = "claude"
	DEEPSEEK = "deepseek"
	GPT4 = "gpt4"

@dataclass
class Message:
	role: str
	content: str

@dataclass
class LLMRouter:
	provider: Provider = Provider.DEEPSEEK
	model: str = "deepseek-chat"
	max_tokens: int = 2048
	system_prompt: str = ""
	history: list[Message] = field(default_factory=list)
	_client: OpenAI = field(default=None, repr=False)

	def __post_init__(self):
		import os
		self._client = OpenAI(
			api_key=os.getenv("DEEPSEEK_API_KEY"),
			base_url="https://api.deepseek.com/v1"
		)

	def chat(self, user_message: str) -> str:
		self.history.append(Message(role="user", content=user_message))

		messages = [ 
			{"role": m.role, "content": m.content} for m in self.history
		]

		if self.provider == Provider.DEEPSEEK:
			response = self._call_deepseek(messages)
		else:
			raise NotImplementedError(f"{self.provider} not yet implemented")

		self.history.append(Message(role="assistant", content=response))
		return response

	def _call_deepseek(self, messages: list[dict]) -> str:
		# Prepend system prompt as a message to adapt for openAI style 
		full_messages = []
		if self.system_prompt:
			full_messages.append({"role": "system", "content": self.system_prompt})
		full_messages.extend(messages)

		kwargs = {
			"model": self.model,
			"max_tokens": self.max_tokens,
			"messages": messages,
		}

		response  = self._client.chat.completions.create(**kwargs)
		return response.choices[0].message.content

	def clear_history(self):
		self.history = []
