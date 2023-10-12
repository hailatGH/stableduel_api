def get_text_from_EL(element, default=None):
    # value = element.text 

    # element will be None if element does not exist
    if element is None:
        return None
    else:
        try:
            value = element.text
        except:
            value = element
    # Value will be None if element does not contain text
    if not value and default:
        return default
    elif value is None:
        return value
    else:
        return value.strip()

def get_float_from_EL(element, default=None):
    if get_text_from_EL(element,default) is None:
        return None

    # Convert value from given EL to float or return default value if error
    try:
        return float(get_text_from_EL(element, default))
    except ValueError:
        return default

def get_int_from_EL(element, default=None):
    # Convert value from given EL to int or return default value if error
    try:
        return int(get_text_from_EL(element, default))
    except ValueError:
        return default
    
