import uuid
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.views import get_current_site

class AccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        user.username = str(uuid.uuid4())

    def save_user(self, request, user, form, commit=True):
        from allauth.account.utils import user_username, user_email, user_field

        data = form.cleaned_data
        email = data.get('email')
        username = data.get('username')
        user_email(user, email)
        user_username(user, username)
        user.set_password(data["password1"])
        self.populate_username(request, user)
        if commit:
            user.save()
        return user

    def get_email_confirmation_url(self, request, emailconfirmation):
        return "%s://%s/verify-email/%s" % (
            request.scheme,
            get_current_site(request).domain,
            emailconfirmation.key,
        )
