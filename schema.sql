-- CivicPulse database schema (SQLite). server.py ise start hote hi apne aap chalata hai.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (            -- citizens (mobile number login, OTP nahi)
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  phone       TEXT NOT NULL UNIQUE,
  name        TEXT DEFAULT 'Citizen',
  created_at  TEXT DEFAULT (datetime('now')),
  last_login  TEXT
);

CREATE TABLE IF NOT EXISTS admins (           -- admin panel users
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  salt          TEXT NOT NULL,
  created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS departments (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  sla_hours  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  base_risk     INTEGER NOT NULL,
  department_id TEXT NOT NULL REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS staff (            -- field staff (login ke saath)
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  department_id TEXT NOT NULL REFERENCES departments(id),
  username      TEXT,
  password_hash TEXT,
  salt          TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_staff_username ON staff(username);

CREATE TABLE IF NOT EXISTS complaints (
  id                TEXT PRIMARY KEY,
  title             TEXT NOT NULL,
  category_id       TEXT NOT NULL REFERENCES categories(id),
  description       TEXT NOT NULL,
  x                 REAL, y REAL,
  lat               REAL, lng REAL,
  route             TEXT,
  status            TEXT NOT NULL DEFAULT 'Open' CHECK (status IN ('Open','Assigned','In Progress','Resolved')),
  staff_id          TEXT REFERENCES staff(id),
  phone             TEXT REFERENCES users(phone),
  created_at        TEXT NOT NULL,
  updated_at        TEXT DEFAULT (datetime('now')),
  dup               INTEGER DEFAULT 0,
  risk              INTEGER DEFAULT 20,
  priority_override INTEGER,
  admin_note        TEXT DEFAULT '',
  staff_note        TEXT DEFAULT '',
  photo             TEXT,
  after_photo       TEXT,
  fb_rating         INTEGER,
  fb_comment        TEXT
);

CREATE TABLE IF NOT EXISTS complaint_history (  -- har status change ka record
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  complaint_id TEXT NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
  status       TEXT NOT NULL,
  changed_by   TEXT,
  note         TEXT,
  changed_at   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_phone  ON complaints(phone);
CREATE INDEX IF NOT EXISTS idx_complaints_route  ON complaints(route);

INSERT OR IGNORE INTO departments VALUES
 ('dept-roads','Civil & Roads Engineering',48),('dept-sanitation','Solid Waste & Sanitation',24),
 ('dept-water','Water Supply & Hydraulics',18),('dept-electrical','Electrical & Street Lighting',36),
 ('dept-drainage','Stormwater & Drainage Div.',24);
INSERT OR IGNORE INTO categories VALUES
 ('pothole','Pothole',30,'dept-roads'),('garbage','Garbage',15,'dept-sanitation'),
 ('water_leakage','Water Leakage',25,'dept-water'),('streetlight','Streetlight',20,'dept-electrical'),
 ('drainage','Drainage',28,'dept-drainage');
INSERT OR IGNORE INTO staff(id,name,department_id) VALUES
 ('s1','Ramesh Verma (Civil)','dept-roads'),('s2','Sunita Patel (Sanitation)','dept-sanitation'),
 ('s3','Anil Sharma (Water)','dept-water'),('s4','Vikram Singh (Electrical)','dept-electrical'),
 ('s5','Deepak Nair (Drainage)','dept-drainage');
