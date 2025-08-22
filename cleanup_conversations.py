# checkout/cleanup_conversations.py (The very final version)

import os
import django
import uuid
from collections import defaultdict

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from messaging.models import Conversation, Message

def run_the_final_merge():
    """
    Merges the last remaining duplicate conversations (one with an int PK,
    one with a UUID PK) for the same participants.
    """
    print("--- Starting the Final Merge Script ---")

    # This dictionary will group conversations by their participants
    conversations_by_participants = defaultdict(list)

    # We fetch all conversations and manually process them
    all_conversations = Conversation.objects.all()
    print(f"Analyzing {all_conversations.count()} remaining conversations...")

    for convo in all_conversations:
        # We create a key based on the sorted usernames of the participants
        participants = convo.participants.all()
        if len(participants) == 2:
            key = tuple(sorted([p.username for p in participants]))
            conversations_by_participants[key].append(convo)

    # Now, find the group that has duplicates and merge them
    for user_pair, convos in conversations_by_participants.items():
        if len(convos) > 1:
            print(f"\nFound {len(convos)} duplicates for users: {user_pair}")

            # Designate the one with the UUID as the primary conversation
            primary_convo = next((c for c in convos if isinstance(c.id, uuid.UUID)), None)
            if not primary_convo:
                 # If none have a UUID, just pick the one with the highest ID
                convos.sort(key=lambda c: str(c.id), reverse=True)
                primary_convo = convos[0]

            print(f"  - Keeping primary conversation with ID: {primary_convo.id}")

            # Merge the others into it
            for dup_convo in convos:
                if dup_convo.id != primary_convo.id:
                    print(f"  - Merging and deleting duplicate ID: {dup_convo.id}")
                    Message.objects.filter(conversation=dup_convo).update(conversation=primary_convo)
                    dup_convo.delete()

    print("\n--- Merge Complete ---")

    # Finally, assign the conversation keys to the now-unique conversations
    print("\n--- Assigning Conversation Keys ---")
    for convo in Conversation.objects.all():
        participants = convo.participants.all()
        if len(participants) == 2:
            usernames = sorted([p.username for p in participants])
            key = "_".join(usernames)
            convo.conversation_key = key
            convo.save()
            print(f"  - Set key for conversation {convo.id} to '{key}'")

    print("\n--- SCRIPT FINISHED SUCCESSFULLY ---")

if __name__ == "__main__":
    run_the_final_merge()