"""
Student Performance Analysis System
Run with: python student_performance.py

Keep students.csv in the same folder as this Python file.
"""

from abc import ABC, abstractmethod
import csv
from pathlib import Path


class Student(ABC):
    """Abstract base class. Double-underscore attributes are name-mangled."""

    VALID_SUBJECTS = ("Math", "English", "Science")

    def __init__(self, student_id, first_name, last_name, programme, marks):
        self.__student_id = str(student_id).strip()
        self.__first_name = str(first_name).strip()
        self.__last_name = str(last_name).strip()
        self.__programme = str(programme).strip()

        if not all((self.__student_id, self.__first_name,
                    self.__last_name, self.__programme)):
            raise ValueError("Student ID, names, and programme cannot be empty.")

        if not isinstance(marks, dict) or not marks:
            raise ValueError("Marks must be a non-empty dictionary.")

        cleaned_marks = {}
        for subject, mark in marks.items():
            numeric_mark = float(mark)
            if not 0 <= numeric_mark <= 100:
                raise ValueError(f"{subject} mark must be between 0 and 100.")
            cleaned_marks[str(subject)] = numeric_mark
        self.__marks = cleaned_marks

    # Read-only accessors protect the underlying data.
    @property
    def student_id(self):
        return self.__student_id

    @property
    def first_name(self):
        return self.__first_name

    @property
    def last_name(self):
        return self.__last_name

    @property
    def full_name(self):
        return f"{self.__first_name} {self.__last_name}"

    @property
    def programme(self):
        return self.__programme

    @property
    def marks(self):
        # Return a copy so callers cannot change the internal dictionary.
        return self.__marks.copy()

    def update_mark(self, subject, mark):
        """Update an existing subject mark after validating it."""
        if subject not in self.__marks:
            raise KeyError(f"Unknown subject: {subject}")
        numeric_mark = float(mark)
        if not 0 <= numeric_mark <= 100:
            raise ValueError("A mark must be between 0 and 100.")
        self.__marks[subject] = numeric_mark

    def average_score(self):
        return sum(self.__marks.values()) / len(self.__marks)

    def grade(self):
        average = self.average_score()
        if average >= 80:
            return "A"
        if average >= 70:
            return "B"
        if average >= 60:
            return "C"
        if average >= 50:
            return "D"
        return "E"

    @staticmethod
    def calculate_average(*marks):
        """
        Flexible interface: accepts any number of marks, e.g.
        calculate_average(75, 80, 70) or calculate_average(75, 80, 70, 90).
        """
        if len(marks) == 1 and isinstance(marks[0], (list, tuple)):
            marks = tuple(marks[0])
        if not marks:
            raise ValueError("Supply at least one mark.")
        values = []
        for mark in marks:
            value = float(mark)
            if not 0 <= value <= 100:
                raise ValueError("Every mark must be between 0 and 100.")
            values.append(value)
        return sum(values) / len(values)

    @abstractmethod
    def student_type(self):
        """Subclasses must provide their own student description."""
        raise NotImplementedError


class AIUStudent(Student):
    """A regular AIU student."""

    def student_type(self):
        return "AIU Student"

    def performance_message(self):
        return f"{self.full_name} is an {self.student_type()}."


class ScholarshipStudent(AIUStudent):
    """AIU student with scholarship information and eligibility checking."""

    def __init__(self, student_id, first_name, last_name, programme,
                 marks, scholarship_amount=0):
        super().__init__(student_id, first_name, last_name, programme, marks)
        self.scholarship_amount = float(scholarship_amount)
        if self.scholarship_amount < 0:
            raise ValueError("Scholarship amount cannot be negative.")

    def is_eligible(self):
        return self.average_score() >= 85

    # Override the shared method to provide scholarship-specific behaviour.
    def student_type(self):
        status = "eligible" if self.is_eligible() else "not eligible"
        return f"Scholarship Student ({status})"

    def performance_message(self):
        if self.is_eligible():
            return (f"{self.full_name} qualifies for scholarship consideration; "
                    f"listed amount: KSh {self.scholarship_amount:,.2f}.")
        return (f"{self.full_name} does not meet the scholarship average "
                f"requirement of 85.")


