from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("new-auction", views.new_auction, name="new_auction"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("my-auctions", views.my_auctions, name="my_auctions"),
    path("closed-auctions", views.closed_auctions, name="closed_auctions"),
    path("categories/", views.categories, name="categories"),
    path("categories/<str:category_name>/",
         views.category_listings, name="category_listings"),
    path("comment/<int:auction_id>", views.comment, name="add_comment"),
    path("auction/<int:auction_id>", views.auction_detail, name="auction_detail"),
    path("bid/<int:auction_id>", views.place_bid, name="place_bid"),
    path("auction/<int:auction_id>/close",
         views.close_auction, name="close_auction")
]
