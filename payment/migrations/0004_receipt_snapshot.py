from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [("payment", "0003_alter_paymenttransaction_opay_reference")]
    operations = [
        migrations.AddField(model_name="paymenttransaction", name="checkout_snapshot", field=models.JSONField(default=dict)),
        migrations.AddField(model_name="paymenttransaction", name="receipt_token", field=models.CharField(max_length=64, unique=True, null=True, blank=True)),
    ]
