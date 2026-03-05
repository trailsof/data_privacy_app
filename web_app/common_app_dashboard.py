from flask import Flask, render_template_string
import sqlite3

app = Flask(__name__)
DB_PATH = "app_permissions.db" 

def get_data(query, params=()):
    """Standard helper to handle DB connections safely."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    data = cur.fetchall()
    conn.close()
    return data


@app.route('/')
def index():
    return render_template_string("""
        <html>
        <head>
            <style>
                body { font-family: sans-serif; background: #121212; color: white; padding: 50px; text-align: center; }
                .nav-card { display: inline-block; background: #1e1e1e; padding: 30px; margin: 20px; border-radius: 15px; 
                           border: 1px solid #333; transition: 0.3s; width: 250px; text-decoration: none; color: white; }
                .nav-card:hover { border-color: #bb86fc; background: #252525; transform: translateY(-5px); }
                h2 { color: #bb86fc; }
            </style>
        </head>
        <body>
            <h1>🛡️ Privacy Lab: Localhost</h1>
            <p>Select a view to analyze Android application risks.</p>
            <a href="/dashboard" class="nav-card">
                <h2>App List</h2>
                <p>Total counts and severity bars for all apps.</p>
            </a>
            <a href="/overlap" class="nav-card">
                <h2>Overlap Matrix</h2>
                <p>Comparison of High-Risk perms for the Top 5 apps.</p>
            </a>
        </body>
        </html>
    """)

@app.route('/dashboard')
def dashboard():
    rows = get_data("""
        SELECT a.name, a.google_play_id, COUNT(ap.permission_id) as total,
               SUM(CASE WHEN p.severity = 'High' THEN 1 ELSE 0 END) as high
        FROM app a
        LEFT JOIN app_permission ap ON a.id = ap.app_id
        LEFT JOIN permission p ON ap.permission_id = p.id
        GROUP BY a.id ORDER BY high DESC
    """)

    html = """
    <html><head><style>
        body { font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 40px; }
        table { width: 100%; border-collapse: collapse; background: #1e1e1e; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #333; }
        th { background: #252525; color: #bb86fc; }
        .risk-bar { height: 10px; background: #333; border-radius: 5px; width: 100px; }
        .risk-fill { height: 100%; background: #cf6679; }
        .high-risk { color: #cf6679; font-weight: bold; }
        .back { display: block; margin-bottom: 20px; color: #03dac6; text-decoration: none; }
    </style></head><body>
        <a href="/" class="back">← Back to Home</a>
        <h1>🛡️ App Privacy Dashboard</h1>
        <table>
            <tr><th>App Name</th><th>Package ID</th><th>Total</th><th>High Risk</th><th>Severity</th></tr>
    """
    for row in rows:
        high = row['high'] or 0
        perc = min((high / 15) * 100, 100) if row['total'] > 0 else 0
        html += f"""
            <tr>
                <td><strong>{row['name']}</strong></td>
                <td><small>{row['google_play_id']}</small></td>
                <td>{row['total']}</td>
                <td class="{'high-risk' if high > 0 else ''}">{high}</td>
                <td><div class="risk-bar"><div class="risk-fill" style="width: {perc}%"></div></div></td>
            </tr>
        """
    return html + "</table></body></html>"

@app.route('/overlap')
def overlap():
    top_5 = ['com.openai.chatgpt', 'com.zhiliaoapp.musically', 'com.instagram.android', 'com.facebook.katana', 'com.whatsapp']
    placeholders = ','.join(['?'] * len(top_5))
    
    perms_rows = get_data(f"""
        SELECT DISTINCT p.android_name 
        FROM permission p
        JOIN app_permission ap ON p.id = ap.permission_id
        JOIN app a ON ap.app_id = a.id
        WHERE p.severity = 'High' AND a.google_play_id IN ({placeholders})
    """, top_5)
    
    apps = get_data(f"SELECT name, google_play_id FROM app WHERE google_play_id IN ({placeholders})", top_5)

    html = """
    <html><head><style>
        body { font-family: sans-serif; background: #0f0f0f; color: white; padding: 20px; }
        table { border-collapse: collapse; margin: 0 auto; }
        th, td { padding: 12px; border: 1px solid #333; text-align: center; }
        .perm-label { text-align: right; font-weight: bold; color: #bbb; background: #1a1a1a; }
        .app-header { writing-mode: vertical-rl; transform: rotate(180deg); padding: 20px 10px; background: #222; }
        .check { background: #ff4d4d; color: white; font-weight: bold; box-shadow: inset 0 0 10px #000; }
        .empty { background: #1a1a1a; color: #444; }
        .back { color: #03dac6; text-decoration: none; }
    </style></head><body>
    <a href="/" class="back">← Back to Home</a>
    <h1 style="text-align:center;">🔴 High-Risk Permission Overlap</h1>
    <table><tr><th></th>"""

    for app_row in apps:
        html += f"<th class='app-header'>{app_row['name']}</th>"
    html += "</tr>"

    for p_row in perms_rows:
        perm = p_row['android_name']
        html += f"<tr><td class='perm-label'>{perm}</td>"
        for app_row in apps:
            exists = get_data("""
                SELECT 1 FROM app_permission ap 
                JOIN app a ON ap.app_id = a.id
                JOIN permission p ON ap.permission_id = p.id
                WHERE a.google_play_id = ? AND p.android_name = ?
            """, (app_row['google_play_id'], perm))
            
            if exists: html += "<td class='check'>YES</td>"
            else: html += "<td class='empty'>-</td>"
        html += "</tr>"

    return html + "</table></body></html>"

if __name__ == '__main__':
    app.run(debug=True, port=5000)