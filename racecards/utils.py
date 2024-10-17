from datetime import datetime

def get_first_post_time(racecard):
    race_date = racecard.races[0]['adjusted_date']
    if(type(race_date) == str):
        race_date = datetime.strptime(race_date, '%Y-%m-%d')
        
    start_time = datetime.strptime(racecard.races[0]['post_time'], '%I:%M%p')
    eta = datetime.combine(race_date, start_time.time())

    return eta


def get_full_race_time(race):
    race_date = race['adjusted_date']
    if(type(race_date) == str):
        race_date = datetime.strptime(race_date, '%Y-%m-%d')
        
    start_time = datetime.strptime(race['post_time'], '%I:%M%p')
    eta = datetime.combine(race_date, start_time.time())

    return eta