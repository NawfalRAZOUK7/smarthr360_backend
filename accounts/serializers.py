from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import exceptions, serializers

# + the new import we just added:
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import (
    EmailVerificationToken,
    LoginActivity,
    LoginAttempt,
    PasswordResetToken,
    User,
)


class UserSerializer(serializers.ModelSerializer):
    """Public user data returned to the frontend."""
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role"]


class RegisterSerializer(serializers.ModelSerializer):
    """Used for /register endpoint."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "role"]

    def create(self, validated_data):
        role = validated_data.pop("role", User.Role.EMPLOYEE)
        password = validated_data.pop("password")

        user = User.objects.create_user(
            role=role,
            **validated_data,
        )
        user.set_password(password)
        user.save()

        # Auto-send email verification (optional)
        token_obj = EmailVerificationToken.create_for_user(user)
        frontend_base = "http://localhost:3000"
        verify_link = f"{frontend_base}/verify-email?token={token_obj.token}"

        send_mail(
            subject="Vérifiez votre adresse email SmartHR360",
            message=(
                "Bonjour,\n\n"
                "Merci de vous être inscrit sur SmartHR360.\n"
                "Veuillez cliquer sur le lien suivant pour vérifier votre adresse email :\n\n"
                f"{verify_link}\n\n"
                "Si vous n'êtes pas à l'origine de cette inscription, ignorez cet email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

        return user


class LoginSerializer(serializers.Serializer):
    """Used for /login endpoint."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def _get_request_meta(self):
        request = self.context.get("request")
        if not request:
            return None, None
        ip = request.META.get("REMOTE_ADDR")
        ua = request.META.get("HTTP_USER_AGENT", "")
        return ip, ua

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        ip, ua = self._get_request_meta()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # optional: we don't log here since we don't have a user FK
            raise serializers.ValidationError("Identifiants invalides.") from None

        # Ensure a LoginAttempt exists
        attempt, _ = LoginAttempt.objects.get_or_create(user=user)

        # 1) Check lockout (robust against locked_until = None)
        if attempt.check_lock_status():
            # 🔧 Robustness fix: handle possible None locked_until
            if attempt.locked_until:
                seconds_left = (attempt.locked_until - timezone.now()).total_seconds()
                if seconds_left < 0:
                    seconds_left = 0
                minutes_left = max(1, int(seconds_left / 60)) if seconds_left > 0 else 0
            else:
                seconds_left = 0
                minutes_left = 0

            # log failed login (locked)
            LoginActivity.objects.create(
                user=user,
                action=LoginActivity.Action.LOGIN,
                success=False,
                ip_address=ip,
                user_agent=ua,
                extra_data={
                    "reason": "locked",
                    "seconds_left": int(seconds_left),
                    "minutes_left": minutes_left,
                },
            )

            raise serializers.ValidationError(
                f"Compte verrouillé. Réessayez dans {minutes_left} minutes."
            )

        # 2) Check password
        if not user.check_password(password):
            # before increment, were we unlocked?
            was_locked_before = attempt.is_locked

            attempt.mark_failed()  # increments & possibly locks

            remaining = attempt.MAX_ATTEMPTS - attempt.failed_attempts

            # log failed login (bad password)
            LoginActivity.objects.create(
                user=user,
                action=LoginActivity.Action.LOGIN,
                success=False,
                ip_address=ip,
                user_agent=ua,
                extra_data={
                    "reason": "invalid_password",
                    "failed_attempts": attempt.failed_attempts,
                    "remaining_attempts": remaining,
                },
            )

            # 🔔 Send email exactly when account becomes locked now
            if not was_locked_before and attempt.is_locked:
                try:
                    send_mail(
                        subject="Votre compte SmartHR360 a été temporairement verrouillé",
                        message=(
                            "Bonjour,\n\n"
                            "Votre compte a été temporairement verrouillé en raison de plusieurs "
                            "tentatives de connexion échouées.\n\n"
                            "Si vous n'êtes pas à l'origine de ces tentatives, nous vous "
                            "conseillons de contacter l'administrateur ou de réinitialiser votre "
                            "mot de passe.\n\n"
                            "Cordialement,\nL'équipe SmartHR360"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                except Exception:
                    # en dev on ignore les erreurs email
                    pass

            raise serializers.ValidationError(
                f"Mot de passe incorrect. Tentatives restantes: {remaining}"
            )

        # 3) Success → reset attempts and log success
        attempt.reset_attempts()

        LoginActivity.objects.create(
            user=user,
            action=LoginActivity.Action.LOGIN,
            success=True,
            ip_address=ip,
            user_agent=ua,
            extra_data=None,
        )

        attrs["user"] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer used for /change-password/
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect.")
        return value

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                "Le nouveau mot de passe doit être différent de l'ancien."
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class LogoutSerializer(serializers.Serializer):
    """
    Serializer used for /logout/ to blacklist the refresh token.
    """
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            raise exceptions.ValidationError("Token invalide ou déjà blacklisté.") from None


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        self.context["user"] = User.objects.filter(email=value).first()
        return value

    def save(self, **kwargs):
        user = self.context.get("user")
        if not user:
            # Return silently for non-existent accounts to avoid leaking existence
            return None

        # Reuse existing active token to avoid duplicates
        token_obj = (
            PasswordResetToken.objects.filter(user=user, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if token_obj and token_obj.is_expired():
            token_obj.delete()
            token_obj = None

        if token_obj is None:
            token_obj = PasswordResetToken.create_for_user(user)

        # In real prod, you'd use your front-end URL
        frontend_base = "http://localhost:3000"
        reset_link = f"{frontend_base}/reset-password?token={token_obj.token}"

        send_mail(
            subject="Réinitialisation de votre mot de passe SmartHR360",
            message=(
                "Bonjour,\n\n"
                "Vous avez demandé la réinitialisation de votre mot de passe.\n"
                f"Veuillez utiliser le lien suivant pour le réinitialiser :\n\n{reset_link}\n\n"
                "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

        return token_obj


class PasswordResetSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        token_value = attrs["token"]
        try:
            token_obj = PasswordResetToken.objects.select_related("user").get(
                token=token_value
            )
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Token invalide."}) from None

        if token_obj.is_used:
            raise serializers.ValidationError({"token": "Ce token a déjà été utilisé."})

        if token_obj.is_expired():
            raise serializers.ValidationError({"token": "Ce token a expiré."})

        attrs["token_obj"] = token_obj
        return attrs

    def save(self, **kwargs):
        token_obj = self.validated_data["token_obj"]
        new_password = self.validated_data["new_password"]
        user = token_obj.user

        user.set_password(new_password)
        user.save()

        token_obj.mark_used()
        return user


class RequestEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            # generic response: do not leak existence
            raise serializers.ValidationError("Aucun utilisateur avec cet email.") from None

        if user.is_email_verified:
            raise serializers.ValidationError("Cet email est déjà vérifié.")
        self.context["user"] = user
        return value

    def save(self, **kwargs):
        user = self.context["user"]
        token_obj = (
            EmailVerificationToken.objects.filter(user=user, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if token_obj and token_obj.is_expired():
            token_obj.delete()
            token_obj = None

        if token_obj is None:
            token_obj = EmailVerificationToken.create_for_user(user)

        frontend_base = "http://localhost:3000"  # adapt later to your real FE URL
        verify_link = f"{frontend_base}/verify-email?token={token_obj.token}"

        send_mail(
            subject="Vérifiez votre adresse email SmartHR360",
            message=(
                "Bonjour,\n\n"
                "Merci de vous être inscrit sur SmartHR360.\n"
                "Veuillez cliquer sur le lien suivant pour vérifier votre adresse email :\n\n"
                f"{verify_link}\n\n"
                "Si vous n'êtes pas à l'origine de cette inscription, ignorez cet email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

        return token_obj


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        token_value = attrs["token"]
        try:
            token_obj = EmailVerificationToken.objects.select_related("user").get(
                token=token_value
            )
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Token invalide."}) from None

        if token_obj.is_used:
            raise serializers.ValidationError({"token": "Ce token a déjà été utilisé."})

        if token_obj.is_expired():
            raise serializers.ValidationError({"token": "Ce token a expiré."})

        attrs["token_obj"] = token_obj
        return attrs

    def save(self, **kwargs):
        token_obj = self.validated_data["token_obj"]
        user = token_obj.user

        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])

        token_obj.mark_used()
        return user
