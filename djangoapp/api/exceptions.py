from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and response.status_code >= 400:
        if response.status_code == 400:
            fields = {}

            for key, value in response.data.items():
                if key.lower() != 'detail':
                    fields[key] = value

            if len(fields) > 0:
                response.data['fields'] = fields

        response.data['status_code'] = response.status_code

        detail = response.data.get('detail', None)
        response.data['detail'] = 'Unknown error' if detail is None else detail
    return response