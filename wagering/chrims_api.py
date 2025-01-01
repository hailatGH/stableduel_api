import json
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta
import requests
import reversion
from enum import Enum, auto
from typing import Optional

from django.conf import settings

from racecards.utils import get_first_post_time
from .utils import get_contest, get_wagering_account, get_bet,prepare_path
from .models import Payout, Account
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-SD-Secret': settings.CHRIMS_SECRET,
    'X-SD-Audit': settings.CHRIMS_AUDIT,
    'X-SD-Decrypt': settings.CHRIMS_DECRYPT,  
}

class HTTP_METHOD(Enum):
    POST = auto()
    GET = auto()
    PUT = auto()
    DELETE = auto()
 
def _chrims_request(method: HTTP_METHOD, path: str, body: Optional[any] = None, custom_headers : Optional[dict] = {}, new_chrims = True ):
    base_url = settings.NEW_CHRIMS_BASE_URL if new_chrims else settings.CHRIMS_BASE_URL
    url = "{}{}".format(base_url, path)
    _headers = dict(**headers, **custom_headers)
    response = requests.request(method=method.name, url=url, json=body, headers=_headers)
    response_data = None
    did_error = False
    try:
        response_data = response.json()
    except JSONDecodeError as e:
        print("Error fetching account details: JSON decode error")
        did_error = True
        response_data = e
    if response.status_code != 200:
        print("Chrims Request Error: {} {}".format(response.status_code, response_data))
        did_error = True
    return response_data,did_error,response.status_code

def fetch_wagering_account(account: Account):
    """Fetch acount details from CHRIMS
    """
    chrims_path = prepare_path("user-account/me", account, {})
    return _chrims_request(HTTP_METHOD.GET, chrims_path)

def update_contest(game, status='openForBetting', method='POST'):
    contest, contest_created = get_contest(game)
    first_post = get_first_post_time(game.racecard)
    start_time = datetime.utcnow() + timedelta(minutes=1)
    chrims_data = {
        'guid': str(contest.id),
        'name': game.name,
        'status': status,
        'contestAmount': game.contest_amount,
        'commissionPercent': game.commission_percent,
        'startBettingDateTimeUtc': start_time.isoformat() + 'Z',
        'endBettingDateTimeUtc': first_post.isoformat() + 'Z',
        'raceDateUtc': first_post.isoformat() + 'Z',
    }

    chrims_response = requests.request(
        method,
        headers=headers,
        url='{}{}'.format(settings.CHRIMS_BASE_URL, 'contests'),
        json=chrims_data,
    )

    contest.chrims_status_code = chrims_response.status_code
    contest.chrims_error = False  if chrims_response.status_code == 200 else True
    try:
        contest.chrims_response = chrims_response.json()
    except JSONDecodeError:
        contest.chrims_response = None

    contest.save()

    return contest

def get_contest_pool(game):
    contest, _ = get_contest(game)

    chrims_response = requests.request(
        "GET",
        headers=headers,
        url='{}{}'.format(settings.CHRIMS_BASE_URL, 'contests/{}'.format(contest.id))
    )

    try:
        chrims_response = chrims_response.json()
    except JSONDecodeError:
        return None

    return chrims_response["value"]

def put_bet(bet, account):
    chrims_data = {
        'guid': str(bet.id),
        'accountGuid': str(account.id),
        'selectionsJSON': str(list(bet.stable.runners.all().values_list('id', flat=True))),
    }

    chrims_response = requests.request(
        "PUT",
        headers=headers,
        url='{}{}'.format(settings.CHRIMS_BASE_URL, 'bets'),
        json=chrims_data,
    )

    try:
        bet.chrims_response = chrims_response.json()
    except JSONDecodeError:
        bet.chrims_response = None

    bet.chrims_status_code = chrims_response.status_code
    bet.chrims_error = False  if chrims_response.status_code == 200 else True
    return bet

def submit_bet(bet, account):
    chrims_data = {
        'betGuid': str(bet.id),
        'accountGuid': str(account.id),
        'selectionsJSON': str(list(bet.stable.runners.all().values_list('id', flat=True))),
    }
    print("____Submit Bet")
    print(chrims_data)
    chrims_response = requests.request(
        "PUT",
        headers=headers,
        url='{}{}'.format(settings.CHRIMS_BASE_URL, 'bets/submit'),
        json=chrims_data,
    )

    try:
        bet.chrims_response = chrims_response.json()
    except JSONDecodeError:
        bet.chrims_response = None

    bet.chrims_status_code = chrims_response.status_code
    bet.chrims_error = False  if chrims_response.status_code == 200 else True
    bet.bet_submitted = True  if chrims_response.status_code == 200 else False

    return bet

