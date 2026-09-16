import os, sqlite3, csv, io
from functools import wraps
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
app=Flask(__name__); app.secret_key=os.getenv('SECRET_KEY','dev')
app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE','false').lower()=='true')
DB=os.getenv('DATABASE_PATH','/data/p10.db')
def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
def init():
 os.makedirs(os.path.dirname(DB),exist_ok=True)
 with conn() as c: c.executescript("""
 CREATE TABLE IF NOT EXISTS players(id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE COLLATE NOCASE,color TEXT NOT NULL DEFAULT '#34d399',active INTEGER NOT NULL DEFAULT 1);
 CREATE TABLE IF NOT EXISTS notebooks(id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE COLLATE NOCASE,description TEXT DEFAULT '');
 CREATE TABLE IF NOT EXISTS games(id INTEGER PRIMARY KEY,notebook_id INTEGER REFERENCES notebooks(id),sequence_no INTEGER,page_no TEXT,played_date TEXT,date_accuracy TEXT DEFAULT 'unknown',status TEXT DEFAULT 'complete',entry_type TEXT DEFAULT 'final',notes TEXT DEFAULT '',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS game_players(id INTEGER PRIMARY KEY,game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,player_id INTEGER NOT NULL REFERENCES players(id),final_score INTEGER,final_phase INTEGER,result_status TEXT DEFAULT 'finished',UNIQUE(game_id,player_id));
 CREATE TABLE IF NOT EXISTS rounds(id INTEGER PRIMARY KEY,game_player_id INTEGER NOT NULL REFERENCES game_players(id) ON DELETE CASCADE,round_no INTEGER NOT NULL,score INTEGER NOT NULL,UNIQUE(game_player_id,round_no));
 CREATE INDEX IF NOT EXISTS ix_gp_player ON game_players(player_id);
 """)
init()
def auth(f):
 @wraps(f)
 def w(*a,**k): return f(*a,**k) if session.get('ok') else redirect(url_for('login',next=request.path))
 return w
def as_int(v):
 try: return int(v) if str(v).strip() else None
 except (ValueError,TypeError): return None
def parse_rounds(raw): return [int(x.strip()) for x in (raw or '').split(',') if x.strip()]
def save_game_players(c,gid,players,form):
 c.execute('DELETE FROM game_players WHERE game_id=?',(gid,))
 for p in players:
  pid=p['id']
  if form.get(f'use_{pid}'):
   try: vals=parse_rounds(form.get(f'rounds_{pid}'))
   except ValueError: raise ValueError(f"Round scores for {p['name']} must be comma-separated whole numbers.")
   final=as_int(form.get(f'score_{pid}')); final=final if final is not None else (sum(vals) if vals else None)
   gp=c.execute('INSERT INTO game_players(game_id,player_id,final_score,final_phase,result_status) VALUES(?,?,?,?,?)',(gid,pid,final,as_int(form.get(f'phase_{pid}')),form.get(f'result_{pid}','finished')))
   for i,v in enumerate(vals,1): c.execute('INSERT INTO rounds(game_player_id,round_no,score) VALUES(?,?,?)',(gp.lastrowid,i,v))
def game_context(c,gid=None):
 players=c.execute('SELECT * FROM players ORDER BY active DESC,name').fetchall(); notebooks=c.execute('SELECT * FROM notebooks ORDER BY name').fetchall(); selected={}; g=None
 if gid:
  g=c.execute('SELECT * FROM games WHERE id=?',(gid,)).fetchone()
  for r in c.execute("SELECT gp.*,(SELECT group_concat(score, ', ') FROM rounds WHERE game_player_id=gp.id ORDER BY round_no) rounds_text FROM game_players gp WHERE game_id=?",(gid,)): selected[r['player_id']]=dict(r)
 return players,notebooks,g,selected
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  if request.form.get('pin')==os.getenv('HOUSEHOLD_PIN','change-me'): session['ok']=1; return redirect(request.args.get('next') or '/')
  flash('Incorrect PIN','bad')
 return render_template('login.html')
