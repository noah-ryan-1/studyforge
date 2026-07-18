import typer
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from pathlib import Path
from studyforge.memory.store import MemoryStore
from studyforge.llm.router import Provider
load_dotenv()
DEBUG = os.getenv("STUDYFORGE_DEBUG", "false").lower() == "true"

app = typer.Typer(
	name="studyforge",
	help="Your AI-powered personal study coach.",
	no_args_is_help=True,
)
console = Console()

DB_PATH = Path.home() / ".studyforge" / "studyforge.db"


def get_store() -> MemoryStore:
	DB_PATH.parent.mkdir(parents=True, exist_ok=True)
	return MemoryStore(str(DB_PATH))

def get_provider(provider: str) -> Provider:
	mapping = {
		"deepseek": Provider.DEEPSEEK,
		"claude": Provider.CLAUDE,
		"gpt4": Provider.GPT4,
	}
	p = mapping.get(provider.lower())
	if not p:
		console.print(f"[red]Unknown provider '{provider}'."
			f"Choose: deepseek, claude, gpt4[/red]")
		raise typer.Exit(1)
	return p

def require_profile(store: MemoryStore):
	if not store.get_profile():
		console.print(
			"[yellow]No Profile found. Run [bold]studyforge onboard[/bold] first.[/yellow]"
		)
		raise typer.Exit(1)

@app.command()
def onboard(
	provider: str = typer.Option("deepseek", "--provider", "-p",
		help="LLM provider: deepseek, claude, gpt4"),
	force: bool = typer.Option(False, "--force", "-f",
		help="Re-run onboarding even if profile exists"),
):
	"""Run the onboarding consultation to build your profile."""
	from studyforge.core.consultation import ConsultationEngine

	store = get_store()
	p = get_provider(provider)

	if store.get_profile() and not force:
		console.print(
			"[yellow]You already have a profile. "
			"Use --force to re-run onboarding.[/yellow]"
		)
		raise typer.Exit(0)

	console.print(Panel(
		"[bold]Welcome to StudyForge[/bold]\n"
		"I'm going to ask you some questions to understand your "
		"goals, schedule, and situation.\n"
		"This usually takes 5-10 minutes.",
		title="Onboarding",
		border_style="blue",
	))

	engine = ConsultationEngine(store, provider=p, debug=DEBUG)
	opening = engine.start()
	console.print(f"\n[bold cyan]StudyForge:[/bold cyan] {opening}\n")

	while not engine.is_complete:
		try:
			user_input = typer.prompt("You")
		except (KeyInterrupt, EOFError):
			console.print("\n[yellow]Onboarding paused. Run again to continue.[/yellow]")
			break

		response = engine.reply(user_input)
		console.print(f"\n[bold cyan]StudyForge:[/bold cyan] {response}\n")

	if engine.is_complete:
		console.print(Panel(
			"[green]Onboarding Complete! Your Profile has been saved.[/green]\n"
			"Run [bold]studyforge status[/bold] to see your profile,\n"
			"or [bold]studyforge chat[/bold] to start using StudyForge.",
			border_style="green",
		))
	store.close()


@app.command()
def chat(
	provider: str = typer.Option("deepseek", "--provider", "-p",
		help="LLM provider: deepseek, claude, gtp4"),
):
	"""Chat with your AI study coach."""
	from studyforge.core.chat_loop import ChatLoop

	store = get_store()
	require_profile(store)
	p = get_provider(provider)

	profile = store.get_profile()
	console.print(Panel(
		f"[bold]Hi {profile.name}[/bold] - what's on your mind?\n"
		"[dim]Type 'exit' or press Crtl+C to end the session[/dim]",
		border_style="blue",
	))

	loop = ChatLoop(store, provider=p)

	while True:
		try:
			user_input = typer.prompt("\nYou").strip()
		except (KeyboardInterrupt, EOFError):
			console.print("\n[yellow]Session end.[/yellow]")
			break

		if not user_input:
			continue

		with console.status("Thinking...", spinner="dots"):
			response = loop.send(user_input)

		console.print(f"\n[bold cyan]Studyforge:[/bold cyan] {response}")

	store.close()


@app.command()
def log(
	topic: str = typer.Argument(..., help="Subject or topic you studied"),
	hours: float = typer.Option(..., "--hours", "-h", prompt="Hours spent"),
	quality: int = typer.Option(..., "--quality", "-q",
		prompt="Quality (1-5)", min=1, max=5),
	notes: str = typer.Option("", "--notes", "-n", help="Optional notes"),
):
	"""Log a completed study session."""
	from studyforge.memory.models import StudySession
	from datetime import datetime

	store = get_store()
	require_profile(store)

	subjects = store.get_subjects()
	match = next(
		(s for s in subjects if topic.lower() in s.name.lower()), None
	)

	if not match:
		console.print(f"[yellow]No subject matching '{topic}' found.[/yellow]")
		console.print("Known subjects: " +
			", ".join(s.name for s in subjects))
		raise typer.Exit(1)

	store.log_session(StudySession(
		subject_id=match.id,
		hours=hours,
		quality=quality,
		notes=notes,
		logged_at=datetime.now().isoformat(),
	))
	console.print(
		f"[green]✅ Logged {hours}h on {match.name} "
		f"(quality: {quality}/5[/green]"
	)
	store.close()


