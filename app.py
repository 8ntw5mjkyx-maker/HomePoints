from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import uuid
from datetime import datetime, date, timedelta
import calendar

app = Flask(__name__)
app.secret_key = 'homepoints-secret-key-change-this-later'
DB = 'homepoints.db'

SUGGESTED_TASKS = [
    {"id": "cook_dinner",       "title": "Cook dinner",        "icon": "🍳", "points": 25, "desc": "~45 min"},
    {"id": "wash_dishes",       "title": "Wash dishes",        "icon": "🍽️", "points": 15, "desc": "~20 min"},
    {"id": "grocery_shopping",  "title": "Grocery shopping",   "icon": "🛒", "points": 30, "desc": "~60 min"},
    {"id": "vacuum",            "title": "Vacuum floors",      "icon": "🧹", "points": 20, "desc": "~30 min"},
    {"id": "mop",               "title": "Mop floors",         "icon": "🫧", "points": 20, "desc": "~30 min"},
    {"id": "clean_bathroom",    "title": "Clean bathroom",     "icon": "🚿", "points": 25, "desc": "~30 min"},
    {"id": "clean_toilet",      "title": "Clean toilet",       "icon": "🚽", "points": 15, "desc": "~15 min"},
    {"id": "laundry",           "title": "Do laundry",         "icon": "👕", "points": 20, "desc": "~20 min"},
    {"id": "fold_laundry",      "title": "Fold & put away",    "icon": "🧺", "points": 15, "desc": "~20 min"},
    {"id": "trash",             "title": "Take out trash",     "icon": "🗑️", "points": 10, "desc": "~5 min"},
    {"id": "wipe_kitchen",      "title": "Wipe kitchen down",  "icon": "✨", "points": 10, "desc": "~10 min"},
    {"id": "clean_fridge",      "title": "Clean fridge",       "icon": "🧊", "points": 25, "desc": "~30 min"},
    {"id": "wash_windows",      "title": "Wash windows",       "icon": "🪟", "points": 20, "desc": "~30 min"},
    {"id": "water_plants",      "title": "Water plants",       "icon": "🌱", "points": 5,  "desc": "~5 min"},
    {"id": "bed_sheets",        "title": "Change bed sheets",  "icon": "🛏️", "points": 20, "desc": "~20 min"},
    {"id": "tidy_living",       "title": "Tidy living room",   "icon": "🛋️", "points": 15, "desc": "~15 min"},
    {"id": "breakfast",         "title": "Cook breakfast",     "icon": "🥞", "points": 15, "desc": "~20 min"},
    {"id": "meal_prep",         "title": "Meal prep",          "icon": "🥗", "points": 35, "desc": "~60 min"},
    {"id": "order_groceries",   "title": "Order groceries",    "icon": "📦", "points": 15, "desc": "~15 min"},
    {"id": "unpack_dishwasher", "title": "Unpack dishwasher",  "icon": "🍶", "points": 10, "desc": "~10 min"},
    {"id": "scrub_shower",      "title": "Scrub shower",       "icon": "🧽", "points": 20, "desc": "~20 min"},
    {"id": "wipe_sink",         "title": "Wipe bathroom sink", "icon": "🪥", "points": 8,  "desc": "~5 min"},
    {"id": "change_bins",       "title": "Change bin bags",    "icon": "🗑️", "points": 8,  "desc": "~5 min"},
    {"id": "clean_microwave",   "title": "Clean microwave",    "icon": "📡", "points": 10, "desc": "~10 min"},
    {"id": "hoover_stairs",     "title": "Hoover stairs",      "icon": "🪜", "points": 10, "desc": "~10 min"},
]

TASK_ICONS = [
    "🍳","🍽️","🛒","🧹","🫧","🚿","🚽","👕","🧺","🗑️",
    "✨","🧊","🪟","🌱","🛏️","📦","🥞","🧽","🪣","🛁",
    "🪴","🌿","🍀","⭐","💪","🏠","🔑","🪥","🧴","🛋️",
    "🖼️","🎵","📚","🍕","🥗","🍜","🧁","☕","🍵","🎮",
    "🎯","🎨","🏋️","🚴","🍶","📡","🪜","🧽","🥦","🍎",
]

