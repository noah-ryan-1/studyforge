from studyforge.integrations.calendar_client import CalendarClient
from studyforge.integrations.calendar_sync import CalendarSync
from studyforge.memory.store import MemoryStore
import os

print("=== Testing CalendarClient ===")
print("(A browser window may open for Google login on first run)\n")

client = CalendarClient()
print("[auth] Connected Successfully\n")

events = client.get_events_this_week()
print(f"[events] Found {len(events)} events this week!:")
for e in events:
	rtype = "recurring" if e.is_recurring else "one-off"
	print(f"  {e.start.strftime('%a %H:%M')} - {e.title} ({rtype})")

upcoming = client.get_upcoming_events(days=30)
print(f"\n[upcoming] Found {len(upcoming)} events in the next 30 days:")
for e in upcoming[:5]:
	print(f"  {e.start.strftime('%d %b')} - {e.title}")

print("\n=== Testing CalendarSync ===")
DB = os.path.expanduser("~/studyforge/studyforge.db")
store = MemoryStore(DB)

syncer = CalendarSync(store)
week_counts = syncer.sync_week()
print(f"Week sync: {week_counts}")

upcoming_counts = syncer.sync_upcoming(days=30)
print(f"Upcoming sync: {upcoming_counts}")

print(f"Recurring blocks in memory:")
for b in store.get_recurring_blocks():
	print(f" {b.day_of_week} {b.start_time}-{b.end_time}: {b.name}")

print("\nOne-off events in memory:")
for e in store.get_one_off_events():
	print(f"  {e.date}: {e.name} ({e.type})")

store.close()
print("\n[done] Calendar Sync Complete")