@app.command()
def rate(
	label: str = typer.Argument(..., help="What you are rating"),
	score: int = typer.Option(..., "--score", "-s",
		prompt="Rating (1-5)", min=1, max=5),
	mood: str = typer.Option("", "--mood", "-m",
		prompt="One word for your mood (optional)"),
	notes: str = typer.Option("", "--notes", "-n", help="Any notes? (optional)"),
	event_type: str = typer.Option("study", "--type", "-t",
		help="Type: study, exam, meeting, social, work"),
):
	"""Rate an event - study session, exam, meeting, or anything else."""
	from studyforge.memory.models import EventRating

	store = get_store()
	require_profile(store)

	store.add_rating(EventRating(
		event_type=event_type,
		event_label=label,
		rating=score,
		mood=mood,
		notes=notes,
	))
	console.print(f"[green]✅ Rated '{label}': {score}/5[/green]")
	store.close()

@app.command()
def status():
	"""Show your current week snapshot."""
	from datetime import datetime, timedelta

	store = get_store()
	require_profile(store)

	profile = store.get_profile()
	subjects = [s for s in store.get_subjects() if s.status == "active"]
	today = datetime.now().date()
	week_start = today - timedelta(days=today.weekday())

	all_sessions = store.get_sessions(limit=200)
	week_sessions = [
		s for s in all_sessions
		if s.logged_at[:10] >= str(week_start)
	]

	hours_by_subject: dict[int, float] = {}
	for s in week_sessions:
		hours_by_subject[s.subject_id] = (
			hours_by_subject.get(s.subject_id, 0.0) + s.hours
		)

	console.print(Panel(
		f"[bold]{profile.name}[/bold] - "
		f"{today.strftime('%A, %d %B %Y')}\n"
		f"Goal: {profile.primary_goal}",
		title="StudyForge Status",
		border_style="blue",
	))

	table = Table(show_header=True, header_style="bold")
	table.add_column("Subject", style="white")
	table.add_column("Grade", justify="center")
	table.add_column("Target", justify="center")
	table.add_column("This week", justify="center")
	table.add_column("Weekly target", justify="center")
	table.add_column("", justify="center")

	for s in subjects:
		logged = hours_by_subject.get(s.id, 0.0)
		target = s.weekly_hours_target
		if target:
			diff = target - logged
			indicator = "✅" if abs(diff) < 0.5 else ("⬆️️" if diff > 0 else "⬇️")
			target_str = f"{target}h"
		else:
			indicator="-"
			target_str = "not set"

		table.add_row(
			s.name,
			f"{s.current_grade}%" if s.current_grade else "-",
			f"{s.target_grade}%" if s.target_grade else "-",
			f"{logged}h",
			target_str,
			indicator,
		)

	console.print(table)

	upcoming = store.get_one_off_events(from_date=str(today))[:3]
	if upcoming:
		console.print("\n[bold]Upcoming:[/bold]")
		for e in upcoming:
			console.print(f"  [cyan]{e.date}[/cyan]  {e.name} ({e.type})")

	store.close()


@app.command()
def daily(
	provider: str = typer.Option("deepseek", "--provider", "-p", help="LLM Provider"),
):
	"""Generate your end-of-day summary and reflection."""
	from studyforge.core.summary import SummaryEngine

	store = get_store()
	require_profile(store)
	p = get_provider(provider)

	with console.status("Generating your daily summary...", spinner="dots"):
		engine = SummaryEngine(store, provider=p)
		summary = engine.generate_daily()

	console.print(Panel(
		summary,
		title="End of Day",
		border_style="cyan",
	))
	store.close()

 
@app.command()
def weekly(
	provider: str = typer.Option("deepseek", "--provider", "-p", help="LLM provider"),
):
	"""Generate your weekly review and next week plan."""
	from studyforge.core.summary import SummaryEngine

	store = get_store()
	require_profile(store)
	p = get_provider(provider)

	with console.status("Generating your weekly review...", spinner="dots"):
		engine = SummaryEngine(store, provider=p)
		summary = engine.generate_weekly()

	console.print(Panel(
		summary,
		title="Weekly Review",
		border_style="magenta",
	))
	store.close()


@app.command()
def check(
	provider: str = typer.Option("deepseek", "--provider", "-p", help="LLM provider"),
):
	"""Run a realism check on your current study target."""
	from studyforge.core.realism import RealismChecker

	store = get_store()
	require_profile(store)
	p = get_provider(provider)

	with console.status("Analysing your schedule...", spinner="dots"):
		checker = RealismChecker(store, provider=p)
		result = checker.check()

	if "error" in result:
		console.print(f"[red]Realism check failed: {result['error']}[/red]")
		raise typer.Exit(1)

	table = Table(show_header=False, box=None)
	table.add_column("Field", style="dim")
	table.add_column("Value", style="white")

	table.add_row("Fixed Commmitments", f"{result.get('fixed_commitment_hours')}h/week")
	table.add_row("Commute", f"{result.get('commute_hours_per_week')}h/week")
	table.add_row("Work/Volunteering", f"{result.get('work_hours_per_week')}h/week")
	table.add_row("Estimated Free Time", f"{result.get('estimated_free_hours')}h/week")
	table.add_row("Your study target", f"{result.get('stated_target_hours')}h/week")
	table.add_row("Realistic?", "[green]Yes[/green]" if result.get("target_is_realistic")
		else "[red]No[/red]"
	)
	table.add_row("Reccomended target", f"{result.get('reccomended_target_hours')}h/week"
		if result.get('reccomended_target_hours') else "")

	console.print(Panel(table, title="Realism Check", border_style="yellow"))

	if result.get("pinch_points"):
		console.print("\n[bold]Pinch points:[/bold]")
		for p_point in result["pinch_points"]:
			console.print(f"  [yellow]•[/yellow] {p_point}")

	console.print(f"\n[bold]Suggestion[/bold] {result.get('suggestion')}")
	console.print(f"\n{result.get('summary')}")
	store.close()


if __name__ == "__main__":
	app() 	
