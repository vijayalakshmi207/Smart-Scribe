from flask import render_template_string, request

COMMON_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Caveat:wght@600;700&display=swap');

:root {
  --purple-accent: #7C3AED;
  --purple-bright: #8B5CF6;
  --purple-soft: #F3E8FF;
  --purple-border: #E9D5FF;
  
  --blue-primary: #2563EB;
  --blue-bright: #3B82F6;
  --blue-soft: #EFF6FF;
  --blue-border: #BFDBFE;

  --teal-accent: #0D9488;
  --teal-bright: #14B8A6;
  --teal-soft: #CCFBF1;
  --teal-border: #99F6E4;

  --cyan-bright: #06B6D4;
  --navy-darkest: #0B0F19;
  --navy-deep: #111827;
  --navy-blue: #1E293B;

  --page-bg: #F8FAFC;
  --card-bg: #FFFFFF;

  --text-dark: #0F172A;
  --text-body: #334155;
  --text-muted: #64748B;
  --text-light: #94A3B8;

  --border-color: #E2E8F0;

  --success: #10B981;
  --success-bg: #ECFDF5;
  --success-border: #A7F3D0;

  --warning: #F59E0B;
  --warning-bg: #FFFBEB;
  --warning-border: #FDE68A;

  --danger: #EF4444;
  --danger-bg: #FEF2F2;
  --danger-border: #FCA5A5;

  --shadow-sm: 0 2px 8px rgba(124, 58, 237, 0.04);
  --shadow-md: 0 10px 30px rgba(124, 58, 237, 0.08);
  --shadow-lg: 0 20px 40px rgba(15, 23, 42, 0.12);
  --shadow-purple: 0 12px 28px rgba(124, 58, 237, 0.25);
  --shadow-teal: 0 12px 28px rgba(13, 148, 136, 0.25);

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 18px;
  --radius-xl: 24px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}

*:focus-visible {
  outline: 3px solid var(--purple-accent);
  outline-offset: 2px;
}

body {
  background-color: var(--navy-darkest);
  color: var(--text-dark);
  min-height: 100vh;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  position: relative;
  overflow-x: hidden;
}

a {
  color: var(--purple-accent);
  text-decoration: none;
  transition: all 0.2s ease;
}

/* SUBTLE ANIMATED BACKGROUND BLOBS */
.animated-bg-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  z-index: 0;
  pointer-events: none;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.22;
}

.blob-1 {
  width: 550px;
  height: 550px;
  background: radial-gradient(circle, #7C3AED 0%, #8B5CF6 100%);
  top: -120px;
  left: -120px;
  animation: floatBlob1 20s ease-in-out infinite;
}

.blob-2 {
  width: 650px;
  height: 650px;
  background: radial-gradient(circle, #2563EB 0%, #3B82F6 100%);
  bottom: -160px;
  right: -160px;
  animation: floatBlob2 24s ease-in-out infinite;
}

.blob-3 {
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, #0D9488 0%, #14B8A6 100%);
  top: 40%;
  left: 35%;
  animation: floatBlob3 22s ease-in-out infinite;
}

@keyframes floatBlob1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(80px, -50px) scale(1.12); }
}

@keyframes floatBlob2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-70px, 70px) scale(0.92); }
}

@keyframes floatBlob3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(60px, 80px) scale(1.1); }
}

/* GLOBAL ENTERPRISE LAYOUT */
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: linear-gradient(180deg, #0B0F19 0%, #111827 100%);
  position: relative;
  z-index: 1;
}

.top-header-bar {
  height: 76px;
  background: rgba(11, 15, 25, 0.95);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 110;
}

.top-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon-3d {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #7C3AED 0%, #2563EB 50%, #0D9488 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
  box-shadow: 0 4px 18px rgba(124, 58, 237, 0.45);
}

.brand-text h2 {
  font-size: 20px;
  font-weight: 800;
  color: #FFFFFF;
  letter-spacing: -0.5px;
  line-height: 1.1;
}

.brand-text p {
  font-size: 11px;
  color: #94A3B8;
  font-weight: 500;
}

