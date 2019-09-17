_NON_BREAKING_SPACE = chr(160)
PRIMARY_PROMPT = "Manabi adapts to how you learn, tracking your strength of memory to determine the optimal time for you to review right before you forget.\n\nSubscribe to unlock unlimited" + _NON_BREAKING_SPACE + "personalized" + _NON_BREAKING_SPACE + "reviews."

STUDENT_PROMPT = "Are you a student, educator, or parent?\nManabi is available to you at a discount."


def _product(product_id, apple_id, subtitle):
    return {
        'product_id': product_id,
        'apple_id': apple_id,
        'subtitle': subtitle,
    }


def purchasing_options():
    return {
        'primary_prompt': PRIMARY_PROMPT,
        'student_prompt': STUDENT_PROMPT,
        'monthly_product': _product(
            'io.manabi.Manabi.monthly', '1217072727', 'Per Month'),
        'annual_product': _product(
            'io.manabi.Manabi.annual', '1217073373', 'Per Year'),
        'student_monthly_product': _product(
            'io.manabi.Manabi.student_monthly', '1217074382', 'Per Month'),
        'student_annual_product': _product(
            'io.manabi.Manabi.student_annual', '1217074383', 'Per Year'),
    }


def manabi_reader_purchasing_options():
    return {
        'student_prompt': STUDENT_PROMPT.replace('Manabi', 'Manabi Reader'),
        'monthly_product': _product(
            'io.manabi.ManabiReader.monthly', '1480319679', 'Per Month'),
        'annual_product': _product(
            'io.manabi.ManabiReader.annual', '1480318554', 'Per Year'),
        'student_monthly_product': _product(
            'io.manabi.ManabiReader.student_monthly',
            '1480319870',
            'Per Month'),
        'student_annual_product': _product(
            'io.manabi.ManabiReader.student_annual', '1480319305', 'Per Year'),
    }
