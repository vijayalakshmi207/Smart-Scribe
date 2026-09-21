import sys
import os

sys.path.insert(0, os.path.abspath('.'))
os.environ['PYTHONUTF8'] = '1'

import app

client = app.app.test_client()

routes_to_test = [
    ('/', 200),
    ('/admin-login', 200),
    ('/admin-register', 200),
    ('/admin-dashboard', 200),
    ('/view-students', 200),
    ('/create-student', 200),
    ('/create-exam', 200),
    ('/view-exams', 200),
    ('/view-submissions', 200),
    ('/student-verification', 200),
]

print("=== TESTING FLASK ROUTES IN APP.PY ===")
failed = False
for route, expected_code in routes_to_test:
    res = client.get(route)
    if res.status_code == expected_code:
        print(f"✅ Route {route} -> Status {res.status_code}")
    else:
        print(f"❌ Route {route} -> Expected {expected_code}, Got {res.status_code}")
        failed = True

# Test /exam-page with student session
with client.session_transaction() as sess:
    sess['student_regno'] = 'REG123'
    sess['student_name'] = 'Test Student'

res = client.get('/exam-page')
if res.status_code == 200:
    print(f"✅ Route /exam-page (with session) -> Status 200")
else:
    print(f"❌ Route /exam-page -> Expected 200, Got {res.status_code}")
    failed = True

# Test API endpoint
res = client.get('/api/admin/stats')
if res.status_code == 200:
    print(f"✅ API /api/admin/stats -> Status 200, Payload: {res.get_json()}")
else:
    print(f"❌ API /api/admin/stats -> Got {res.status_code}")
    failed = True

if failed:
    sys.exit(1)
else:
    print("\n🎉 ALL ROUTE TESTS PASSED PERFECTLY!")