.top-header-center {
  flex: 1;
  max-width: 440px;
  margin: 0 32px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input-wrapper svg {
  position: absolute;
  left: 16px;
  color: #64748B;
}

.search-input {
  width: 100%;
  padding: 10px 16px 10px 44px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 30px;
  color: #FFFFFF;
  font-size: 13px;
  outline: none;
  transition: all 0.2s ease;
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--purple-accent);
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.25);
}

.top-header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.slogan-handwritten {
  font-family: 'Caveat', cursive;
  font-size: 24px;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.5px;
}

.header-action-icon {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94A3B8;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.app-body {
  display: flex;
  flex: 1;
  padding: 24px 32px 32px;
  gap: 24px;
}

/* SIDEBAR */
.sidebar {
  width: 240px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 13px 20px;
  color: #94A3B8;
  text-decoration: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #FFFFFF;
}

.nav-link.active {
  background: linear-gradient(135deg, var(--purple-accent) 0%, var(--blue-primary) 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 18px rgba(124, 58, 237, 0.4);
}

.nav-link svg {
  stroke-width: 2;
}

.sidebar-promo-card {
  margin-top: auto;
  margin-bottom: 16px;
  background: linear-gradient(180deg, rgba(124, 58, 237, 0.15) 0%, rgba(13, 148, 136, 0.2) 100%);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: var(--radius-lg);
  padding: 20px 16px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.promo-quote {
  font-size: 12px;
  color: #C4B5FD;
  line-height: 1.5;
  font-weight: 600;
  font-style: italic;
}

.logout-link {
  color: #F87171 !important;
}

.logout-link:hover {
  background: rgba(239, 68, 68, 0.12) !important;
}

/* MAIN CONTENT CONTAINER PANEL */
.main-content-panel {
  flex: 1;
  background: var(--page-bg);
  border-radius: 28px;
  padding: 36px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
  min-height: calc(100vh - 130px);
}

/* DASHBOARD PANEL LAYOUT */
.dashboard-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
}

.dash-welcome {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-dark);
  letter-spacing: -0.6px;
}

.text-purple { color: var(--purple-accent); }
.text-blue { color: var(--blue-primary); }
.text-teal { color: var(--teal-accent); }

.dash-sub {
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 4px;
}

.header-quote-box {
  background: #FFFFFF;
  border-left: 3.5px solid var(--purple-accent);
  padding: 10px 16px;
  border-radius: 8px;
  box-shadow: var(--shadow-sm);
}

.header-quote-box p {
  font-size: 12px;
  font-style: italic;
  color: var(--text-muted);
  font-weight: 500;
}

/* PROCESS / PROGRESS UI STEPPER BAR */
.student-progress-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #FFFFFF;
  border-radius: var(--radius-xl);
  padding: 20px 32px;
  margin-bottom: 32px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  overflow-x: auto;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.step-num {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #F1F5F9;
  color: var(--text-muted);
  font-weight: 800;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #CBD5E1;
}

.step-item.active .step-num {
  background: linear-gradient(135deg, var(--purple-accent) 0%, var(--blue-primary) 100%);
  color: #FFFFFF;
  border: none;
  box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
}

.step-item.completed .step-num {
  background: var(--teal-accent);
  color: #FFFFFF;
  border: none;
}

.step-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-dark);
}

.step-line {
  flex: 1;
  min-width: 24px;
  max-width: 60px;
  height: 3px;
  background: #E2E8F0;
  border-radius: 2px;
  margin: 0 8px;
}

.step-line.active {
  background: linear-gradient(90deg, var(--purple-accent) 0%, var(--teal-accent) 100%);
}

/* METRICS GRID */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 24px;
  margin-bottom: 36px;
}

