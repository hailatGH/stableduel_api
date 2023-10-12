# from celery import chain, shared_task
# from datetime import datetime, timedelta

# from equibaseimport.functions import harness_result

# @shared_task(bind=True)
# def harness_result_function_call(self, track_code):
#     harness_result(track_code)

# @shared_task(bind=True)
# def harness_result_schedule(self, start_time, end_time, track_code):
#     current_time = datetime.now()
#     if start_time <= current_time <= end_time:
#         next_execution_time = current_time + timedelta(minutes=15)
#         chain(harness_result_function_call.s(track_code))()
#         harness_result_schedule.apply_async(args=(start_time, end_time, track_code), eta=next_execution_time, expires=end_time)