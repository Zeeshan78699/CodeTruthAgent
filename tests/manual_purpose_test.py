from ai.purpose_analysis_engine import (
    PurposeAnalysisEngine
)

engine = PurposeAnalysisEngine()

sample_code = '''

def process_refund(payment_id):

    validate_payment(payment_id)

    update_database(payment_id)

    send_email(payment_id)

    db.commit()

'''

result = engine.analyze_purpose(
    function_name="process_refund",
    code=sample_code,
    docstring="Processes customer refunds"
)

print(result)