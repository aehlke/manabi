
LIST_DELIMITER = '+'
#LIST_DELIMITER = u' '


def clean_query(query_params, structure):
    '''
    Parses request object GET or POST parameters into Python objects.

    `query_params` is either request.GET or request.POST

    `structure` is a dict mapping parameter names to types, e.g.:
        `{'count': int, 'card_ids': list}`

    Returns a dictionary.
    '''
    cleaned = {}

    # Initialize known fields with null values.
    #for field, type_ in structure.items():
        #cleaned[field] = None

    # Clean the data.
    for param, val in query_params.items():
        # Default to an "identity" constructor.
        type_ = structure.get(param, lambda x: x)
        if type_ == bool:
            type_ = bool_
        cleaned[param] = type_(val)

    return cleaned



# Helper "types" to use with clean_query

def bool_(query_param):
    s = str(query_param).lower()
    if s == 'true':
        return True
    elif s == 'false':
        return False
    else:
        return bool(query_param)

def int_list(query_param):
    return [int(e) for e in query_param.split(LIST_DELIMITER)]


