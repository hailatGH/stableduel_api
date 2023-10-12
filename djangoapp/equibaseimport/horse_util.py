import string
import unicodedata
from .utils import get_int_from_EL, get_text_from_EL, get_float_from_EL
import requests
import base64
from django.conf import settings
from datetime import datetime
punctuation_map = dict((ord(char), None) for char in string.punctuation)


def get_horse_id(horse_name):
    return clean_name(horse_name)


def clean_name(name):

    name = strip_accents(name)
    name = name.lower()
    name = name.strip()

    if ("(") in name:
        name = name.split(" (")[0]


    if isinstance(name, str):
        name = name.translate(str.maketrans('','',"-0/123456789^.(){}<>-!_`',"))
    elif isinstance(name, unicode):
        name = name.translate(punctuation_map)

    name = name.replace(" ", ".")

    return name



def strip_accents(text):
    """
    Strip accents from input String.

    :param text: The input string.
    :type text: String.

    :returns: The processed String.
    :rtype: String.
    """
    
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)

def get_past_performance_data(past_performance_EL):

    past_performance = {}

    past_performance['date'] = get_text_from_EL(past_performance_EL.find('RaceDate'), '')

    race_type = get_text_from_EL(past_performance_EL.find('RaceType/RaceType'), '')
    grade = get_text_from_EL(past_performance_EL.find('Grade'), '')
    if grade is not None and race_type == "STK":
        race_type = "G" + grade

    past_performance['race'] = {
        'track': get_text_from_EL(past_performance_EL.find('Track/TrackID'), ''),
        'race_number': get_text_from_EL(past_performance_EL.find('RaceNumber'), ''),
        'race_type': race_type
    }
    past_performance['distance'] = get_text_from_EL(past_performance_EL.find('Distance/PublishedValue'), '')
    past_performance['surface'] = get_text_from_EL(past_performance_EL.find('Course/Surface/Value'), '')

    position = 0
    lengths = 0

    for point_of_call in past_performance_EL.findall('Start/PointOfCall'):
        if(get_text_from_EL(point_of_call.find('PointOfCall'), '') == 'F'):
            position = get_int_from_EL(point_of_call.find('Position'), 0)

            if position == 1:
                lengths = get_float_from_EL(point_of_call.find('LengthsAhead'), 0.0) / 100
            else:
                lengths = get_float_from_EL(point_of_call.find('LengthsBehind'), 0.0) / 100
        else:
            continue

    past_performance['finish'] = {
        'position': position,
        'lengths': lengths
    }

    performance_figure = get_float_from_EL(past_performance_EL.find('Start/SpeedFigure'), '')
    odds_text = past_performance_EL.find('Start/Odds').text
    odds = 0
    if (odds_text is not None):
        odds = float(odds_text) / 100

    past_performance['odds'] = odds
    past_performance['performance_figure'] = performance_figure

    return past_performance











def get_harness_past_performance_data(past_performance_EL):

    past_performance = {}

    past_performance['date'] = get_text_from_EL(past_performance_EL.find('date'), '')

    race_type = ""
    grade = get_text_from_EL(past_performance_EL.find('Grade'), '')
    if grade is not None and race_type == "STK":
        race_type = "G" + grade

    past_performance['race'] = {
        'track': get_text_from_EL(past_performance_EL.find('track'), ''),
        'race_number': get_text_from_EL(past_performance_EL.find('racenum'), ''),
        'race_type': race_type
    }
    past_performance['distance'] = get_text_from_EL(past_performance_EL.find('dist'), '')
    past_performance['surface'] = 'D'

    position = 0
    lengths = 0

    # for point_of_call in past_performance_EL.findall('Start/PointOfCall'):
    #     if(get_text_from_EL(point_of_call.find('PointOfCall'), '') == 'F'):
    #         position = get_int_from_EL(point_of_call.find('Position'), 0)

    #         if position == 1:
    #             lengths = get_float_from_EL(point_of_call.find('LengthsAhead'), 0.0) / 100
    #         else:
    #             lengths = get_float_from_EL(point_of_call.find('LengthsBehind'), 0.0) / 100
    #     else:
    #         continue
    # finall_call_position= get_int_from_EL(past_performance_EL.find('call_fn_po'))
    # if finall_call_position == 1:
    position = get_int_from_EL(past_performance_EL.find('call_fn_po'), 0.0)
    if position == 1:
        try:
            lengths = get_float_from_EL(past_performance_EL.find('compli_la2'), 0.0)
        except:
            lengths = 0.0
    else:
        try:
            lengths = get_float_from_EL(past_performance_EL.find('call_fn_lb'), 0.0)
        except:
            lengths = 0.0
    

            


    past_performance['finish'] = {
        'position': position,
        'lengths': lengths
    }
    performance_figure = get_float_from_EL(past_performance_EL.find('sr'), '')
    odds_text = past_performance_EL.find('odds').text
    odds = 0
    if (odds_text is not None):
        odds = float(odds_text) / 100

    past_performance['odds'] = odds
    past_performance['performance_figure'] = performance_figure
    
    return past_performance