@app.get('/logout')
def logout(): session.clear(); return redirect('/login')
@app.get('/')
@auth
def home():
 with conn() as c:
  counts=c.execute('SELECT (SELECT COUNT(*) FROM games) games,(SELECT COUNT(*) FROM players WHERE active=1) players,(SELECT COUNT(*) FROM notebooks) notebooks').fetchone()
  games=c.execute("SELECT g.*,n.name notebook,(SELECT COUNT(*) FROM game_players x WHERE x.game_id=g.id) player_count FROM games g LEFT JOIN notebooks n ON n.id=g.notebook_id ORDER BY COALESCE(g.played_date,'0000') DESC,g.id DESC LIMIT 15").fetchall()
 return render_template('home.html',counts=counts,games=games)
@app.route('/players',methods=['GET','POST'])
@auth
def players():
 with conn() as c:
  if request.method=='POST':
   try: c.execute('INSERT INTO players(name,color) VALUES(?,?)',(request.form['name'].strip(),request.form['color'])); c.commit(); flash('Player added')
   except sqlite3.IntegrityError: flash('Player already exists','bad')
   return redirect('/players')
  rows=c.execute('SELECT * FROM players ORDER BY active DESC,name').fetchall()
 return render_template('players.html',rows=rows)
@app.route('/players/<int:pid>/edit',methods=['GET','POST'])
@auth
def player_edit(pid):
 with conn() as c:
  p=c.execute('SELECT * FROM players WHERE id=?',(pid,)).fetchone()
  if not p: return ('Not found',404)
  if request.method=='POST':
   try: c.execute('UPDATE players SET name=?,color=?,active=? WHERE id=?',(request.form['name'].strip(),request.form['color'],1 if request.form.get('active') else 0,pid)); c.commit(); flash('Player updated'); return redirect('/players')
   except sqlite3.IntegrityError: flash('That player name is already in use','bad')
 return render_template('player_edit.html',p=p)
@app.post('/players/<int:pid>/toggle')
@auth
def toggle(pid):
 with conn() as c: c.execute('UPDATE players SET active=1-active WHERE id=?',(pid,)); c.commit()
 return redirect('/players')
@app.route('/notebooks',methods=['GET','POST'])
@auth
def notebooks():
 with conn() as c:
  if request.method=='POST':
   try: c.execute('INSERT INTO notebooks(name,description) VALUES(?,?)',(request.form['name'].strip(),request.form.get('description',''))); c.commit(); flash('Notebook added')
   except sqlite3.IntegrityError: flash('Notebook already exists','bad')
   return redirect('/notebooks')
  rows=c.execute('SELECT n.*,(SELECT COUNT(*) FROM games g WHERE g.notebook_id=n.id) game_count FROM notebooks n ORDER BY name').fetchall()
 return render_template('notebooks.html',rows=rows)
@app.route('/notebooks/<int:nid>/edit',methods=['GET','POST'])
@auth
def notebook_edit(nid):
 with conn() as c:
  n=c.execute('SELECT * FROM notebooks WHERE id=?',(nid,)).fetchone()
  if not n: return ('Not found',404)
  if request.method=='POST':
   try: c.execute('UPDATE notebooks SET name=?,description=? WHERE id=?',(request.form['name'].strip(),request.form.get('description',''),nid)); c.commit(); flash('Notebook updated'); return redirect('/notebooks')
   except sqlite3.IntegrityError: flash('That notebook name is already in use','bad')
 return render_template('notebook_edit.html',n=n)
@app.post('/notebooks/<int:nid>/delete')
@auth
def notebook_delete(nid):
 with conn() as c: c.execute('UPDATE games SET notebook_id=NULL WHERE notebook_id=?',(nid,)); c.execute('DELETE FROM notebooks WHERE id=?',(nid,)); c.commit()
 flash('Notebook deleted. Its games were kept under No notebook.'); return redirect('/notebooks')
@app.get('/api/notebooks/<int:nid>/next-sequence')
@auth
def next_sequence(nid):
 with conn() as c: value=c.execute('SELECT COALESCE(MAX(sequence_no),0)+1 FROM games WHERE notebook_id=?',(nid,)).fetchone()[0]
 return jsonify(next=value)
