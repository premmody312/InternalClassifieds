from django.contrib import admin
from .models import User, Listings, Category, WatchList, Bet, Comments,AdminDecision


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id", "password", "last_login", "is_superuser", "username", "first_name", "last_name", "email", "is_staff",
        "is_active", "date_joined")


class ListingsAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "start_bid", "url_img", "get_category", "create_date", "user_id", "open",
        "max_bet", "win")

    def get_category(self, obj):
        return "\n".join([a.cat for a in obj.category.all()])

    def user_id(self, obj):
        return obj.author_id

    user_id.short_description = "author id"


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "cat")


class WatchListAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "id_list")

    def id_list(self, obj):
        return obj.id_listing_id

    id_list.short_description = "ID List"

    def user_id(self, obj):
        return obj.id_user_id

    user_id.short_description = "User id"

class AdminDecisionAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "id_list")

    def id_list(self, obj):
        return obj.id_listing_id

    id_list.short_description = "ID List"

    def user_id(self, obj):
        return obj.id_user_id

    user_id.short_description = "User id"


class BetAdmin(admin.ModelAdmin):
    list_display = ("id", "id_list", "user_id", "newBet")

    def id_list(self, obj):
        return obj.id_listing_id

    id_list.short_description = "ID List"

    def user_id(self, obj):
        return obj.id_user_id

    user_id.short_description = "User id"


class CommentsAdmin(admin.ModelAdmin):
    list_display = ("id", "id_list", "user_id", "text", "create_date")

    def id_list(self, obj):
        return obj.id_listing_id

    id_list.short_description = "ID List"

    def user_id(self, obj):
        return obj.id_user_id

    user_id.short_description = "User id"


# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Listings, ListingsAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(WatchList, WatchListAdmin)
admin.site.register(Bet, BetAdmin)
admin.site.register(Comments, CommentsAdmin)
admin.site.register(AdminDecision, AdminDecisionAdmin)