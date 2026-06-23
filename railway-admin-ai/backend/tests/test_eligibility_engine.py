import os
import sys

# Ensure backend root is in search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from app.core.eligibility_engine import EligibilityEngine
from app.database.connection import AsyncSessionLocal

async def test_eligibility_engine():
    engine = EligibilityEngine()

    print("--- Running Eligibility Engine Coordination Tests ---")

    async with AsyncSessionLocal() as db:
        # Case 1: Document Gate blocked (APAR missing)
        print("\n--- Test 1: Missing Required Documents ---")
        res1 = await engine.evaluate(
            query="Am I eligible for promotion?",
            domain="Promotion",
            submitted_docs=["Service Book"],
            extracted_facts={"years_of_service": 6, "apar_rating": "Outstanding", "passed_exam": True, "penalty_history": []},
            conversation_history=[],
            db=db
        )
        print(f"Eligibility Status: {res1.eligibility_status}")
        print(f"Decision: {res1.decision}")
        assert res1.decision == "Cannot Determine"
        assert "DOCUMENT REQUIREMENT NOTICE" in res1.document_demand_notice

        # Case 2: Fact Gate blocked (passed_exam missing)
        print("\n--- Test 2: Missing Key Facts ---")
        res2 = await engine.evaluate(
            query="Am I eligible for promotion?",
            domain="Promotion",
            submitted_docs=["Service Book", "APAR (last 3 years)", "Departmental Exam Result"],
            extracted_facts={"years_of_service": 6, "apar_rating": "Outstanding"},
            conversation_history=[],
            db=db
        )
        print(f"Eligibility Status: {res2.eligibility_status}")
        print(f"Decision: {res2.decision}")
        print(f"Missing Information: {res2.missing_information}")
        print(f"Follow-up Questions: {res2.follow_up_questions}")
        assert res2.decision == "Cannot Determine"
        assert "passed_exam" in res2.missing_information

        # Case 3: Complete execution (Everything present)
        print("\n--- Test 3: Complete Data Present ---")
        res3 = await engine.evaluate(
            query="Am I eligible for promotion? I have served for 6 years.",
            domain="Promotion",
            submitted_docs=["Service Book", "APAR (last 3 years)", "Departmental Exam Result"],
            extracted_facts={"years_of_service": 6, "apar_rating": "Outstanding", "passed_exam": True, "penalty_history": []},
            conversation_history=[],
            db=db
        )
        print(f"Decision: {res3.decision}")
        print(f"Status: {res3.eligibility_status}")
        print(f"Confidence Level: {res3.confidence_level}")
        print(f"Supporting Rules count: {len(res3.supporting_rules)}")
        print(f"Administrative Notes / Reasoning:")
        print(res3.administrative_notes)

        assert res3.decision in ["Eligible", "Not Eligible", "Cannot Determine"]
        
    print("\nAll Eligibility Engine tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_eligibility_engine())