@app.route('/games/new',methods=['GET','POST'])
@auth
def game_new():
 with conn() as c:
  ps,ns,g,selected=game_context(c)
  if request.method=='POST':
   try:
    cur=c.execute('INSERT INTO games(notebook_id,sequence_no,page_no,played_date,date_accuracy,status,entry_type,notes) VALUES(?,?,?,?,?,?,?,?)',(request.form.get('notebook_id') or None,as_int(request.form.get('sequence_no')),request.form.get('page_no'),request.form.get('played_date') or None,request.form.get('date_accuracy'),request.form.get('status'),request.form.get('entry_type'),request.form.get('notes'))); save_game_players(c,cur.lastrowid,ps,request.form); c.commit(); return redirect(f'/games/{cur.lastrowid}')
   except ValueError as e: c.rollback(); flash(str(e),'bad')
 return render_template('game_form.html',players=ps,notebooks=ns,g=g,selected=selected,editing=False)
@app.route('/games/<int:gid>/edit',methods=['GET','POST'])
@auth
def game_edit(gid):
 with conn() as c:
  ps,ns,g,selected=game_context(c,gid)
  if not g: return ('Not found',404)
  if request.method=='POST':
   try:
    c.execute('UPDATE games SET notebook_id=?,sequence_no=?,page_no=?,played_date=?,date_accuracy=?,status=?,entry_type=?,notes=? WHERE id=?',(request.form.get('notebook_id') or None,as_int(request.form.get('sequence_no')),request.form.get('page_no'),request.form.get('played_date') or None,request.form.get('date_accuracy'),request.form.get('status'),request.form.get('entry_type'),request.form.get('notes'),gid)); save_game_players(c,gid,ps,request.form); c.commit(); flash('Game updated'); return redirect(f'/games/{gid}')
   except ValueError as e: c.rollback(); flash(str(e),'bad')
 return render_template('game_form.html',players=ps,notebooks=ns,g=g,selected=selected,editing=True)
@app.post('/games/<int:gid>/duplicate')
@auth
def game_duplicate(gid):
 with conn() as c:
  g=c.execute('SELECT * FROM games WHERE id=?',(gid,)).fetchone()
  if not g: return ('Not found',404)
  seq=c.execute('SELECT COALESCE(MAX(sequence_no),0)+1 FROM games WHERE notebook_id IS ?',(g['notebook_id'],)).fetchone()[0]
  ng=c.execute('INSERT INTO games(notebook_id,sequence_no,page_no,played_date,date_accuracy,status,entry_type,notes) VALUES(?,?,?,?,?,?,?,?)',(g['notebook_id'],seq,None,date.today().isoformat(),'exact','draft',g['entry_type'],'Duplicated from game '+str(gid)))
  for gp in c.execute('SELECT player_id FROM game_players WHERE game_id=?',(gid,)).fetchall(): c.execute("INSERT INTO game_players(game_id,player_id,result_status) VALUES(?,?,'finished')",(ng.lastrowid,gp['player_id']))
  c.commit(); flash('Game duplicated with blank scores'); return redirect(f'/games/{ng.lastrowid}/edit')
@app.get('/games/<int:gid>')
@auth
def game(gid):
 with conn() as c: g=c.execute('SELECT g.*,n.name notebook FROM games g LEFT JOIN notebooks n ON n.id=g.notebook_id WHERE g.id=?',(gid,)).fetchone(); rows=c.execute("SELECT gp.*,p.name,p.color,(SELECT group_concat(score,', ') FROM rounds r WHERE r.game_player_id=gp.id ORDER BY round_no) round_scores FROM game_players gp JOIN players p ON p.id=gp.player_id WHERE gp.game_id=? ORDER BY gp.final_score",(gid,)).fetchall()
 if not g:return ('Not found',404)
 return render_template('game.html',g=g,rows=rows)
@app.post('/games/<int:gid>/delete')
@auth
def game_delete(gid):
 with conn() as c: c.execute('DELETE FROM games WHERE id=?',(gid,)); c.commit()
 return redirect('/history')
@app.get('/history')
@auth
def history():
 with conn() as c: rows=c.execute("SELECT g.*,n.name notebook,group_concat(p.name,', ') players FROM games g LEFT JOIN notebooks n ON n.id=g.notebook_id LEFT JOIN game_players gp ON gp.game_id=g.id LEFT JOIN players p ON p.id=gp.player_id GROUP BY g.id ORDER BY n.name,COALESCE(g.sequence_no,999999),g.id").fetchall()
 return render_template('history.html',rows=rows)
