from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

# Models: Your application should have at least three models in addition to the User model: one for auction listings, one for bids, and one for comments made on auction listings.
# It’s up to you to decide what fields each model should have, and what the types of those fields should be. You may have additional models if you would like.


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class AuctionListing(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(auto_now_add=True)
# check if the auction is active or not
    is_active = models.BooleanField(default=True)
    # many to one relationship with User model
    # Add a field to track the winner of the auction
    # This field can be null if the auction is still ongoing
    # if the user is deleted, the winner will be set to null
    winner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_auctions')

    def __str__(self):
        return self.title


class Bid(models.Model):
    auction_listing = models.ForeignKey(
        AuctionListing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.bid_amount} by {self.bidder.username}"

class Watchlist(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='watchlist')
    auction_listing = models.ForeignKey(
        AuctionListing, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'auction_listing'],
                name='unique_user_auction'
            )
        ]

    def __str__(self):
        return f"{self.auction_listing.title}"


class Comment(models.Model):
    auction_listing = models.ForeignKey(
        AuctionListing, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.commenter.username} on {self.auction_listing.title}: {self.content[:100]}"
