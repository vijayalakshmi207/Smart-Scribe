import re

# Read current app1.py
with open('app1.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Split at CELL 4 marker and ADMIN API marker
cell4_marker = "# ==================== ORIGINAL NOTEBOOK CELL 4 ===================="
api_marker = "# ─── ADMIN ─────────────────────────────────────────────────"

parts_1 = code.split(cell4_marker)
prefix = parts_1[0] + cell4_marker + "\n\n"

parts_2 = parts_1[1].split(api_marker)
suffix = "\n\n" + api_marker + parts_2[1]

# New Redesigned UI Code
ui_code = r'''COMMON_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --primary: #D082D9;
  --primary-hover: #C06ECA;
  --primary-dark: #2A1035;
  --primary-light: #FAF4FB;
  --primary-border: #EBCBEF;
  --primary-glow: rgba(208, 130, 217, 0.22);

  --bg-body: #F8F6FA;
  --bg-sidebar: #1C0A24;
  --bg-sidebar-hover: rgba(208, 130, 217, 0.12);
  --bg-sidebar-active: #D082D9;

  --card-bg: #FFFFFF;
  --text-dark: #2D1436;
  --text-muted: #6B6575;
  --text-light: #9A94A6;

  --border-color: #EFEAF2;
  --border-focus: #D082D9;

  --success: #10B981;
  --success-bg: #ECFDF5;
  --success-border: #A7F3D0;

  --danger: #EF4444;
  --danger-bg: #FEF2F2;
  --danger-border: #FCA5A5;

  --warning: #F59E0B;
  --warning-bg: #FFFBEB;
  --warning-border: #FDE68A;

  --blue: #3B82F6;
  --blue-bg: #EFF6FF;

  --shadow-sm: 0 2px 8px rgba(42, 16, 53, 0.04);
  --shadow-md: 0 8px 24px rgba(42, 16, 53, 0.07);
  --shadow-lg: 0 16px 40px rgba(42, 16, 53, 0.10);

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Plus Jakarta Sans', 'Segoe UI', -apple-system, sans-serif;
}

body {
  background-color: var(--bg-body);
  color: var(--text-dark);
  min-height: 100vh;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

a {
  color: var(--primary);
  text-decoration: none;
  transition: all 0.2s ease;
}

a:hover {
  color: var(--primary-hover);
}

/* APP SHELL WITH SIDEBAR */
.app-shell {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 260px;
  background-color: var(--bg-sidebar);
  color: #FFFFFF;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 100;
  transition: transform 0.3s ease;
}

.sidebar-header {
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-badge {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #D082D9 0%, #9B40A5 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 800;
  font-size: 22px;
  box-shadow: 0 4px 14px rgba(208, 130, 217, 0.4);
}

.logo-text h2 {
  font-size: 18px;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: -0.3px;
}

.logo-text p {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  font-weight: 500;
}

.sidebar-nav {
  padding: 20px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.nav-link:hover {
  background-color: var(--bg-sidebar-hover);
  color: #FFFFFF;
}

.nav-link.active {
  background-color: var(--bg-sidebar-active);
  color: #FFFFFF;
  box-shadow: 0 4px 14px rgba(208, 130, 217, 0.35);
}

.nav-link svg {
  width: 20px;
  height: 20px;
  stroke-width: 2;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 16px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.main-wrapper {
  flex: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.top-bar {
  background: #FFFFFF;
  height: 72px;
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 90;
  box-shadow: var(--shadow-sm);
}

.mobile-toggle {
  display: none;
  background: none;
  border: none;
  color: var(--text-dark);
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-sm);
}

.top-bar-title h1 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-dark);
}

.top-bar-title p {
  font-size: 12px;
  color: var(--text-muted);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-light);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  border: 2px solid var(--primary-border);
}

.content-area {
  padding: 32px;
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

/* CARDS & CONTAINERS */
.card {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  padding: 32px;
  margin-bottom: 24px;
}

/* BUTTONS */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
  text-decoration: none;
  line-height: 1.2;
}

.btn-primary {
  background: var(--primary);
  color: #FFFFFF;
  box-shadow: 0 4px 14px var(--primary-glow);
}

.btn-primary:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(208, 130, 217, 0.35);
  color: #FFFFFF;
}

.btn-secondary {
  background: #FFFFFF;
  color: var(--text-dark);
  border: 1.5px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-body);
  border-color: var(--primary);
  color: var(--primary);
}

.btn-danger {
  background: var(--danger);
  color: #FFFFFF;
}

.btn-danger:hover {
  background: #DC2626;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3);
  color: #FFFFFF;
}

.btn-sm {
  padding: 8px 14px;
  font-size: 13px;
  border-radius: var(--radius-sm);
}

.btn-lg {
  padding: 14px 32px;
  font-size: 16px;
  border-radius: var(--radius-md);
}

/* FORMS */
.form-group {
  margin-bottom: 22px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-dark);
  margin-bottom: 8px;
}

.form-control {
  width: 100%;
  padding: 12px 16px;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  color: var(--text-dark);
  background: #FFFFFF;
  transition: all 0.2s ease;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--primary-glow);
}

/* TABLES */
.table-container {
  background: #FFFFFF;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.table th {
  background: #FAF8FC;
  padding: 16px 20px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}

.table td {
  padding: 16px 20px;
  font-size: 14px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-dark);
}

.table tbody tr:last-child td {
  border-bottom: none;
}

.table tbody tr:hover td {
  background-color: #FDFBFE;
}

/* BADGES */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.badge-success {
  background: var(--success-bg);
  color: #047857;
  border: 1px solid var(--success-border);
}

.badge-warning {
  background: var(--warning-bg);
  color: #B45309;
  border: 1px solid var(--warning-border);
}

.badge-primary {
  background: var(--primary-light);
  color: var(--primary-dark);
  border: 1px solid var(--primary-border);
}

/* EMPTY STATE */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-state-icon {
  width: 64px;
  height: 64px;
  background: var(--primary-light);
  color: var(--primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  font-size: 28px;
}

.empty-state h3 {
  font-size: 18px;
  color: var(--text-dark);
  margin-bottom: 6px;
}

.empty-state p {
  color: var(--text-muted);
  font-size: 14px;
  margin-bottom: 20px;
}

/* RESPONSIVE */
@media (max-width: 900px) {
  .sidebar {
    transform: translateX(-100%);
  }
  .sidebar.open {
    transform: translateX(0);
  }
  .main-wrapper {
    margin-left: 0;
  }
  .mobile-toggle {
    display: block;
  }
  .content-area {
    padding: 20px 16px;
  }
}
"""

def render_admin_layout(active_page, title, subtitle, content_html):
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} — SmartScribe Admin</title>
        <style>{COMMON_CSS}</style>
    </head>
    <body>
    <div class="app-shell">
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="logo-badge">S</div>
                <div class="logo-text">
                    <h2>SmartScribe</h2>
                    <p>AI Exam Assistant</p>
                </div>
            </div>
            <nav class="sidebar-nav">
                <a href="/admin-dashboard" class="nav-link {'active' if active_page == 'dashboard' else ''}">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
                    Dashboard
                </a>
                <a href="/create-student" class="nav-link {'active' if active_page == 'create-student' else ''}">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/></svg>
                    Add Student
                </a>
                <a href="/view-students" class="nav-link {'active' if active_page == 'view-students' else ''}">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
                    View Students
                </a>
                <a href="/create-exam" class="nav-link {'active' if active_page == 'create-exam' else ''}">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                    Add Exam
                </a>
                <a href="/view-exams" class="nav-link {'active' if active_page == 'view-exams' else ''}">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                    View Exams
                </a>
                <a href="/view-submissions" class="nav-link {'active' if active_page == 'view-submissions' else ''}">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                    Submissions
                </a>
            </nav>
            <div class="sidebar-footer">
                <a href="/" class="nav-link" style="color: #EF4444;">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
                    Logout
                </a>
            </div>
        </aside>

        <div class="main-wrapper">
            <header class="top-bar">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <button class="mobile-toggle" onclick="document.getElementById('sidebar').classList.toggle('open')">
                        <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
                    </button>
                    <div class="top-bar-title">
                        <h1>{title}</h1>
                        <p>{subtitle}</p>
                    </div>
                </div>
                <div class="user-profile">
                    <span style="font-size: 14px; font-weight: 600; color: var(--text-dark);">Admin</span>
                    <div class="user-avatar">A</div>
                </div>
            </header>

            <main class="content-area">
                {content_html}
            </main>
        </div>
    </div>
    </body>
    </html>
    """)

@app.route('/')
def home():
    return render_template_string("""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>SmartScribe - AI Exam Assistant</title>
    <style>""" + COMMON_CSS + """
        .hero-bg {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 40px 20px;
            background: radial-gradient(circle at 50% 0%, #FAF2FC 0%, #F8F6FA 70%);
        }
        .hero-container {
            max-width: 900px;
            width: 100%;
            text-align: center;
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 18px;
            background: var(--primary-light);
            border: 1px solid var(--primary-border);
            border-radius: 30px;
            color: var(--primary-dark);
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 24px;
        }
        .hero-title {
            font-size: 42px;
            font-weight: 800;
            color: var(--text-dark);
            letter-spacing: -1px;
            margin-bottom: 12px;
        }
        .hero-subtitle {
            font-size: 18px;
            color: var(--text-muted);
            max-width: 620px;
            margin: 0 auto 48px;
        }
        .role-selection {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 28px;
            margin-bottom: 40px;
        }
        .role-card {
            background: #FFFFFF;
            border-radius: var(--radius-xl);
            padding: 40px 32px;
            text-align: left;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            border: 2px solid var(--border-color);
            box-shadow: var(--shadow-md);
            position: relative;
            overflow: hidden;
        }
        .role-card:hover {
            transform: translateY(-8px);
            border-color: var(--primary);
            box-shadow: 0 20px 40px rgba(208, 130, 217, 0.2);
        }
        .role-icon-box {
            width: 64px;
            height: 64px;
            border-radius: 18px;
            background: var(--primary-light);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            margin-bottom: 24px;
            border: 1px solid var(--primary-border);
        }
        .role-card h3 {
            font-size: 22px;
            font-weight: 700;
            color: var(--text-dark);
            margin-bottom: 8px;
        }
        .role-card p {
            color: var(--text-muted);
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 24px;
        }
        .role-cta {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 700;
            color: var(--primary);
        }
    </style></head><body>
    <div class="hero-bg">
        <div class="hero-container">
            <div class="hero-badge">
                <span>✨</span> AI-Powered Inclusive Examination Platform
            </div>
            <h1 class="hero-title">SmartScribe</h1>
            <p class="hero-subtitle">AI Exam Assistant for Visually Impaired Students — Providing secure biometric authentication and real-time voice-guided assessment.</p>
            
            <div class="role-selection">
                <div class="role-card" onclick="window.location.href='/admin-login'">
                    <div class="role-icon-box">👨‍💼</div>
                    <h3>Administrator</h3>
                    <p>Register students, upload PDF question papers, manage examinations and review submitted answer sheets.</p>
                    <div class="role-cta">Enter Admin Portal →</div>
                </div>
                <div class="role-card" onclick="window.location.href='/student-verification'">
                    <div class="role-icon-box">👩‍🎓</div>
                    <h3>Student Portal</h3>
                    <p>Verify face & voice identity to enter your examination environment with full voice-assistant support.</p>
                    <div class="role-cta">Start Examination →</div>
                </div>
            </div>
        </div>
    </div>
    </body></html>
    """)

@app.route('/admin-login')
def admin_login():
    return render_template_string("""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Admin Login - SmartScribe</title>
    <style>""" + COMMON_CSS + """
        .auth-wrapper {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: radial-gradient(circle at 50% 0%, #FAF2FC 0%, #F8F6FA 70%);
        }
        .auth-card {
            width: 100%;
            max-width: 440px;
            background: #FFFFFF;
            border-radius: var(--radius-xl);
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-lg);
            padding: 40px;
        }
        .auth-header {
            text-align: center;
            margin-bottom: 32px;
        }
        .auth-header .logo-badge {
            margin: 0 auto 16px;
        }
    </style></head><body>
    <div class="auth-wrapper">
        <div class="auth-card">
            <div class="auth-header">
                <div class="logo-badge">S</div>
                <h2 style="font-size:24px;font-weight:800;color:var(--text-dark);">Admin Login</h2>
                <p style="font-size:13px;color:var(--text-muted);margin-top:4px;">Sign in to access your administrative dashboard</p>
            </div>
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="u" placeholder="Enter your username" class="form-control">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="p" placeholder="Enter your password" class="form-control">
            </div>
            <button class="btn btn-primary" onclick="login()" style="width:100%;margin-top:8px;">Sign In →</button>
            
            <div style="text-align:center;margin-top:24px;font-size:14px;color:var(--text-muted);">
                Don't have an account? <a href="/admin-register" style="font-weight:600;">Register here</a>
            </div>
            <div style="text-align:center;margin-top:16px;">
                <a href="/" style="font-size:13px;color:var(--text-muted);">← Back to Home</a>
            </div>
        </div>
    </div>
    <script>
        function login(){
            fetch('/api/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},
                body:JSON.stringify({username:document.getElementById('u').value,password:document.getElementById('p').value})})
            .then(r=>r.json()).then(d=>{if(d.success)window.location.href='/admin-dashboard';else alert('Invalid credentials');});
        }
        document.addEventListener('keydown',e=>{if(e.key==='Enter')login();});
    </script></body></html>
    """)

@app.route('/admin-register')
def admin_register():
    return render_template_string("""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Admin Registration - SmartScribe</title>
    <style>""" + COMMON_CSS + """
        .auth-wrapper {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: radial-gradient(circle at 50% 0%, #FAF2FC 0%, #F8F6FA 70%);
        }
        .auth-card {
            width: 100%;
            max-width: 440px;
            background: #FFFFFF;
            border-radius: var(--radius-xl);
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-lg);
            padding: 40px;
        }
    </style></head><body>
    <div class="auth-wrapper">
        <div class="auth-card">
            <div style="text-align:center;margin-bottom:32px;">
                <div class="logo-badge" style="margin:0 auto 16px;">S</div>
                <h2 style="font-size:24px;font-weight:800;color:var(--text-dark);">Register Admin Account</h2>
                <p style="font-size:13px;color:var(--text-muted);margin-top:4px;">Create a new administrator account</p>
            </div>
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="u" placeholder="Choose a username" class="form-control">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="p" placeholder="Create a password" class="form-control">
            </div>
            <div class="form-group">
                <label>Confirm Password</label>
                <input type="password" id="c" placeholder="Confirm your password" class="form-control">
            </div>
            <button class="btn btn-primary" onclick="reg()" style="width:100%;margin-top:8px;">Create Account →</button>
            
            <div style="text-align:center;margin-top:24px;font-size:14px;color:var(--text-muted);">
                Already have an account? <a href="/admin-login" style="font-weight:600;">Sign in</a>
            </div>
            <div style="text-align:center;margin-top:16px;">
                <a href="/" style="font-size:13px;color:var(--text-muted);">← Back to Home</a>
            </div>
        </div>
    </div>
    <script>
        function reg(){
            const u=document.getElementById('u').value,p=document.getElementById('p').value,c=document.getElementById('c').value;
            if(p!==c){alert('Passwords do not match');return;}
            fetch('/api/admin/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})})
            .then(r=>r.json()).then(d=>{if(d.success){alert('Registered! Please login.');window.location.href='/admin-login';}else alert(d.message);});
        }
    </script></body></html>
    """)

@app.route('/admin-dashboard')
def admin_dashboard():
    dashboard_body = """
    <div style="margin-bottom: 28px;">
        <h2 style="font-size: 24px; font-weight: 800; color: var(--text-dark);">Good morning, Admin 👋</h2>
        <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">Manage students, examinations and submissions from one place.</p>
    </div>

    <!-- STATISTICS CARDS -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin-bottom: 36px;">
        <div class="card" style="margin-bottom: 0; padding: 24px; display: flex; align-items: center; gap: 20px;">
            <div style="width: 56px; height: 56px; border-radius: 16px; background: var(--primary-light); color: var(--primary); display: flex; align-items: center; justify-content: center; font-size: 26px; border: 1px solid var(--primary-border);">👥</div>
            <div>
                <div id="ts" style="font-size: 32px; font-weight: 800; color: var(--text-dark); line-height: 1;">0</div>
                <div style="font-size: 13px; font-weight: 600; color: var(--text-muted); margin-top: 4px;">Total Students</div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 0; padding: 24px; display: flex; align-items: center; gap: 20px;">
            <div style="width: 56px; height: 56px; border-radius: 16px; background: var(--blue-bg); color: var(--blue); display: flex; align-items: center; justify-content: center; font-size: 26px;">📚</div>
            <div>
                <div id="te" style="font-size: 32px; font-weight: 800; color: var(--text-dark); line-height: 1;">0</div>
                <div style="font-size: 13px; font-weight: 600; color: var(--text-muted); margin-top: 4px;">Total Exams</div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 0; padding: 24px; display: flex; align-items: center; gap: 20px;">
            <div style="width: 56px; height: 56px; border-radius: 16px; background: var(--success-bg); color: var(--success); display: flex; align-items: center; justify-content: center; font-size: 26px;">📥</div>
            <div>
                <div id="tsub" style="font-size: 32px; font-weight: 800; color: var(--text-dark); line-height: 1;">0</div>
                <div style="font-size: 13px; font-weight: 600; color: var(--text-muted); margin-top: 4px;">Total Submissions</div>
            </div>
        </div>
    </div>

    <!-- QUICK ACTIONS -->
    <h3 style="font-size: 18px; font-weight: 700; color: var(--text-dark); margin-bottom: 20px;">Quick Actions</h3>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px;">
        <div class="card" onclick="window.location.href='/create-student'" style="margin-bottom: 0; cursor: pointer; text-align: center; padding: 28px 20px; border: 2px solid transparent; transition: all 0.2s ease;">
            <div style="font-size: 40px; margin-bottom: 12px;">➕</div>
            <h4 style="font-size: 16px; font-weight: 700; color: var(--text-dark);">Add Student</h4>
            <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Register new student profile</p>
        </div>

        <div class="card" onclick="window.location.href='/view-students'" style="margin-bottom: 0; cursor: pointer; text-align: center; padding: 28px 20px; border: 2px solid transparent; transition: all 0.2s ease;">
            <div style="font-size: 40px; margin-bottom: 12px;">👥</div>
            <h4 style="font-size: 16px; font-weight: 700; color: var(--text-dark);">View Students</h4>
            <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Manage student directory</p>
        </div>

        <div class="card" onclick="window.location.href='/create-exam'" style="margin-bottom: 0; cursor: pointer; text-align: center; padding: 28px 20px; border: 2px solid transparent; transition: all 0.2s ease;">
            <div style="font-size: 40px; margin-bottom: 12px;">📝</div>
            <h4 style="font-size: 16px; font-weight: 700; color: var(--text-dark);">Add Exam</h4>
            <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Upload question papers</p>
        </div>

        <div class="card" onclick="window.location.href='/view-exams'" style="margin-bottom: 0; cursor: pointer; text-align: center; padding: 28px 20px; border: 2px solid transparent; transition: all 0.2s ease;">
            <div style="font-size: 40px; margin-bottom: 12px;">📚</div>
            <h4 style="font-size: 16px; font-weight: 700; color: var(--text-dark);">View Exams</h4>
            <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Review created exams</p>
        </div>

        <div class="card" onclick="window.location.href='/view-submissions'" style="margin-bottom: 0; cursor: pointer; text-align: center; padding: 28px 20px; border: 2px solid var(--primary); background: var(--primary-light); transition: all 0.2s ease;">
            <div style="font-size: 40px; margin-bottom: 12px;">📥</div>
            <h4 style="font-size: 16px; font-weight: 700; color: var(--primary-dark);">View Submissions</h4>
            <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Check completed answer sheets</p>
        </div>
    </div>

    <script>
        fetch('/api/admin/stats').then(r=>r.json()).then(d=>{
            document.getElementById('ts').textContent=d.totalStudents;
            document.getElementById('te').textContent=d.totalExams;
            document.getElementById('tsub').textContent=d.totalSubmissions;
        });
    </script>
    """
    return render_admin_layout('dashboard', 'Admin Dashboard', 'Manage students, examinations and submissions from one place.', dashboard_body)

@app.route('/view-submissions')
def view_submissions():
    with get_db() as conn:
        subs = conn.cursor().execute(
            "SELECT id,reg_no,student_name,exam_name,pdf_filename,submitted_at FROM exam_submissions ORDER BY submitted_at DESC"
        ).fetchall()
    rows = ''
    for s in subs:
        fname = s['pdf_filename'] or f"{s['student_name']}.{s['exam_name']}.pdf"
        rows += f"""<tr>
            <td style="font-weight:600;">{s['reg_no']}</td>
            <td>{s['student_name']}</td>
            <td><span class="badge badge-primary">{s['exam_name']}</span></td>
            <td style="color:var(--text-muted);font-size:13px;">{s['submitted_at']}</td>
            <td>
                <a href="/api/admin/download-submission/{s['id']}" class="btn btn-sm btn-primary">⬇ Download PDF</a>
                <button onclick="deleteSubmission({s['id']})" class="btn btn-sm btn-danger" style="margin-left:6px;">🗑 Delete</button>
            </td>
        </tr>"""
    if not rows:
        rows = """<tr><td colspan="5">
            <div class="empty-state">
                <div class="empty-state-icon">📥</div>
                <h3>No submissions yet</h3>
                <p>Student answer sheets will appear here once exams are completed.</p>
            </div>
        </td></tr>"""

    body = f"""
    <div class="table-container">
        <table class="table">
            <thead>
                <tr>
                    <th>Registration No</th>
                    <th>Student Name</th>
                    <th>Exam Name</th>
                    <th>Submitted At</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>

    <script>
    function deleteSubmission(id) {{
        if (!confirm('Delete this submitted answer sheet? This action cannot be undone.')) return;
        fetch('/api/admin/delete-submission/' + id, {{method:'POST'}})
            .then(r=>r.json())
            .then(d=>{{if(d.success){{alert('Submission deleted successfully.');location.reload();}}else{{alert(d.message||'Could not delete submission.');}}}})
            .catch(err=>alert('Delete failed: '+err));
    }}
    </script>
    """
    return render_admin_layout('view-submissions', 'Student Submissions', 'Review and manage submitted answer sheets.', body)

@app.route('/create-student')
def create_student():
    body = """
    <div style="max-width: 680px; margin: 0 auto;">
        <div class="card">
            <!-- STEP INDICATOR -->
            <div style="display:flex; justify-content:space-between; margin-bottom:32px; padding-bottom:20px; border-bottom:1px solid var(--border-color);">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:32px; height:32px; border-radius:50%; background:var(--primary); color:white; font-weight:700; display:flex; align-items:center; justify-content:center; font-size:14px;">1</div>
                    <span style="font-size:13px; font-weight:700; color:var(--text-dark);">Information</span>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:32px; height:32px; border-radius:50%; background:var(--primary-light); color:var(--primary); font-weight:700; display:flex; align-items:center; justify-content:center; font-size:14px; border:1px solid var(--primary-border);">2</div>
                    <span style="font-size:13px; font-weight:700; color:var(--text-dark);">Face Capture</span>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:32px; height:32px; border-radius:50%; background:var(--primary-light); color:var(--primary); font-weight:700; display:flex; align-items:center; justify-content:center; font-size:14px; border:1px solid var(--primary-border);">3</div>
                    <span style="font-size:13px; font-weight:700; color:var(--text-dark);">Voice Studio</span>
                </div>
            </div>

            <h3 style="font-size:20px; font-weight:800; color:var(--text-dark); margin-bottom:24px;">Register New Student</h3>

            <!-- Section 1 -->
            <div class="form-group">
                <label>Registration Number</label>
                <input type="text" id="regNo" placeholder="e.g. 2024001" class="form-control">
            </div>
            <div class="form-group">
                <label>Full Name</label>
                <input type="text" id="studentName" placeholder="Enter student's full name" class="form-control">
            </div>

            <!-- Section 2: Face Photo -->
            <div class="form-group" style="margin-top:28px;">
                <label style="display:flex; align-items:center; gap:8px;">
                    <span>📸</span> Student Photo (Face Recognition)
                </label>
                <input type="file" id="studentImage" accept="image/*" onchange="previewImg(event)" class="form-control">
                <div style="text-align:center;">
                    <img id="imgPreview" style="max-width:180px; max-height:180px; display:none; margin:16px auto 0; border-radius:12px; border:3px solid var(--primary); shadow:var(--shadow-md);">
                </div>
                <div style="font-size:12px; color:var(--warning); margin-top:8px; display:flex; align-items:center; gap:4px;">
                    ⚠️ Ensure the face is centered, well-lit, and without sunglasses/hats.
                </div>
            </div>

            <!-- Section 3: Voice Studio -->
            <div class="form-group" style="margin-top:28px;">
                <label style="display:flex; align-items:center; gap:8px;">
                    <span>🎙️</span> Voice Sample Registration
                </label>
                <div style="background:var(--primary-light); border:2px dashed var(--primary-border); border-radius:var(--radius-lg); padding:24px; text-align:center;">
                    <p style="color:var(--text-muted); font-size:13px; margin-bottom:16px;">
                        Ask the student to speak clearly for <strong>5–8 seconds</strong>.<br>
                        <em>"My name is [Name] and my registration number is [Reg No]"</em>
                    </p>
                    <button class="btn btn-primary" id="recBtn" onclick="startRec()">🎙️ Start Recording</button>
                    <button class="btn btn-danger" id="stopBtn" onclick="stopRec()" style="display:none;">⏹ Stop Recording</button>
                    
                    <div id="voiceStatus" style="font-size:13px; color:var(--text-muted); margin-top:12px; min-height:20px;">Press Start Recording to begin</div>
                    <audio id="voicePlayback" controls style="display:none; width:100%; margin-top:14px; border-radius:8px;"></audio>
                    <div id="wavNotice" style="display:none; font-size:12px; color:var(--success); font-weight:600; margin-top:8px;">✅ Voice recorded successfully!</div>
                </div>
            </div>

            <div style="display:flex; gap:12px; margin-top:32px;">
                <button class="btn btn-primary" onclick="registerStudent()" style="flex:1;">✅ Register Student</button>
                <button class="btn btn-secondary" onclick="window.location.href='/admin-dashboard'">Cancel</button>
            </div>
        </div>
    </div>

    <script>
    let imageData=null, voiceB64=null, mediaRecorder=null, audioChunks=[], autoStopTimer=null;

    function previewImg(event){
        const file=event.target.files[0];
        if(!file) return;
        const reader=new FileReader();
        reader.onload=e=>{
            document.getElementById('imgPreview').src=e.target.result;
            document.getElementById('imgPreview').style.display='block';
            imageData=e.target.result;
        };
        reader.readAsDataURL(file);
    }

    async function startRec(){
        audioChunks=[]; voiceB64=null;
        document.getElementById('voicePlayback').style.display='none';
        document.getElementById('wavNotice').style.display='none';
        let stream;
        try{
            stream=await navigator.mediaDevices.getUserMedia({audio:{sampleRate:16000,channelCount:1,echoCancellation:true}});
        }catch(e){
            alert('Microphone access denied: '+e.message);
            return;
        }
        const mime=MediaRecorder.isTypeSupported('audio/wav')?'audio/wav':
                   MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?'audio/webm;codecs=opus':'audio/webm';
        mediaRecorder=new MediaRecorder(stream,{mimeType:mime});
        mediaRecorder.ondataavailable=e=>audioChunks.push(e.data);
        mediaRecorder.onstop=()=>{
            const blob=new Blob(audioChunks,{type:mime});
            document.getElementById('voicePlayback').src=URL.createObjectURL(blob);
            document.getElementById('voicePlayback').style.display='block';
            const reader=new FileReader();
            reader.onload=e=>{
                voiceB64=e.target.result.split(',')[1];
                document.getElementById('voiceStatus').textContent='✅ Voice recorded ('+(blob.size/1024).toFixed(1)+' KB). You can play it back above.';
                document.getElementById('wavNotice').style.display='block';
            };
            reader.readAsDataURL(blob);
            stream.getTracks().forEach(t=>t.stop());
        };
        mediaRecorder.start();
        document.getElementById('recBtn').style.display='none';
        document.getElementById('stopBtn').style.display='inline-flex';
        document.getElementById('voiceStatus').textContent='🔴 Recording... speak clearly now';
        autoStopTimer=setTimeout(()=>{ if(mediaRecorder&&mediaRecorder.state==='recording')stopRec(); },10000);
    }

    function stopRec(){
        if(autoStopTimer){clearTimeout(autoStopTimer);autoStopTimer=null;}
        if(mediaRecorder&&mediaRecorder.state==='recording')mediaRecorder.stop();
        document.getElementById('recBtn').style.display='inline-flex';
        document.getElementById('stopBtn').style.display='none';
    }

    function registerStudent(){
        const regNo=document.getElementById('regNo').value.trim();
        const name=document.getElementById('studentName').value.trim();
        if(!regNo||!name){alert('Please fill registration number and name');return;}
        if(!imageData){alert('Please upload a student photo');return;}
        if(!voiceB64){alert('Please record a voice sample (Step 3)');return;}
        const btn=event.target;btn.disabled=true;btn.textContent='Registering...';
        fetch('/api/admin/create-student',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({regNo,name,image:imageData,voice:voiceB64})})
        .then(r=>r.json()).then(d=>{
            if(d.success){alert('Student registered successfully!');window.location.href='/view-students';}
            else{alert('Error: '+(d.message||'Unknown error'));btn.disabled=false;btn.textContent='✅ Register Student';}
        }).catch(e=>{alert('Network error: '+e.message);btn.disabled=false;btn.textContent='✅ Register Student';});
    }
    </script>
    """
    return render_admin_layout('create-student', 'Add Student', 'Register a new student with biometric face and voice profiles.', body)

@app.route('/view-students')
def view_students():
    with get_db() as conn:
        students = conn.cursor().execute("SELECT reg_no,name,image,voice_embedding FROM students ORDER BY created_at DESC").fetchall()
    cards = ''
    if students:
        for s in students:
            has_voice = '<span class="badge badge-success">✅ Voice Registered</span>' if s['voice_embedding'] else '<span class="badge badge-warning">⚠️ No Voice</span>'
            cards += f'''
            <div class="card student-item-card" style="margin-bottom:0; text-align:center; padding:24px;" data-search="{s['name'].lower()} {s['reg_no'].lower()}">
                <div style="width:96px; height:96px; border-radius:50%; margin:0 auto 16px; overflow:hidden; border:3px solid var(--primary); box-shadow:var(--shadow-sm);">
                    <img src="{s['image']}" alt="{s['name']}" style="width:100%; height:100%; object-fit:cover;">
                </div>
                <h4 style="font-size:16px; font-weight:700; color:var(--text-dark); margin-bottom:4px;">{s['name']}</h4>
                <p style="font-size:13px; color:var(--text-muted); margin-bottom:12px;">Reg: {s['reg_no']}</p>
                <div style="margin-bottom:16px;">{has_voice}</div>
                <button onclick="delS('{s['reg_no']}')" class="btn btn-sm btn-danger" style="width:100%;">🗑 Delete Student</button>
            </div>'''
    else:
        cards = '''<div style="grid-column:1/-1;">
            <div class="empty-state">
                <div class="empty-state-icon">👥</div>
                <h3>No registered students yet</h3>
                <p>Add your first student to start managing profiles.</p>
                <a href="/create-student" class="btn btn-primary">➕ Add Student</a>
            </div>
        </div>'''

    body = f"""
    <div style="margin-bottom:24px;">
        <input type="text" id="studentSearchInput" onkeyup="filterStudents()" placeholder="🔍 Search students by name or registration number..." class="form-control" style="max-width:400px;">
    </div>

    <div id="studentsGrid" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:20px;">
        {cards}
    </div>

    <script>
    function delS(r){{
        if(confirm('Delete student '+r+'? This cannot be undone.')){{
            fetch('/api/admin/delete-student',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{regNo:r}})}})
                .then(r=>r.json()).then(d=>{{if(d.success)location.reload();}});
        }}
    }}
    function filterStudents(){{
        const q=document.getElementById('studentSearchInput').value.toLowerCase();
        document.querySelectorAll('.student-item-card').forEach(el=>{{
            el.style.display=el.dataset.search.includes(q)?'block':'none';
        }});
    }}
    </script>
    """
    return render_admin_layout('view-students', 'Student Directory', 'Manage registered students and voice authentication status.', body)

@app.route('/create-exam', methods=['GET'])
def create_exam_page():
    body = """
    <div style="max-width: 680px; margin: 0 auto;">
        <div class="card">
            <h3 style="font-size:20px; font-weight:800; color:var(--text-dark); margin-bottom:16px;">Create New Examination</h3>
            
            <div style="background:var(--primary-light); border:1px solid var(--primary-border); border-radius:var(--radius-md); padding:16px; margin-bottom:24px; font-size:13px; color:var(--primary-dark);">
                📌 <strong>PDF Requirements:</strong> Upload a PDF question paper containing numbered questions (e.g., <em>1. What is photosynthesis? 2. What is chlorophyll?</em>). Questions will be parsed automatically.
            </div>

            <div class="form-group">
                <label>Exam Title</label>
                <input type="text" id="examName" placeholder="e.g. Biology Midterm Exam" class="form-control">
            </div>

            <div class="form-group">
                <label>Duration (Minutes)</label>
                <input type="number" id="duration" value="60" min="1" class="form-control">
            </div>

            <div class="form-group">
                <label>Question Paper PDF</label>
                <div style="border:2px dashed var(--border-color); border-radius:var(--radius-lg); padding:32px; text-align:center; background:#FAF8FC;" id="dropzone">
                    <div style="font-size:36px; margin-bottom:8px;">📄</div>
                    <div style="font-size:14px; font-weight:600; color:var(--text-dark);">Upload Question Paper PDF</div>
                    <div style="font-size:12px; color:var(--text-muted); margin-top:4px; margin-bottom:16px;">PDF files only</div>
                    
                    <input type="file" id="pdfFile" accept="application/pdf" onchange="showFileName()" style="display:none;">
                    <button class="btn btn-secondary" onclick="document.getElementById('pdfFile').click()">Choose File</button>
                    <div id="fileName" style="font-size:13px; font-weight:600; color:var(--primary); margin-top:12px;">No PDF selected</div>
                </div>
            </div>

            <button class="btn btn-primary" id="createBtn" onclick="createExam()" style="width:100%; margin-top:12px;">🚀 Create Examination</button>
            <div id="status" style="display:none; margin-top:16px; padding:12px; border-radius:var(--radius-md); font-size:13px; font-weight:600;"></div>
        </div>
    </div>

    <script>
    function showFileName() {
        const fileInput = document.getElementById('pdfFile');
        const fileName = document.getElementById('fileName');
        if (fileInput.files.length > 0) {
            fileName.textContent = "Selected: " + fileInput.files[0].name;
        } else {
            fileName.textContent = "No PDF selected";
        }
    }

    function showStatus(message, type) {
        const status = document.getElementById('status');
        status.textContent = message;
        status.style.display = 'block';
        if(type==='success'){
            status.style.background='var(--success-bg)'; status.style.color='#047857'; status.style.border='1px solid var(--success-border)';
        } else if(type==='error'){
            status.style.background='var(--danger-bg)'; status.style.color='#DC2626'; status.style.border='1px solid var(--danger-border)';
        } else {
            status.style.background='var(--primary-light)'; status.style.color='var(--primary-dark)'; status.style.border='1px solid var(--primary-border)';
        }
    }

    async function createExam() {
        const name = document.getElementById('examName').value.trim();
        const duration = document.getElementById('duration').value;
        const fileInput = document.getElementById('pdfFile');
        const btn = document.getElementById('createBtn');

        if (!name) { showStatus('❌ Please enter an exam name.', 'error'); return; }
        if (!fileInput.files.length) { showStatus('❌ Please select a PDF question paper.', 'error'); return; }
        const file = fileInput.files[0];
        if (file.type !== 'application/pdf') { showStatus('❌ Please select a PDF file only.', 'error'); return; }

        btn.disabled = true; btn.textContent = '⏳ Creating Exam...';
        showStatus('📄 Reading question paper...', 'info');

        try {
            const reader = new FileReader();
            reader.onload = async function(e) {
                const pdfBase64 = e.target.result;
                showStatus('🤖 Extracting questions from PDF...', 'info');
                try {
                    const response = await fetch('/api/admin/create-exam', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: name, duration: parseInt(duration) || 60, pdf: pdfBase64 })
                    });
                    const data = await response.json();
                    if (!response.ok || !data.success) {
                        throw new Error(data.message || data.error || 'Failed to create exam');
                    }
                    showStatus('✅ Exam created successfully! ' + data.question_count + ' questions detected.', 'success');
                    btn.textContent = '✅ Exam Created';
                    setTimeout(function() { window.location.href = '/view-exams'; }, 1800);
                } catch(error) {
                    console.error('Create exam error:', error);
                    showStatus('❌ ' + error.message, 'error');
                    btn.disabled = false; btn.textContent = '🚀 Create Exam';
                }
            };
            reader.onerror = function() {
                showStatus('❌ Could not read the PDF file.', 'error');
                btn.disabled = false; btn.textContent = '🚀 Create Exam';
            };
            reader.readAsDataURL(file);
        } catch(error) {
            console.error(error);
            showStatus('❌ Something went wrong. Please try again.', 'error');
            btn.disabled = false; btn.textContent = '🚀 Create Exam';
        }
    }
    </script>
    """
    return render_admin_layout('create-exam', 'Create Exam', 'Upload question papers and configure examination settings.', body)

@app.route('/view-exams')
def view_exams():
    with get_db() as conn:
        exams = conn.cursor().execute("SELECT id,name,duration_minutes,created_at FROM exams ORDER BY created_at DESC").fetchall()
    cards = ''
    if exams:
        for e in exams:
            cards += f"""<div class="card" style="margin-bottom:0;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
                    <h3 style="font-size:18px; font-weight:700; color:var(--text-dark);">{e['name']}</h3>
                    <span class="badge badge-primary">⏱ {e['duration_minutes'] or 60} mins</span>
                </div>
                <p style="font-size:13px; color:var(--text-muted); margin-bottom:20px;">📅 Created: {e['created_at']}</p>
                <div style="display:flex; gap:10px;">
                    <button onclick="window.open('/api/exam/pdf/{e['id']}','_blank')" class="btn btn-sm btn-secondary" style="flex:1;">📄 View PDF</button>
                    <button onclick="deleteExam('{e['id']}')" class="btn btn-sm btn-danger" style="flex:1;">🗑 Delete Exam</button>
                </div>
            </div>"""
    else:
        cards = """<div style="grid-column:1/-1;">
            <div class="empty-state">
                <div class="empty-state-icon">📚</div>
                <h3>No examinations created yet</h3>
                <p>Upload your first question paper to create an exam.</p>
                <a href="/create-exam" class="btn btn-primary">➕ Create Exam</a>
            </div>
        </div>"""

    body = f"""
    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:24px;">
        {cards}
    </div>

    <script>
    function deleteExam(id) {{
        if (!confirm('Delete this exam/question paper? This action cannot be undone.')) return;
        fetch('/api/admin/delete-exam/' + encodeURIComponent(id), {{method:'POST'}})
            .then(r=>r.json())
            .then(d=>{{if(d.success){{alert('Exam deleted successfully.');location.reload();}}else{{alert(d.message||'Could not delete exam.');}}}})
            .catch(err=>alert('Delete failed: '+err));
    }}
    </script>
    """
    return render_admin_layout('view-exams', 'Exam Management', 'View created exams, preview question papers and delete exams.', body)

@app.route('/student-verification')
def student_verification():
    return render_template_string("""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>Student Verification - SmartScribe</title>
    <style>""" + COMMON_CSS + """
        .verify-wrapper {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background: radial-gradient(circle at 50% 0%, #FAF2FC 0%, #F8F6FA 70%);
        }
        .verify-nav {
            padding: 20px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #FFFFFF;
            border-bottom: 1px solid var(--border-color);
        }
        .step-bar {
            display: flex;
            justify-content: center;
            gap: 16px;
            margin: 24px 0;
        }
        .step {
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            background: #EFEAF2;
            color: var(--text-muted);
            transition: all 0.3s ease;
        }
        .step.active { background: var(--primary); color: white; box-shadow: 0 4px 12px var(--primary-glow); }
        .step.done { background: var(--success-bg); color: #047857; border: 1px solid var(--success-border); }
        .box {
            max-width: 520px;
            margin: 0 auto;
            background: #FFFFFF;
            border-radius: var(--radius-xl);
            padding: 32px;
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border-color);
        }
        .cam-prev {
            width: 100%;
            height: 300px;
            background: #111;
            border-radius: var(--radius-lg);
            margin: 16px 0;
            overflow: hidden;
            position: relative;
        }
        .status-box {
            padding: 14px;
            border-radius: var(--radius-md);
            margin: 16px 0;
            display: none;
            font-weight: 600;
            font-size: 14px;
            text-align: center;
        }
        .ok { background: var(--success-bg); color: #047857; border: 1px solid var(--success-border); }
        .err { background: var(--danger-bg); color: #DC2626; border: 1px solid var(--danger-border); }
        .voice-box {
            max-width: 520px;
            margin: 20px auto;
            background: #FFFFFF;
            border-radius: var(--radius-xl);
            padding: 32px;
            box-shadow: var(--shadow-lg);
            border: 2px dashed var(--primary-border);
            text-align: center;
            display: none;
        }
    </style></head><body>
    <div class="verify-wrapper">
        <header class="verify-nav">
            <div style="display:flex;align-items:center;gap:12px;">
                <div class="logo-badge">S</div>
                <span style="font-size:18px;font-weight:800;color:var(--text-dark);">SmartScribe</span>
            </div>
            <a href="/" class="btn btn-secondary btn-sm">← Home</a>
        </header>

        <div style="flex:1; padding: 32px 20px;">
            <div style="max-width: 520px; margin: 0 auto 20px;">
                <input type="text" id="regNo" placeholder="Enter Registration Number" class="form-control" style="font-size:18px; text-align:center; padding:16px; font-weight:700;">
            </div>

            <div class="step-bar">
                <div class="step active" id="step1">1 — Face</div>
                <div class="step" id="step2">2 — Voice</div>
                <div class="step" id="step3">3 — Exam</div>
            </div>

            <div id="statusMsg" class="status-box"></div>

            <!-- FACE BOX -->
            <div class="box" id="faceBox">
                <h3 style="color:var(--text-dark); text-align:center; font-size:20px; font-weight:800;">Step 1: Face Verification</h3>
                <div class="cam-prev">
                    <video id="cam" autoplay style="width:100%;height:100%;object-fit:cover;"></video>
                    <canvas id="camCanvas" style="display:none;"></canvas>
                </div>
                <div style="text-align:center;">
                    <button class="btn btn-primary" id="capBtn" onclick="captureImg()">📸 Capture Face</button>
                    <button class="btn btn-secondary" id="retakeBtn" onclick="retake()" style="display:none;">🔄 Retake</button>
                </div>
                <div id="faceStatus" style="text-align:center; margin-top:10px; color:var(--text-muted); font-size:13px;"></div>
                <button class="btn btn-primary" id="verifyFaceBtn" onclick="verifyFace()" style="margin-top:20px; width:100%;">Verify Face →</button>
            </div>

            <!-- VOICE BOX -->
            <div class="voice-box" id="voiceBox">
                <h3 style="color:var(--primary-dark); font-size:20px; font-weight:800; margin-bottom:12px;">Step 2: Voice Verification</h3>
                <p style="color:var(--text-muted); margin-bottom:16px; font-size:14px;">
                    Please say: <strong>"My name is [your name] and I am ready for my exam"</strong>
                </p>
                <div style="display:flex; justify-content:center; gap:10px;">
                    <button class="btn btn-danger" id="vRecBtn" onclick="startVoice()">🎙️ Record Voice</button>
                    <button class="btn btn-secondary" id="vStopBtn" onclick="stopVoice()" style="display:none;">⏹ Stop</button>
                </div>
                <div id="vStatus" style="font-size:14px; color:var(--text-muted); margin-top:12px;">Press Record to begin</div>
                <audio id="vPlayback" controls style="display:none; width:100%; margin-top:14px; border-radius:8px;"></audio>
                <button class="btn btn-primary" id="verifyVoiceBtn" onclick="verifyVoice()" style="margin-top:20px; width:100%; display:none;">Verify Voice →</button>
            </div>
        </div>
    </div>

    <script>
    let capturedImg=null,faceCaptured=false,voiceB64=null,vMR=null,vChunks=[],vAutoStop=null;

    navigator.mediaDevices.getUserMedia({video:true})
        .then(s=>{document.getElementById('cam').srcObject=s;})
        .catch(()=>showStatus('Camera access denied','err'));

    function showStatus(msg,type){
        const d=document.getElementById('statusMsg');
        d.textContent=msg; d.className='status-box '+type; d.style.display='block';
        setTimeout(()=>d.style.display='none',6000);
    }
    function setStep(n){
        ['step1','step2','step3'].forEach((id,i)=>{
            document.getElementById(id).className='step'+(i+1<n?' done':i+1===n?' active':'');
        });
    }
    function captureImg(){
        const v=document.getElementById('cam'),c=document.getElementById('camCanvas');
        c.width=v.videoWidth;c.height=v.videoHeight;
        c.getContext('2d').drawImage(v,0,0);
        capturedImg=c.toDataURL('image/jpeg');
        const img=document.createElement('img');img.src=capturedImg;img.style='width:100%;height:100%;object-fit:cover;';
        v.style.display='none';v.parentNode.appendChild(img);
        document.getElementById('capBtn').style.display='none';
        document.getElementById('retakeBtn').style.display='inline-flex';
        document.getElementById('faceStatus').textContent='✅ Face captured!';
        faceCaptured=true;
    }
    function retake(){
        capturedImg=null;faceCaptured=false;
        const v=document.getElementById('cam');v.style.display='block';
        const img=v.parentNode.querySelector('img');if(img)img.remove();
        document.getElementById('capBtn').style.display='inline-flex';
        document.getElementById('retakeBtn').style.display='none';
        document.getElementById('faceStatus').textContent='';
    }
    function verifyFace(){
        const regNo=document.getElementById('regNo').value.trim();
        if(!regNo){showStatus('Enter registration number','err');return;}
        if(!faceCaptured){showStatus('Capture your face first','err');return;}
        const btn=document.getElementById('verifyFaceBtn');btn.disabled=true;btn.textContent='Verifying...';
        fetch('/api/student/verify-face',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({regNo,image:capturedImg})})
        .then(r=>r.json()).then(d=>{
            if(d.success){
                showStatus('✅ Face verified! Now verify your voice.','ok');
                document.getElementById('faceBox').style.opacity='0.55';
                document.getElementById('voiceBox').style.display='block';
                setStep(2);
            }else{showStatus('❌ '+d.message,'err');btn.disabled=false;btn.textContent='Verify Face →';}
        }).catch(()=>{showStatus('Error. Try again.','err');btn.disabled=false;btn.textContent='Verify Face →';});
    }

    async function startVoice(){
        vChunks=[];voiceB64=null;
        document.getElementById('vPlayback').style.display='none';
        let stream;
        try{stream=await navigator.mediaDevices.getUserMedia({audio:{sampleRate:16000,channelCount:1,echoCancellation:true}});}
        catch(e){showStatus('Microphone denied: '+e.message,'err');return;}
        const mime=MediaRecorder.isTypeSupported('audio/wav')?'audio/wav':
                   MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?'audio/webm;codecs=opus':'audio/webm';
        vMR=new MediaRecorder(stream,{mimeType:mime});
        vMR.ondataavailable=e=>vChunks.push(e.data);
        vMR.onstop=()=>{
            const blob=new Blob(vChunks,{type:mime});
            document.getElementById('vPlayback').src=URL.createObjectURL(blob);
            document.getElementById('vPlayback').style.display='block';
            const reader=new FileReader();
            reader.onload=e=>{
                voiceB64=e.target.result.split(',')[1];
                document.getElementById('vStatus').textContent='✅ Recording done. Press Verify Voice.';
                document.getElementById('verifyVoiceBtn').style.display='block';
            };
            reader.readAsDataURL(blob);
            stream.getTracks().forEach(t=>t.stop());
        };
        vMR.start();
        document.getElementById('vRecBtn').style.display='none';
        document.getElementById('vStopBtn').style.display='inline-flex';
        document.getElementById('vStatus').textContent='🔴 Recording... speak clearly';
        vAutoStop=setTimeout(()=>{if(vMR&&vMR.state==='recording')stopVoice();},8000);
    }
    function stopVoice(){
        if(vAutoStop){clearTimeout(autoStopTimer);vAutoStop=null;}
        if(vMR&&vMR.state==='recording')vMR.stop();
        document.getElementById('vRecBtn').style.display='inline-flex';
        document.getElementById('vStopBtn').style.display='none';
    }
    function verifyVoice(){
        const regNo=document.getElementById('regNo').value.trim();
        if(!voiceB64){showStatus('Record voice first','err');return;}
        const btn=document.getElementById('verifyVoiceBtn');btn.disabled=true;btn.textContent='Verifying voice...';
        fetch('/api/student/verify-voice',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({regNo,voice:voiceB64})})
        .then(r=>r.json()).then(d=>{
            if(d.success){
                showStatus('✅ Voice verified! Entering exam...','ok');
                setStep(3);
                setTimeout(()=>window.location.href='/exam-page?regNo='+regNo,1200);
            }else{showStatus('❌ '+d.message+' — please try again','err');btn.disabled=false;btn.textContent='Verify Voice →';}
        }).catch(()=>{showStatus('Error. Try again.','err');btn.disabled=false;btn.textContent='Verify Voice →';});
    }
    </script></body></html>
    """)

@app.route('/exam-page')
def exam_page():
    regNo = request.args.get('regNo', '')
    return render_template_string("""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    <title>SmartScribe — Examination Environment</title>
    <style>""" + COMMON_CSS + """
        body { background: #FAF7FC; font-size: 18px; }
        .exam-shell {
            max-width: 960px;
            margin: 20px auto;
            padding: 0 16px;
        }
        .exam-header-bar {
            background: var(--bg-sidebar);
            color: white;
            padding: 20px 28px;
            border-radius: var(--radius-xl);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-lg);
            margin-bottom: 24px;
        }
        .timer-box {
            background: rgba(255,255,255,0.12);
            color: #FFFFFF;
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 22px;
            font-weight: 800;
            border: 1px solid rgba(255,255,255,0.2);
            letter-spacing: 1px;
        }
        .timer-box.warn { color: #FF6B6B; background: rgba(255,71,87,0.2); animation: blink 0.8s infinite; }
        @keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.4;} }
        
        .status-bubble {
            background: #FFFFFF;
            border: 3px solid var(--primary);
            border-radius: var(--radius-xl);
            padding: 28px;
            font-size: 22px;
            font-weight: 600;
            color: var(--text-dark);
            line-height: 1.6;
            min-height: 100px;
            margin-bottom: 24px;
            text-align: center;
            box-shadow: var(--shadow-md);
        }
        .mic-area {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            background: #FFFFFF;
            padding: 24px;
            border-radius: var(--radius-xl);
            border: 1px solid var(--border-color);
        }
        .mic-icon { font-size: 64px; }
        .mic-icon.listening { animation: pulse 1.2s infinite; }
        @keyframes pulse { 0%,100%{transform:scale(1);} 50%{transform:scale(1.2);} }
        .mic-label { font-size: 16px; color: var(--text-muted); font-weight: 600; }
        .mic-label.active { color: var(--primary); font-weight: 800; }
        .wave-anim { display: none; justify-content: center; gap: 6px; height: 40px; align-items: center; }
        .wave-anim.show { display: flex; }
        .wbar { width: 8px; background: var(--primary); border-radius: 4px; animation: wave 1s ease-in-out infinite; }
        .wbar:nth-child(1){height:16px;animation-delay:0s;}.wbar:nth-child(2){height:32px;animation-delay:.15s;}
        .wbar:nth-child(3){height:46px;animation-delay:.3s;}.wbar:nth-child(4){height:32px;animation-delay:.45s;}
        .wbar:nth-child(5){height:16px;animation-delay:.6s;}
        @keyframes wave{0%,100%{transform:scaleY(.4);}50%{transform:scaleY(1);}}
        
        .transcript-box {
            background: var(--primary-light);
            border: 2px dashed var(--primary);
            border-radius: var(--radius-lg);
            padding: 20px;
            font-size: 18px;
            color: var(--text-dark);
            min-height: 60px;
            display: none;
            margin-bottom: 20px;
        }
        .transcript-box.show { display: block; }
        .progress-wrap { background: #EFEAF2; border-radius: 10px; height: 12px; margin-bottom: 8px; display: none; overflow:hidden; }
        .progress-wrap.show { display: block; }
        .progress-fill { background: var(--primary); height: 100%; border-radius: 10px; transition: width .4s; }
        .progress-text { text-align: center; color: var(--text-muted); font-size: 15px; font-weight: 700; margin-bottom: 16px; display: none; }
        .progress-text.show { display: block; }
        
        .hint-box {
            background: var(--success-bg);
            border: 1px solid var(--success-border);
            border-radius: var(--radius-lg);
            padding: 16px 24px;
            font-size: 15px;
            color: #047857;
            display: none;
            margin-top: 20px;
        }
        .hint-box.show { display: block; }
        .hint-pill { display: inline-block; background: white; padding: 4px 12px; border-radius: 20px; margin: 4px; border: 1px solid var(--success-border); font-weight: 700; }
        .voice-warn { display: none; background: var(--warning-bg); border: 2px solid var(--warning); color: #B45309; border-radius: var(--radius-md); padding: 14px; font-size: 15px; font-weight: 700; margin-bottom: 16px; text-align: center; }
        .voice-warn.show { display: block; }
    </style></head><body>
    <div class="exam-shell">
        <div class="exam-header-bar">
            <div style="display:flex;align-items:center;gap:12px;">
                <div class="logo-badge">S</div>
                <h1 style="font-size:20px;font-weight:800;color:white;">SmartScribe Exam</h1>
            </div>
            <div style="display:flex;align-items:center;gap:16px;">
                <div class="timer-box" id="timerBox">--:--</div>
                <button class="btn btn-secondary btn-sm" onclick="confirmLogout()" style="background:rgba(255,255,255,0.15);color:white;border-color:rgba(255,255,255,0.3);">🚪 Logout</button>
            </div>
        </div>

        <div class="voice-warn" id="voiceWarn">⚠️ Warning: Unrecognised voice detected — please speak yourself</div>
        <div class="status-bubble" id="statusBubble">Initializing... please wait.</div>
        
        <div class="progress-text" id="progressText">Question 1 of 0</div>
        <div class="progress-wrap" id="progressWrap"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>

        <div class="mic-area">
            <div class="mic-icon" id="micIcon">🎙️</div>
            <div class="mic-label" id="micLabel">Waiting...</div>
            <div class="wave-anim" id="waveAnim">
                <div class="wbar"></div><div class="wbar"></div><div class="wbar"></div>
                <div class="wbar"></div><div class="wbar"></div>
            </div>
        </div>

        <div class="transcript-box" id="transcriptBox">
            <div style="font-size:12px;color:var(--primary);font-weight:700;margin-bottom:6px;">🗣️ I heard:</div>
            <div id="transcriptText"></div>
        </div>

        <div class="hint-box" id="hintBox">
            <strong>Voice Commands:</strong>
            <span class="hint-pill">"next" → next question</span>
            <span class="hint-pill">"repeat" → hear again</span>
            <span class="hint-pill">"submit" → finish exam</span>
        </div>

        <div class="submit-area" id="submitArea" style="display:none; text-align:center; margin-top:32px;">
            <p style="color:var(--text-muted); margin-bottom:12px;">Or click to submit:</p>
            <button class="btn btn-primary btn-lg" id="submitBtn" onclick="manualSubmit()">📄 Submit Exam</button>
        </div>
    </div>

    <script>
    const urlP = new URLSearchParams(window.location.search);
    const regNo = urlP.get('regNo') || '""" + regNo + """';
    if(!regNo){alert('No reg number. Please verify first.');window.location.href='/student-verification';}

    let questions=[], answers=[], currentIndex=0, examId=null, examName='', studentName='';
    let examDurSec=3600, timerLeft=0, timerIntvl=null;

    const S = {IDLE:'idle',WAIT:'waiting_start',SEL:'selecting_exam',
               READQ:'reading_q',LISTENS:'listening_ans',CONFIRM:'confirming_ans',
               SUBMIT_Q:'asking_submit',SUBMITTING:'submitting'};
    let state = S.IDLE;

    let recognition=null, finalT='', interimT='', isSpeaking=false, silTimer=null;
    let recognitionRunning = false;
    let recognitionStarting = false;
    let answerBuffer = '';
    let restartTimer = null;
    let availExams=[];

    function startTimer(s){
        timerLeft=s;
        timerIntvl=setInterval(()=>{
            timerLeft--; updateTimerUI();
            if(timerLeft<=300) document.getElementById('timerBox').classList.add('warn');
            if(timerLeft>0 && timerLeft<=60 && timerLeft%30===0) speak(timerLeft+' seconds remaining.');
            if(timerLeft<=0){clearInterval(timerIntvl); autoSubmit();}
        },1000);
    }
    function updateTimerUI(){
        const m=Math.floor(timerLeft/60), s=timerLeft%60;
        document.getElementById('timerBox').textContent=String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');
    }
    function autoSubmit(){
        stopListening();
        const cur=(finalT+interimT).trim(); if(cur) saveAnswer(cur);
        setStatus('⏰ Time is up! Submitting...');
        speak('Time is up. Submitting your exam now.',()=>doSubmit());
    }

    function setStatus(msg){ document.getElementById('statusBubble').textContent=msg; }
    function setMic(st){
        const ic=document.getElementById('micIcon'), lb=document.getElementById('micLabel'), wv=document.getElementById('waveAnim');
        if(st==='listening'){ic.textContent='🎙️';ic.className='mic-icon listening';lb.textContent='🔴 Listening... speak now';lb.className='mic-label active';wv.classList.add('show');}
        else if(st==='speaking'){ic.textContent='🔊';ic.className='mic-icon';lb.textContent='Speaking...';lb.className='mic-label';wv.classList.remove('show');}
        else{ic.textContent='🎙️';ic.className='mic-icon';lb.textContent='Waiting...';lb.className='mic-label';wv.classList.remove('show');}
    }
    function showT(t){document.getElementById('transcriptText').textContent=t;document.getElementById('transcriptBox').classList.add('show');}
    function hideT(){document.getElementById('transcriptBox').classList.remove('show');}
    function showProgress(){
        ['progressText','progressWrap','hintBox','submitArea'].forEach(id=>document.getElementById(id).style.display='block');
    }
    function updProgress(){
        const pct=((currentIndex+1)/questions.length)*100;
        document.getElementById('progressFill').style.width=pct+'%';
        document.getElementById('progressText').textContent='Question '+(currentIndex+1)+' of '+questions.length;
    }

    function speak(text, cb){
        isSpeaking=true; setMic('speaking');
        window.speechSynthesis.cancel();
        const u=new SpeechSynthesisUtterance(text);
        u.rate=1.05; u.pitch=1;
        u.onend=()=>{isSpeaking=false; if(cb)cb();};
        u.onerror=()=>{isSpeaking=false; if(cb)cb();};
        window.speechSynthesis.speak(u);
    }

    function initRec(){
        if(!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)){
            setStatus('❌ Speech recognition is not supported. Please use Google Chrome.');
            return false;
        }
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SR();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        recognition.onstart = function(){
            recognitionRunning = true;
            recognitionStarting = false;
            console.log('🎤 Microphone listening started');
            setMic('listening');
        };

        recognition.onresult = function(ev){
            finalT = ''; interimT = '';
            for(let i = ev.resultIndex; i < ev.results.length; i++){
                const t = ev.results[i][0].transcript;
                if(ev.results[i].isFinal){ finalT += t; }else{ interimT += t; }
            }
            const currentSpeech = (finalT + interimT).trim();
            const lower = currentSpeech.toLowerCase();
            if(currentSpeech){ showT(currentSpeech); console.log('🎤 Heard:', currentSpeech); }

            if(state === S.WAIT){
                if(lower.includes('yes') || lower.includes('yeah') || lower.includes('yep') || lower.includes('ready') || lower.includes('start')){
                    stopListening(); startExamFlow(); return;
                }
            } else if(state === S.SEL){
                const m = matchExam(lower);
                if(m !== null){ stopListening(); examId = availExams[m].id; examName = availExams[m].name; loadQuestions(); return; }
            } else if(state === S.LISTENS){
                if(finalT){ answerBuffer += ' ' + finalT.trim(); answerBuffer = answerBuffer.trim(); }
                const displayText = (answerBuffer + ' ' + interimT).trim();
                if(displayText){ showT(displayText); console.log('📝 Current answer:', displayText); }
                resetSilTimer();
                const commandText = currentSpeech.toLowerCase();
                const words = commandText.trim().split(/\s+/);
                const isShort = words.length <= 4;

                if(isShort && (commandText.includes('next') || commandText.includes('done') || commandText.includes('move on'))){
                    stopListening(); saveAnswer(answerBuffer); confirmAndProceed(); return;
                }
                if(isShort && (commandText.includes('repeat') || commandText.includes('again') || commandText.includes('reread'))){
                    stopListening(); readQ(); return;
                }
                if(isShort && (commandText.includes('submit') || commandText.includes('finish') || commandText.includes('end exam'))){
                    stopListening(); saveAnswer(answerBuffer); askSubmit(); return;
                }
            } else if(state === S.CONFIRM){
                if(lower.includes('next') || lower.includes('yes') || lower.includes('continue') || lower.includes('ok')){
                    stopListening(); goNext(); return;
                } else if(lower.includes('repeat') || lower.includes('again') || lower.includes('no') || lower.includes('redo')){
                    stopListening(); readQ(); return;
                } else if(lower.includes('submit') || lower.includes('finish')){
                    stopListening(); askSubmit(); return;
                }
            } else if(state === S.SUBMIT_Q){
                if(lower.includes('yes') || lower.includes('submit') || lower.includes('confirm') || lower.includes('ok')){
                    stopListening(); doSubmit(); return;
                } else if(lower.includes('no') || lower.includes('cancel') || lower.includes('back')){
                    stopListening(); state = S.LISTENS; readQ(); return;
                }
            }
        };

        recognition.onerror = function(e){
            console.log('🎤 Speech recognition error:', e.error);
            recognitionStarting = false;
            if(e.error === 'not-allowed' || e.error === 'service-not-allowed'){
                recognitionRunning = false; setMic('idle');
                setStatus('❌ Microphone permission denied. Please allow microphone access in Chrome.');
                return;
            }
            if(e.error === 'audio-capture'){
                recognitionRunning = false; setMic('idle');
                setStatus('❌ Microphone not found. Please check your microphone.');
                return;
            }
            recognitionRunning = false; scheduleRecognitionRestart();
        };

        recognition.onend = function(){
            console.log('🎤 Speech recognition ended');
            recognitionRunning = false; recognitionStarting = false;
            if([S.LISTENS, S.WAIT, S.SEL, S.CONFIRM, S.SUBMIT_Q].includes(state) && !isSpeaking){
                scheduleRecognitionRestart();
            }
        };
        return true;
    }

    function scheduleRecognitionRestart(){
        if(restartTimer){ clearTimeout(restartTimer); }
        restartTimer = setTimeout(()=>{
            restartTimer = null;
            if(!recognition || recognitionRunning || recognitionStarting){ return; }
            if(![S.LISTENS, S.WAIT, S.SEL, S.CONFIRM, S.SUBMIT_Q].includes(state)){ return; }
            try{
                recognitionStarting = true; recognition.start();
                console.log('🔄 Speech recognition restarted');
            }catch(e){
                recognitionStarting = false; scheduleRecognitionRestart();
            }
        }, 700);
    }

    function startListening(){
        finalT = ''; interimT = ''; hideT();
        if(!recognition){
            setStatus('❌ Voice recognition is not available. Please use Google Chrome.');
            setMic('idle'); return;
        }
        setMic('listening'); setStatus('🎤 Listening... Please speak now.');
        if(recognitionRunning || recognitionStarting){ return; }
        try{
            recognitionStarting = true; recognition.start();
        }catch(e){
            recognitionStarting = false; scheduleRecognitionRestart();
        }
    }

    function stopListening(){
        clearSilTimer(); setMic('idle');
        try{ recognition.stop(); }catch(e){}
    }

    function resetSilTimer(){
        clearSilTimer();
        silTimer = setTimeout(()=>{
            if(state === S.LISTENS && !isSpeaking){
                const ans = answerBuffer.trim();
                if(ans.length > 1){
                    setStatus('🎤 You can continue your answer or say NEXT when finished.');
                    resetSilTimer();
                }
            }
        },5000);
    }

    function clearSilTimer(){ if(silTimer){clearTimeout(silTimer);silTimer=null;} }

    function fmtTTS(q){
        const pat=/(?:^|\s)([a-dA-D])\)\s*/g;
        const matches=[...q.matchAll(pat)];
        if(!matches.length) return q;
        const stem=q.substring(0,matches[0].index).trim();
        let res=stem;
        matches.forEach((m,idx)=>{
            const letter=m[1].toLowerCase();
            const start=m.index+m[0].length;
            const end=idx+1<matches.length?matches[idx+1].index:q.length;
            const opt=q.substring(start,end).trim().replace(/\.$/, '');
            res+='. '+letter+', '+opt;
        });
        return res;
    }

    function init(){
        if(!initRec()) return;
        fetch('/api/student/data?regNo='+regNo).then(r=>r.json()).then(d=>{ if(d.name)studentName=d.name; });
        fetch('/api/student/available-exams').then(r=>r.json()).then(d=>{
            availExams=d.exams||[]; greet();
        });
    }

    function greet(){
        state=S.WAIT;
        const g=studentName
            ?('Hello '+studentName+'! Welcome to SmartScribe. Are you ready to begin your exam? Say YES when ready.')
            :'Welcome to SmartScribe exam. Are you ready? Say YES when ready.';
        setStatus(g); speak(g,()=>startListening());
    }

    function matchExam(text){
        text = (text || '').toLowerCase().trim();
        const numberWords = ['zero','one','two','three','four','five','six','seven','eight','nine','ten'];
        for(let i = 0; i < availExams.length; i++){
            const num = i + 1; const word = numberWords[num];
            if(new RegExp(`\\\\b${num}\\\\b`).test(text) || new RegExp(`\\\\b${word}\\\\b`).test(text) || text.includes('option ' + word) || text.includes('option ' + num)){ return i; }
            if(availExams[i].name && text.includes(availExams[i].name.toLowerCase())){ return i; }
        }
        return null;
    }

    function startExamFlow(){
        if(availExams.length===0){speak('No exams available. Contact your administrator.');return;}
        if(availExams.length===1){examId=availExams[0].id;examName=availExams[0].name;loadQuestions();return;}
        state=S.SEL;
        let msg='You have '+availExams.length+' exams available. ';
        availExams.forEach((e,i)=>msg+='Option '+(i+1)+': '+e.name+'. ');
        msg+='Say the number or name of your exam.';
        setStatus(msg); speak(msg,()=>startListening());
    }

    function loadQuestions(){
        setStatus('Loading exam...'); speak('Loading '+examName+'. Please wait.',null);
        fetch('/api/exam/questions/'+examId).then(r=>r.json()).then(d=>{
            if(d.questions&&d.questions.length>0){
                questions=d.questions; answers=new Array(questions.length).fill('');
                examDurSec=(d.duration_minutes||60)*60;
                currentIndex=0; showProgress(); updProgress();
                startTimer(examDurSec);
                const intro='Exam loaded. You have '+questions.length+' questions and '+(d.duration_minutes||60)+
                    ' minutes. After each question I will start recording your answer. '+
                    'Say NEXT after your answer, REPEAT to hear the question again, or SUBMIT when finished. '+
                    'Starting now. Question 1.';
                setStatus('✅ Exam started!'); speak(intro,()=>readQ());
            }else{speak('No questions found. Contact your administrator.');}
        }).catch(()=>speak('Error loading exam. Please try again.'));
    }

    function readQ(){
        state=S.READQ; updProgress(); clearSilTimer(); hideT();
        const raw = questions[currentIndex];
        const cleanQuestion = raw.replace(/^\s*\d+\s*[\.\):\-]?\s*/, '').trim();
        const spoken = fmtTTS(cleanQuestion);
        setStatus('📢 Q'+(currentIndex+1)+': '+raw);
        speak('Question '+(currentIndex+1)+'. '+spoken,()=>{
            state = S.LISTENS;
            finalT = ''; interimT = ''; answerBuffer = '';
            setStatus('🎤 Listening... speak your answer.');
            startListening(); resetSilTimer();
        });
    }

    function saveAnswer(text){
        const cleaned = (text || '').trim();
        if(cleaned){ answers[currentIndex] = cleaned; }
    }

    function confirmAndProceed(){
        state=S.CONFIRM;
        const ans=answers[currentIndex];
        if(!ans||!ans.trim()){
            const m='I did not catch your answer. Say REPEAT to hear the question again, or NEXT to skip.';
            setStatus('⚠️ '+m); speak(m,()=>startListening()); return;
        }
        const m='I recorded: '+ans+'. Say NEXT to move on, or REPEAT to redo this question.';
        setStatus('✅ Recorded: '+ans); speak(m,()=>startListening());
    }

    function goNext(){
        if(currentIndex<questions.length-1){currentIndex++;readQ();}else{askSubmit();}
    }

    function askSubmit(){
        state=S.SUBMIT_Q;
        const m='You have completed all '+questions.length+' questions. Say YES to submit and download your answer sheet, or NO to go back to the last question.';
        setStatus('📄 Ready to submit?'); speak(m,()=>startListening());
    }

    function manualSubmit(){
        if(state===S.SUBMITTING) return;
        const cur=(finalT+interimT).trim(); if(cur) saveAnswer(cur);
        stopListening();
        if(confirm('Submit your exam now? Your answers will be downloaded as a PDF.')) doSubmit();
    }

    function doSubmit(){
        if(state===S.SUBMITTING) return;
        state=S.SUBMITTING;
        clearInterval(timerIntvl); 
        const btn=document.getElementById('submitBtn');
        if(btn){btn.disabled=true;btn.textContent='⏳ Submitting...';}
        setMic('idle'); setStatus('⏳ Submitting and generating your answer PDF...');
        speak('Submitting your exam. Please wait.',null);
        const aData=questions.map((q,i)=>({question:q,answer:answers[i]||''}));
        fetch('/api/exam/submit',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({regNo,examId,examName,studentName,answers:aData})})
        .then(res=>{if(!res.ok)throw new Error('Server error '+res.status);return res.blob();})
        .then(blob=>{
            const url=window.URL.createObjectURL(blob);
            const a=document.createElement('a');a.href=url;
            const sn=(studentName||regNo).replace(/[^a-zA-Z0-9]/g,'_');
            const se=(examName||'Exam').replace(/[^a-zA-Z0-9]/g,'_');
            a.download=sn+'.'+se+'.pdf';
            document.body.appendChild(a);a.click();a.remove();
            window.URL.revokeObjectURL(url);
            setStatus('🎉 Exam submitted! Answer sheet downloaded.');
            speak('Congratulations! Your exam has been submitted and your answer sheet downloaded. Well done!',null);
            document.getElementById('timerBox').textContent='Done';
            document.getElementById('timerBox').classList.remove('warn');
        }).catch(err=>{
            console.error(err);
            setStatus('❌ Submission error. Please contact your invigilator.');
            speak('There was an error submitting. Please inform your invigilator.',null);
            if(btn){btn.disabled=false;btn.textContent='📄 Submit Exam';}
            state=S.SUBMIT_Q;
        });
    }

    function confirmLogout(){
        if(confirm('Logout? Unsaved answers will be lost.')){
            window.speechSynthesis.cancel();
            clearInterval(timerIntvl); 
            if(recognition)try{recognition.stop();}catch(e){}
            window.location.href='/';
        }
    }

    window.addEventListener('load',()=>setTimeout(init,500));
    window.addEventListener('beforeunload',()=>{
        window.speechSynthesis.cancel(); 
        if(recognition)try{recognition.stop();}catch(e){}
    });
    </script></body></html>
    """, regNo=regNo)
'''

full_code = prefix + ui_code.strip() + suffix

with open('app1.py', 'w', encoding='utf-8') as f:
    f.write(full_code)

print("SUCCESS: app1.py updated with redesigned UI!")
