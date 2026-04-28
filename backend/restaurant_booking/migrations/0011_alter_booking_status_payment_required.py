from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("restaurant_booking", "0010_bookingpayment_and_profile_booking_fees"),
    ]

    operations = [
        migrations.AlterField(
            model_name="booking",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Chờ thanh toán"),
                    ("CONFIRMED", "Đã xác nhận"),
                    ("CANCELLED", "Đã hủy"),
                    ("COMPLETED", "Hoàn thành"),
                    ("NO_SHOW", "Không đến"),
                ],
                default="PENDING",
                max_length=20,
                verbose_name="Trạng thái",
            ),
        ),
    ]
