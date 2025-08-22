# in checkout/messaging/migrations/0002_merge_duplicate_conversations.py

from django.db import migrations
from collections import defaultdict

def merge_conversations(apps, schema_editor):
    Conversation = apps.get_model('messaging', 'Conversation')
    Message = apps.get_model('messaging', 'Message')
    User = apps.get_model('auth', 'User')

    print("\n--- Starting data migration to merge duplicate conversations ---")

    conversations_by_participants = defaultdict(list)

    for convo in Conversation.objects.all():
        participant_ids = tuple(sorted([p.id for p in convo.participants.all()]))
        if len(participant_ids) == 2:
            conversations_by_participants[participant_ids].append(convo)

    merged_count = 0

    for participant_ids, convos in conversations_by_participants.items():
        if len(convos) > 1:
            convos.sort(key=lambda c: (c.last_message_time is not None, c.last_message_time, str(c.id)), reverse=True)
            primary_convo = convos[0]
            duplicates_to_merge = convos[1:]

            for dup_convo in duplicates_to_merge:
                Message.objects.filter(conversation=dup_convo).update(conversation=primary_convo)
                dup_convo.delete()
                merged_count += 1

    print(f"--- Merge complete. Deleted {merged_count} duplicates. ---")

    print("\n--- Assigning conversation keys ---")
    for convo in Conversation.objects.all():
        participants = list(convo.participants.all())
        if len(participants) == 2:
            usernames = sorted([p.username for p in participants])
            key = "_".join(usernames)
            convo.conversation_key = key
            convo.save(update_fields=['conversation_key'])

    print("--- Data migration finished successfully. ---")

class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(merge_conversations, migrations.RunPython.noop),
    ]