def get_pa_past_performance_data(past_performance_EL):

    past_performance = {}

    past_performance['date'] = get_text_from_EL(past_performance_EL.attrib['date'], '')

    race_type = ""
    grade = get_text_from_EL(past_performance_EL.find('Grade'), '')
    if grade is not None and race_type == "STK":
        race_type = "G" + grade

    past_performance['race'] = {
        'track': get_text_from_EL(past_performance_EL.attrib['course'], ''),
        'race_number': get_text_from_EL(past_performance_EL.find('racenum'), ''),
        'race_type': race_type
    }
    Distance = past_performance_EL.find('Distance')
    past_performance['distance'] = Distance.attrib['value'],
    past_performance['surface'] = get_text_from_EL(past_performance_EL.find('Course/Surface/Value'), '')

    position = 0
    lengths = 0

    # for point_of_call in past_performance_EL.findall('Start/PointOfCall'):
    #     if(get_text_from_EL(point_of_call.find('PointOfCall'), '') == 'F'):
    #         position = get_int_from_EL(point_of_call.find('Position'), 0)

    #         if position == 1:
    #             lengths = get_float_from_EL(point_of_call.find('LengthsAhead'), 0.0) / 100
    #         else:
    #             lengths = get_float_from_EL(point_of_call.find('LengthsBehind'), 0.0) / 100
    #     else:
    #         continue
    # finall_call_position= get_int_from_EL(past_performance_EL.find('call_fn_po'))
    # if finall_call_position == 1:
    Result = past_performance_EL.find('Result')
    if Result != None :
        position = get_int_from_EL(Result.attrib['finishPos'], 0.0)
        if position == 1:
            try:
                for Horse in past_performance_EL.findall('FormHorse')[:3]:
                    Result = Horse.find('Result')
                    position= get_int_from_EL(Result.attrib['finishPos'], 0.0)
                    if position != 2:
                        continue
                    elif position == 2:
                        lengths = get_float_from_EL(Result.attrib['btnDistance'], 0.0)
                    else:
                        lengths = 0.0
            except:
                lengths = 0.0
            
        else:
            try:
                lengths = get_float_from_EL(Result.attrib['btnDistance'], 0.0)
            except:
                lengths = 0.0

    past_performance['finish'] = {
        'position': position,
        'lengths': lengths
    }

    performance_figure = get_float_from_EL(past_performance_EL.find('sr'), '')
    try:
        StartingPrice = past_performance_EL.find('StartingPrice/Price')
        numerator = get_int_from_EL(StartingPrice.attrib['numerator'], 0)
        denominator = get_int_from_EL(StartingPrice.attrib['denominator'], 0)
        odds = int(numerator)/int(denominator)
        odds = float (odds/100)
    except:
        odds = 0
    # odds_text = past_performance_EL.find('odds')
    # odds = 0
    # if (odds_text is not None):
    #     odds_text = odds_text.textodds_text = past_performance_EL.find('odds')
    # odds = 0
    # if (odds_text is not None):
    #     odds_text = odds_text.text
    #     odds = float(odds_text) / 100
    #     odds = float(odds_text) / 100

    past_performance['odds'] = odds
    past_performance['performance_figure'] = 80
    
    return past_performance





