from django.db import models
from django.conf import settings


class ResetToken(models.Model):
    # Ref the user that requested the password reset
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    # Unique token string
    token = models.CharField(max_length=255,
                             unique=True)

    # Token expiry date
    expiry_date = models.DateTimeField()

    # Whether this token has been used already
    used = models.BooleanField(default=False)

    def __str__(self):
        # Short string for easy debugging
        return (
            f"ResetToken(user={self.user.username},"
            f"token={self.token[:10]}...,"
            f"used={self.used})"
        )
