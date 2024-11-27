from celery.decorators import task
from celery import shared_task
from celery.utils.log import get_task_logger
from rest_framework.response import Response
from django.conf import settings
from .models import User
import requests

logger = get_task_logger(__name__)

@shared_task(name="drip_integration_task",autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 2})
def drip_integration_task(user_id):
    pass
    # #Integrate DRIP
    # user = User.objects.get(id=user_id)
    # logger.info("DRIP Integration")
    # headers = {'Content-type': 'application/json',
    #            'User-Agent': 'StableDuel'}
    # data = {
    #     'subscribers': [
    #         {
    #             'email': user.email,
    #             'custom_fields': {
    #                 'first_name': user.first_name, 
    #                 'last_name': user.last_name
    #             },
    #         },
    #     ],
    # }
    # post= 'https://api.getdrip.com/v2/' + settings.DRIP_ACCOUNT_ID  + '/subscribers'

    # response = requests.post('https://api.getdrip.com/v2/' + settings.DRIP_ACCOUNT_ID  + '/subscribers',auth=(settings.DRIP_API_TOKEN, ''),headers=headers,json=data)
    # if not response.ok:
    #     raise Exception('DRIP Connection Error')