def get_pa_past_performance_data_from_API(race_date,race_id,horse_id):
    past_performance = {}
    # username = "Stable_Duel"
    # password = "zPVVK2aeYT"
    username="stableduelm"
    passwordATR="U8lc7ztV7i2z"
    # username= settings.ATR_USER_NAME
    # passwordATR = settings.PASSWORD_ATR
    race_date = race_date
    # race_date = datetime.strptime(race_date, "%Y-%m-%d %H:%M:%S")
    race_date = race_date.strftime("%Y%m%d")
    # api_meeting_url = f"https://webapi.attheraces.com/api/v3/RaceData?fixtureDate={race_date}"  # Replace with the actual API URL
    api_meeting_url = f"https://atrapi.attheraces.com/api/v3/RaceData?fixtureDate={race_date}"  # Replace with the actual API URL
    auth_header = {"Authorization": "Basic " + (base64.b64encode(f"{username}:{passwordATR}".encode("utf-8")).decode("utf-8"))}
    # Prepare the request headers
    # print (username)
    # print (passwordATR)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        # "Host": "sd-api-dev.stableduel.com",
        "Ocp-Apim-Subscription-Key": "005d4cbd87e14adeb9d1cbb988a4b43d",
    }
    headers.update(auth_header)
    # Send GET request to the API
    meeting_response=requests.get(api_meeting_url, headers=headers)
    # print (meeting_response.text)
    json_meeting_response = meeting_response.json()
    if json_meeting_response is not None:
        meetings = json_meeting_response['meeting']
        for meeting in meetings:
            for race in meeting ['race']:
                pa_race_id=race['pA_RACEID']
               
                if pa_race_id == int(race_id):
                    api_race_id= race['raceid']
                    
                    break
    # api_race_url = f"https://webapi.attheraces.com/api/v3/RaceData?raceid={api_race_id}"  # Replace with the actual API URL
    api_race_url = f"https://atrapi.attheraces.com/api/v3/RaceData?raceid={api_race_id}"  # Replace with the actual API URL
 
    race_response=requests.get(api_race_url, headers=headers)
    json_race_response = race_response.json()
    
    if json_race_response is not None:
            horses = json_race_response['horses']['horse']
            for horse in horses:
                pa_horse_id = horse['pa_id']
                if pa_horse_id == int(horse_id):
                    api_horse_id= horse['horseID']
                    break
    # api_horse_url = f"https://webapi.attheraces.com/api/v3/horse?horseId={api_horse_id}"
    api_horse_url = f"https://atrapi.attheraces.com/api/v3/horse?horseId={api_horse_id}"
    horse_response = requests.get(api_horse_url, headers=headers)

    
    past_performances = []
    if horse_response.status_code == 200:
        json_horse_response =horse_response.json()
        
        if json_horse_response is not None:
            races = json_horse_response['race']
            races= races[-6:]
            
            for race in races:
                past_performance['date']=race['sortDate']
                past_performance['race']={
                    'track':race['courseName'],
                    'race_number':race['raceNumber'],
                    'race_type':race['raceType'],
                }
                past_performance['distance']=str(race['distance'])
                past_performance['surface'] =race['trackType']
                position = 0
                lengths = 0.0
                if race['finishPositionSpecified']:
                    position=race['finishPosition']
                
                if position == 1:
                    try:
                        lengths = race['distanceAhead']
                    except:
                        lengths = 0.0
                else:
                    try:
                        lengths = race['distanceBehind']
                    except:
                        lengths = 0.0
                past_performance['finish'] = {
                    'position': position,
                    'lengths': lengths
                }
                if race["officialRatingSpecified"]:
                    performance_figure= race["officialRating"]
                else:
                    performance_figure = 0
                try:
                    StartingPrice = race['startingPrice']
                    odds = int(StartingPrice)
                    # odds = float (odds/100)
                except:
                    odds = 0
                
                past_performance['odds'] = odds
                past_performance['performance_figure'] = performance_figure
                past_performances.append(past_performance)

            return past_performances
                
        else:
            
            
            return past_performances
    else:
        print("Failed to retrieve API response. Status code:", horse_response.status_code)
        return past_performances





