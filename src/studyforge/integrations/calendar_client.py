from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

@dataclass
class CalendarEvent:
	id: str
	title: str
	start: datetime
	end: datetime
	calendar_id: str = "primary"
	is_recurring: bool = False
	recurrence_id: str | None = None


SCOPES = ["https://www.googleapis.com/auth/calendar"]

CREDS_PATH = Path.home() / "studyforge" / "credentials.json"
TOKEN_PATH = Path.home() / "studyforge" / "toke.json"

class CalendarClient:
	def __init__(self):
		self.service = self.authenticate()

	def authenticate(self):
		creds = None

		if TOKEN_PATH.exists():
			creds = Credentials.from_authorized_user_file(
				str(TOKEN_PATH), SCOPES
			)

		if not creds or not creds.valid:
			if creds and creds.expired and creds.refresh_token:
				creds.refresh(Request())
			else:
				if not CREDS_PATH.exists():
					raise FileNotFoundError(
						f"credentials.json not found at {CREDS_PATH}\n"
						"Download it from Google Cloud Console -> "
						"APIs & Services -> Credentials"
					)
				flow = InstalledAppFlow.from_client_secrets_file(
					str(CREDS_PATH), SCOPES
				)
				creds = flow.run_local_server(port=0)

			TOKEN_PATH.write_text(creds.to_json())

		return build("calendar", "v3", credentials=creds)

	def get_events_this_week(self) -> list[CalendarEvent]:
		"""Fetch all events in current week."""
		today = datetime.now(timezone.utc).date()
		week_start = today - timedelta(days=today.weekday())
		week_end = week_start + timedelta(days=7)

		time_min = datetime.combine(week_start,
			datetime.min.time()).replace(tzinfo=timezone.utc).isoformat()
		time_max = datetime.combine(week_end,
			datetime.min.time()).replace(tzinfo=timezone.utc).isoformat()

		result = self.service.events().list(
			calendarId="primary",
			timeMin=time_min,
			timeMax=time_max,
			singleEvents=True,
			orderBy="startTime"
		).execute()

		return [self._parse_event(e) for e in result.get("items", [])]

	def get_upcoming_events(self, days: int = 30) -> list[CalendarEvent]:
		"""Fetch all the events in the next N days."""
		now = datetime.now(timezone.utc)
		time_max = (now + timedelta(days=days)).isoformat()

		result = self.service.events().list(
			calendarId="primary",
			timeMin=now.isoformat(),
			timeMax=time_max,
			singleEvents=True,
			orderBy="startTime",
			maxResults=50,
		).execute()

		return [self._parse_event(e) for e in result.get("items", [])]

	def _parse_event(self, raw: dict) -> CalendarEvent:
		start_raw = raw["start"]
		end_raw = raw["end"]

		if "dateTime" in start_raw:
			start = datetime.fromisoformat(
				start_raw["dateTime"].replace("Z", "+00:00")
			)
			end = datetime.fromisoformat(
				end_raw["dateTime"].replace("Z", "+00:00")
			)
		else:
			#all-day-event
			start = datetime.fromisoformat(start_raw["date"]).replace(
				tzinfo=timezone.utc
			)
			end = datetime.fromisoformat(end_raw["date"]).replace(
				tzinfo=timezone.utc
			)
		return CalendarEvent(
			id=raw["id"],
			title=raw.get("summary", "Untitled"),
			start=start,
			end=end,
			is_recurring="recurringEventId" in raw,
			recurrence_id=raw.get("recurringEventId"),
		)
