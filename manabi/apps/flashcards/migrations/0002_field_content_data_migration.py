# -*- coding: utf-8 -*-


from django.db import models, migrations


def forwards(apps, schema_editor):
    Fact = apps.get_model('flashcards', 'Fact')
    FactType = apps.get_model('flashcards', 'FactType')
    FieldType = apps.get_model('flashcards', 'FieldType')
    FieldContent = apps.get_model('flashcards', 'FieldContent')

    # print FactType.objects.all().values()

    try:
        e = FieldType.objects.get(name='expression', fact_type_id=1)
        r = FieldType.objects.get(name='reading', fact_type_id=1)
        m = FieldType.objects.get(name='meaning', fact_type_id=1)
    except FieldType.DoesNotExist:
        print 'Missing FieldType rows; skipping migration.'
        return

    print "Migrating {} facts".format(Fact.objects.all().count())
    i = 0
    for fact in Fact.objects.all().iterator():
        print i,
        i += 1
        fields = FieldContent.objects.filter(fact=fact)


        field_contents = fact.fieldcontent_set.all().order_by('field_type__ordinal')
        if fact.synchronized_with:
            continue
            #field_contents = fact.synchronized_with.fieldcontent_set.all().order_by('field_type__ordinal')
        print "Migrating from: {}".format(' / '.join([f.content for f in field_contents]))


        fact.meaning = field_contents[0].content
        fact.reading = field_contents[1].content
        fact.expression = field_contents[2].content
        fact.save()


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards),
    ]
