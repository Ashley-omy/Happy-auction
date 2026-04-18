from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Max, Prefetch
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import AuctionListing, Bid, Category, Comment, User, Watchlist
from .serializers import (
    AuctionCreateSerializer,
    AuctionDetailSerializer,
    AuctionListSerializer,
    CategorySerializer,
    CommentSerializer,
)


def get_auction_queryset(request):
    queryset = (
        AuctionListing.objects.select_related("category", "owner", "winner")
        .annotate(highest_bid=Max("bids__bid_amount"))
        .order_by("-created_at")
    )

    if request.user.is_authenticated:
        queryset = queryset.prefetch_related(
            Prefetch(
                "watchlist_set",
                queryset=Watchlist.objects.filter(user=request.user),
            )
        )

    return queryset


def get_auction_detail_queryset(request):
    return get_auction_queryset(request).prefetch_related(
        Prefetch("bids", queryset=Bid.objects.select_related("bidder").order_by("-bid_amount")),
        Prefetch("comments", queryset=Comment.objects.select_related("commenter").order_by("-created_at")),
    )


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf(request):
    return Response({"detail": "CSRF cookie set."})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def auction_list(request):
    if request.method == "GET":
        status_filter = request.query_params.get("status", "active")
        owner_filter = request.query_params.get("owner")
        watchlist_filter = request.query_params.get("watchlist")
        category_filter = request.query_params.get("category")
        auctions = get_auction_queryset(request)

        if status_filter == "active":
            auctions = auctions.filter(is_active=True)
        elif status_filter == "closed":
            auctions = auctions.filter(is_active=False)

        if owner_filter == "me":
            if not request.user.is_authenticated:
                return Response({"error": "Authentication required."}, status=401)
            auctions = auctions.filter(owner=request.user)

        if watchlist_filter == "me":
            if not request.user.is_authenticated:
                return Response({"error": "Authentication required."}, status=401)
            auctions = auctions.filter(watchlist__user=request.user)

        if category_filter:
            auctions = auctions.filter(category__name=category_filter)

        auctions = auctions.distinct()

        serializer = AuctionListSerializer(
            auctions,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    if not request.user.is_authenticated:
        return Response({"error": "Authentication required."}, status=401)

    serializer = AuctionCreateSerializer(data=request.data)
    if serializer.is_valid():
        auction = serializer.save(owner=request.user)
        output = AuctionDetailSerializer(auction, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def auction_detail(request, auction_id):
    auction = get_object_or_404(get_auction_detail_queryset(request), id=auction_id)
    serializer = AuctionDetailSerializer(auction, context={"request": request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def place_bid(request, auction_id):
    auction = get_object_or_404(AuctionListing, id=auction_id)

    if not auction.is_active:
        return Response({"error": "Auction is closed."}, status=400)

    raw_amount = request.data.get("bid_amount")
    if raw_amount in [None, ""]:
        return Response({"error": "bid_amount is required."}, status=400)

    try:
        bid_amount = Decimal(str(raw_amount))
    except (InvalidOperation, ValueError):
        return Response({"error": "Invalid bid_amount."}, status=400)

    current_highest = auction.bids.aggregate(Max("bid_amount"))["bid_amount__max"]
    if current_highest is None:
        current_highest = auction.starting_bid

    if bid_amount <= current_highest:
        return Response(
            {"error": f"Bid must be higher than current price ({current_highest})."},
            status=400,
        )

    bid = Bid.objects.create(
        auction_listing=auction,
        bidder=request.user,
        bid_amount=bid_amount,
    )
    return Response(
        {
            "message": "Bid placed.",
            "bid": {
                "id": bid.id,
                "bid_amount": str(bid.bid_amount),
                "bidder_username": bid.bidder.username,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def close_auction_api(request, auction_id):
    auction = get_object_or_404(AuctionListing, id=auction_id)

    if request.user != auction.owner:
        return Response({"error": "Only the owner can close this auction."}, status=403)

    if not auction.is_active:
        return Response({"error": "Auction is already closed."}, status=400)

    highest_bid = auction.bids.order_by("-bid_amount").first()
    if highest_bid:
        auction.winner = highest_bid.bidder

    auction.is_active = False
    auction.save()

    serializer = AuctionDetailSerializer(
        get_object_or_404(get_auction_detail_queryset(request), id=auction.id),
        context={"request": request},
    )
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_comment(request, auction_id):
    auction = get_object_or_404(AuctionListing, id=auction_id)
    content = (request.data.get("content") or "").strip()

    if not content:
        return Response({"error": "content is required."}, status=400)

    comment = Comment.objects.create(
        auction_listing=auction,
        commenter=request.user,
        content=content,
    )
    serializer = CommentSerializer(comment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_watchlist(request):
    auction_id = request.data.get("auction_id")
    if not auction_id:
        return Response({"error": "auction_id is required."}, status=400)

    auction = get_object_or_404(AuctionListing, id=auction_id)
    watch_item = Watchlist.objects.filter(
        user=request.user,
        auction_listing=auction,
    ).first()

    if watch_item:
        watch_item.delete()
        return Response({"in_watchlist": False})

    Watchlist.objects.create(user=request.user, auction_listing=auction)
    return Response({"in_watchlist": True}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def category_list(request):
    categories = Category.objects.all().order_by("name")
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)
    if not user:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    login(request, user)
    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_api(request):
    logout(request)
    return Response({"message": "Logged out."})


@api_view(["POST"])
@permission_classes([AllowAny])
def register_api(request):
    username = request.data.get("username")
    email = request.data.get("email", "")
    password = request.data.get("password")
    confirmation = request.data.get("confirmation")

    if not username or not password:
        return Response(
            {"error": "username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if password != confirmation:
        return Response(
            {"error": "Passwords must match."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.create_user(username, email, password)
        user.save()
    except IntegrityError:
        return Response(
            {"error": "Username already taken."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    login(request, user)
    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def me_api(request):
    if not request.user.is_authenticated:
        return Response({"authenticated": False, "user": None})

    return Response(
        {
            "authenticated": True,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
            },
        }
    )
