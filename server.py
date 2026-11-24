"""CivicPulse server - sirf Python standard library (pip install ki zaroorat nahi).
Chalane ke liye:  python server.py   ->  http://localhost:3000
Database: civicpulse.db (SQLite), tables schema.sql se banti hain."""
import http.server, sqlite3, json, os, hashlib, secrets, mimetypes

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'civicpulse.db')
PORT = int(os.environ.get('PORT', 3000))
BLOCKED = {'civicpulse.db', 'server.py', 'schema.sql'}

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys = ON')
    return c

def hp(pw, salt):
    return hashlib.sha256((salt + pw).encode()).hexdigest()

def migrate(c):  # purani database mein staff login columns jodta hai
    cols = [r[1] for r in c.execute('PRAGMA table_info(staff)')]
    if cols:
        for col in ('username', 'password_hash', 'salt'):
            if col not in cols:
                c.execute(f'ALTER TABLE staff ADD COLUMN {col} TEXT')
        c.commit()

STAFF_USERS = {'s1': 'ramesh', 's2': 'sunita', 's3': 'anil', 's4': 'vikram', 's5': 'deepak'}

def init_db():
    c = conn()
    migrate(c)
    with open(os.path.join(ROOT, 'schema.sql'), encoding='utf-8') as f:
        c.executescript(f.read())
    if not c.execute("SELECT 1 FROM admins WHERE username='admin'").fetchone():
        salt = secrets.token_hex(8)
        c.execute('INSERT INTO admins(username,password_hash,salt) VALUES(?,?,?)', ('admin', hp('ROHIT', salt), salt))
    for sid, un in STAFF_USERS.items():
        r = c.execute('SELECT password_hash FROM staff WHERE id=?', (sid,)).fetchone()
        if r and not r[0]:
            salt = secrets.token_hex(8)
            c.execute('UPDATE staff SET username=?,password_hash=?,salt=? WHERE id=?', (un, hp('STAFF123', salt), salt, sid))
    c.commit()
    return c

def counts(c):
    names = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    return {n: c.execute(f'SELECT COUNT(*) FROM {n}').fetchone()[0] for n in names}

def to_js(r):
    return {'id': r['id'], 'title': r['title'], 'category': r['category_id'], 'description': r['description'],
            'x': r['x'], 'y': r['y'], 'lat': r['lat'], 'lng': r['lng'], 'route': r['route'], 'status': r['status'],
            'staffId': r['staff_id'] or '', 'phone': r['phone'] or '', 'createdAt': r['created_at'], 'dup': r['dup'],
            'risk': r['risk'], 'override': r['priority_override'], 'note': r['admin_note'] or '',
            'staffNote': r['staff_note'] or '', 'photo': r['photo'], 'after': r['after_photo'],
            'fb': {'r': r['fb_rating'], 'c': r['fb_comment'] or ''} if r['fb_rating'] else None}

COLS = ['id','title','category_id','description','x','y','lat','lng','route','status','staff_id','phone','created_at',
        'dup','risk','priority_override','admin_note','staff_note','photo','after_photo','fb_rating','fb_comment']
UPSERT = (f"INSERT INTO complaints({','.join(COLS)}) VALUES({','.join(':'+k for k in COLS)}) "
          f"ON CONFLICT(id) DO UPDATE SET {','.join(f'{k}=excluded.{k}' for k in COLS if k != 'id')}, updated_at=datetime('now')")