.metric-card {
  background: #FFFFFF;
  border-radius: var(--radius-lg);
  padding: 24px 28px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  overflow: hidden;
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s ease;
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.metric-icon-box {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.purple-icon { background: var(--purple-soft); color: var(--purple-accent); border: 1px solid var(--purple-border); }
.blue-icon { background: var(--blue-soft); color: var(--blue-primary); border: 1px solid var(--blue-border); }
.teal-icon { background: var(--teal-soft); color: var(--teal-accent); border: 1px solid var(--teal-border); }
.orange-icon { background: #FFFBEB; color: #F59E0B; border: 1px solid #FDE68A; }

.metric-content { flex: 1; }
.metric-label { font-size: 13px; font-weight: 600; color: var(--text-muted); }
.metric-number-row { display: flex; align-items: baseline; gap: 12px; margin-top: 4px; }
.metric-num { font-size: 34px; font-weight: 800; color: var(--text-dark); line-height: 1; letter-spacing: -1px; }
.metric-trend { font-size: 12px; font-weight: 700; color: var(--success); }

/* QUICK ACTIONS GRID */
.quick-actions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.quick-actions-header h3 {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-dark);
}

.see-all-link {
  font-size: 13px;
  font-weight: 700;
  color: var(--purple-accent);
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.action-card {
  background: #FFFFFF;
  border-radius: var(--radius-lg);
  padding: 24px 20px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  position: relative;
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s ease, border-color 0.22s ease;
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 35px -10px rgba(124, 58, 237, 0.2);
  border-color: var(--purple-accent);
}

.action-icon-badge {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.bg-purple-subtle { background: var(--purple-soft); color: var(--purple-accent); border: 1px solid var(--purple-border); }
.bg-blue-subtle { background: var(--blue-soft); color: var(--blue-primary); border: 1px solid var(--blue-border); }
.bg-teal-subtle { background: var(--teal-soft); color: var(--teal-accent); border: 1px solid var(--teal-border); }
.bg-amber-subtle { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.bg-rose-subtle { background: #FFF1F2; color: #E11D48; border: 1px solid #FECDD3; }

.action-card h4 {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-dark);
  margin-bottom: 4px;
}

.action-card p {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
  margin-bottom: 16px;
}

.action-circle-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  margin-left: auto;
  transition: transform 0.2s ease;
}

.action-card:hover .action-circle-btn {
  transform: translateX(3px);
}

.btn-purple { background: var(--purple-soft); color: var(--purple-accent); }
.btn-blue { background: var(--blue-soft); color: var(--blue-primary); }
.btn-teal { background: var(--teal-soft); color: var(--teal-accent); }
.btn-amber { background: #FFFBEB; color: #D97706; }
.btn-rose { background: #FFF1F2; color: #E11D48; }

/* ENTERPRISE FORM & BUTTON STYLES (ACCESSIBLE & HIGH CONTRAST) */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 28px;
  min-height: 48px;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  text-decoration: none;
  line-height: 1.2;
}

.btn-primary {
  background: linear-gradient(135deg, var(--purple-accent) 0%, var(--blue-primary) 100%);
  color: #FFFFFF;
  box-shadow: var(--shadow-purple);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #6D28D9 0%, #1D4ED8 100%);
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(124, 58, 237, 0.45);
  color: #FFFFFF;
}

.btn-teal {
  background: linear-gradient(135deg, var(--teal-accent) 0%, #059669 100%);
  color: #FFFFFF;
  box-shadow: var(--shadow-teal);
}

.btn-teal:hover {
  background: linear-gradient(135deg, #0F766E 0%, #047857 100%);
  transform: translateY(-2px);
  color: #FFFFFF;
}

.btn-secondary {
  background: #FFFFFF;
  color: var(--text-dark);
  border: 1.5px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.btn-secondary:hover {
  background: var(--page-bg);
  border-color: var(--purple-accent);
  color: var(--purple-accent);
  transform: translateY(-1px);
}

.btn-danger {
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.25);
}

.btn-danger:hover {
  background: #B91C1C;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.35);
  color: #FFFFFF;
}

.btn-sm { padding: 8px 16px; min-height: 36px; font-size: 13px; border-radius: var(--radius-sm); }
.btn-lg { padding: 16px 36px; min-height: 54px; font-size: 17px; border-radius: var(--radius-md); }

.card {
  background: #FFFFFF;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  padding: 32px;
  margin-bottom: 24px;
}

.form-group { margin-bottom: 22px; }
.form-group label { display: block; font-size: 14px; font-weight: 700; color: var(--text-dark); margin-bottom: 8px; }
.form-control {
  width: 100%;
  padding: 14px 18px;
  min-height: 48px;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 15px;
  color: var(--text-dark);
  background: #FFFFFF;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}
.form-control:focus {
  outline: none;
  border-color: var(--purple-accent);
  box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.2);
}

/* TABLES */
.table-container {
  background: #FFFFFF;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}
.table { width: 100%; border-collapse: collapse; text-align: left; }
.table th {
  background: #F8FAFC;
  padding: 16px 20px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}
.table td { padding: 16px 20px; font-size: 14px; border-bottom: 1px solid var(--border-color); color: var(--text-dark); }
.table tbody tr:last-child td { border-bottom: none; }
.table tbody tr:hover td { background-color: #F1F5F9; }

.badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; }
.badge-success { background: var(--success-bg); color: #047857; border: 1px solid var(--success-border); }
.badge-warning { background: var(--warning-bg); color: #B45309; border: 1px solid var(--warning-border); }
.badge-primary { background: var(--purple-soft); color: var(--purple-accent); border: 1px solid var(--purple-border); }

.empty-state { text-align: center; padding: 60px 20px; }
.empty-state-icon {
  width: 60px; height: 60px; background: var(--purple-soft); color: var(--purple-accent); border-radius: 50%;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; font-size: 26px;
}
.empty-state h3 { font-size: 18px; color: var(--text-dark); margin-bottom: 6px; }
.empty-state p { color: var(--text-muted); font-size: 14px; margin-bottom: 20px; }

@media (max-width: 900px) {
  .app-body { padding: 16px; flex-direction: column; }
  .sidebar { width: 100%; }
  .main-content-panel { padding: 20px; min-height: auto; }
}
"""

def render_admin_layout(active_page, title, subtitle, content_html):
    dash_act = 'active' if active_page == 'dashboard' else ''
    cstud_act = 'active' if active_page == 'create-student' else ''
    vstud_act = 'active' if active_page == 'view-students' else ''
    cexam_act = 'active' if active_page == 'create-exam' else ''
    vexam_act = 'active' if active_page == 'view-exams' else ''
    vsub_act = 'active' if active_page == 'view-submissions' else ''

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} — SmartScribe Enterprise</title>
        <style>{COMMON_CSS}</style>
    </head>
    <body>
    <div class="animated-bg-overlay">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
    </div>
    <div class="app-shell">
        <header class="top-header-bar">
            <div class="top-header-left">
                <div class="brand-logo-container">
                    <div class="logo-icon-3d">
                        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M12 6v8"/><path d="M8 10h8"/></svg>
                    </div>
                    <div class="brand-text">
                        <h2>SmartScribe</h2>
                        <p>AI Exam Assistant for Visually Impaired Students</p>
                    </div>
                </div>
            </div>
            <div class="top-header-center">
                <div class="search-input-wrapper">
                    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                    <input type="text" placeholder="Search students, exams..." class="search-input">
                </div>
            </div>
            <div class="top-header-right">
                <div class="slogan-handwritten">Education Without Limits</div>
                <div class="header-action-icon">
                    <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                </div>
            </div>
        </header>

        <div class="app-body">
            <aside class="sidebar" id="sidebar">
                <nav class="sidebar-nav">
                    <a href="/admin-dashboard" class="nav-link {dash_act}">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
                        Home
                    </a>
                    <a href="/view-students" class="nav-link {vstud_act}">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                        Students
                    </a>
                    <a href="/view-exams" class="nav-link {vexam_act}">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                        Exams
                    </a>
                    <a href="/view-submissions" class="nav-link {vsub_act}">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        Submissions
                    </a>
                </nav>

                <div class="sidebar-promo-card">
                    <div class="sidebar-promo-text">
                        <p class="promo-quote">"Same Education, Same Opportunities, A Brighter Tomorrow"</p>
                    </div>
                </div>

                <div class="sidebar-footer">
                    <a href="/" class="nav-link logout-link">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
                        Logout
                    </a>
                </div>
            </aside>

            <main class="main-content-panel">
                {content_html}
            </main>
        </div>
    </div>
    </body>
    </html>
    """)
