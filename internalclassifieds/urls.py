from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("create/", views.create, name="create"),
    # path("search", views.search, name="search"),
    path("search/", views.search, name="search"),
    path("categories/", views.all_categories, name="allCategories"),
    path("categories/<str:title_cat>/", views.categories, name="categories"),
    path("listings/<int:id_listing>/", views.listings, name="listings"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("watchlist_index/<int:id_listing>", views.watchlist_index, name="watchlistIndex"),
    path("watchlist_listing/<int:id_listing>", views.watchlist_listing, name="watchlistListing"),
    path("watchlist_watchlist/<int:id_listing>", views.watchlist_watchlist, name="watchlistWatchlist"),
    path("add_comment/<int:id_listing>", views.add_comment, name="addComment"),
    path("add_bet/<int:id_listing>", views.add_bet, name="addBet"),
    path("close_auction/<int:id_listing>", views.close_auction, name="closeAuction"),
    path("winlist/", views.win_list, name="winlist"),
    path("admin_decision/", views.admin_decision, name="admin_decision"),
    path("admin_decision_index/<int:id_listing>", views.admin_decision_index, name="admin_decision_index"),
    path("admin_decision_listing/<int:id_listing>", views.admin_decision_listing, name="admin_decision_listing"),
    path("admin_decision_watchlist/<int:id_listing>", views.admin_decision_watchlist, name="admin_decision_watchlist"),
    path("visible/", views.visible_decision, name="visible_decision"),
    path("visible_index/<int:id_listing>", views.visible_decision_index, name="visible_decision_index"),
    path("visible_listing/<int:id_listing>", views.visible_decision_listing, name="visible_decision_listing"),
    path("visible_watchlist/<int:id_listing>", views.visible_decision_watchlist, name="visible_decision_watchlist"),
    path("admin_delete/", views.admin_delete, name="admin_delete"),
    path("admin_delete_index/<int:id_listing>", views.admin_delete_index, name="admin_delete_index"),
    path("admin_delete_listing/<int:id_listing>", views.admin_delete_listing, name="admin_delete_listing")
]
