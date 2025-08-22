# listings/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Review, Listing
from decimal import Decimal

@receiver(post_save, sender=Review)
def award_credit_for_review(sender, instance, created, **kwargs):
    """
    Awards 0.10 credit points to a user's profile when they create a review.
    """
    if created:
        profile = instance.author.profile
        # Use Decimal for precision with currency
        credit_to_award = Decimal('0.10')
        profile.credit_balance += credit_to_award
        profile.save(update_fields=['credit_balance'])

@receiver(pre_save, sender=Listing)
def auto_update_listing_status(sender, instance, **kwargs):
    """
    Automatically updates the listing status based on stock changes.
    - If stock is increased from 0 to >0, status becomes 'available'.
    - If stock is set to 0, status becomes 'sold'.
    """
    if instance.pk:  # Check if this is an existing object
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            # Case 1: Restocking a sold-out item
            if old_instance.stock == 0 and instance.stock > 0:
                instance.status = 'available'
            # Case 2: Stock is depleted
            elif old_instance.stock > 0 and instance.stock == 0:
                instance.status = 'sold'
        except sender.DoesNotExist:
            # This can happen in rare cases, like a data migration.
            # We can safely ignore it.
            pass