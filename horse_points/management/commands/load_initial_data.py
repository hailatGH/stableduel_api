from django.core.management.base import BaseCommand, CommandError

from horse_points.models import HorsePoint
from stables.models import Runner
from follows.models import Follows

class Command(BaseCommand):
    help = 'Load initial data from the system'

    def handle(self, *args, **options):
        runners = Runner.objects.all()

        for r in runners:
            if(r.score is not None):
                horse_point, _ = HorsePoint.objects.get_or_create(external_id=r.external_id, defaults={'points':0,'count':0})
                horse_point.points += r.score
                horse_point.count +=1
                horse_point.save() 

        follows = Follows.objects.all()
        horse_points = HorsePoint.objects.all()
        for f in follows:
            for hp in horse_points:
                if f.horse == hp.external_id:
                    f.horse_point = hp
                    f.save()

