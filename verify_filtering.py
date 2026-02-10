import datetime

def filter_courses(courses):
    filtered_courses = []
    for course in courses:
        # Check if teacher is N/A or None or empty string
        teacher = course.get('discipline', {}).get('teacher', 'N/A')
        is_teacher_missing = teacher in ('N/A', None, '')

        # Check if course type is "Libre"
        course_type = course.get('type', 'N/A')
        is_unimportant = course_type == 'Libre'

        if not is_teacher_missing and not is_unimportant:
            filtered_courses.append(course)
        else:
            print(f"Filtering out: {course.get('name')} (Teacher: {teacher}, Type: {course_type})")
            
    return filtered_courses

# Mock courses for testing
mock_courses = [
    {
        "name": "Maths",
        "discipline": {"teacher": "Mr. Smith"},
        "type": "Cours"
    },
    {
        "name": "Physics", 
        "discipline": {"teacher": "Mrs. Jones"},
        "type": "TP"
    },
    {
        "name": "Self Study",
        "discipline": {"teacher": "N/A"},
        "type": "Libre"
    },
    {
        "name": "No Teacher Course",
        "discipline": {"teacher": "N/A"}, 
        "type": "Cours"
    },
    {
        "name": "Empty Teacher Course",
        "discipline": {"teacher": ""},
        "type": "Cours"
    },
     {
        "name": "None Teacher Course",
        "discipline": {"teacher": None},
        "type": "Cours"
    }
]

print("Original Courses:")
for c in mock_courses:
    print(f"- {c['name']}")

print("\nRunning Filter...")
final_courses = filter_courses(mock_courses)

print("\nFiltered Courses:")
for c in final_courses:
    print(f"- {c['name']}")

expected = ["Maths", "Physics"]
actual = [c['name'] for c in final_courses]

if actual == expected:
    print("\nSUCCESS: Filtering logic is correct.")
else:
    print(f"\nFAILURE: Expected {expected}, got {actual}")