AVATAR_SKINS = ["#FFDBAC","#F1C27D","#E8BEAC","#C68642","#8D5524","#4A2912"]
AVATAR_HAIRS = ["#2C1810","#8B4513","#DAA520","#FF6B35","#DC143C","#4B0082","#1a1a2e","#FF69B4","#00CED1","#A0A0A0"]
AVATAR_TOPS  = ["#7c6ff7","#34d399","#f472b6","#fbbf24","#60a5fa","#f87171","#a78bfa","#fb923c"]

FREQUENCY_OPTIONS = [
    {"value": "once",      "label": "Once"},
    {"value": "daily",     "label": "Every day"},
    {"value": "weekdays",  "label": "Weekdays only"},
    {"value": "2x_week",   "label": "Twice a week"},
    {"value": "3x_week",   "label": "Three times a week"},
    {"value": "weekly",    "label": "Once a week"},
    {"value": "biweekly",  "label": "Every 2 weeks"},
    {"value": "monthly",   "label": "Once a month"},
]

DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
GROCERY_CATEGORIES = [
    '🥦 Vegetables','🍎 Fruit','🥩 Meat & Fish','🧀 Dairy',
    '🥖 Bread & Bakery','🥫 Canned & Dry','🧃 Drinks',
    '🧹 Cleaning','🧴 Personal care','📦 Other'
]

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_db(conn):
    c = conn.cursor()
    existing = [row[1] for row in c.execute("PRAGMA table_info(tasks)").fetchall()]
    for col, sql in [
        ("icon",         "ALTER TABLE tasks ADD COLUMN icon TEXT DEFAULT '⭐'"),
        ("done_together","ALTER TABLE tasks ADD COLUMN done_together INTEGER DEFAULT 0"),
        ("frequency",    "ALTER TABLE tasks ADD COLUMN frequency TEXT DEFAULT 'once'"),
    ]:
        if col not in existing:
            c.execute(sql)
    u_existing = [row[1] for row in c.execute("PRAGMA table_info(users)").fetchall()]
    for col, sql in [
        ("avatar_skin",        "ALTER TABLE users ADD COLUMN avatar_skin INTEGER DEFAULT 0"),
        ("avatar_hair",        "ALTER TABLE users ADD COLUMN avatar_hair INTEGER DEFAULT 0"),
        ("avatar_top",         "ALTER TABLE users ADD COLUMN avatar_top INTEGER DEFAULT 0"),
        ("hidden_suggestions", "ALTER TABLE users ADD COLUMN hidden_suggestions TEXT DEFAULT ''"),
    ]:
        if col not in u_existing:
            c.execute(sql)
    conn.commit()

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        household_id TEXT,
        points INTEGER DEFAULT 0,
        avatar_skin INTEGER DEFAULT 0,
        avatar_hair INTEGER DEFAULT 0,
        avatar_top INTEGER DEFAULT 0,
        hidden_suggestions TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS households (
        id TEXT PRIMARY KEY, name TEXT NOT NULL,
        created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        household_id TEXT NOT NULL, title TEXT NOT NULL,
        icon TEXT DEFAULT '⭐', description TEXT, points INTEGER DEFAULT 10,
        task_type TEXT DEFAULT 'spontaneous', day_of_week TEXT,
        frequency TEXT DEFAULT 'once', assigned_to INTEGER,
        created_by INTEGER NOT NULL, completed_by INTEGER,
        completed_at TIMESTAMP, done_together INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        household_id TEXT NOT NULL, title TEXT NOT NULL,
        description TEXT, points_cost INTEGER DEFAULT 50,
        created_by INTEGER NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reward_id INTEGER NOT NULL, bought_by INTEGER NOT NULL,
        redeemed_by INTEGER, status TEXT DEFAULT 'pending',
        purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS grocery_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        household_id TEXT NOT NULL, name TEXT NOT NULL,
        quantity TEXT DEFAULT '1', category TEXT DEFAULT '📦 Other',
        checked INTEGER DEFAULT 0, added_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        household_id TEXT NOT NULL, title TEXT NOT NULL,
        url TEXT, notes TEXT, added_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS monthly_bonuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        household_id TEXT NOT NULL, user_id INTEGER NOT NULL,
        month TEXT NOT NULL, bonus_points INTEGER DEFAULT 50,
        awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    migrate_db(conn)
    conn.close()

with app.app_context():
    init_db()
app.jinja_env.globals["enumerate"] = enumerate

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' not in session: return None
    conn = get_db()
    u = conn.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone()
    conn.close()
    return u

def get_household_members(hid):
    conn = get_db()
    m = conn.execute('SELECT * FROM users WHERE household_id=?',(hid,)).fetchall()
    conn.close()
    return m

def get_hidden_suggestions(user):
    try:
        h = user['hidden_suggestions'] or ''
        return set(h.split(',')) if h else set()
    except: return set()

def check_monthly_bonus(hid):
    now = datetime.now()
    if now.day != 1: return
    month_str = now.strftime('%Y-%m')
    conn = get_db()
    if conn.execute('SELECT * FROM monthly_bonuses WHERE household_id=? AND month=?',(hid,month_str)).fetchone():
        conn.close(); return
    last = (now.replace(day=1)-timedelta(days=1)).strftime('%Y-%m')
    winner = conn.execute('''SELECT completed_by, COUNT(*) as cnt FROM tasks
        WHERE household_id=? AND status="done" AND strftime("%Y-%m",completed_at)=?
        GROUP BY completed_by ORDER BY cnt DESC LIMIT 1''',(hid,last)).fetchone()
    if winner and winner['completed_by']:
        conn.execute('UPDATE users SET points=points+50 WHERE id=?',(winner['completed_by'],))
        conn.execute('INSERT INTO monthly_bonuses (household_id,user_id,month,bonus_points) VALUES (?,?,?,50)',
                     (hid,winner['completed_by'],month_str))
        conn.commit()
    conn.close()

@app.context_processor
def inject_globals():
    return dict(user=get_current_user(), avatar_skins=AVATAR_SKINS,
                avatar_hairs=AVATAR_HAIRS, avatar_tops=AVATAR_TOPS)

# ── Auth ──────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        u = conn.execute('SELECT * FROM users WHERE username=? AND password=?',
            (request.form['username'].strip(), hash_password(request.form['password']))).fetchone()
        conn.close()
        if u: session['user_id'] = u['id']; return redirect(url_for('dashboard'))
        flash('Wrong username or password.','error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (username,password) VALUES (?,?)',
                (request.form['username'].strip(), hash_password(request.form['password'])))
            conn.commit()
            u = conn.execute('SELECT * FROM users WHERE username=?',(request.form['username'].strip(),)).fetchone()
            session['user_id'] = u['id']; conn.close()
            return redirect(url_for('household_setup'))
        except sqlite3.IntegrityError:
            conn.close(); flash('Username taken.','error')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

