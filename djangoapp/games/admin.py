import csv

from analytics.amplitude_api import amplitude_contest_result
from django.contrib import admin
from django.db.models import Count, Q
from django.http import HttpResponse
from django_summernote.admin import SummernoteModelAdmin
from games.forms import BannerForm
from games.models import Banner, Game, GameUser, GameExcludeUsers, GamePayout
from games.tasks import cancel_game, finish_game
from notifications.constants import Action, Lifespan, Type
from notifications.models import Notification
from notifications.push_notifications import PushToUsersNotification
from stable_points.models import StablePoint
from stables.models import (Stable, calculate_scores_ranks,
                            calculate_stable_is_valid, invalid_stables)
from stables.notifications import IncompleteStableNotification
from wagering.chrims_api import finalize_bets

from .notifications import FirstPostNotification
from games.forms import GameUserFormSet, GamePayoutFormSet
class GameUserInlineAdmin(admin.TabularInline):
    model=  GameUser
    formset = GameUserFormSet
    verbose_name = "Private User"
    verbose_name_plural = "Private Users"
    extra = 0

class GameExcludeUserInlineAdmin(admin.TabularInline):
    model=  GameExcludeUsers
    # formset = GameUserFormSet
    verbose_name = "Exclude User"
    verbose_name_plural = "Exclude Users"
    extra = 0

class GamePayoutInlineAdmin(admin.TabularInline):
    model = GamePayout
    formset = GamePayoutFormSet
    verbose_name = "Payout"
    verbose_name_plural = "Payouts"
    extra = 0

@admin.register(Game)
class GameAdmin(SummernoteModelAdmin):
    list_display = ["name", "started", "finished", "archived" ]
    search_fields = ["name"]
    raw_id_fields = ["racecard",]
    inlines = [GameUserInlineAdmin, GameExcludeUserInlineAdmin, GamePayoutInlineAdmin]

    actions = [
        'mark_incomplete_stables_invalid',
        'send_scratch_notifications',
        'send_incomplete_notifications',
        'send_first_post_notifications',
        'finish_game',
        'cancel_game',
        'archive_game',
        'export_stables',
    ]

    def send_scratch_notifications(self, request, queryset):
        for game in queryset:
            auth0_ids = list(game.stable_set.filter(~Q(is_valid_at_start=False)).filter(runners__scratched=True).distinct().values_list('user__auth0_id', flat=True))

            if (len(auth0_ids)):
                pn = PushToUsersNotification(Type.SCRATCH, Action.GO_TO_STABLE, Lifespan.PERSISTENT_CONDITIONAL, auth0_ids, None)
                pn.title = 'Scratches in stable'
                pn.message = 'There are scratches in your stable. Please update your stable'
                pn.send()

            self.message_user(request, "{} users messaged about scratched runners".format(len(auth0_ids)))

    send_scratch_notifications.short_description = "Send scratch notifications for selected games"


    def send_first_post_notifications(self, request, queryset):
        for game in queryset:
            
            pn = FirstPostNotification(game)
            pn.send()

            self.message_user(request, "Sent message about first post for game: {}".format(str(game.name)))
    
    send_first_post_notifications.short_description = "Send notifications about 30 minutes to post"

    def send_incomplete_notifications(self, request, queryset):
        for game in queryset:
            auth0_ids = [stable.user.auth0_id for stable in invalid_stables(game)]
            auth0_ids = list(set(auth0_ids))
            print(auth0_ids)

            if (len(auth0_ids)):
                pn = IncompleteStableNotification(auth0_ids)
                pn.send()

            self.message_user(request, "{} users messaged about incomplete stables".format(len(auth0_ids)))
    
    send_incomplete_notifications.short_description = "Send notifications about incomplete stables"

    def mark_incomplete_stables_invalid(self, request, queryset):
        for game in queryset:

            valid_stable_count, invalid_stables_count = calculate_stable_is_valid(game)
            calculate_scores_ranks(game)

            stables = Stable.objects.filter(game=game).annotate(runner_count=Count('runners')).prefetch_related('runners')
            finalize_bets(stables)
            game.started = True
            game.game_state = Game.LIVE
            game.save()
            
        self.message_user(request, "Game started ({} valid and {} invalid stables)".format(valid_stable_count, invalid_stables_count))

    mark_incomplete_stables_invalid.short_description = 'Start game'

    def finish_game(self, request, queryset):
        for game in queryset:
            finish_game(game.id)

        self.message_user(request, "Games have been finished")

    finish_game.short_description = 'Finish game'

    def cancel_game(self, request, queryset):
        for game in queryset:
            cancel_game(game.id)

        self.message_user(request, "Games have been cancelled")

    cancel_game.short_description = 'Cancel Game'


    def archive_game(self, request, queryset):
        for game in queryset:
            game.archived = True
            game.save()

        self.message_user(request, "Games have been archived")

    archive_game.short_description = 'Archive game'

    def export_stables(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=stables.csv'
        writer = csv.writer(response)
        field_names = [
            'game',
            'stable_id',
            'email',
            'first_name',
            'last_name',
            'stable_name',
            'has_scratches',
            'is_incomplete',
            'scratch_count',
            'runner_count',
            'score',
            'rank',
            'is_valid_at_start',
            'scratch_limit_reached',
            'scratches_at_finish',
            'stable_count_at_finish',
        ]
        writer.writerow(field_names)

        for game in queryset:
            stables = Stable.objects.filter(game=game).select_related('user')
            for stable in stables:
                runners = stable.runners.all()
                scratches = [runner for runner in runners if runner.scratched]

                writer.writerow([
                    game.name,
                    stable.id,
                    stable.user.email,
                    stable.user.first_name,
                    stable.user.last_name,
                    stable.user.profile.stable_name,
                    len(scratches) > 0,
                    len(runners) < 10,
                    len(scratches),
                    len(runners),
                    stable.score if stable.rank is not None else None,
                    stable.rank,
                    stable.is_valid_at_start,
                    stable.scratch_limit_reached,
                    stable.scratches_at_finish,
                    stable.stable_count_at_finish,
                ])

        return response
        self.message_user(request, "Stables exported")

    export_stables.short_description = 'Export stables'
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    form=BannerForm
    list_display = ["name", "game", "link","visibility", "image",]

@admin.register(GameUser)
class GameUserAdmin(admin.ModelAdmin):
    list_display = ["game", "user"]
    # inlines = [UserInlineAdmin]
    
@admin.register(GameExcludeUsers)
class GameExcludeUsersAdmin(admin.ModelAdmin):
    list_display = ["game", "user"]