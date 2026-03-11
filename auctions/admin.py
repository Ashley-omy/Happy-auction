from django.contrib import admin
from .models import User, Category, auctionListing, Bid, Comment, Watchlist


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


class BidInline(admin.TabularInline):
    model = Bid
    extra = 1
    can_delete = True


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    can_delete = True


@admin.register(auctionListing)
class AuctionListingAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "owner",
                    "starting_bid", "is_active", "winner", "created_at")
    list_filter = ("is_active", "category", "created_at")
    search_fields = ("title", "description",
                     "owner__username", "winner__username")
    autocomplete_fields = ("owner", "winner", "category")
    readonly_fields = ("created_at",)
    inlines = [BidInline, CommentInline]
    ordering = ("-created_at",)


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "auction_listing", "bidder", "bid_amount")
    search_fields = ("auction_listing__title", "bidder__username")
    autocomplete_fields = ("auction_listing", "bidder")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "auction_listing", "commenter",
                    "short_content", "created_at")
    search_fields = ("auction_listing__title",
                     "commenter__username", "content")
    autocomplete_fields = ("auction_listing", "commenter")
    readonly_fields = ("created_at",)

    def short_content(self, obj):
        return obj.content[:50] + ("..." if len(obj.content) > 50 else "")
    short_content.short_description = "Content"


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "auction_listing")
    search_fields = ("user__username", "auction_listing__title")
    autocomplete_fields = ("user", "auction_listing")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_superuser", "is_active")
