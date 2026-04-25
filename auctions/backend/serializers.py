from decimal import Decimal

from rest_framework import serializers

from .models import AuctionListing, Bid, Category, Comment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class BidSerializer(serializers.ModelSerializer):
    bidder_username = serializers.CharField(source="bidder.username", read_only=True)

    class Meta:
        model = Bid
        fields = ["id", "bidder", "bidder_username", "bid_amount"]
        read_only_fields = ["id", "bidder", "bidder_username"]


class CommentSerializer(serializers.ModelSerializer):
    commenter_username = serializers.CharField(
        source="commenter.username",
        read_only=True,
    )

    class Meta:
        model = Comment
        fields = ["id", "commenter", "commenter_username", "content", "created_at"]
        read_only_fields = ["id", "commenter", "commenter_username", "created_at"]


class AuctionListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    current_price = serializers.SerializerMethodField()
    in_watchlist = serializers.SerializerMethodField()

    class Meta:
        model = AuctionListing
        fields = [
            "id",
            "title",
            "description",
            "starting_bid",
            "image_url",
            "category",
            "owner",
            "owner_username",
            "is_active",
            "created_at",
            "current_price",
            "in_watchlist",
        ]
        read_only_fields = [
            "id",
            "owner",
            "owner_username",
            "is_active",
            "created_at",
            "current_price",
            "in_watchlist",
        ]

    def get_current_price(self, obj):
        # Prefer annotated value from queryset to avoid per-row DB hits.
        annotated = getattr(obj, "highest_bid", None)
        if annotated is not None:
            return annotated

        # If bids are prefetched, compute in Python without extra query.
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        if "bids" in prefetched:
            bids = prefetched["bids"]
            if bids:
                return max(bid.bid_amount for bid in bids)
            return obj.starting_bid

        # Fallback: single query when optimization is not provided.
        highest = obj.bids.order_by("-bid_amount").first()
        return highest.bid_amount if highest else obj.starting_bid

    def get_image_url(self, obj):
        if not obj.image_url:
            return ""

        # Support legacy rows that stored full URLs before ImageField migration.
        name = getattr(obj.image_url, "name", "")
        if isinstance(name, str) and name.startswith(("http://", "https://")):
            return name

        request = self.context.get("request")
        image_path = obj.image_url.url
        if request:
            return request.build_absolute_uri(image_path)
        return image_path

    def get_in_watchlist(self, obj):
        # Prefer precomputed flag from view/queryset.
        precomputed = getattr(obj, "in_watchlist", None)
        if precomputed is not None:
            return precomputed

        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        # If watchlist relation is prefetched, avoid query.
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        if "watchlist_set" in prefetched:
            return any(w.user_id == request.user.id for w in prefetched["watchlist_set"])

        # Fallback query.
        return obj.watchlist_set.filter(user=request.user).exists()


class AuctionDetailSerializer(AuctionListSerializer):
    bids = BidSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    winner_username = serializers.CharField(source="winner.username", read_only=True)

    class Meta(AuctionListSerializer.Meta):
        fields = AuctionListSerializer.Meta.fields + [
            "closed_at",
            "winner",
            "winner_username",
            "bids",
            "comments",
        ]


class AuctionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuctionListing
        fields = ["title", "description", "starting_bid", "image_url", "category"]

    def validate_starting_bid(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("Starting bid must be greater than 0.")
        return value