def stats_data(c):
 leaders=c.execute("""SELECT p.id,p.name,p.color,COUNT(gp.id) games,ROUND(AVG(gp.final_score),1) avg_score,MIN(gp.final_score) low,MAX(gp.final_score) high,SUM(CASE WHEN gp.final_score=(SELECT MIN(x.final_score) FROM game_players x WHERE x.game_id=gp.game_id AND x.result_status='finished' AND x.final_score IS NOT NULL) THEN 1 ELSE 0 END) wins FROM players p LEFT JOIN game_players gp ON gp.player_id=p.id AND gp.result_status='finished' AND gp.final_score IS NOT NULL GROUP BY p.id HAVING games>0 ORDER BY avg_score""").fetchall()
 trend=[dict(x) for x in c.execute("SELECT g.id,COALESCE(g.played_date,'Unknown') label,p.name,p.color,gp.final_score FROM games g JOIN game_players gp ON gp.game_id=g.id JOIN players p ON p.id=gp.player_id WHERE g.status='complete' AND gp.result_status='finished' AND gp.final_score IS NOT NULL ORDER BY COALESCE(g.played_date,'9999'),g.id").fetchall()]
 recent=c.execute("SELECT g.id,g.played_date,n.name notebook,group_concat(p.name||' '||COALESCE(gp.final_score,'?'),', ') summary FROM games g LEFT JOIN notebooks n ON n.id=g.notebook_id JOIN game_players gp ON gp.game_id=g.id JOIN players p ON p.id=gp.player_id GROUP BY g.id ORDER BY g.id DESC LIMIT 5").fetchall()
 return leaders,trend,recent
@app.get('/stats')
@auth
def stats():
 with conn() as c: leaders,trend,recent=stats_data(c)
 return render_template('stats.html',leaders=leaders,trend=trend)
@app.get('/tv')
@auth
def tv():
 with conn() as c:
  leaders,trend,recent=stats_data(c)
  active=c.execute("SELECT * FROM live_games WHERE status IN ('lobby','active') ORDER BY id DESC LIMIT 1").fetchone()
  live_roster=[]; live_rounds=[]
  if active:
   live_roster=[dict(x) for x in c.execute("""SELECT lp.id,lp.active,lp.current_phase,p.name,p.color,upper(substr(p.name,1,1)) initial,
   COALESCE((SELECT SUM(COALESCE(s.approved_score,s.submitted_score)) FROM live_scores s WHERE s.live_player_id=lp.id AND s.status='approved'),0) total_score,
   (SELECT s.status FROM live_scores s WHERE s.live_player_id=lp.id AND s.live_game_id=lp.live_game_id AND s.round_no=active_round.round_no) score_status
   FROM live_players lp JOIN players p ON p.id=lp.player_id JOIN live_games active_round ON active_round.id=lp.live_game_id
   WHERE lp.live_game_id=? ORDER BY lp.active DESC,total_score,p.name""",(active['id'],)).fetchall()]
   live_rounds=[dict(x) for x in c.execute("""SELECT s.round_no,p.name,p.color,COALESCE(s.approved_score,s.submitted_score) score
   FROM live_scores s JOIN live_players lp ON lp.id=s.live_player_id JOIN players p ON p.id=lp.player_id
   WHERE s.live_game_id=? AND s.status='approved' ORDER BY s.round_no,p.name""",(active['id'],)).fetchall()]
  headtohead=c.execute("""SELECT a.name player1,b.name player2,
  SUM(CASE WHEN ga.final_score<gb.final_score THEN 1 ELSE 0 END) p1wins,
  SUM(CASE WHEN gb.final_score<ga.final_score THEN 1 ELSE 0 END) p2wins,
  COUNT(*) games
  FROM game_players ga JOIN game_players gb ON gb.game_id=ga.game_id AND ga.player_id<gb.player_id
  JOIN players a ON a.id=ga.player_id JOIN players b ON b.id=gb.player_id
  WHERE ga.result_status='finished' AND gb.result_status='finished' AND ga.final_score IS NOT NULL AND gb.final_score IS NOT NULL
  GROUP BY ga.player_id,gb.player_id ORDER BY games DESC LIMIT 1""").fetchone()
 return render_template('tv.html',leaders=leaders,trend=trend,recent=recent,active=active,live_roster=live_roster,live_rounds=live_rounds,headtohead=headtohead)

