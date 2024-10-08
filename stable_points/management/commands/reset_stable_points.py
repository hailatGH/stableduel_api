from django.core.management.base import BaseCommand, CommandError

from stable_points.models import StablePoint

class Command(BaseCommand):
    help = 'Reset all Stable points to zero'

    def add_arguments(self, parser):
        parser.add_argument(
            '--game_id',
            type=str,
            help='ID of game',
        )

        pass

    def handle(self, *args, **options):
        stable_points = StablePoint.objects.all().select_related('stable')
        if (options['game_id']):
            stable_points = stable_points.filter(stable__game_id=options['game_id'])
            for stable_point in stable_points:
                stable_point.points = 0
                stable_point.notes = "Stable Points deleted for cancelled Game {}".format(options['game_id'])
                stable_point.save()
            
        else:
            for stable_point in stable_points:
                stable_point.points = 0
                stable_point.notes = ''
                stable_point.save()
        


        