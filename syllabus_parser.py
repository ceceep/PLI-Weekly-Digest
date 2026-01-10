"""
AI-powered syllabus parser using Anthropic Claude
"""
import os
import json
from datetime import datetime
from anthropic import Anthropic
import PyPDF2
from models import Course, Session, Assignment, Reading, get_session

class SyllabusParser:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def extract_text_from_pdf(self, pdf_path):
        """Extract text content from PDF"""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def parse_syllabus(self, pdf_path):
        """Parse syllabus PDF and extract structured data"""
        print(f"Reading PDF: {pdf_path}")
        text = self.extract_text_from_pdf(pdf_path)

        print("Sending to Claude for parsing...")
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"""You are a syllabus parser. Extract structured data from this course syllabus.

Return JSON with this structure:
{{
    "course": {{
        "name": "Course name",
        "code": "Course code (e.g., EDUC 263B)",
        "instructor": "Instructor name"
    }},
    "sessions": [
        {{
            "session_number": 1,
            "title": "Session title",
            "date": "2026-01-10",
            "time": "9-12",
            "location": "In person, room 1102",
            "description": "Brief description"
        }}
    ],
    "assignments": [
        {{
            "title": "Assignment name",
            "description": "Description",
            "due_date": "2026-02-02",
            "points": 100
        }}
    ],
    "readings": [
        {{
            "title": "Reading title",
            "authors": "Author names",
            "citation": "Full citation",
            "pages": "pp. 1-35",
            "due_date": "2026-01-10",
            "url": "URL if provided"
        }}
    ]
}}

SYLLABUS TEXT:
{text}

Return ONLY valid JSON, no markdown formatting."""
            }]
        )

        response_text = message.content[0].text

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        data = json.loads(response_text)
        return data

    def import_to_database(self, syllabus_data):
        """Import parsed syllabus data into database"""
        db = get_session()

        try:
            # Create course
            course_data = syllabus_data['course']
            course = Course(
                name=course_data['name'],
                code=course_data.get('code'),
                instructor=course_data.get('instructor')
            )
            db.add(course)
            db.flush()  # Get course ID

            # Create sessions
            for session_data in syllabus_data.get('sessions', []):
                session = Session(
                    course_id=course.id,
                    session_number=session_data.get('session_number'),
                    title=session_data.get('title'),
                    date=datetime.strptime(session_data['date'], '%Y-%m-%d').date(),
                    time=session_data.get('time'),
                    location=session_data.get('location'),
                    description=session_data.get('description')
                )
                db.add(session)

            # Create assignments
            for assignment_data in syllabus_data.get('assignments', []):
                assignment = Assignment(
                    course_id=course.id,
                    title=assignment_data['title'],
                    description=assignment_data.get('description'),
                    due_date=datetime.strptime(assignment_data['due_date'], '%Y-%m-%d').date(),
                    points=assignment_data.get('points')
                )
                db.add(assignment)

            # Create readings
            for reading_data in syllabus_data.get('readings', []):
                reading = Reading(
                    course_id=course.id,
                    title=reading_data['title'],
                    authors=reading_data.get('authors'),
                    citation=reading_data.get('citation'),
                    pages=reading_data.get('pages'),
                    due_date=datetime.strptime(reading_data['due_date'], '%Y-%m-%d').date(),
                    url=reading_data.get('url')
                )
                db.add(reading)

            db.commit()
            print(f"Successfully imported course: {course.name}")
            return course.id

        except Exception as e:
            db.rollback()
            print(f"Error importing to database: {e}")
            raise
        finally:
            db.close()


if __name__ == "__main__":
    # Test the parser
    parser = SyllabusParser()

    # Example usage
    syllabus_path = "/Users/ceceepenney/Downloads/Education 263B Course Syllabus_Spring 2026 [FINAL].pdf"

    if os.path.exists(syllabus_path):
        data = parser.parse_syllabus(syllabus_path)
        print(json.dumps(data, indent=2))

        # Import to database
        course_id = parser.import_to_database(data)
        print(f"Imported course ID: {course_id}")
    else:
        print(f"Syllabus not found at: {syllabus_path}")
