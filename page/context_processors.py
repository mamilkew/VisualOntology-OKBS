from django.utils import timezone
from django.db.models import Avg, Count, Min, Max, Sum


def navbarmain(request):
    from page.models import Forcegraph
    raw_query = "SELECT DISTINCT ON (page_title) " \
                "*, max(published_date) FROM page_forcegraph " \
                "WHERE published_date is not null " \
                "GROUP BY page_title, id " \
                "ORDER BY page_title ASC, published_date DESC"

    from page.models import Timelinegraph
    timeline_bar = Timelinegraph.objects.filter(published_date__lte=timezone.now()).order_by('published_date')

    return {'navbarMain': Forcegraph.objects.raw(raw_query), 'navbar_timeline': timeline_bar}