# === P10 TV DASHBOARD V2 PATCH ===
@app.get('/players/<int:pid>/stats')
@auth
def player_stats(pid):
 with conn() as c:
  p=c.execute('SELECT * FROM players WHERE id=?',(pid,)).fetchone(); s=c.execute("SELECT COUNT(*) played,SUM(result_status='finished') completed,SUM(result_status='dnf') dnfs,ROUND(AVG(CASE WHEN result_status='finished' THEN final_score END),1) avg_score,MIN(CASE WHEN result_status='finished' THEN final_score END) low,MAX(CASE WHEN result_status='finished' THEN final_score END) high,ROUND(AVG(CASE WHEN result_status='finished' THEN final_phase END),1) avg_phase FROM game_players WHERE player_id=?",(pid,)).fetchone(); trend=[dict(x) for x in c.execute("SELECT COALESCE(g.played_date,'Unknown') label,gp.final_score FROM game_players gp JOIN games g ON g.id=gp.game_id WHERE gp.player_id=? AND gp.result_status='finished' AND gp.final_score IS NOT NULL ORDER BY COALESCE(g.played_date,'9999'),g.id",(pid,)).fetchall()]
 return render_template('player_stats.html',p=p,s=s,trend=trend)
@app.get('/export.csv')
@auth
def export():
 with conn() as c: rows=c.execute("SELECT g.id,n.name notebook,g.sequence_no,g.page_no,g.played_date,g.date_accuracy,g.status,p.name player,gp.final_score,gp.final_phase,gp.result_status FROM games g LEFT JOIN notebooks n ON n.id=g.notebook_id JOIN game_players gp ON gp.game_id=g.id JOIN players p ON p.id=gp.player_id ORDER BY g.id,p.name").fetchall()
 out=io.StringIO(); w=csv.writer(out); w.writerow(rows[0].keys() if rows else ['game_id']); [w.writerow(tuple(r)) for r in rows]
 return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=p10-export.csv'})


# === P10 LIVE V2 PATCH ===
def live_init():
 with conn() as c: c.executescript("""
 CREATE TABLE IF NOT EXISTS live_games(id INTEGER PRIMARY KEY,code TEXT NOT NULL UNIQUE,status TEXT NOT NULL DEFAULT 'lobby',host_player_id INTEGER REFERENCES players(id),round_no INTEGER NOT NULL DEFAULT 1,created_at TEXT DEFAULT CURRENT_TIMESTAMP,ended_at TEXT);
 CREATE TABLE IF NOT EXISTS live_players(id INTEGER PRIMARY KEY,live_game_id INTEGER NOT NULL REFERENCES live_games(id) ON DELETE CASCADE,player_id INTEGER NOT NULL REFERENCES players(id),device_token TEXT,active INTEGER NOT NULL DEFAULT 1,current_phase INTEGER NOT NULL DEFAULT 1,UNIQUE(live_game_id,player_id));
 CREATE TABLE IF NOT EXISTS live_scores(id INTEGER PRIMARY KEY,live_game_id INTEGER NOT NULL REFERENCES live_games(id) ON DELETE CASCADE,round_no INTEGER NOT NULL,live_player_id INTEGER NOT NULL REFERENCES live_players(id) ON DELETE CASCADE,submitted_score INTEGER,approved_score INTEGER,phase_completed INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'pending',submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,reviewed_at TEXT,UNIQUE(live_game_id,round_no,live_player_id));
 """)
live_init()
def live_ux_migrate():
 with conn() as c:
  cols={r['name'] for r in c.execute('PRAGMA table_info(live_games)').fetchall()}
  if 'round_state' not in cols: c.execute("ALTER TABLE live_games ADD COLUMN round_state TEXT NOT NULL DEFAULT 'playing'")
live_ux_migrate()
def live_code():
 import secrets,string
 alphabet='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
 return ''.join(secrets.choice(alphabet) for _ in range(4))
def get_live(c,code): return c.execute('SELECT * FROM live_games WHERE code=?',(code.upper(),)).fetchone()
def live_roster(c,gid):
 return c.execute("""SELECT lp.*,p.name,p.color,upper(substr(p.name,1,1)) initial,
 (SELECT status FROM live_scores s WHERE s.live_game_id=lp.live_game_id AND s.round_no=(SELECT round_no FROM live_games WHERE id=lp.live_game_id) AND s.live_player_id=lp.id) score_status
 FROM live_players lp JOIN players p ON p.id=lp.player_id WHERE lp.live_game_id=? ORDER BY p.name""",(gid,)).fetchall()
