from django.urls import path
from . import api_views

urlpatterns = [
    path("auctions/", api_views.auction_list, name="api_auction_list"),
    path("auctions/<int:auction_id>/",
         api_views.auction_detail, name="api_auction_detail"),
    path("auctions/<int:auction_id>/bid/",
         api_views.place_bid, name="api_place_bid"),
    path("auctions/<int:auction_id>/comment/",
         api_views.add_comment, name="api_add_comment"),
    path("watchlist/toggle/", api_views.toggle_watchlist,
         name="api_toggle_watchlist"),
    path("categories/", api_views.category_list, name="api_categories"),
    path("auth/login/", api_views.login_api, name="api_login"),
    path("auth/logout/", api_views.logout_api, name="api_logout"),
    path("auth/register/", api_views.register_api, name="api_register"),
    path("auth/csrf/", api_views.csrf, name="api_csrf"),
    path("auth/me/", api_views.me_api, name="api_me"),
]
