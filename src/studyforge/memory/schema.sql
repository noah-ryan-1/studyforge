CREATE TABLE IF NOT EXISTS user_profile (
	id      INTEGER PRIMARY KEY,
	name    TEXT,
	primary_goal TEXT,
	weekly_hours_target INTEGER DEFAULT 20,
	commute_minutes INTEGER DEFAULT 0,
	commute_days_per_week INTEGER DEFAULT 5,
	created_at TEXT DEFAULT (datetime('now')),
	updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS subjects (
	id      INTEGER PRIMARY KEY AUTOINCREMENT,
	name    TEXT NOT NULL,
	status  TEXT NOT NULL DEFAULT 'active'
		CHECK(status IN ('active', 'past', 'paused')),
	current_grade REAL,
	target_grade REAL,
	final_grade REAL,
	priority INTEGER DEFAULT 1,
	weekly_hours_target REAL DEFAULT NULL,
	year_taken TEXT, 
	notes  TEXT DEFAULT '',
	created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recurring_blocks (
	id  INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	type TEXT NOT NULL CHECK(type IN ('lecture', 'lab', 'tutorial', 'other')),
	day_of_week TEXT NOT NULL,
	start_time TEXT NOT NULL,
	end_time TEXT NOT NULL,
	location TEXT DEFAULT '',
	notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS work_volunteering (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	type TEXT NOT NULL CHECK(type IN ('job', 'volunteering', 'placement', 'internship')),
	day_of_week TEXT,
	start_time TEXT,
	end_time TEXT,
	is_recurring INTEGER DEFAULT 1, 
	hours_per_week REAL,
	notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS one_off_events (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	type TEXT NOT NULL CHECK(type IN ('exam', 'assignment_due', 'appointment', 'social', 'travel', 'other')),
	date TEXT NOT NULL,
	start_time TEXT,
	end_time TEXT,
	notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS past_experience (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	category TEXT NOT NULL CHECK (category IN (
		'subject', 'course', 'job', 'project',
		'skill', 'certification', 'research', 'other'
	)),
	name TEXT NOT NULL, 
	description TEXT DEFAULT '',
	grade REAL, 
	year TEXT,
	relevance TEXT DEFAULT '',
	created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS memory_fragments (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	category TEXT NOT NULL CHECK(category IN (
		 	'preference', 'commitment', 'social', 'constraint',
			'goal_detail', 'personal', 'health', 'observation'
	)),
	content TEXT NOT NULL,
	source  TEXT DEFAULT 'consultation',
	created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS event_ratings (
	id  INTEGER PRIMARY KEY AUTOINCREMENT, 
	event_type TEXT NOT NULL, -- 'study', 'exam', etc
	event_label TEXT NOT NULL, -- ' Linear Algebra session', 'meet-up with friends'
	rating INTEGER CHECK(rating BETWEEN 1 AND 5),
	mood TEXT, -- 'energised', 'drained', 'neutral', 'stressed'
	notes TEXT DEFAULT '',
	rated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS summaries (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	type TEXT NOT NULL CHECK(type IN ('daily', 'weekly')), -- to add monthly 
	content TEXT NOT NULL, -- full LLM generated summary text
	period_start TEXT NOT NULL, -- ISO date
	period_end   TEXT NOT NULL, 
	created_at   TEXT DEFAULT (datetime('now'))
);


CREATE TABLE IF NOT EXISTS study_sessions (
	id   INTEGER PRIMARY KEY AUTOINCREMENT,
	subject_id INTEGER REFERENCES subjects(id),
	hours REAL NOT NULL, 
	quality INTEGER CHECK(quality BETWEEN 1 AND 5),
	notes TEXT DEFAULT '',
	logged_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS conversation_turns (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
	content TEXT NOT NULL, 
	context_tag TEXT DEFAULT 'general',
	created_at TEXT DEFAULT (datetime('now'))
);
