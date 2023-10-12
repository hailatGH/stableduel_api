from json.decoder import JSONDecodeError

import requests
from django.http import JsonResponse,  HttpResponseServerError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.exceptions import ParseError

from django.db.models import Sum
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from wagering.models import State, Transaction
from wagering.serializers import WageringStateSerializer
from .utils import get_wagering_account, build_url, prepare_data, prepare_path

import logging
log = logging.getLogger()
from django.conf import settings
from datetime import datetime
import hashlib
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.urls import reverse
from users.models import Profile


class WageringStateView(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for data to be viewed or edited.
    """
    queryset = State.objects.all().order_by("name")
    serializer_class = WageringStateSerializer
    
    @method_decorator(cache_page(30))
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @method_decorator(cache_page(30))
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, ])
def wagering_proxy(req):
    request_path = req.path.replace('/api/wagering/', '')
    account, _ = get_wagering_account(req.user)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-SD-Secret': 'H0m3Str3tcH!',
        'X-SD-Audit': 'false',
        'X-SD-Decrypt': 'false',  
    }

    chrims_data = prepare_data(req.method, request_path, req.data, account)
    chrims_path = prepare_path(request_path, account, req.query_params)

    # set service fee to 0 regardless of what is received from apps
    if request_path == 'user-account/me/deposit' or request_path == 'user-account/me/deposit/':
        chrims_data['serviceFee'] = 0

    
    url=build_url(chrims_path, request_path)

    chrims_response = requests.request( req.method,
        headers=headers,
        url=url,
        json=chrims_data,
    )


    try:
        response_json = chrims_response.json()
        log.critical(f"Chrims_response_{response_json}")
        if request_path == 'user-account/me/activity' or request_path == 'user-account/me/activity/':
            new_items = []
            for item in response_json:
                if item['transactionType'] == 'abandoned':
                    item['transactionType'] = 'cancelBet'
                    item['transactionTypeDescription'] = 'CancelBet'

                new_items.append(item.copy())
            response_json = new_items

        return Response(response_json, status=chrims_response.status_code)
    except JSONDecodeError:
        return Response(None, status=chrims_response.status_code)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated, ])
def openNuveiOrder(request):
    amount = request.data["amount"]
    if amount == None or amount == 0:
        raise ParseError("Deposit amount is required")
    
    if not isinstance(amount, float) and not isinstance(amount, int):
        raise ParseError("Invalid deposit amount")
    
    profile = request.user.profile
    
    # Get the deposit limit and get the total daily transaction and compare if exceeded
    today = timezone.now().date()
    today_total_transaction_amount = Transaction.objects.filter(user=request.user, created_at__date=today).aggregate(total=Sum('amount'))['total']
    deposit_limit = Profile.objects.get(user=request.user).deposit_limit
    
    if (today_total_transaction_amount + amount) >= deposit_limit:
        return HttpResponseServerError("Unable to create deposit order because the total daily transaction exceeds deposit limit!")
    
    
    transaction = Transaction.objects.create(user=request.user, amount=amount )
    transaction.save()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    merchantId = settings.NUVEI_MERCHANT_ID
    siteId = settings.NUVEI_MERCHANT_SITE_ID
    currency = "GBP" if profile.country == "UK" else "USD"
    secretKey = settings.NUVEI_SECRET_KEY
    requestId = f"{request.user.id}-{datetime.now().strftime('%d%m%Y-%H%M')}"

    message = merchantId + siteId + requestId + str(amount) + currency + timestamp + secretKey
    country = "US" if profile.country == "USA" else profile.country
    hash_object = hashlib.sha256(message.encode())
    checksum = hash_object.hexdigest()
    data = {  
        "merchantId": merchantId,
        "merchantSiteId": siteId,
        "clientUniqueId":  str(transaction.id),
        "clientRequestId": requestId,
        "currency": currency, 
        "amount": str(amount),
        "userDetails": {
            "country": country,
            "email": request.user.email
        },
        "timeStamp":timestamp,
        "checksum": checksum    
    }

    with requests.post(f"{settings.NUVEI_URL}/openOrder.do", json=data) as response:
        if response.status_code == 200:
            try:
                response_json = response.json()
                transaction.status = response_json["status"]
                transaction.session_token = response_json["sessionToken"]
                transaction.save()
                return redirect(reverse('checkout-deposit', kwargs={"transactionId": str(transaction.id)}))
            except JSONDecodeError as e:
                log.error(e)
                return HttpResponseServerError("Unable to create deposit order")
        else:
            try:
                response_body = response.json()
            except:
                response_body = response.text
            log.critical("Failed to open nuvei order")
            log.critical(response_body)
            return HttpResponseServerError("Unable to create deposit order")

class CheckoutDepositView(TemplateView):
    template_name='wagering/deposit.html'
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        transactionId = kwargs["transactionId"]
        if transactionId == None:
            raise ParseError("Deposit transaction not found")
        try:
            transaction = Transaction.objects.get(pk=transactionId)
        except Transaction.DoesNotExist:
            raise ParseError("Deposit transaction not found")
        context["isDev"] = settings.DEBUG
        context["amount"] = transaction.amount
        context["nuvei_data"] = {
            "sessionToken": transaction.session_token,
            "merchantId": settings.NUVEI_MERCHANT_ID,
            "siteId": settings.NUVEI_MERCHANT_SITE_ID,
            "transactionId": str(transactionId)
        }
        context["user_data"] = {
            "fullName": transaction.user.get_short_name(),
            "email": transaction.user.email,
            "country": transaction.user.profile.country
        }
        return context