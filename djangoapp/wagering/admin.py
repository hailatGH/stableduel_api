import csv, io

from django.http import HttpResponse
from django.contrib import admin
from django.contrib.admin import widgets
from django import forms
from django.urls import path
from django.shortcuts import render, redirect

from games.models import Game
from stables.models import Stable
from .models import Account, Payout, Contest, Bet, State
from .chrims_api import submit_payouts
from analytics.amplitude_api import amplitude_contest_settled
from reversion.admin import VersionAdmin

CREDIT = "Credit"
CASH = "Cash"

PAYOUT_MODE_CHOICES = (
    (CREDIT, "Credit"),
    (CASH, "Cash")
)


class CsvExportForm(forms.Form):
    game = forms.ModelChoiceField(queryset=Game.objects.filter(),
            label="Game")
class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["email", "id"]
    search_fields = ["user__email", "id"]

    def email(self, obj):
        return obj.user.email

@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ["game", "id", "chrims_status_code", "chrims_error" ]
    list_select_related = (
        'game',
    )
    search_fields = ["stable__game__name", "id"]

@admin.register(Bet)
class BetAdmin(VersionAdmin):
    list_display = ["email", "game", "stable_id", "id", "chrims_status_code", "chrims_error", "contest_id", "bet_submitted"]
    list_select_related = (
        'stable',
        'stable__game',
        'stable__game__contest',
        'stable__user',
    )
    search_fields = ["stable__user__email", "id", "stable__game__name", "stable__game__contest__id", "stable__id"]
    list_filter = ['bet_submitted', ]

    def email(self, obj):
        return obj.stable.user.email
    def game(self, obj):
        return obj.stable.game.name
    def contest_id(self, obj):
        return obj.stable.game.contest.id
    def stable_id(self, obj):
        return obj.stable.id


def export_stables(game):
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
        'score',
        'rank',
        'void_amount',
        'payout_amount',
    ]
    writer.writerow(field_names)

    stables = Stable.objects.filter(game=game, is_valid_at_start=True, scratch_limit_reached=False).select_related('user')
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
            stable.score if stable.rank is not None else None,
            stable.rank,
            0,
            0,
        ])


    return response
    self.message_user(request, "Stables exported")

@admin.register(Payout)
class PayoutAdmin(VersionAdmin):
    change_list_template = "wagering/admin/payouts_changelist.html"
    list_display = ['id', 'game', 'email', 'contest_id', 'void_amount', 'payout_amount',  'chrims_status_code', 'chrims_error', 'submitted']
    list_select_related = (
        'bet__stable',
        'bet__stable__game',
        'bet__stable__game__contest',
        'bet__stable__user',
    )
    search_fields = ["bet__stable__user__email", "id", "bet__stable__game__name", "bet__stable__game__contest__id"]
    list_filter = ['submitted', 'bet__stable__game', ]

    def email(self, obj):
        return obj.bet.stable.user.email
    def game(self, obj):
        return obj.bet.stable.game.name
    def contest_id(self, obj):
        return obj.bet.stable.game.contest.id

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
            path('export-csv/', self.export_csv),
            path('submit-payouts/', self.submit_payouts),
        ]
        return my_urls + urls

    def import_csv(self, request):
        STABLE_ID_COLUMN = 1
        VOID_AMOUNT_COLUMN = 8
        PAYOUT_AMOUNT_COLUMN = 9
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            reader = csv.reader(io_string)
            next(reader)
            for row in reader:
                stable = Stable.objects.get(id=int(row[STABLE_ID_COLUMN]))
                payout, _ = Payout.objects.get_or_create(bet=stable.bet)
                payout.payout_amount=row[PAYOUT_AMOUNT_COLUMN]
                payout.void_amount=row[VOID_AMOUNT_COLUMN]
                payout.save()

            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = CsvImportForm()
        payload = {
            "form": form,
            "submit_label": 'Import Payouts',
        }
        return render(
            request, "wagering/admin/payouts_form.html", payload
        )

    def export_csv(self, request):
        if request.method == "POST":
            game_id = int(request.POST['game'])
            game = Game.objects.get(id=game_id)
            self.message_user(request, "Your csv file has been exported")
            return export_stables(game)
        form = CsvExportForm()
        payload = {
            "form": form,
            "submit_label": 'Export Stables',
        }
        return render(
            request, "wagering/admin/payouts_form.html", payload
        )

    def submit_payouts(self, request):
        if request.method == "POST":
            game_id = int(request.POST['game'])

            game = Game.objects.get(id=game_id)
            submit_payouts(game)
            amplitude_contest_settled(game)
            self.message_user(request, "Payouts have been submitted")
            return redirect("..")
        form = CsvExportForm()
        payload = {
            "form": form,
            "submit_label": 'Submit Payouts',
        }
        return render(
            request, "wagering/admin/payouts_form.html", payload
        )


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ["name", "abbreviation"]
    ordering = ("name",)

