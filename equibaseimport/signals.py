# from datetime import datetime
# from django.dispatch import receiver
# from django.db.models.signals import post_save

# from racecards.models import Racecard
# from racecards.utils import get_full_race_time
# from equibaseimport.tasks import harness_result_schedule
        
# @receiver(post_save, sender=Racecard)
# def racecard_model_save_handler(sender, instance, created, **kwargs):
#     if instance.mode == "HARNESS":
#         if created:
#             # get the races json 
#             races = instance.races[0]
#             track_code = instance.track
#             start_time = get_full_race_time(instance.races[0])
#             end_time = get_full_race_time(instance.races[-1])
            
#             harness_result_schedule.apply_async(args=(start_time, end_time, track_code), countdown=(start_time - datetime.now()).total_seconds(), expires=end_time)