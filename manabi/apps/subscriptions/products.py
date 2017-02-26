_NON_BREAKING_SPACE = unichr(160)
PRIMARY_PROMPT = "Manabi adapts to how you learn, tracking your strength of memory to determine the optimal time for you to review right before you forget.\n\nSubscribe to unlock unlimited" + _NON_BREAKING_SPACE + "personalized" + _NON_BREAKING_SPACE + "reviews."

STUDENT_PROMPT = "Are you a student, educator, or parent?\nManabi is available to you at a discount."


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
