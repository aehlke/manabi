# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('template', models.SmallIntegerField(choices=[(0, b'Production'), (1, b'Recognition'), (2, b'Kanji Reading'), (3, b'Kanji Writing')])),
                ('active', models.BooleanField(default=True, db_index=True)),
                ('ease_factor', models.FloatField(null=True, blank=True)),
                ('interval', models.FloatField(db_index=True, null=True, blank=True)),
                ('due_at', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('last_ease_factor', models.FloatField(null=True, blank=True)),
                ('last_interval', models.FloatField(null=True, blank=True)),
                ('last_due_at', models.DateTimeField(null=True, blank=True)),
                ('last_reviewed_at', models.DateTimeField(null=True, blank=True)),
                ('last_review_grade', models.PositiveIntegerField(null=True, blank=True)),
                ('last_failed_at', models.DateTimeField(null=True, blank=True)),
                ('review_count', models.PositiveIntegerField(default=0, editable=False)),
                ('new_card_ordinal', models.PositiveIntegerField(null=True, blank=True)),
                ('suspended', models.BooleanField(default=False, db_index=True)),
                ('leech', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CardHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('response', models.PositiveIntegerField(editable=False)),
                ('reviewed_at', models.DateTimeField()),
                ('ease_factor', models.FloatField(null=True, blank=True)),
                ('interval', models.FloatField(db_index=True, null=True, blank=True)),
                ('was_new', models.BooleanField(default=False, db_index=True)),
                ('question_duration', models.FloatField(null=True, blank=True)),
                ('duration', models.FloatField(null=True, blank=True)),
                ('card', models.ForeignKey(to='flashcards.Card')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CardTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(max_length=200, blank=True)),
                ('front_template_name', models.CharField(max_length=50)),
                ('back_template_name', models.CharField(max_length=50)),
                ('front_prompt', models.CharField(max_length=200, blank=True)),
                ('back_prompt', models.CharField(max_length=200, blank=True)),
                ('js_template', models.TextField(max_length=600, blank=True)),
                ('card_synchronization_group', models.SmallIntegerField(null=True, blank=True)),
                ('generate_by_default', models.BooleanField(default=True)),
                ('ordinal', models.IntegerField(null=True, blank=True)),
                ('hide_front', models.BooleanField(default=False)),
                ('allow_blank_back', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['ordinal'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Deck',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(max_length=2000, blank=True)),
                ('picture', models.FileField(null=True, upload_to=b'/deck_media/', blank=True)),
                ('priority', models.IntegerField(default=0, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('shared', models.BooleanField(default=False)),
                ('shared_at', models.DateTimeField(null=True, blank=True)),
                ('suspended', models.BooleanField(default=False, db_index=True)),
                ('active', models.BooleanField(default=True, db_index=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('synchronized_with', models.ForeignKey(related_name='subscriber_decks', blank=True, to='flashcards.Deck', null=True)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Fact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('new_fact_ordinal', models.PositiveIntegerField(null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('expression', models.CharField(max_length=500)),
                ('reading', models.CharField(max_length=1500, blank=True)),
                ('meaning', models.CharField(max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(null=True, blank=True)),
                ('deck', models.ForeignKey(blank=True, to='flashcards.Deck', null=True)),
                ('synchronized_with', models.ForeignKey(related_name='subscriber_facts', blank=True, to='flashcards.Fact', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FactType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('active', models.BooleanField(default=True)),
                ('many_children_per_fact', models.NullBooleanField()),
                ('space_factor', models.FloatField(default=0.1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('parent_fact_type', models.ForeignKey(related_name='child_fact_types', blank=True, to='flashcards.FactType', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FieldContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.CharField(max_length=1000, blank=True)),
                ('media_uri', models.URLField(blank=True)),
                ('media_file', models.FileField(null=True, upload_to=b'/card_media/', blank=True)),
                ('cached_transliteration_without_markup', models.CharField(max_length=1000, blank=True)),
                ('fact', models.ForeignKey(to='flashcards.Fact')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FieldType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('display_name', models.CharField(max_length=50)),
                ('unique', models.BooleanField(default=True)),
                ('blank', models.BooleanField(default=False)),
                ('editable', models.BooleanField(default=True)),
                ('numeric', models.BooleanField(default=False)),
                ('multi_line', models.BooleanField(default=True)),
                ('choices', models.CharField(help_text=b'Use a pickled choices tuple. The "none" value is used to indicate no selection, so don\'t use it in the choices tuple.', max_length=1000, blank=True)),
                ('help_text', models.CharField(max_length=500, blank=True)),
                ('language', models.CharField(blank=True, max_length=3, null=True, choices=[(b'eng', b'English'), (b'jpn', b'Japanese')])),
                ('character_restriction', models.CharField(blank=True, max_length=3, null=True, choices=[(b'num', b'Numeric'), (b'knj', b'Kanji'), (b'kna', b'Kana'), (b'hir', b'Hiragana'), (b'kat', b'Katakana')])),
                ('accepts_media', models.BooleanField(default=False)),
                ('media_restriction', models.CharField(blank=True, max_length=3, null=True, choices=[(b'img', b'Image'), (b'vid', b'Video'), (b'snd', b'Sound')])),
                ('hidden_in_form', models.BooleanField(default=False)),
                ('disabled_in_form', models.BooleanField(default=False, help_text=b'Disable this field when adding/editing a fact. If hidden_in_form is also True, then it will supress the Add `name` link in the form.')),
                ('hidden_in_grid', models.BooleanField(default=False)),
                ('grid_column_width', models.CharField(max_length=10, blank=True)),
                ('ordinal', models.IntegerField(null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('fact_type', models.ForeignKey(to='flashcards.FactType')),
                ('transliteration_field_type', models.OneToOneField(related_name='reverse_transliteration_field_type', null=True, blank=True, to='flashcards.FieldType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Textbook',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(blank=True)),
                ('isbn', models.CharField(max_length=13)),
                ('custom_title', models.CharField(help_text=b'Set this to override the Amazon product name.', max_length=200, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UndoCardReview',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('pickled_card', models.CharField(max_length=255)),
                ('card', models.ForeignKey(to='flashcards.Card')),
                ('card_history', models.ForeignKey(to='flashcards.CardHistory')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='fieldtype',
            unique_together=set([('ordinal', 'fact_type'), ('name', 'fact_type'), ('display_name', 'fact_type')]),
        ),
        migrations.AddField(
            model_name='fieldcontent',
            name='field_type',
            field=models.ForeignKey(to='flashcards.FieldType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='fact',
            unique_together=set([('deck', 'synchronized_with')]),
        ),
        migrations.AddField(
            model_name='deck',
            name='textbook_source',
            field=models.ForeignKey(blank=True, to='flashcards.Textbook', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cardtemplate',
            name='fact_type',
            field=models.ForeignKey(to='flashcards.FactType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cardtemplate',
            name='requisite_field_types',
            field=models.ManyToManyField(to='flashcards.FieldType', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='cardtemplate',
            unique_together=set([('ordinal', 'fact_type'), ('name', 'fact_type')]),
        ),
        migrations.AddField(
            model_name='card',
            name='deck',
            field=models.ForeignKey(to='flashcards.Deck'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='card',
            name='fact',
            field=models.ForeignKey(to='flashcards.Fact'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='card',
            name='legacy_template',
            field=models.ForeignKey(to='flashcards.CardTemplate', blank=True, null=True, db_index=False),
            preserve_default=True,
        ),
    ]
