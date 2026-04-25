from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auctions", "0007_auctionlisting_closed_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auctionlisting",
            name="image_url",
            field=models.ImageField(blank=True, null=True, upload_to="auction_images/"),
        ),
    ]
