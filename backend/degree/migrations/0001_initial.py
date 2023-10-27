# Generated by Django 3.2.20 on 2023-10-27 04:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DegreePlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program', models.CharField(choices=[('EU_BSE', 'Engineering BSE'), ('EU_BAS', 'Engineering BAS'), ('AU_BA', 'College BA'), ('WU_BS', 'Wharton BS')], help_text='\nThe program code for this degree plan, e.g., EU_BSE\n', max_length=10)),
                ('degree', models.CharField(help_text='\nThe degree code for this degree plan, e.g., BSE\n', max_length=4)),
                ('major', models.CharField(help_text='\nThe major code for this degree plan, e.g., BIOL\n', max_length=4)),
                ('concentration', models.CharField(help_text='\nThe concentration code for this degree plan, e.g., BMAT\n', max_length=4, null=True)),
                ('year', models.IntegerField(help_text='\nThe effective year of this degree plan, e.g., 2023\n')),
            ],
        ),
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, help_text='\nThe title for this rule.\n', max_length=200)),
                ('num_courses', models.PositiveSmallIntegerField(help_text='\nThe minimum number of courses or subrules required for this rule. Only non-null\nif this is a Rule leaf.\n', null=True)),
                ('credits', models.DecimalField(decimal_places=2, help_text='\nThe minimum number of CUs required for this rule. Only non-null\nif this is a Rule leaf. Can be \n', max_digits=4, null=True)),
                ('q', models.TextField(help_text='\nString representing a Q() object that returns the set of courses\nsatisfying this rule. Only non-null/non-empty if this is a Rule leaf.\nThis Q object is expected to be normalized before it is serialized\nto a string.\n', max_length=1000)),
                ('degree_plan', models.ForeignKey(help_text='\nThe degree plan that has this rule.\n', on_delete=django.db.models.deletion.CASCADE, to='degree.degreeplan')),
                ('parent', models.ForeignKey(help_text="\nThis rule's parent Rule if it has one.\n", null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='degree.rule')),
            ],
        ),
        migrations.AddConstraint(
            model_name='rule',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('credits__isnull', True), ('credits__gt', 0), _connector='OR'), models.Q(('num_courses__isnull', True), ('num_courses__gt', 0), _connector='OR')), name='num_course_credits_gt_0'),
        ),
    ]