def post_bet(bet, account):
    constest = bet.stable.game.contest
    game = bet.stable.game

    data, did_error, status_code = fetch_wagering_account(account)

    if did_error or data == None:
        bet.chrims_error = True
        bet.chrims_response = data
        bet.chrims_status_code = status_code
        bet.bet_submitted = False

        return bet
    
    # Default to zero bets
    bet_amount = 0
    # If user credits are enough for game fee
    entry_fee = float(bet.stable.game.entry_fee)
    if entry_fee >0 and data["gameCreditsTotal"] >= entry_fee:
        bet.credit = True
    #   Deduct from credit
        data, did_error, status_code = deduct_from_credits(account, entry_fee, game)
        if did_error: 
            bet.chrims_error = True
            bet.chrims_status_code = status_code
            bet.chrims_response = data

            bet.bet_submitted = False

            return bet
    else:
        # Set bet amount to entry fee (Amount will be deducted from account balance)
        bet_amount = entry_fee

    chrims_data = {
        'guid': str(bet.id),
        'accountGuid': str(account.id),
        'contestGuid': str(constest.id),
        'betDateUtc': datetime.utcnow().isoformat() + 'Z',
        'fundFromRewards': False,
        'unitStake': bet_amount,
        'totalStake': bet_amount,
        'selectionsJSON': None,
    }
    
    chrims_response = requests.request(
        "POST",
        headers=headers,
        url='{}{}'.format(settings.CHRIMS_BASE_URL, 'bets'),
        json=chrims_data,
    )

    bet.chrims_status_code = "200" #chrims_response.status_code
    bet.chrims_error = False  if chrims_response.status_code == 200 else True
    bet.bet_submitted = True  if chrims_response.status_code == 200 else False

    try:
        bet.chrims_response = chrims_response.json()
    except JSONDecodeError:
        bet.chrims_response = None

    return bet

def update_bet(stable):
    bet, bet_created = get_bet(stable)
    account, _ = get_wagering_account(stable.user)

    serialized_stable = None

    if bet_created or bet.bet_submitted == False:
        bet = post_bet(bet, account)
    else:
        bet = put_bet(bet, account)

    if stable.is_submitted:
        bet = submit_bet(bet, account)

    # todo if submitted check the bet response

    with reversion.create_revision():
        bet.save()
        reversion.set_user(stable.user)
        reversion.set_comment("CHRIMS Bet Update")
    return bet

def finalize_bet(stable):
    bet, _ = get_bet(stable)
    account, _ = get_wagering_account(stable.user)

    chrims_data = {
        'betGuid': str(bet.id),
        'accountGuid': str(account.id),
    }
    print('____Chrims Data')
    print(chrims_data)
    chrims_response = requests.request(
        "PUT",
        headers=headers,
        url='{}{}'.format(settings.CHRIMS_BASE_URL, 'bets/finalize'),
        json=chrims_data,
    )

    try:
        bet.chrims_response = chrims_response.json()
    except JSONDecodeError:
        bet.chrims_response = None

    bet.chrims_status_code = chrims_response.status_code
    bet.chrims_error = False  if chrims_response.status_code == 200 else True

    with reversion.create_revision():
        bet.save()
        reversion.set_user(stable.user)
        reversion.set_comment("CHRIMS Bet Finalized")

    return bet

def abandon_bet(stable):
    bet, _ = get_bet(stable)
    account, _ = get_wagering_account(stable.user)

    if bet.credit == True:
        data, did_error, status_code = refund_credits(account, bet.stable.game.entry_fee, bet.stable.game)
        if did_error:
            bet.chrims_error = True
            bet.chrims_status_code = status_code
            bet.chrims_response = data

            bet.save()
            with reversion.create_revision():
                bet.save()
                reversion.set_user(stable.user)
                reversion.set_comment("CHRIMS Bet Abandonement failed on credit refund")

            return bet
        
    chrims_data = {
        'betGuid': str(bet.id),
        'accountGuid': str(account.id),
    }

    chrims_response = requests.request(
        "PUT",
        headers=headers,
        url='{}{}'.format(settings.CHRIMS_BASE_URL, 'bets/abandon'),
        json=chrims_data,
    )
    

    try:
        bet.chrims_response = chrims_response.json()
    except JSONDecodeError:
        bet.chrims_response = None
    
    bet.chrims_status_code = chrims_response.status_code
    bet.chrims_error = False  if chrims_response.status_code == 200 else True

    with reversion.create_revision():
        bet.save()
        reversion.set_user(stable.user)
        reversion.set_comment("CHRIMS Bet Abandoned")

    return bet