# ── Avatar ────────────────────────────────────────────────────
@app.route('/avatar', methods=['GET','POST'])
@login_required
def avatar():
    user = get_current_user()
    if request.method == 'POST':
        conn = get_db()
        conn.execute('UPDATE users SET avatar_skin=?,avatar_hair=?,avatar_top=? WHERE id=?',
            (int(request.form.get('skin',0)), int(request.form.get('hair',0)),
             int(request.form.get('top',0)), user['id']))
        conn.commit(); conn.close()
        flash('Avatar updated! ✨','success')
        return redirect(url_for('dashboard'))
    return render_template('avatar.html', user=user)

# ── Household ─────────────────────────────────────────────────
@app.route('/household', methods=['GET','POST'])
@login_required
def household_setup():
    user = get_current_user()
    if request.method == 'POST':
        conn = get_db()
        if request.form.get('action') == 'create':
            hid = str(uuid.uuid4())[:8].upper()
            conn.execute('INSERT INTO households (id,name,created_by) VALUES (?,?,?)',
                (hid, request.form['household_name'].strip(), user['id']))
            conn.execute('UPDATE users SET household_id=? WHERE id=?',(hid,user['id']))
            conn.commit(); conn.close()
            flash(f'Household created! Code: {hid}','success')
            return redirect(url_for('dashboard'))
        else:
            hid = request.form['household_code'].strip().upper()
            h = conn.execute('SELECT * FROM households WHERE id=?',(hid,)).fetchone()
            if h:
                conn.execute('UPDATE users SET household_id=? WHERE id=?',(hid,user['id']))
                conn.commit(); conn.close()
                flash(f'Joined {h["name"]}!','success')
                return redirect(url_for('dashboard'))
            conn.close(); flash('Code not found.','error')
    return render_template('household.html', user=user)

