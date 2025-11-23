from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import User, UserChangeHistory


@receiver(pre_save, sender=User)
def track_user_changes(sender, instance, **kwargs):
    if instance.pk:  # Ensures this is an update, not a new instance
        try:
            old_user = User.objects.get(pk=instance.pk)
        except User.DoesNotExist:
            return  # If the user doesn't exist, skip

        # Compare old and new values
        for field in instance._meta.fields:
            field_name = field.name
            old_value = getattr(old_user, field_name, None)
            new_value = getattr(instance, field_name, None)

            if old_value != new_value:
                # Save change history
                UserChangeHistory.objects.create(
                    user=instance,
                    changed_by=getattr(
                        instance, "_changed_by", None
                    ),  # Optional: track who made the change
                    field_changed=field_name,
                    old_value=old_value,
                    new_value=new_value,
                )