def cancel_bet(stable):
    bet, _ = get_bet(stable)
    account, _ = get_wagering_account(stable.user)

    if bet.credit == True:
        data, did_error, status_code = refund_credits(account, bet.stable.game.entry_fee, bet.stable.game)
        if did_error:
            bet.chrims_error = True
            bet.chrims_status_code = status_code
            bet.chrims_response = data

            bet.save()
            with reversion.create_revision():
                bet.save()
                reversion.set_user(stable.user)
                reversion.set_comment("CHRIMS Bet Cancellation failed on credit refund")

            return bet
        
    chrims_data = {
        'betGuid': str(bet.id),
        'accountGuid': str(account.id),
    }

    chrims_response = requests.request(
        "PUT",
        headers=headers,
        url='{}{}'.format(settings.CHRIMS_BASE_URL, 'bets/cancel'),
        json=chrims_data,
    )

    bet.chrims_status_code = chrims_response.status_code
    bet.chrims_error = False  if chrims_response.status_code == 200 else True

    try:
        bet.chrims_response = chrims_response.json()
    except JSONDecodeError:
        bet.chrims_response = None
    
    with reversion.create_revision():
        bet.save()
        reversion.set_user(stable.user)
        reversion.set_comment("CHRIMS Bet Cancelled")
    return bet
  
def finalize_bets(stables):
    valid_stables = stables.filter(is_valid_at_start=True)
    invalid_stables = stables.filter(is_valid_at_start=False)

    # bet finalization happens when the stable is created now
    for stable in valid_stables:
        finalize_bet(stable)

    for stable in invalid_stables:
        abandon_bet(stable)

def payout_bet(payout):
    chrims_data = {
        'betGuid': str(payout.bet.id),
        'payoutAmount': float(payout.payout_amount),
        'voidAmount': float(payout.void_amount),
    }

    chrims_response = requests.request(
        "POST",
        headers=headers,
        url='{}{}'.format(settings.CHRIMS_BASE_URL, 'bets/payout'),
        json=chrims_data,
    )

    try:
        payout.chrims_response = chrims_response.json()
    except JSONDecodeError:
        payout.chrims_response = None

    payout.chrims_status_code = chrims_response.status_code
    payout.chrims_error = False  if chrims_response.status_code == 200 else True
    payout.submitted = True if payout.chrims_status_code == 200 or payout.submitted == True else False

    with reversion.create_revision():
        payout.save()
        reversion.set_user(payout.bet.stable.user)
        reversion.set_comment("CHRIMS Payout Sent")

    return payout

def payout_bet_to_credit(payout):
    chrims_data = {
        'betGuid': str(payout.bet.id),
        'payoutAmount': float(payout.payout_amount),
        'voidAmount': float(payout.void_amount),
    }

    chrims_response = requests.request(
        "POST",
        headers=headers,
        url='{}{}'.format(settings.CHRIMS_BASE_URL, 'bets/gamecredits/payout'),
        json=chrims_data,
    )

    try:
        payout.chrims_response = chrims_response.json()
    except JSONDecodeError:
        payout.chrims_response = None

    payout.chrims_status_code = chrims_response.status_code
    payout.chrims_error = False  if chrims_response.status_code == 200 else True
    payout.submitted = True if payout.chrims_status_code == 200 or payout.submitted == True else False

    with reversion.create_revision():
        payout.save()
        reversion.set_user(payout.bet.stable.user)
        reversion.set_comment("CHRIMS Payout Sent")

    return payout

def submit_payouts(game):
    payouts = Payout.objects.filter(bet__stable__game=game)
    for payout in payouts:
        if payout.bet.credit or game.entry_fee == 0:
            payout_bet_to_credit(payout)
        else:
            payout_bet(payout)

def deduct_from_credits(account: Account, amount: float, game):
    chrims_path = prepare_path("user-account/me/gamecredits/", account)
    return _chrims_request(HTTP_METHOD.POST, chrims_path, {"amount": float(-abs(amount)), "description": f"{game.name} Fee"})

def refund_credits(account: Account, amount: float, game):
    chrims_path = prepare_path("user-account/me/gamecredits/", account);
    return _chrims_request(HTTP_METHOD.POST, chrims_path, {"amount": float(amount), "description": f"{game.name} Refund"})