def get_workout_data(workout_EL):

    workout = {}

    workout['date'] = get_text_from_EL(workout_EL.find('Date'), '')
    workout['track'] = {
        'id': get_text_from_EL(workout_EL.find('Track/TrackID'), ''),
        'distance': get_text_from_EL(workout_EL.find('Distance/PublishedValue'), ''),
        'condition': get_text_from_EL(workout_EL.find('TrackCondition/Value'), '')
    }

    workout['timing'] = get_int_from_EL(workout_EL.find('Timing'), 0)
    workout['type'] = get_text_from_EL(workout_EL.find('TypeOfWorkout/Value'), '')
    workout['ranking'] = {
        'rank': get_int_from_EL(workout_EL.find('Ranking'), 0),
        'total': get_int_from_EL(workout_EL.find('NumberInRankingGroup'), 0) 
    }

    return workout

def get_pedigree_data(horse_EL):
    pedigree = {}

    pedigree['breeder'] = get_text_from_EL(horse_EL.find('BreederName'), '')
    pedigree['sire'] = get_text_from_EL(horse_EL.find('Sire/HorseName'), '')


    dam_EL = horse_EL.find('Dam')

    pedigree['dam'] = {
        'name': get_text_from_EL(dam_EL.find('HorseName'), ''),
        'sire': get_text_from_EL(dam_EL.find('Sire/HorseName'), '')
    }
    
    pedigree['type'] = get_text_from_EL(horse_EL.find('BreedType/Value'), '')
    pedigree['color'] = get_text_from_EL(horse_EL.find('Color/Value'), '')
    pedigree['sex'] = get_text_from_EL(horse_EL.find('Sex/Value'), '')
    pedigree['foaling_date'] = get_text_from_EL(horse_EL.find('FoalingDate'), '')
    pedigree['foaling_area'] = get_text_from_EL(horse_EL.find('FoalingArea'), '')

    return pedigree





def get_pedigree_data_harness(horse_EL):
    pedigree = {}

    pedigree['breeder'] = get_text_from_EL(horse_EL.find('breed_name'), '')
    pedigree['sire'] = get_text_from_EL(horse_EL.find('sire/sirename'), '')


    dam_EL = horse_EL.find('dam')

    pedigree['dam'] = {
        'name': get_text_from_EL(dam_EL.find('damname'), ''),
        'sire': get_text_from_EL(dam_EL.find('damsire'), '')
    }
    
    # pedigree['type'] = get_text_from_EL(horse_EL.find('breedtype'), '')
    pedigree['type'] = 'SB'
    pedigree['color'] = get_text_from_EL(horse_EL.find('color'), '')
    pedigree['sex'] = get_text_from_EL(horse_EL.find('sex'), '')
    pedigree['foaling_date'] = get_text_from_EL(horse_EL.find('foalingdate'), '')
    pedigree['foaling_area'] = get_text_from_EL(horse_EL.find('foalingarea'), '')

    return pedigree