@app.route('/live',methods=['GET','POST'])
@auth
def live_home():
 with conn() as c:
  players=c.execute('SELECT * FROM players WHERE active=1 ORDER BY name').fetchall()
  if request.method=='POST':
   chosen=[int(x) for x in request.form.getlist('players')]
   if len(chosen)<2: flash('Select at least two players','bad'); return render_template('live_home.html',players=players)
   host=as_int(request.form.get('host_player_id'))
   if host not in chosen: flash('Host must be a selected player','bad'); return render_template('live_home.html',players=players)
   code=live_code()
   while c.execute('SELECT 1 FROM live_games WHERE code=?',(code,)).fetchone(): code=live_code()
   g=c.execute('INSERT INTO live_games(code,host_player_id) VALUES(?,?)',(code,host))
   for pid in chosen: c.execute('INSERT INTO live_players(live_game_id,player_id) VALUES(?,?)',(g.lastrowid,pid))
   c.commit(); return redirect(f'/live/{code}/host')
  active=c.execute("SELECT lg.*,p.name host_name FROM live_games lg LEFT JOIN players p ON p.id=lg.host_player_id WHERE lg.status!='ended' ORDER BY lg.id DESC").fetchall()
 return render_template('live_home.html',players=players,active=active)
@app.route('/live/join',methods=['GET','POST'])
@auth
def live_join():
 code=(request.form.get('code') or request.args.get('code') or '').upper()
 if request.method=='POST' and code:
  with conn() as c:
   g=get_live(c,code)
   if not g: flash('Game code not found','bad')
   else: return render_template('live_join.html',g=g,roster=live_roster(c,g['id']))
 return render_template('live_join.html',g=None,roster=[])
@app.post('/live/<code>/claim/<int:lpid>')
@auth
def live_claim(code,lpid):
 import secrets
 token=secrets.token_urlsafe(24); session[f'live_{code.upper()}']=token
 with conn() as c: c.execute('UPDATE live_players SET device_token=? WHERE id=? AND live_game_id=(SELECT id FROM live_games WHERE code=?)',(token,lpid,code.upper())); c.commit()
 return redirect(f'/live/{code.upper()}/player')
@app.get('/live/<code>/player')
@auth
def live_player(code):
 token=session.get(f'live_{code.upper()}')
 with conn() as c:
  g=get_live(c,code)
  if not g:return ('Game not found',404)
  me=c.execute('SELECT lp.*,p.name,p.color FROM live_players lp JOIN players p ON p.id=lp.player_id WHERE lp.live_game_id=? AND lp.device_token=?',(g['id'],token)).fetchone()
  if not me:return redirect(f'/live/join?code={code.upper()}')
  roster=live_roster(c,g['id']); score=c.execute('SELECT * FROM live_scores WHERE live_game_id=? AND round_no=? AND live_player_id=?',(g['id'],g['round_no'],me['id'])).fetchone()
 return render_template('live_player.html',g=g,me=me,roster=roster,score=score)
@app.post('/live/<code>/submit')
@auth
def live_submit(code):
 token=session.get(f'live_{code.upper()}')
 with conn() as c:
  g=get_live(c,code); me=c.execute('SELECT * FROM live_players WHERE live_game_id=? AND device_token=?',(g['id'],token)).fetchone() if g else None
  if not g or not me or g['status']!='active' or g['round_state']!='scoring': return ('Score entry is not open',400)
  score=as_int(request.form.get('score'))
  if score is None or score<0: flash('Enter a valid score','bad'); return redirect(f'/live/{code}/player')
  c.execute("""INSERT INTO live_scores(live_game_id,round_no,live_player_id,submitted_score,phase_completed,status)
  VALUES(?,?,?,?,?,'pending') ON CONFLICT(live_game_id,round_no,live_player_id) DO UPDATE SET submitted_score=excluded.submitted_score,phase_completed=excluded.phase_completed,status='pending',submitted_at=CURRENT_TIMESTAMP,approved_score=NULL,reviewed_at=NULL""",(g['id'],g['round_no'],me['id'],score,1 if request.form.get('phase_completed') else 0)); c.commit()
 return redirect(f'/live/{code}/player')
