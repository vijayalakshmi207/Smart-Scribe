with open('app1.py', 'r', encoding='utf-8') as f:
    orig_code = f.read()

# Lines 1 to 777: backend core functions
marker1 = "# ==================== ORIGINAL NOTEBOOK CELL 4 ===================="
backend_part = orig_code.split(marker1)[0]

# API routes & main entry point
marker2 = "# ─── ADMIN ─────────────────────────────────────────────────"
api_part = marker2 + orig_code.split(marker2)[1]

with open('scratch/ui_module.py', 'r', encoding='utf-8') as f:
    ui_module_code = f.read()

with open('scratch/ui_routes.py', 'r', encoding='utf-8') as f:
    ui_routes_code = f.read()

# Remove the import line from ui_routes_code
ui_routes_code = ui_routes_code.replace("from scratch.ui_module import COMMON_CSS, render_admin_layout\n", "")
ui_routes_code = ui_routes_code.replace("def attach_ui_routes(app, get_db):\n", "")

# Un-indent the route handlers inside attach_ui_routes by 4 spaces
unindented_routes = []
for line in ui_routes_code.splitlines():
    if line.startswith("    "):
        unindented_routes.append(line[4:])
    else:
        unindented_routes.append(line)

new_ui_part = ui_module_code.replace("from flask import render_template_string, request\n", "") + "\n\n" + "\n".join(unindented_routes)

merged_app1 = backend_part + marker1 + "\n\n" + new_ui_part + "\n\n" + api_part

with open('app1.py', 'w', encoding='utf-8') as f:
    f.write(merged_app1)

print("Merged successfully into app1.py!")
