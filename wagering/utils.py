from .models import Account, Contest, Bet
from urllib.parse import urlencode
from django.conf import settings

import re
uuid4_regex = "[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}\Z"
new_chrims_route_regexes = list(map(lambda regex_string: re.compile(regex_string, re.I),
        [
            "^user-account[/]?$",
            "^user-account/me[/]?$",
            "^user-account/me/activity[/]?$",
            "^Promo[/]?.*",
            "${}/rank[/]?$".format(uuid4_regex),
            "${}/percentage[/]?$".format(uuid4_regex)
        ]
    ))



def get_wagering_account(user):
    return Account.objects.get_or_create(user=user)

def get_contest(game):
    return Contest.objects.get_or_create(game=game)

def get_bet(stable):
    return Bet.objects.get_or_create(stable=stable)

def prepare_data(method, path, incoming_data, account):
    data = {k: v for k, v in incoming_data.items()}

    path_parts = path.split('/')
    endpoint = path_parts[0]

    if method not in ['POST', 'PUT', ]:
        return data

    if endpoint in ['user-account', ]:
        data['guid'] = str(account.id)
    elif endpoint not in ['management-values', ]:
        data['accountGuid'] = str(account.id)    
    
    return data

def prepare_path(request_path, account, query_dict : dict = {}):
    path_parts = request_path.split('/')
    prepared_parts = [part if part != 'me' else str(account.id) for part in path_parts]
    joined_path = '/'.join(prepared_parts)
    if query_dict:
        query_string = urlencode(query_dict)
        return joined_path + "?{}".format(query_string)
    else:
        return joined_path

def is_new_chrims_route(path):
    return any(route_regex.match(path) for route_regex in new_chrims_route_regexes)


def get_chrims_base_url(path):
    """Get the corresponding base url for a path.

    Returns "settings.NEW_CHRIMS_BASE_URL" if path is a "New Chrims Route"

    Defaults to "settings.CHRIMS_BASE_URL"
    """
    return settings.NEW_CHRIMS_BASE_URL if is_new_chrims_route(path) else settings.CHRIMS_BASE_URL

# build url based on route path
def build_url(path, original_path):
    """Build a full chrims URL"""
    return '{}{}'.format(get_chrims_base_url(original_path) , path)