@app.get('/live/<code>/host')
@auth
def live_host(code):
 with conn() as c:
  g=get_live(c,code)
  if not g:return ('Game not found',404)
  roster=live_roster(c,g['id'])
  scores=c.execute("""SELECT s.*,p.name,p.color,upper(substr(p.name,1,1)) initial,lp.current_phase FROM live_scores s JOIN live_players lp ON lp.id=s.live_player_id JOIN players p ON p.id=lp.player_id WHERE s.live_game_id=? AND s.round_no=? ORDER BY p.name""",(g['id'],g['round_no'])).fetchall()
  host_player=c.execute("SELECT lp.*,p.name,p.color,upper(substr(p.name,1,1)) initial FROM live_players lp JOIN players p ON p.id=lp.player_id WHERE lp.live_game_id=? AND lp.player_id=?",(g['id'],g['host_player_id'])).fetchone()
  host_score=c.execute('SELECT * FROM live_scores WHERE live_game_id=? AND round_no=? AND live_player_id=?',(g['id'],g['round_no'],host_player['id'])).fetchone() if host_player else None
 return render_template('live_host.html',g=g,roster=roster,scores=scores,host_player=host_player,host_score=host_score)
@app.post('/live/<code>/start')
@auth
def live_start(code):
 with conn() as c: c.execute("UPDATE live_games SET status='active',round_state='playing' WHERE code=? AND status='lobby'",(code.upper(),)); c.commit()
 return redirect(f'/live/{code}/host')
@app.post('/live/<code>/end-round')
@auth
def live_end_round(code):
 with conn() as c:
  c.execute("UPDATE live_games SET round_state='scoring' WHERE code=? AND status='active'",(code.upper(),)); c.commit()
 return redirect(f'/live/{code}/host')
@app.post('/live/<code>/host-submit')
@auth
def live_host_submit(code):
 with conn() as c:
  g=get_live(c,code); hp=c.execute('SELECT * FROM live_players WHERE live_game_id=? AND player_id=?',(g['id'],g['host_player_id'])).fetchone() if g else None; score=as_int(request.form.get('score'))
  if not g or not hp or g['status']!='active' or g['round_state']!='scoring' or score is None or score<0: flash('Host score could not be submitted','bad'); return redirect(f'/live/{code}/host')
  c.execute("""INSERT INTO live_scores(live_game_id,round_no,live_player_id,submitted_score,phase_completed,status) VALUES(?,?,?,?,?,'pending') ON CONFLICT(live_game_id,round_no,live_player_id) DO UPDATE SET submitted_score=excluded.submitted_score,phase_completed=excluded.phase_completed,status='pending',submitted_at=CURRENT_TIMESTAMP,approved_score=NULL,reviewed_at=NULL""",(g['id'],g['round_no'],hp['id'],score,1 if request.form.get('phase_completed') else 0)); c.commit()
 return redirect(f'/live/{code}/host')
@app.post('/live/<code>/player/<int:lpid>/left')
@auth
def live_player_left(code,lpid):
 with conn() as c:
  g=get_live(c,code)
  if not g:return ('Game not found',404)
  c.execute('UPDATE live_players SET active=0 WHERE id=? AND live_game_id=?',(lpid,g['id'])); c.commit(); flash('Player marked as left. Recorded rounds will be retained as DNF.')
 return redirect(f'/live/{code}/host')
@app.post('/live/<code>/review/<int:sid>')
@auth
def live_review(code,sid):
 action=request.form.get('action'); approved=as_int(request.form.get('approved_score'))
 with conn() as c:
  if action=='reject': c.execute("UPDATE live_scores SET status='rejected',reviewed_at=CURRENT_TIMESTAMP WHERE id=? AND live_game_id=(SELECT id FROM live_games WHERE code=?)",(sid,code.upper()))
  else: c.execute("UPDATE live_scores SET status='approved',approved_score=COALESCE(?,submitted_score),reviewed_at=CURRENT_TIMESTAMP WHERE id=? AND live_game_id=(SELECT id FROM live_games WHERE code=?)",(approved,sid,code.upper()))
  c.commit()
 return redirect(f'/live/{code}/host')
