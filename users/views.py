from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST

from mailing.permissions import is_manager

from .forms import LoginForm, RegisterForm
from .models import UserProfile


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, email_verified=False)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            confirm_url = request.build_absolute_uri(
                reverse("users:verify_email", kwargs={"uidb64": uid, "token": token})
            )
            send_mail(
                subject="Подтверждение регистрации",
                message=f"Перейдите по ссылке для подтверждения email: {confirm_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
            messages.success(
                request,
                "Регистрация успешна. Проверьте email и перейдите по ссылке для подтверждения.",
            )
            return redirect("users:login")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.save()
        messages.success(request, "Email подтверждён. Теперь вы можете войти в систему.")
        return redirect("users:login")

    messages.error(request, "Ссылка для подтверждения недействительна.")
    return redirect("users:login")


def user_login(request):
    if request.user.is_authenticated:
        return redirect("mailing:home")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        profile = getattr(user, "profile", None)
        if profile and profile.is_blocked:
            messages.error(request, "Ваш аккаунт заблокирован.")
            return render(request, "users/login.html", {"form": form})
        login(request, user)
        return redirect("mailing:home")

    return render(request, "users/login.html", {"form": form})


@login_required
@require_POST
def block_user(request, pk):
    if not is_manager(request.user):
        messages.error(request, "Недостаточно прав.")
        return redirect("mailing:home")

    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "Нельзя заблокировать себя.")
        return redirect("users:user_list")

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.is_blocked = True
    profile.save()
    user.is_active = False
    user.save()
    messages.success(request, f"Пользователь {user.username} заблокирован.")
    return redirect("users:user_list")


@login_required
def user_list(request):
    if not is_manager(request.user):
        messages.error(request, "Недостаточно прав.")
        return redirect("mailing:home")

    users = User.objects.order_by("username")
    for u in users:
        UserProfile.objects.get_or_create(user=u)
    users = User.objects.select_related("profile").order_by("username")
    return render(request, "users/user_list.html", {"users": users})
