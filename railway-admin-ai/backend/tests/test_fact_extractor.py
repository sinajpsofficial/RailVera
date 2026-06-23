import os
import sys

# Ensure backend root is in search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.document_intelligence.extractors.service_book_extractor import ServiceBookExtractor

def test_service_book_extractor():
    extractor = ServiceBookExtractor()

    # Input simulated text from Service Book
    text = (
        "SERVICE BOOK OF INDIAN RAILWAYS\n"
        "Name: Chad Smith\n"
        "Employee ID: E100249\n"
        "Designation: Locomotive Driver\n"
        "Department: Transportation (Power)\n"
        "Pay Level: 6\n"
        "Date of Birth: 01-06-1992\n"
        "Date of Appointment: 15-08-2020\n"
        "Due to retire: 30-06-2052\n"
        "History of service remarks:\n"
        "- Promoted on 12-05-2022 to Driver Grade II.\n"
        "- Promoted on 01-10-2024 to Driver Grade I.\n"
        "- Minor penalty issued in 2023 with censure.\n"
    )

    print("--- Running Fact Extractor Verification ---")
    facts = extractor.extract(text)

    # Print out extracted facts
    print("Extracted Employee Facts:")
    for key, value in facts.items():
        print(f"  {key}: {value}")

    # Assertions for correctness
    assert facts["employee_name"] == "Chad Smith"
    assert facts["employee_id"] == "E100249"
    assert facts["designation"] == "Locomotive Driver"
    assert facts["department"] == "Transportation (Power)"
    assert facts["pay_level"] == "6"
    assert facts["appointment_date"] == "15-08-2020"
    assert facts["date_of_birth"] == "01-06-1992"
    assert facts["retirement_date"] == "30-06-2052"
    assert len(facts["promotion_history"]) == 2
    assert facts["promotion_history"][0]["date"] == "12-05-2022"
    assert facts["promotion_history"][1]["date"] == "01-10-2024"
    assert len(facts["penalty_history"]) == 1
    assert facts["penalty_history"][0]["year"] == "2023"

    print("\nAll fact extraction assertions passed successfully!")

if __name__ == "__main__":
    test_service_book_extractor()