def get_pedigree_data_pa(horse_EL):
    pedigree = {}
    try:
        sire = get_text_from_EL(horse_EL.find('Breeding[@type="Sire"]').attrib['name'], '')
    except:
        sire = ''
    try:
        breeder = get_text_from_EL(horse_EL.find('Breeder').attrib['name'], '')
    except:
        breeder = ''
    pedigree['sire'] = sire
    pedigree['breeder'] = breeder

    try:
        dam_sire = get_text_from_EL(horse_EL.find('Breeding[@type="DamSire"]').attrib['name'], '')
    except:
        dam_sire = ''

    pedigree['dam'] = {
        'name': get_text_from_EL(horse_EL.find('Breeding[@type="Dam"]').attrib['name'], ''),
        'sire': dam_sire
    }
    
    # pedigree['type'] = get_text_from_EL(horse_EL.find('breedtype'), '')
    pedigree['type'] = get_text_from_EL(horse_EL.attrib['bred'], '')
    pedigree['Weight']=get_text_from_EL(horse_EL.find('Weight').attrib['value'], '')
    pedigree['color'] = get_text_from_EL(horse_EL.find('Colour').attrib['type'], '')
    pedigree['sex'] = get_text_from_EL(horse_EL.find('Sex').attrib['type'], '')
    pedigree['foaling_date'] = get_text_from_EL(horse_EL.find('FoalDate').attrib['date'], '')
    pedigree['foaling_area'] = get_text_from_EL(horse_EL.find('FoalingArea'), '')
    return pedigree







def get_career_data(race_summary_ELs):
    
    starts  = 0
    wins    = 0
    seconds = 0
    thirds  = 0
    earnings = 0.0

    for race_summary_EL in race_summary_ELs:
        #Per discussion with Equibase, only D&T records should be added for horse as others
        #are subsets of these
        if(get_text_from_EL(race_summary_EL.find('Surface/Value'),'') in ["D","T"]):
            starts += get_int_from_EL(race_summary_EL.find('NumberOfStarts'), 0)
            wins += get_int_from_EL(race_summary_EL.find('NumberOfWins'), 0)
            seconds += get_int_from_EL(race_summary_EL.find('NumberOfSeconds'), 0)
            thirds += get_int_from_EL(race_summary_EL.find('NumberOfThirds'), 0)
            earnings += get_float_from_EL(race_summary_EL.find('EarningsUSA'), 0.0)
        
    return {
        'starts': starts,
        'wins': wins,
        'seconds': seconds,
        'thirds': thirds,
        'earnings': earnings
    }

def get_career_data_harness(horse_EL):
    
    starts  = 0
    wins    = 0
    seconds = 0
    thirds  = 0
    earnings = 0.0

    # for horse_EL in horse_ELs:
        #Per discussion, only D records should be added for horse as there is no other surface value in harness
        # RCA91_AL_S 
        # RCA91_AL_1
        # RCA91_AL_2 
        # RCA91_AL_3 
        # ERA91AL_PD
        
    starts += get_int_from_EL(horse_EL.find('rcaty_s'), 0)
    wins += get_int_from_EL(horse_EL.find('rcaty_1'), 0)
    seconds += get_int_from_EL(horse_EL.find('rcaty_2'), 0)
    thirds += get_int_from_EL(horse_EL.find('rcaty_3'), 0)
    earnings += get_float_from_EL(horse_EL.find('eratyal_pd'), 0.0)
    
    return {
        'starts': starts,
        'wins': wins,
        'seconds': seconds,
        'thirds': thirds,
        'earnings': earnings
    }


def get_career_data_pa(horse_EL):
    
    starts  = 0
    wins    = 0
    # seconds = 0
    # thirds  = 0
    places = 0
    earnings = 0.0

    # for horse_EL in horse_ELs:
        #Per discussion, only D records should be added for horse as there is no other surface value in harness
        # RCA91_AL_S 
        # RCA91_AL_1
        # RCA91_AL_2 
        # RCA91_AL_3 
        # ERA91AL_PD
    Career = horse_EL.find('Career')
    starts += get_int_from_EL(Career.attrib['runs'], 0)
    wins += get_int_from_EL(Career.attrib['wins'], 0)
    # seconds += get_int_from_EL(horse_EL.find('rcaty_2'), 0)
    # thirds += get_int_from_EL(horse_EL.find('rcaty_3'), 0)
    places += get_int_from_EL(Career.attrib['places'], 0)
    earnings += get_float_from_EL(Career.attrib['prizeMoney'], 0.0)
    
    return {
        'starts': starts,
        'wins': wins,
        'places': places,
        # 'seconds': seconds,
        # 'thirds': thirds,
        'earnings': earnings
    }