def put_all(c, arr):
    for d in arr:
        phone = d.get('phone') or None
        if phone:
            c.execute('INSERT OR IGNORE INTO users(phone) VALUES(?)', (phone,))
        old = c.execute('SELECT status FROM complaints WHERE id=?', (d['id'],)).fetchone()
        fb = d.get('fb') or {}
        row = {'id': d['id'], 'title': d['title'], 'category_id': d['category'], 'description': d['description'],
               'x': d.get('x'), 'y': d.get('y'), 'lat': d.get('lat'), 'lng': d.get('lng'), 'route': d.get('route'),
               'status': d.get('status', 'Open'), 'staff_id': d.get('staffId') or None, 'phone': phone,
               'created_at': d.get('createdAt'), 'dup': d.get('dup', 0), 'risk': d.get('risk', 20),
               'priority_override': d.get('override'), 'admin_note': d.get('note', ''),
               'staff_note': d.get('staffNote', ''), 'photo': d.get('photo'), 'after_photo': d.get('after'),
               'fb_rating': fb.get('r'), 'fb_comment': fb.get('c')}
        c.execute(UPSERT, row)
        if old is None:
            c.execute('INSERT INTO complaint_history(complaint_id,status,changed_by,note) VALUES(?,?,?,?)',
                      (d['id'], row['status'], phone or 'system', 'Complaint registered'))
        elif old['status'] != row['status']:
            c.execute('INSERT INTO complaint_history(complaint_id,status,changed_by,note) VALUES(?,?,?,?)',
                      (d['id'], row['status'], row['staff_id'] or 'admin', f"{old['status']} -> {row['status']}"))
    ids = [d['id'] for d in arr]
    c.execute(f"DELETE FROM complaints WHERE id NOT IN ({','.join('?' * len(ids))})", ids)
    c.commit()

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def js(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def body(self):
        n = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(n) or b'null')

    def do_GET(self):
        u = self.path.split('?')[0]
        if u == '/api/health':
            c = conn(); t = counts(c); c.close()
            return self.js(200, {'server': 'ok', 'database': 'ok', 'engine': 'SQLite', 'tables': t})
        if u == '/api/db':
            c = conn(); rows = [to_js(r) for r in c.execute('SELECT * FROM complaints ORDER BY created_at DESC')]; c.close()
            return self.js(200, rows)
        if u.startswith('/api/history/'):
            c = conn()
            rows = [dict(r) for r in c.execute('SELECT * FROM complaint_history WHERE complaint_id=? ORDER BY id', (u.split('/')[-1],))]
            c.close()
            return self.js(200, rows)
        name = 'login.html' if u == '/' else os.path.normpath(u.lstrip('/'))
        f = os.path.join(ROOT, name)
        if not f.startswith(ROOT) or os.path.basename(f) in BLOCKED or not os.path.isfile(f):
            return self.js(404, {'error': 'not found'})
        data = open(f, 'rb').read()
        self.send_response(200)
        self.send_header('Content-Type', (mimetypes.guess_type(f)[0] or 'application/octet-stream') + ('; charset=utf-8' if f.endswith(('.html', '.css', '.js')) else ''))
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_PUT(self):
        if self.path.split('?')[0] != '/api/db':
            return self.js(404, {'error': 'not found'})
        try:
            arr = self.body()
            assert isinstance(arr, list)
            c = conn(); put_all(c, arr); c.close()
            print('💾 Database updated:', len(arr), 'complaints')
            self.js(200, {'saved': len(arr)})
        except Exception as e:
            self.js(400, {'error': str(e)})

    def do_POST(self):
        u = self.path.split('?')[0]
        try:
            d = self.body() or {}
            c = conn()
            if u == '/api/login-citizen':
                p = str(d.get('phone', ''))
                if not (len(p) == 10 and p.isdigit() and p[0] in '6789'):
                    c.close(); return self.js(400, {'error': 'invalid phone'})
                c.execute('INSERT OR IGNORE INTO users(phone,name) VALUES(?,?)', (p, d.get('name') or 'Citizen'))
                c.execute("UPDATE users SET last_login=datetime('now') WHERE phone=?", (p,))
                c.commit(); c.close()
                print('👤 Citizen login:', p)
                return self.js(200, {'ok': True})
            if u == '/api/login-admin':
                r = c.execute('SELECT * FROM admins WHERE username=?', (str(d.get('username', '')).lower(),)).fetchone()
                c.close()
                if r and secrets.compare_digest(r['password_hash'], hp(str(d.get('password', '')), r['salt'])):
                    print('🔐 Admin login OK')
                    return self.js(200, {'ok': True})
                return self.js(401, {'error': 'wrong credentials'})
            if u == '/api/login-staff':
                r = c.execute('SELECT * FROM staff WHERE username=?', (str(d.get('username', '')).lower(),)).fetchone()
                c.close()
                if r and r['password_hash'] and secrets.compare_digest(r['password_hash'], hp(str(d.get('password', '')), r['salt'])):
                    print('🔧 Staff login OK:', r['name'])
                    return self.js(200, {'ok': True, 'staffId': r['id'], 'name': r['name']})
                return self.js(401, {'error': 'wrong credentials'})
            c.close()
            self.js(404, {'error': 'not found'})
        except Exception as e:
            self.js(400, {'error': str(e)})

if __name__ == '__main__':
    c = init_db(); t = counts(c); c.close()
    print(f'✅ Server connected   -> http://localhost:{PORT}')
    print(f'✅ Database connected -> {DB}')
    print(f'📊 Tables ({len(t)}): ' + ', '.join(f'{k}({v})' for k, v in t.items()))
    http.server.ThreadingHTTPServer(('0.0.0.0', PORT), H).serve_forever()
