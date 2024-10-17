from django.core.management.base import BaseCommand, CommandError
import xml.etree.ElementTree as ET

from racecards.models import Track, Racecard
from stables.models import Runner

from equibaseimport import horse_util

class Command(BaseCommand):
    help = 'Load racecard from given Equibase XML file'

    def add_arguments(self, parser):
        parser.add_argument('race_date', type=str)

        pass

    def handle(self, *args, **options):
        file_path = '/home/vagrant/stableduel/test-files/CHARTD_01_IND.xml' #options['file']
        race_date = options['race_date']
        print(race_date)
    
        tree = ET.parse(file_path)
        root = tree.getroot()
        trackEL = root.find('Track')
        track_code = trackEL.find('TrackID').text
        track_name = trackEL.find('TrackName').text
        track_country = trackEL.find('Country').text
        track, _ = Track.objects.get_or_create(code=track_code, name=track_name, country=track_country)
        print(track)

        file_path = '/home/vagrant/stableduel/test-files/SIMD_01_IND.xml' #options['file']
        tree = ET.parse(file_path)
        root = tree.getroot()
        racecard, _ = Racecard.objects.get_or_create(track=track, race_date=race_date)
        races = []
        for raceEL in root.findall('Race'):
            race_number = raceEL.find('RaceNumber').text
            race = {
                'race_number': race_number,
                'surface': raceEL.find('Course/Surface/Value').text,
                'post_time': raceEL.find('PostTime').text,
                'race_type': raceEL.find('RaceType/RaceType').text,
                'race_type_description': raceEL.find('RaceType/Description').text,
                'distance': raceEL.find('Distance/PublishedValue').text,
                'division': raceEL.find('Division').text,
            }
            print(race)
            races.append(race)

            for starterEL in raceEL.findall('Starters'):
                runner, _ = Runner.objects.get_or_create(racecard=racecard, external_id=starterEL.find('Horse/RegistrationNumber').text)
                runner.race_number = race_number
                runner.post_position = starterEL.find('PostPosition').text
                runner.name = starterEL.find('Horse/HorseName').text
                runner.trainer = "{} {}".format(starterEL.find('Trainer/FirstName').text, starterEL.find('Trainer/LastName').text)
                runner.jockey =  "{} {}".format(starterEL.find('Jockey/FirstName').text, starterEL.find('Jockey/LastName').text)
                runner.owner =  "{} {}".format(starterEL.find('Owner/FirstName').text, starterEL.find('Owner/LastName').text)
                runner.odds = starterEL.find('Odds').text

                runner.pedigree = horse_util.get_pedigree_data(starterEL.find('Horse'))

                runner.career_stats = horse_util.get_career_data(starterEL.findall('RaceSummary'))

                past_performances = []

                for past_performance_EL in starterEL.findall('PastPerformance')[:5]:
                    past_performance = horse_util.get_past_performance_data(past_performance_EL)
                    past_performances.append(past_performance)

                runner.past_performance = past_performances

                workouts = []

                for workout_EL in starterEL.findall('Workout'):
                    workout = horse_util.get_workout_data(workout_EL)
                    workouts.append(workout)

                runner.workouts = workouts

                runner.save()
                print(runner)


        racecard.races = races
        racecard.save()

        print(racecard)


        self.stdout.write(self.style.SUCCESS('Finished parsing XML file'))