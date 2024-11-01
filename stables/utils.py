from sys import maxsize
import math
from django_redis import get_redis_connection


odds_to_salary = {
    '1-9':20000,
    '1-5':15000,
    '1-3':14500,
    '2-5':14000,
    '1-2':13000,
    '3-5':12000,
    '4-5':11000,
    '5-5':10000,
    'Even':10000,
    '1-1':10000,
    '11-10':9950,
    '7-4':9900,
    '6-5':9800,
    '13-8':9700,
    '3-2':9500,
    '7-5':9600,
    '5-4':9450,
    '8-5':9400,
    '9-4':9300,
    '9-5':9200,
    '2-1':9000,
    '5-2':8500,
    '3-1':8000,
    '7-2':7500,
    '4-1':7000,
    '9-2':6500,
    '5-1':6000,
    '6-1':5000,
    '7-1':4000,
    '8-1':3000,
    '9-1':2000,
    '10-1':1000,
    '12-1':750,
    '13-1':600, #FIXME: Added no idea the correct salary
    '15-1':500,
    '16-1':400, #FIXME: Added no idea the correct salary
    '18-1':300, #FIXME: Added no idea the correct salary
    '20-1':250,
    '25-1':100,
    '30-1':50,
    '35-1':25, #FIXME: Added no idea the correct salary
    '40-1':0,
    '50-1':0,
    '55-1':0,
    #new
    '11-4':8250, #FIXME: Added no idea the correct salary
    '13-2':4500, #FIXME: Added no idea the correct salary
    '10-11':10500, #FIXME: Added no idea the correct salary 
    '14-1':675, #FIXME: Added no idea the correct salary
    '66-1':0, #FIXME: Added no idea the correct salary
    '6-4':9500, #FIXME: Added no idea the correct salary
    '15-2':3500, #FIXME: Added no idea the correct salary
    '10-3':8000, #FIXME: Added no idea the correct salary
    '33-1':30, #FIXME: Added no idea the correct salary
    '11-2':5500, #FIXME: Added no idea the correct salary

}

fractional_odds_to_salary = [
    {
        "min": 0,
        "max": 0.2,
        "salary": 20000
    },
    {
        "min": 0.2,
        "max": 0.4,
        "salary": 15000
    },
    {
        "min": 0.4,
        "max": 0.5,
        "salary": 14000
    },
    {
        "min": 0.5,
        "max": 0.6,
        "salary": 13000
    },
    {
        "min": 0.6,
        "max": 0.8,
        "salary": 12000
    },
    {
        "min": 0.8,
        "max": 1.0,
        "salary": 11000
    },
    {
        "min": 1.0,
        "max": 1.2,
        "salary": 10000
    },
    {
        "min": 1.2,
        "max": 1.4,
        "salary": 9800
    },
    {
        "min": 1.4,
        "max": 1.5,
        "salary": 9600
    },
    {
        "min": 1.5,
        "max": 1.6,
        "salary": 9500
    },
    {
        "min": 1.6,
        "max": 1.8,
        "salary": 9400
    },
    {
        "min": 1.8,
        "max": 2.0,
        "salary": 9200
    },
    {
        "min": 2.0,
        "max": 2.5,
        "salary": 9000
    },
    {
        "min": 2.5,
        "max": 3,
        "salary": 8500
    },
    {
        "min": 3.0,
        "max": 3.5,
        "salary": 8000
    },
    {
        "min": 3.5,
        "max": 4.0,
        "salary": 7500
    },
    {
        "min": 4.0,
        "max": 4.5,
        "salary": 7000
    },
    {
        "min": 4.5,
        "max": 5.0,
        "salary": 6500
    },
    {
        "min": 5.0,
        "max": 6.0,
        "salary": 6000
    },
    {
        "min": 6.0,
        "max": 7.0,
        "salary": 5000
    },
    {
        "min": 7.0,
        "max": 8.0,
        "salary": 4000
    },
    {
        "min": 8.0,
        "max": 9.0,
        "salary": 3000
    },
    {
        "min": 9.0,
        "max": 10.0,
        "salary": 2000
    },
    {
        "min": 10.0,
        "max": 12.0,
        "salary": 1000
    },
    {
        "min": 12.0,
        "max": 13.0,
        "salary": 750
    },
    {
        "min": 13.0,
        "max": 15.0,
        "salary": 600
    },
    {
        "min": 15.0,
        "max": 16.0,
        "salary": 500
    },
    {
        "min": 16.0,
        "max": 18.0,
        "salary": 400
    },
    {
        "min": 18.0,
        "max": 20.0,
        "salary": 300
    },
    {
        "min": 20.0,
        "max": 25.0,
        "salary": 250
    },
    {
        "min": 25.0,
        "max": 30.0,
        "salary": 100
    },
    {
        "min": 30.0,
        "max": 35.0,
        "salary": 50
    },
    {
        "min": 35.0,
        "max": 40.0,
        "salary": 25
    },
    {
        "min": 40.0,
        "max": maxsize,
        "salary": 0
    }
]

def get_salary(odds):
    if odds is not None and len(odds) > 0:

        odds = odds.replace("/","-")
        if odds not in odds_to_salary:

            numerator = int(odds.split("-")[0])
            denomiator = int(odds.split("-")[1])

            if denomiator == 1 and numerator > 40:
                return 0
            else:
                odds_salary=calculate_odds_to_salary(numerator/denomiator)
                return odds_salary
                # raise  Exception("unknown odds! %s" % odds)
        return odds_to_salary[odds]

    return 0
    
def get_fractional_salary(odds):
    salary = fractional_odds_to_salary[:-1]
    for mapping in fractional_odds_to_salary:
        if odds >= mapping['min'] and odds < mapping['max']:
            salary = mapping
            break
    return salary['salary']


def count_stables_with_score(score : float, game_id):
    conn = get_redis_connection('default')
    score_str = str(score)
    count = conn.zcount(f"stable_scores_{game_id}",score_str, score_str)
    return count if count != None else 0
def calculate_odds_to_salary(odds):
  if odds >= 1 and odds <= 10:
    return -999.96 * odds + 10999.8
  elif odds < 1:
    return 10481 * math.pow(odds, -0.275) 
  else:
    return 2000000 * math.pow(odds, -3.262)
