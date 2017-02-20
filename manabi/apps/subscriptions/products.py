PRIMARY_PROMPT = "Manabi adapts to how you learn each individual term, tracking your strength of memory to determine the optimal time for you to refresh right before you forget. Subscribe to unlock unlimited personalized reviews."

STUDENT_PROMPT = "Are you a student, educator, or parent of a student? Manabi is available to you at a discount."


def _product(product_id_suffix, subtitle):
    return {
        'product_id': 'io.manabi.Manabi.' + product_id_suffix,
        'subtitle': subtitle,
    }


def purchasing_options():
    return {
        'primary_prompt': PRIMARY_PROMPT,
        'student_prompt': STUDENT_PROMPT,
        'monthly_product': _product('monthly', 'Per Month'),
        'annual_product': _product('annual', 'Per Year'),
        'student_monthly_product': _product('student_monthly', 'Per Month'),
        'student_annual_product': _product('student_annual', 'Per Year'),
    }