# ── Dashboard ─────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    if not user['household_id']: return redirect(url_for('household_setup'))
    check_monthly_bonus(user['household_id'])
    conn = get_db()
    household = conn.execute('SELECT * FROM households WHERE id=?',(user['household_id'],)).fetchone()
    members = get_household_members(user['household_id'])
    today = date.today().strftime('%A')
    today_tasks = conn.execute('''SELECT * FROM tasks WHERE household_id=? AND status="pending"
        AND (day_of_week=? OR task_type="spontaneous")
        ORDER BY task_type DESC, created_at DESC LIMIT 10''',(user['household_id'],today)).fetchall()
    week_tasks = conn.execute('''SELECT * FROM tasks WHERE household_id=? AND status="pending"
        AND task_type="planned" ORDER BY
        CASE day_of_week WHEN "Monday" THEN 1 WHEN "Tuesday" THEN 2 WHEN "Wednesday" THEN 3
        WHEN "Thursday" THEN 4 WHEN "Friday" THEN 5 WHEN "Saturday" THEN 6 WHEN "Sunday" THEN 7 END''',
        (user['household_id'],)).fetchall()
    month_str = datetime.now().strftime('%Y-%m')
    monthly_stats = []
    for m in members:
        row = conn.execute('''SELECT COUNT(*) as cnt, COALESCE(SUM(points),0) as pts FROM tasks
            WHERE completed_by=? AND status="done" AND strftime("%Y-%m",completed_at)=?''',
            (m['id'],month_str)).fetchone()
        monthly_stats.append({'member':dict(m),'tasks':row['cnt'],'points':row['pts']})
    monthly_stats.sort(key=lambda x: x['points'], reverse=True)
    last_bonus = conn.execute('''SELECT monthly_bonuses.*, users.username FROM monthly_bonuses
        JOIN users ON monthly_bonuses.user_id=users.id
        WHERE monthly_bonuses.household_id=? ORDER BY awarded_at DESC LIMIT 1''',(user['household_id'],)).fetchone()
    conn.close()
    return render_template('dashboard.html', user=user, household=household, members=members,
        today_tasks=today_tasks, week_tasks=week_tasks, monthly_stats=monthly_stats,
        last_bonus=last_bonus, today=today)

# ── Tasks ─────────────────────────────────────────────────────
@app.route('/tasks')
@login_required
def tasks():
    user = get_current_user()
    view = request.args.get('view','week')
    conn = get_db()
    members = get_household_members(user['household_id'])
    planned = {}
    for day in DAYS:
        planned[day] = conn.execute('''SELECT * FROM tasks WHERE household_id=? AND task_type="planned"
            AND day_of_week=? AND status="pending" ORDER BY title''',(user['household_id'],day)).fetchall()
    spontaneous = conn.execute('''SELECT * FROM tasks WHERE household_id=? AND task_type="spontaneous"
        AND status="pending" ORDER BY created_at DESC''',(user['household_id'],)).fetchall()
    conn.close()
    hidden = get_hidden_suggestions(user)
    visible_suggested = [s for s in SUGGESTED_TASKS if s['id'] not in hidden]
    today = date.today()
    return render_template('tasks.html', user=user, planned=planned, spontaneous=spontaneous,
        days=DAYS, members=members, suggested=visible_suggested, all_suggested_count=len(SUGGESTED_TASKS),
        icons=TASK_ICONS, now=datetime.now(), view=view, frequencies=FREQUENCY_OPTIONS,
        today=today, current_month=today.strftime('%B %Y'),
        month_days=calendar.monthcalendar(today.year, today.month))

@app.route('/tasks/hide-suggested', methods=['POST'])
@login_required
def hide_suggested():
    user = get_current_user()
    hidden = get_hidden_suggestions(user)
    hidden.add(request.form.get('sug_id',''))
    conn = get_db()
    conn.execute('UPDATE users SET hidden_suggestions=? WHERE id=?',(','.join(hidden),user['id']))
    conn.commit(); conn.close()
    return redirect(url_for('tasks'))

