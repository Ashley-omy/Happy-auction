from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Max
from .models import Bid, Category, User, Watchlist, auctionListing, Comment
from django.contrib.auth.decorators import login_required


def index(request):
    auctions = (
        auctionListing.objects
        .filter(is_active=True)
        .annotate(highest_bid=Max('bids__bid_amount'))
        .order_by('-created_at')
    )
    if request.user.is_authenticated:
        watchlisted_ids = set(
            Watchlist.objects.filter(user=request.user)
            .values_list('auction_listing_id', flat=True)
        )
        for auction in auctions:
            auction.in_watchlist = auction.id in watchlisted_ids
    else:
        for auction in auctions:
            auction.in_watchlist = False

    return render(request, "auctions/index.html", {
        "auctions": auctions,
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def new_auction(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        starting_bid = request.POST["starting_bid"]
        # Optional fields. if not provided, it will be an empty string
        image_url = request.POST.get(
            "image_url", "")
        category_id = request.POST.get("category")
        category = None
        if category_id:
            category = Category.objects.get(id=category_id)
        # Create a new auction listing
        auction_listing = auctionListing(
            title=title,
            description=description,
            starting_bid=starting_bid,
            image_url=image_url,
            category=category,
            owner=request.user
        )
        auction_listing.save()

        return HttpResponseRedirect(reverse("index"))
    else:
        categories = Category.objects.all()
        return render(request, "auctions/new_auction.html", {
            "categories": categories
        })


def auction_detail(request, auction_id):
    try:
        auction = auctionListing.objects.get(id=auction_id)
        bid = Bid.objects.filter(auction_listing=auction).order_by(
            '-bid_amount').first()
    except auctionListing.DoesNotExist:
        return HttpResponse("Auction not found.", status=404)

    auction = auctionListing.objects.get(id=auction_id)
    if request.user.is_authenticated:
        watchlisted_ids = set(
            Watchlist.objects.filter(user=request.user)
            .values_list('auction_listing_id', flat=True)
        )
        auction.in_watchlist = auction.id in watchlisted_ids
    else:
        auction.in_watchlist = False

    auction.has_comments = auction.comments.exists()

    return render(request, "auctions/auction_detail.html", {
        "auction": auction,
        "bid": bid
    })


def place_bid(request, auction_id):
    if request.method == "POST":
        try:
            auction = auctionListing.objects.get(id=auction_id)
        except auctionListing.DoesNotExist:
            return HttpResponse("Auction not found.", status=404)

        current_highest = auction.bids.aggregate(
            Max('bid_amount'))['bid_amount__max']
        if current_highest is None:
            current_highest = float(auction.starting_bid)

        bid_amount = float(request.POST["bid_amount"])

        if bid_amount <= current_highest:
            return render(request, "auctions/auction_detail.html", {
                "auction": auction,
                "message": f"Bid must be higher than the current highest bid (${current_highest})."
            })

        bid = Bid(
            auction_listing=auction,
            bidder=request.user,
            bid_amount=bid_amount
        )
        bid.save()

        return HttpResponseRedirect(reverse("auction_detail", args=(auction_id,)))
    else:
        return HttpResponse("Invalid request method.", status=405)


@login_required
def watchlist(request):
    if request.method == "POST":
        auction_id = request.POST["auction_id"]
        auction = get_object_or_404(auctionListing, id=auction_id)

        watchlist_item = Watchlist.objects.filter(
            user=request.user,
            auction_listing=auction
        ).first()

        if watchlist_item:
            watchlist_item.delete()
        else:
            Watchlist.objects.create(
                user=request.user,
                auction_listing=auction
            )

        return redirect(reverse("watchlist"))
    else:
        # extract only the auction listings in the user's watchlist
        watchlist_qs = Watchlist.objects.filter(
            user=request.user).select_related('auction_listing')

        auctions = []
        for item in watchlist_qs:
            auction = item.auction_listing
            auction.in_watchlist = True
            auctions.append(auction)

        return render(request, "auctions/watchlist.html", {
            "auctions": auctions
        })


@login_required
def close_auction(request, auction_id):
    auction = get_object_or_404(auctionListing, id=auction_id)

    if request.user != auction.owner:
        return HttpResponse("You are not the owner of this auction.", status=403)

    if not auction.is_active:
        return HttpResponse("Auction is already closed.", status=400)

    highest_bid = auction.bids.order_by('-bid_amount').first()
    if highest_bid:
        auction.winner = highest_bid.bidder

    auction.is_active = False
    auction.save()

    return redirect(reverse("auction_detail", args=[auction_id]))


def closed_auctions(request):
    auctions = (
        auctionListing.objects
        .filter(is_active=False)
        .annotate(highest_bid=Max('bids__bid_amount'))
    )
    return render(request, "auctions/closed_auctions.html", {
        "auctions": auctions
    })


@login_required
@login_required
def my_auctions(request):
    auctions = (
        auctionListing.objects
        .filter(owner=request.user)
        .annotate(highest_bid=Max('bids__bid_amount'))
    )
    return render(request, "auctions/my_auctions.html", {
        "auctions": auctions
    })


@login_required
def comment(request, auction_id):
    if request.method == "POST":
        auction = get_object_or_404(auctionListing, id=auction_id)
        content = request.POST["comment_text"]

        comment = Comment(
            auction_listing=auction,
            commenter=request.user,
            content=content
        )
        comment.save()

        return HttpResponseRedirect(reverse("auction_detail", args=(auction_id,)))
    else:
        return HttpResponse("Invalid request method.", status=405)


def categories(request):
    categories = Category.objects.all()
    return render(request, "auctions/categories.html", {
        "categories": categories
    })


def category_listings(request, category_name):
    category = Category.objects.filter(name=category_name).first()
    listings = auctionListing.objects.filter(
        category=category, is_active=True)
    return render(request, "auctions/category_listings.html", {
        "category": category,
        "listings": listings
    })
