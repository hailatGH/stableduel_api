from config.pagination import CustomPagination
from django.core.paginator import Paginator, InvalidPage
from rest_framework.exceptions import NotFound
from django.utils.functional import cached_property

from stables.models import get_stable_score_count, get_stable_ids
from .models import Game

class LeaderboardPaginator(Paginator):
    def __init__(self, queryset, page_size, request):
        self.request = request
        self.game = Game.objects.get(id=self.request.query_params.get('game', None))
        super().__init__(queryset, page_size)

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        stables = self.object_list.filter(id__in=get_stable_ids(self.game, top, bottom))
        stables = sorted(stables, key=lambda stable: stable.score, reverse=True)
        return self._get_page(stables, number, self)

    @cached_property
    def count(self):
        """Return the total number of objects, across all pages."""
        print("GET THE COUNT")
        return get_stable_score_count(self.game)

class LeaderboardPagination(CustomPagination):
    django_paginator_class = LeaderboardPaginator
    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size, request)
        page_number = request.query_params.get(self.page_query_param, 1)
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return list(self.page)