def archive_live_game(c,g):
 existing=c.execute('SELECT id FROM games WHERE notes=?',(f"Live game {g['code']}",)).fetchone()
 if existing:return existing['id']
 ng=c.execute("INSERT INTO games(played_date,date_accuracy,status,entry_type,notes) VALUES(?,'exact','complete','rounds',?)",(date.today().isoformat(),f"Live game {g['code']}"))
 for lp in c.execute('SELECT * FROM live_players WHERE live_game_id=?',(g['id'],)).fetchall():
  total=c.execute("SELECT COALESCE(SUM(COALESCE(approved_score,submitted_score)),0) FROM live_scores WHERE live_game_id=? AND live_player_id=? AND status='approved'",(g['id'],lp['id'])).fetchone()[0]
  gp=c.execute('INSERT INTO game_players(game_id,player_id,final_score,final_phase,result_status) VALUES(?,?,?,?,?)',(ng.lastrowid,lp['player_id'],total,lp['current_phase'],'finished' if lp['active'] else 'dnf'))
  for r in c.execute("SELECT round_no,COALESCE(approved_score,submitted_score) score FROM live_scores WHERE live_game_id=? AND live_player_id=? AND status='approved' ORDER BY round_no",(g['id'],lp['id'])).fetchall(): c.execute('INSERT INTO rounds(game_player_id,round_no,score) VALUES(?,?,?)',(gp.lastrowid,r['round_no'],r['score']))
 return ng.lastrowid
@app.post('/live/<code>/next-round')
@auth
def live_next(code):
 with conn() as c:
  g=get_live(c,code); active=c.execute('SELECT COUNT(*) FROM live_players WHERE live_game_id=? AND active=1',(g['id'],)).fetchone()[0]
  submitted=c.execute("SELECT COUNT(*) FROM live_scores s JOIN live_players lp ON lp.id=s.live_player_id WHERE s.live_game_id=? AND s.round_no=? AND lp.active=1 AND s.status IN ('pending','approved')",(g['id'],g['round_no'])).fetchone()[0]
  if submitted!=active: flash('Every active player must submit. Mark a missing player as Left Game if needed.','bad'); return redirect(f'/live/{code}/host')
  c.execute("UPDATE live_scores SET status='approved',approved_score=COALESCE(approved_score,submitted_score),reviewed_at=CURRENT_TIMESTAMP WHERE live_game_id=? AND round_no=? AND status='pending'",(g['id'],g['round_no']))
  winners=c.execute("SELECT lp.id FROM live_players lp JOIN live_scores s ON s.live_player_id=lp.id WHERE lp.live_game_id=? AND lp.active=1 AND lp.current_phase=10 AND s.round_no=? AND s.phase_completed=1 AND s.status='approved'",(g['id'],g['round_no'])).fetchall()
  c.execute("UPDATE live_players SET current_phase=current_phase+1 WHERE id IN (SELECT live_player_id FROM live_scores WHERE live_game_id=? AND round_no=? AND phase_completed=1 AND status='approved') AND current_phase<10",(g['id'],g['round_no']))
  if winners:
   hid=archive_live_game(c,g); c.execute("UPDATE live_games SET status='ended',ended_at=CURRENT_TIMESTAMP WHERE id=?",(g['id'],)); c.commit(); flash('Phase 10 completed. Game added to history.'); return redirect(f'/games/{hid}')
  c.execute("UPDATE live_games SET round_no=round_no+1,round_state='playing' WHERE id=?",(g['id'],)); c.commit()
 return redirect(f'/live/{code}/host')
@app.post('/live/<code>/end')
@auth
def live_end(code):
 with conn() as c: c.execute("UPDATE live_games SET status='ended',ended_at=CURRENT_TIMESTAMP WHERE code=?",(code.upper(),)); c.commit()
 return redirect('/live')
@app.get('/api/live/<code>/state')
@auth
def live_state(code):
 with conn() as c:
  g=get_live(c,code)
  if not g:return jsonify(error='not found'),404
  roster=[dict(x) for x in live_roster(c,g['id'])]
 return jsonify(status=g['status'],round_no=g['round_no'],round_state=g['round_state'],roster=roster)
# === END P10 LIVE V2 PATCH ===


# === P10 PWA THEME PATCH ===
@app.get('/manifest.webmanifest')
def pwa_manifest():
 return app.send_static_file('manifest.webmanifest')
@app.get('/service-worker.js')
def pwa_service_worker():
 response=app.send_static_file('service-worker.js')
 response.headers['Service-Worker-Allowed']='/'
 response.headers['Cache-Control']='no-cache'
 return response
@app.get('/offline')
def pwa_offline():
 return render_template('offline.html')
