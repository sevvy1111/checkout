# in messaging/migrations/0002_merge_duplicate_conversations.py

from django.db import migrations
from collections import defaultdict

def merge_conversations(apps, schema_editor):
    """
    Finds and merges duplicate conversations for the same participants,
    preserving all messages.
    """
    Conversation = apps.get_model('messaging', 'Conversation')
    Message = apps.get_model('messaging', 'Message')
    User = apps.get_model('auth', 'User') # Or your user model app

    print("\n--- Starting data migration to merge duplicate conversations ---")

    conversations_by_participants = defaultdict(list)

    # We must iterate through users to avoid loading all conversations at once,
    # which can cause memory issues on a live server.
    for user in User.objects.all():
        for convo in user.conversations.all():
            participant_ids = tuple(sorted([p.id for p in convo.participants.all()]))
            if len(participant_ids) == 2 and convo not in conversations_by_participants[participant_ids]:
                conversations_by_participants[participant_ids].append(convo)

    print(f"Found {len(conversations_by_participants)} unique participant groups.")
    merged_count = 0

    for participant_ids, convos in conversations_by_participants.items():
        if len(convos) > 1:
            print(f"  - Found {len(convos)} duplicates for users with IDs {participant_ids}.")

            # Sort to find the best one to keep (e.g., the most recent)
            convos.sort(key=lambda c: (c.last_message_time is not None, c.last_message_time, c.id), reverse=True)
            primary_convo = convos[0]
            duplicates_to_merge = convos[1:]

            print(f"    - Keeping primary conversation ID: {primary_convo.id}")

            for dup_convo in duplicates_to_merge:
                print(f"    - Merging messages from duplicate ID: {dup_convo.id}")
                Message.objects.filter(conversation=dup_convo).update(conversation=primary_convo)
                dup_convo.delete()
                merged_count += 1

    print(f"--- Merge complete. Merged and deleted {merged_count} duplicates. ---")

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
        ('messaging', '0001_initial'), # Make sure this matches your previous migration file
        ('accounts', '0001_initial'),   # Dependency on the user model
    ]

    operations = [
        migrations.RunPython(merge_conversations, migrations.RunPython.noop),
    ]