@app.route('/tasks/reset-suggested', methods=['POST'])
@login_required
def reset_suggested():
    conn = get_db()
    conn.execute("UPDATE users SET hidden_suggestions='' WHERE id=?",(session['user_id'],))
    conn.commit(); conn.close()
    flash('Suggestions reset!','success')
    return redirect(url_for('tasks'))

@app.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    user = get_current_user()
    task_type = request.form.get('task_type','spontaneous')
    conn = get_db()
    conn.execute('''INSERT INTO tasks (household_id,title,icon,description,points,task_type,
        day_of_week,frequency,assigned_to,created_by) VALUES (?,?,?,?,?,?,?,?,?,?)''',
        (user['household_id'], request.form['title'].strip(),
         request.form.get('icon','⭐'), request.form.get('description','').strip(),
         int(request.form.get('points',10)), task_type,
         request.form.get('day_of_week') if task_type=='planned' else None,
         request.form.get('frequency','once'), request.form.get('assigned_to') or None, user['id']))
    conn.commit(); conn.close()
    flash(f'{request.form.get("icon","⭐")} "{request.form["title"]}" added!','success')
    return redirect(url_for('tasks'))

@app.route('/tasks/add-suggested', methods=['POST'])
@login_required
def add_suggested_task():
    user = get_current_user()
    task_type = request.form.get('task_type','spontaneous')
    conn = get_db()
    conn.execute('''INSERT INTO tasks (household_id,title,icon,points,task_type,day_of_week,frequency,created_by)
        VALUES (?,?,?,?,?,?,?,?)''',
        (user['household_id'], request.form['title'], request.form.get('icon','⭐'),
         int(request.form.get('points',10)), task_type,
         request.form.get('day_of_week') if task_type=='planned' else None,
         request.form.get('frequency','once'), user['id']))
    conn.commit(); conn.close()
    flash(f'{request.form.get("icon","⭐")} "{request.form["title"]}" added!','success')
    return redirect(url_for('tasks'))

@app.route('/tasks/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    user = get_current_user()
    together = request.form.get('together') == 'yes'
    conn = get_db()
    task = conn.execute('SELECT * FROM tasks WHERE id=? AND household_id=?',(task_id,user['household_id'])).fetchone()
    if task and task['status']=='pending':
        pts = task['points'] * 2 if together else task['points']
        conn.execute('UPDATE tasks SET status="done",completed_by=?,completed_at=?,done_together=? WHERE id=?',
                     (user['id'],datetime.now(),1 if together else 0,task_id))
        conn.execute('UPDATE users SET points=points+? WHERE id=?',(pts,user['id']))
        if together:
            for o in conn.execute('SELECT * FROM users WHERE household_id=? AND id!=?',(user['household_id'],user['id'])).fetchall():
                conn.execute('UPDATE users SET points=points+? WHERE id=?',(pts,o['id']))
            flash(f'Together! Everyone got +{pts} pts! 🎉','success')
        else:
            flash(f'+{pts} pts! ⭐','success')
        conn.commit()
    conn.close()
    return redirect(request.referrer or url_for('tasks'))

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    user = get_current_user()
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE id=? AND household_id=?',(task_id,user['household_id']))
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for('tasks'))

# ── Stats ─────────────────────────────────────────────────────
@app.route('/stats')
@login_required
def stats():
    user = get_current_user()
    conn = get_db()
    members = get_household_members(user['household_id'])
    all_task_titles = conn.execute('''SELECT DISTINCT title FROM tasks
        WHERE household_id=? AND status="done" ORDER BY title''',(user['household_id'],)).fetchall()
    conn.close()
    return render_template('stats.html', user=user, members=members, all_task_titles=all_task_titles)

