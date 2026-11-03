from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("degree", "0009_rule_transfer_credit_allowed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="degree",
            name="program",
            field=models.CharField(
                choices=[
                    ("EU_BSE", "Engineering BSE"),
                    ("EU_BAS", "Engineering BAS"),
                    ("AU_BA", "College BA"),
                    ("WU_BS", "Wharton BS"),
                    ("NU_BSN", "Nursing BSN"),
                    ("EM_MSE", "Engineering MSE"),
                    ("EU_BSE_MANT", "M&T - Engineering BSE"),
                    ("EU_BAS_MANT", "M&T - Engineering BAS"),
                    ("WU_BS_MANT", "M&T - Wharton BS"),
                    ("WU_BS_MAT_U", "M&T - Wharton BS (Undeclared)"),
                ],
                help_text="\nThe program code for this degree, e.g., EU_BSE\n",
                max_length=16,
            ),
        ),
    ]