class PerformanceAnalyzer:
    """Works with student objects rather than copying student records."""

    def __init__(self, students):
        self.students = list(students)
        if not self.students:
            raise ValueError("At least one student is required.")

    def highest_average(self):
        return max(self.students, key=lambda student: student.average_score())

    def lowest_average(self):
        return min(self.students, key=lambda student: student.average_score())

    def class_average(self):
        return sum(s.average_score() for s in self.students) / len(self.students)


def load_students(csv_file):
    """Load records from CSV and create the appropriate objects."""
    students = []
    csv_file = Path(csv_file)

    with csv_file.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {"StudentID", "FName", "LName", "Programme",
                    "Math", "English", "Science"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain these columns: {sorted(required)}")

        for row in reader:
            marks = {
                "Math": float(row["Math"]),
                "English": float(row["English"]),
                "Science": float(row["Science"]),
            }
            average = Student.calculate_average(*marks.values())
            if average >= 85:
                students.append(ScholarshipStudent(
                    row["StudentID"], row["FName"], row["LName"],
                    row["Programme"], marks, scholarship_amount=50000
                ))
            else:
                students.append(AIUStudent(
                    row["StudentID"], row["FName"], row["LName"],
                    row["Programme"], marks
                ))
    return students


def generate_report(students, output_file="performance_report.txt"):
    """Create a detailed student report and class summary."""
    analyzer = PerformanceAnalyzer(students)
    lines = ["STUDENT PERFORMANCE ANALYSIS REPORT", "=" * 40, ""]

    for student in students:
        lines.extend([
            f"Student ID: {student.student_id}",
            f"Name: {student.full_name}",
            f"Programme: {student.programme}",
            "Subject marks: " + ", ".join(
                f"{subject}: {mark:g}" for subject, mark in student.marks.items()
            ),
            f"Average score: {student.average_score():.2f}%",
            f"Grade: {student.grade()}",
            f"Student type: {student.student_type()}",
        ])
        if isinstance(student, ScholarshipStudent):
            lines.append(f"Scholarship eligible (average >= 85): "
                         f"{'Yes' if student.is_eligible() else 'No'}")
            lines.append(f"Scholarship amount listed: KSh "
                         f"{student.scholarship_amount:,.2f}")
        else:
            lines.append("Scholarship eligibility: Not assessed for this student type")
        lines.extend(["-" * 40, ""])

    highest = analyzer.highest_average()
    lowest = analyzer.lowest_average()
    lines.extend([
        "CLASS PERFORMANCE SUMMARY",
        "=" * 40,
        f"Highest average: {highest.full_name} "
        f"({highest.average_score():.2f}%)",
        f"Lowest average: {lowest.full_name} "
        f"({lowest.average_score():.2f}%)",
        f"Overall class average: {analyzer.class_average():.2f}%",
        "",
        "POLYMORPHISM DEMONSTRATION",
        "=" * 40,
    ])
    # The same method call produces different behaviour by object type.
    for student in students:
        lines.append(student.performance_message())

    report_text = "\n".join(lines)
    Path(output_file).write_text(report_text, encoding="utf-8")
    print(report_text)
    print(f"\nReport saved to: {Path(output_file).resolve()}")


def main():
    data_file = Path(__file__).with_name("students.csv")
    try:
        students = load_students(data_file)
        generate_report(students, Path(__file__).with_name("performance_report.txt"))

        # Flexible-interface examples:
        print("\nFLEXIBLE AVERAGE EXAMPLES")
        print("Three separate marks:", Student.calculate_average(75, 80, 70))
        print("A variable number of marks:", Student.calculate_average(90, 85, 88, 92))
    except (OSError, ValueError, KeyError) as error:
        print(f"Could not run the analysis: {error}")


if __name__ == "__main__":
    main()