@app.route('/stats/data')
@login_required
def stats_data():
    user = get_current_user()
    task_filter = request.args.get('task','')
    period = request.args.get('period','month')
    conn = get_db()
    members = get_household_members(user['household_id'])
    date_filter = {'week':(date.today()-timedelta(days=7)).isoformat(),
                   'month':date.today().replace(day=1).isoformat(),
                   'all':'2000-01-01'}.get(period,'2000-01-01')
    result = []
    for m in members:
        q = 'SELECT COUNT(*) as cnt, COALESCE(SUM(points),0) as pts FROM tasks WHERE completed_by=? AND status="done" AND completed_at>=?'
        params = [m['id'],date_filter]
        if task_filter: q += ' AND title=?'; params.append(task_filter)
        row = conn.execute(q,params).fetchone()
        weekly = []
        for i in range(6,-1,-1):
            d = (date.today()-timedelta(days=i)).isoformat()
            q2 = 'SELECT COUNT(*) as cnt FROM tasks WHERE completed_by=? AND status="done" AND date(completed_at)=?'
            p2 = [m['id'],d]
            if task_filter: q2 += ' AND title=?'; p2.append(task_filter)
            wd = conn.execute(q2,p2).fetchone()
            weekly.append({'date':d,'count':wd['cnt']})
        result.append({'name':m['username'],'tasks':row['cnt'],'points':row['pts'],'weekly':weekly})
    conn.close()
    return jsonify(result)

# ── Shop ──────────────────────────────────────────────────────
@app.route('/shop')
@login_required
def shop():
    user = get_current_user()
    conn = get_db()
    rewards = conn.execute('''SELECT rewards.*, users.username as creator_name FROM rewards
        LEFT JOIN users ON rewards.created_by=users.id
        WHERE rewards.household_id=? ORDER BY rewards.points_cost''',(user['household_id'],)).fetchall()
    my_purchases = conn.execute('''SELECT purchases.*, rewards.title as reward_title, rewards.points_cost
        FROM purchases JOIN rewards ON purchases.reward_id=rewards.id
        WHERE purchases.bought_by=? ORDER BY purchases.purchased_at DESC''',(user['id'],)).fetchall()
    owed_to_me = conn.execute('''SELECT purchases.*, rewards.title as reward_title, users.username as buyer_name
        FROM purchases JOIN rewards ON purchases.reward_id=rewards.id
        JOIN users ON purchases.bought_by=users.id
        WHERE purchases.redeemed_by=? AND purchases.status="pending"''',(user['id'],)).fetchall()
    conn.close()
    return render_template('shop.html', user=user, rewards=rewards, my_purchases=my_purchases, owed_to_me=owed_to_me)

@app.route('/shop/add', methods=['POST'])
@login_required
def add_reward():
    user = get_current_user()
    conn = get_db()
    conn.execute('INSERT INTO rewards (household_id,title,description,points_cost,created_by) VALUES (?,?,?,?,?)',
        (user['household_id'],request.form['title'].strip(),request.form.get('description','').strip(),
         int(request.form.get('points_cost',50)),user['id']))
    conn.commit(); conn.close(); flash('Reward added!','success')
    return redirect(url_for('shop'))

@app.route('/shop/buy/<int:reward_id>', methods=['POST'])
@login_required
def buy_reward(reward_id):
    user = get_current_user()
    conn = get_db()
    reward = conn.execute('SELECT * FROM rewards WHERE id=? AND household_id=?',(reward_id,user['household_id'])).fetchone()
    if not reward: flash('Not found.','error'); conn.close(); return redirect(url_for('shop'))
    if user['points'] < reward['points_cost']:
        flash(f'Need {reward["points_cost"]} pts!','error'); conn.close(); return redirect(url_for('shop'))
    others = conn.execute('SELECT * FROM users WHERE household_id=? AND id!=?',(user['household_id'],user['id'])).fetchall()
    redeemed_by = others[0]['id'] if others else user['id']
    conn.execute('INSERT INTO purchases (reward_id,bought_by,redeemed_by) VALUES (?,?,?)',(reward_id,user['id'],redeemed_by))
    conn.execute('UPDATE users SET points=points-? WHERE id=?',(reward['points_cost'],user['id']))
    conn.commit(); conn.close(); flash(f'Bought "{reward["title"]}"! 🎉','success')
    return redirect(url_for('shop'))

@app.route('/shop/fulfill/<int:purchase_id>', methods=['POST'])
@login_required
def fulfill_purchase(purchase_id):
    conn = get_db()
    conn.execute('UPDATE purchases SET status="fulfilled" WHERE id=? AND redeemed_by=?',(purchase_id,session['user_id']))
    conn.commit(); conn.close(); flash('Fulfilled!','success')
    return redirect(url_for('shop'))

