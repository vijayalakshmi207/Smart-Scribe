import sys
import os
import re

sys.path.insert(0, os.path.abspath('.'))
os.environ['PYTHONUTF8'] = '1'

import app

client = app.app.test_client()

required_ids_per_route = {
    '/admin-login': ['u', 'p'],
    '/admin-register': ['u', 'p', 'c'],
    '/admin-dashboard': ['ts', 'te', 'tsub'],
    '/create-student': ['regNo', 'studentName', 'studentImage', 'imgPreview', 'recBtn', 'stopBtn', 'voiceStatus', 'voicePlayback'],
    '/create-exam': ['examName', 'duration', 'pdfFile', 'fileName', 'createBtn', 'status'],
    '/student-verification': ['cam', 'capBtn', 'retakeBtn', 'verifyFaceBtn', 'voiceBox', 'vRecBtn', 'vStopBtn', 'vStatus', 'vPlayback', 'verifyVoiceBtn', 'statusMsg'],
}

print("=== VERIFYING ELEMENT ID PRESERVATION IN APP.PY ===")
failed = False

for route, expected_ids in required_ids_per_route.items():
    res = client.get(route)
    html = res.get_data(as_text=True)
    for elem_id in expected_ids:
        pattern = rf'id=["\']{elem_id}["\']'
        if re.search(pattern, html):
            print(f"  ✅ [{route}] id=\"{elem_id}\" found")
        else:
            print(f"  ❌ [{route}] id=\"{elem_id}\" MISSING!")
            failed = True

# Exam page check with session
with client.session_transaction() as sess:
    sess['student_regno'] = 'REG123'
    sess['student_name'] = 'Test Student'

res = client.get('/exam-page')
html = res.get_data(as_text=True)
exam_ids = ['timerBox', 'statusBubble', 'micIcon', 'micLabel', 'waveAnim', 'transcriptBox', 'transcriptText', 'hintBox', 'submitArea', 'submitBtn']
for elem_id in exam_ids:
    pattern = rf'id=["\']{elem_id}["\']'
    if re.search(pattern, html):
        print(f"  ✅ [/exam-page] id=\"{elem_id}\" found")
    else:
        print(f"  ❌ [/exam-page] id=\"{elem_id}\" MISSING!")
        failed = True

if failed:
    sys.exit(1)
else:
    print("\n🎉 ALL 100% OF ELEMENT IDS ARE PRESERVED EXACTLY IN APP.PY!")
