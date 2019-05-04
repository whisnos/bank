from django.conf.urls import url, include
from .views import nsm_query, get_ali_userid, nsmbackcall

urlpatterns = [
    url(r'^nsm_query', nsm_query),
    url(r'^get_ali_userid', get_ali_userid),
    url(r'^nsmbackcall', nsmbackcall),
]
