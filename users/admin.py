from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model

from .forms import UserChangeForm, UserCreationForm
from notifications.push_notifications import PushToUsersNotification
from notifications.constants import Type, Lifespan, Action
from .models import Profile

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = auth_admin.UserAdmin.fieldsets
    list_display = ["username", "is_superuser"]
    search_fields = ["email"]
    actions = ['send_scratch_notifications', ]

    def send_scratch_notifications(self, request, queryset):
        auth0_ids = list(queryset.distinct().values_list('auth0_id', flat=True))
        print(auth0_ids)
        pn = PushToUsersNotification(Type.SCRATCH, Action.GO_TO_STABLE, Lifespan.PERSISTENT, auth0_ids, None)
        pn.title = 'Scratched horse in your stable'
        pn.message = 'You have a scratched horse in your stable.'
        pn.send()
        self.message_user(request, "{} users messaged about scratched runners".format(len(auth0_ids)))
    send_scratch_notifications.short_description = "Send scratch notifications for selected users"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user__email"]
    search_fields = ["user__email"]

    def user__email(self, obj):
        if obj.user:
            return obj.user.email
        return None
