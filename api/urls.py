from django.urls import include, path, re_path
from rest_framework import routers

from users.views import CurrentUserDetails, SignupUserView, CurrentProfileUpdate, BeamsAuthView, ValidateBirthdayView, GamstopExcludeUsersCheck
from stables.views import StableViewSet, RunnerViewSet, HorseDetailView, CanCreateStableView
from games.views import GameViewSet, LobbyView
from racecards.views import RacecardViewSet, TrackViewSet, HarnessTracksDetailImportView
from equibaseimport.views import PAImportView, EquibaseImportView, EquibaseImportChangeView, EquibaseImportResultsView, EquibaseImportOfficialResultsView, TrackmasterImportView, HarnessImportView, HarnessImportOfficialResultsView, TrackImportView,TrackmasterHarnessImportView, PATracksDetailImportView, PAImportOfficialResultsView
from notifications.views import NotificationViewSet, InterestsView
from stable_points.views import GlobalLeaderboardView
from user_history.views import UserHistoryView, PastPerformancesView
from follows.views import UserFollowsViewSet, UsersFollowersView, UserFollowsUsersView, UserFollowsHorsesView
from .views import VersionRequirementView, error_500
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from wagering.views import wagering_proxy, WageringStateView, openNuveiOrder, CheckoutDepositView

router = routers.DefaultRouter()
router.register(r'stables', StableViewSet)
router.register(r'games', GameViewSet)
router.register(r'racecards', RacecardViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'runners', RunnerViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'follows', UserFollowsViewSet)

schema_view = get_schema_view(
   openapi.Info(
      title="StableDuel API",
      default_version='v1',
      description="",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="rhunter@apaxsoftware.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path("", include(router.urls)),
    path("leaderboard/", LobbyView.as_view(), name="leaderboard"),
    path("global-leaderboard/", GlobalLeaderboardView.as_view(), name="global-leaderboard"),
    path('user-history/<id>', UserHistoryView.as_view()),
    path('user-history/<id>/past-performances/', PastPerformancesView.as_view()),
    
   #  The API for the GAMSTOP Integration Start
    path("check-exclude-status/", GamstopExcludeUsersCheck.as_view(), name="check-exclude-status"),
   #  The API for the GAMSTOP Integration Stop
    
    path("me/", CurrentUserDetails.as_view(), name="me"),
    path("me/interests/", InterestsView.as_view(), name="interests"),
    path("me/cancreatestable/", CanCreateStableView.as_view(), name="cancreatestable"),
    path("profile/", CurrentProfileUpdate.as_view(), name="profile"),
    path("profile/birthday/validate", ValidateBirthdayView.as_view(), name="validate_birthday"),
    path("signup/", SignupUserView.as_view(), name="signup"),
    path("equibaseimport/", EquibaseImportView.as_view(), name="equibaseimport"),
    path("paimport/", PAImportView.as_view(), name="paimport"),
    path("equibasechangeimport/", EquibaseImportChangeView.as_view(), name="equibasechangeimport"),
    path("equibaseresultsimport/", EquibaseImportResultsView.as_view(), name="equibaseresultsimport"),
    path("equibaseofficialresultsimport/", EquibaseImportOfficialResultsView.as_view(), name="equibaseofficialresultsimport"),
    path("trackmasterimport/", TrackmasterImportView.as_view(), name="trackmasterimport"),

    ############ NEW
    path("harnessofficialresultsimport/", HarnessImportOfficialResultsView.as_view(), name="harnessofficialresultsimport"),
    path("trackmasterharnessimport/", TrackmasterHarnessImportView.as_view(), name="trackmasterharnessimport"),
    path("harnessimport/", HarnessImportView.as_view(), name="harnessimport"),
    path("harnesstrackdetailimport/", HarnessTracksDetailImportView.as_view(), name="harnesstrackdetailimport"),
    path("patrackdetailimport/", PATracksDetailImportView.as_view(), name="patrackdetailimport"),
    path("paofficialresultsimportimport/", PAImportOfficialResultsView.as_view(), name="paofficialresultsimport"),
    

    ###############

    ## Track import
    path("trackimport/", TrackImportView.as_view(), name='trackimport'),
    path("follows-users/", UserFollowsUsersView.as_view(), name="follows_users"),
    path("follows-horses/", UserFollowsHorsesView.as_view(), name="follows_horses"),
    path("followers/", UsersFollowersView.as_view(), name="followers"),
    path("horses/<external_id>/", HorseDetailView.as_view(), name="horsedetails"),
    path("pusher/beams-auth", BeamsAuthView.as_view(), name="beams_auth"),
    path("version-requirements/", VersionRequirementView.as_view(), name="version_requirement"),
    path("celery-tracker/", include("django_celery_tracker.urls")),
    path("admin/statuscheck/", include("celerybeat_status.urls")),
    path('error-500/', error_500),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('wagering/states', WageringStateView.as_view({'get': 'list'}), name='wagering_states'),
    path('open-deposit-order/', openNuveiOrder, name='open-deposit-order'),
    path('deposit/<uuid:transactionId>/checkout/', CheckoutDepositView.as_view(), name="checkout-deposit" ),
    re_path(r'^wagering/', wagering_proxy, name='wagering-proxy')
]
