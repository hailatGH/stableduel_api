import uuid

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField

class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

class Contest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.OneToOneField(
        'games.Game',
        on_delete=models.DO_NOTHING,
    )
    chrims_status_code = models.CharField(max_length=20, blank=True, null=True)
    chrims_error = models.BooleanField(default=False)
    chrims_response = JSONField(null=True, blank=True)

    def __str__(self):
        return str(self.id)


class Bet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stable = models.OneToOneField(
        'stables.Stable',
        null=True,
        on_delete=models.CASCADE,
    )

    chrims_status_code = models.CharField(max_length=20, blank=True, null=True)
    credit = models.BooleanField(default = False)
    chrims_error = models.BooleanField(default=False)
    chrims_response = JSONField(null=True, blank=True)
    bet_submitted = models.BooleanField(default=True)

    def __str__(self):
        return "{} {} {}".format(self.stable.game.name, self.stable.user.email, str(self.id))


class Payout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bet = models.OneToOneField(
        Bet,
        on_delete=models.DO_NOTHING,
    )
    payout_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    void_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    chrims_status_code = models.CharField(max_length=20, blank=True, null=True)
    chrims_error = models.BooleanField(default=False)
    chrims_response = JSONField(null=True, blank=True)
    submitted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

class State(models.Model):
    name=models.CharField(max_length=50)
    abbreviation=models.CharField(max_length=2)


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    session_token = models.CharField(max_length=50, default="CREATED")

    # Transaction Status
    status = models.CharField(max_length=50, default="CREATED")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return str(self.id)