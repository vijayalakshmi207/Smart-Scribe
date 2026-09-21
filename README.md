# SmartScribe

### AI-Based Voice-Enabled Examination System for Visually Impaired Students

SmartScribe is an AI-powered examination system designed to provide an accessible and secure examination experience for visually impaired students. It combines face verification, voice verification, speech recognition, text-to-speech, and automated answer-sheet generation in a single platform.

## Technologies Used

- Python
- Flask
- HTML, CSS, JavaScript
- SQLite
- Face Recognition
- Voice Recognition
- Speech Recognition
- Text-to-Speech
- OpenCV
- Librosa
- NumPy
- ReportLab

## Key Features

- Admin login and dashboard
- Student registration and management
- Face registration and verification
- Voice registration and verification
- Voice-based examination
- Text-to-speech question reading
- Speech-based answer recording
- Voice commands such as **NEXT**, **REPEAT**, and **SUBMIT**
- Examination timer
- Question paper PDF upload
- Automatic answer-sheet PDF generation
- Submission management
- Answer-sheet download
- Exam and submission deletion
- Accessibility-focused interface

## How to Run

Install the required packages:

```bash
pip install -r requirements.txt
Run the application:
python app.py
If your updated application uses app1.py:
python app1.py
Open the URL shown in the terminal in Google Chrome.

Instructions for Evaluators
The complete project can be tested using the following steps.

1. Admin Login
Open the Admin Login page.
Use the demo admin credentials:
Username: admin
Password: admin123

2. Register a Student
After logging in:
•	Go to Create/Register Student 
•	Enter a student name 
•	Enter a registration number 
•	Upload or capture a clear face photo 
•	Record a clear voice sample 
•	Click Create Student 
Evaluators can use their own photo and voice for this demonstration.

3. Create an Exam
Go to Create Exam.
•	Enter an exam name 
•	Set the examination duration 
•	Upload the question paper PDF 
•	Create the exam 

4. Logout
Logout from the Admin Portal.

5. Student Verification
Open the Student Login page.
Enter the same registration number used during registration.
The system will perform:
Face Verification → Voice Verification
Use the same person's face and voice that were registered.

6. Take the Exam
After successful verification:
•	Select the available exam 
•	Questions will be read aloud 
•	Answer questions using your voice 
•	Use voice commands such as NEXT and REPEAT 
•	Monitor the examination timer 

7. Submit
After answering the questions, use the SUBMIT command or submission control.
The system will generate the student's answer-sheet PDF.

8. View Submissions
From the Admin Portal:
•	Open View Submissions 
•	View submitted examinations 
•	Download answer-sheet PDFs 
•	Delete submissions when required 

Expected Output
The evaluator should be able to verify:
•	Admin login 
•	Student registration 
•	Face registration and verification 
•	Voice registration and verification 
•	Exam creation 
•	Question paper upload 
•	Voice-based question answering 
•	Voice commands 
•	Examination timer 
•	Exam submission 
•	Automatic answer-sheet PDF generation 
•	Submission management 
•	Answer-sheet download 

Browser Requirements
For the best experience, use Google Chrome and allow:
•	Camera permission 
•	Microphone permission 
For reliable face and voice verification, use a clear camera view, sufficient lighting, and a quiet environment.

SmartScribe
Accessible. Voice-Enabled. Intelligent.