# ── Groceries ─────────────────────────────────────────────────
@app.route('/groceries')
@login_required
def groceries():
    user = get_current_user()
    conn = get_db()
    items = conn.execute('''SELECT grocery_items.*, users.username as added_by_name
        FROM grocery_items LEFT JOIN users ON grocery_items.added_by=users.id
        WHERE grocery_items.household_id=?
        ORDER BY grocery_items.checked, grocery_items.category, grocery_items.created_at''',(user['household_id'],)).fetchall()
    conn.close()
    grouped = {}
    for item in items:
        cat = item['category']
        if cat not in grouped: grouped[cat] = []
        grouped[cat].append(item)
    return render_template('groceries.html', user=user, grouped=grouped, categories=GROCERY_CATEGORIES)

@app.route('/groceries/add', methods=['POST'])
@login_required
def add_grocery():
    user = get_current_user()
    conn = get_db()
    conn.execute('INSERT INTO grocery_items (household_id,name,quantity,category,added_by) VALUES (?,?,?,?,?)',
        (user['household_id'],request.form['name'].strip(),request.form.get('quantity','1'),
         request.form.get('category','📦 Other'),user['id']))
    conn.commit(); conn.close()
    return redirect(url_for('groceries'))

@app.route('/groceries/check/<int:item_id>', methods=['POST'])
@login_required
def check_grocery(item_id):
    conn = get_db()
    item = conn.execute('SELECT * FROM grocery_items WHERE id=?',(item_id,)).fetchone()
    if item:
        conn.execute('UPDATE grocery_items SET checked=? WHERE id=?',(0 if item['checked'] else 1,item_id))
        conn.commit()
    conn.close()
    return redirect(url_for('groceries'))

@app.route('/groceries/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_grocery(item_id):
    user = get_current_user()
    conn = get_db()
    conn.execute('DELETE FROM grocery_items WHERE id=? AND household_id=?',(item_id,user['household_id']))
    conn.commit(); conn.close()
    return redirect(url_for('groceries'))

@app.route('/groceries/clear-checked', methods=['POST'])
@login_required
def clear_checked_groceries():
    user = get_current_user()
    conn = get_db()
    conn.execute('DELETE FROM grocery_items WHERE household_id=? AND checked=1',(user['household_id'],))
    conn.commit(); conn.close()
    return redirect(url_for('groceries'))

# ── Recipes ───────────────────────────────────────────────────
@app.route('/recipes')
@login_required
def recipes():
    user = get_current_user()
    conn = get_db()
    recs = conn.execute('''SELECT recipes.*, users.username as added_by_name
        FROM recipes LEFT JOIN users ON recipes.added_by=users.id
        WHERE recipes.household_id=? ORDER BY recipes.created_at DESC''',(user['household_id'],)).fetchall()
    conn.close()
    return render_template('recipes.html', user=user, recipes=recs)

@app.route('/recipes/add', methods=['POST'])
@login_required
def add_recipe():
    user = get_current_user()
    conn = get_db()
    conn.execute('INSERT INTO recipes (household_id,title,url,notes,added_by) VALUES (?,?,?,?,?)',
        (user['household_id'],request.form['title'].strip(),
         request.form.get('url','').strip(),request.form.get('notes','').strip(),user['id']))
    conn.commit(); conn.close(); flash('Recipe added! 🍽️','success')
    return redirect(url_for('recipes'))

@app.route('/recipes/delete/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    user = get_current_user()
    conn = get_db()
    conn.execute('DELETE FROM recipes WHERE id=? AND household_id=?',(recipe_id,user['household_id']))
    conn.commit(); conn.close()
    return redirect(url_for('recipes'))

# ── Wheel ─────────────────────────────────────────────────────
@app.route('/wheel')
@login_required
def wheel():
    user = get_current_user()
    conn = get_db()
    pending = conn.execute('SELECT * FROM tasks WHERE household_id=? AND status="pending" ORDER BY RANDOM() LIMIT 20',(user['household_id'],)).fetchall()
    members = get_household_members(user['household_id'])
    conn.close()
    return render_template('wheel.html', user=user, pending_tasks=pending, members=members)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
