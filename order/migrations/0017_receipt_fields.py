from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("order", "0016_order_applied_offers_order_discount_amount")]
    operations = [
        migrations.AddField(model_name="order", name="receipt_token", field=models.CharField(max_length=64, unique=True, null=True, blank=True, db_index=True)),
        migrations.AddField(model_name="order", name="payment_method", field=models.CharField(max_length=20, default="visa")),
        migrations.AddField(model_name="order", name="amount_paid", field=models.DecimalField(max_digits=12, decimal_places=2, default=0)),
    ]
