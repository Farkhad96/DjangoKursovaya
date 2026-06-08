from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST

from .cache_utils import get_home_statistics, get_user_statistics
from .forms import MailingForm, MessageForm, RecipientForm
from .models import Mailing, Message, Recipient
from .permissions import (
    check_owner_edit,
    check_owner_or_manager_view,
    get_mailing_queryset,
    get_message_queryset,
    get_recipient_queryset,
    is_manager,
)
from .services import MailingSendError, send_mailing


@cache_page(60)
def home(request):
    stats = get_home_statistics(request.user)
    return render(request, "mailing/home.html", stats)


@login_required
def statistics(request):
    stats = get_user_statistics(request.user)
    return render(request, "mailing/statistics.html", stats)


# --- Recipients ---

@login_required
def recipient_list(request):
    recipients = get_recipient_queryset(request.user)
    return render(request, "mailing/recipient_list.html", {"recipients": recipients})


@login_required
def recipient_create(request):
    if request.method == "POST":
        form = RecipientForm(request.POST)
        if form.is_valid():
            recipient = form.save(commit=False)
            recipient.owner = request.user
            recipient.save()
            messages.success(request, "Получатель добавлен.")
            return redirect("mailing:recipient_list")
    else:
        form = RecipientForm()
    return render(request, "mailing/recipient_form.html", {"form": form, "title": "Добавить получателя"})


@login_required
def recipient_update(request, pk):
    recipient = get_object_or_404(Recipient, pk=pk)
    check_owner_edit(request.user, recipient)
    if request.method == "POST":
        form = RecipientForm(request.POST, instance=recipient)
        if form.is_valid():
            form.save()
            messages.success(request, "Получатель обновлён.")
            return redirect("mailing:recipient_list")
    else:
        form = RecipientForm(instance=recipient)
    return render(request, "mailing/recipient_form.html", {"form": form, "title": "Редактировать получателя"})


@login_required
def recipient_delete(request, pk):
    recipient = get_object_or_404(Recipient, pk=pk)
    check_owner_edit(request.user, recipient)
    if request.method == "POST":
        recipient.delete()
        messages.success(request, "Получатель удалён.")
        return redirect("mailing:recipient_list")
    return render(request, "mailing/recipient_confirm_delete.html", {"object": recipient})


# --- Messages ---

@login_required
def message_list(request):
    messages_qs = get_message_queryset(request.user)
    return render(request, "mailing/message_list.html", {"messages_list": messages_qs})


@login_required
def message_create(request):
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.owner = request.user
            msg.save()
            messages.success(request, "Сообщение создано.")
            return redirect("mailing:message_list")
    else:
        form = MessageForm()
    return render(request, "mailing/message_form.html", {"form": form, "title": "Добавить сообщение"})


@login_required
def message_update(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    check_owner_edit(request.user, msg)
    if request.method == "POST":
        form = MessageForm(request.POST, instance=msg)
        if form.is_valid():
            form.save()
            messages.success(request, "Сообщение обновлено.")
            return redirect("mailing:message_list")
    else:
        form = MessageForm(instance=msg)
    return render(request, "mailing/message_form.html", {"form": form, "title": "Редактировать сообщение"})


@login_required
def message_delete(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    check_owner_edit(request.user, msg)
    if request.method == "POST":
        msg.delete()
        messages.success(request, "Сообщение удалено.")
        return redirect("mailing:message_list")
    return render(request, "mailing/message_confirm_delete.html", {"object": msg})


# --- Mailings ---

@login_required
def mailing_list(request):
    mailings = get_mailing_queryset(request.user)
    return render(request, "mailing/mailing_list.html", {"mailings": mailings, "is_manager": is_manager(request.user)})


@login_required
def mailing_create(request):
    if request.method == "POST":
        form = MailingForm(request.POST, user=request.user)
        if form.is_valid():
            mailing = form.save(commit=False)
            mailing.owner = request.user
            mailing.save()
            form.save_m2m()
            messages.success(request, "Рассылка создана.")
            return redirect("mailing:mailing_list")
    else:
        form = MailingForm(user=request.user)
    return render(request, "mailing/mailing_form.html", {"form": form, "title": "Создать рассылку"})


@login_required
def mailing_update(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    check_owner_edit(request.user, mailing)
    if request.method == "POST":
        form = MailingForm(request.POST, instance=mailing, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Рассылка обновлена.")
            return redirect("mailing:mailing_list")
    else:
        form = MailingForm(instance=mailing, user=request.user)
    return render(request, "mailing/mailing_form.html", {"form": form, "title": "Редактировать рассылку"})


@login_required
def mailing_delete(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    check_owner_edit(request.user, mailing)
    if request.method == "POST":
        mailing.delete()
        messages.success(request, "Рассылка удалена.")
        return redirect("mailing:mailing_list")
    return render(request, "mailing/mailing_confirm_delete.html", {"object": mailing})


@login_required
@require_POST
def mailing_send(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    check_owner_or_manager_view(request.user, mailing)
    if not is_manager(request.user):
        check_owner_edit(request.user, mailing)

    try:
        success, failure = send_mailing(mailing)
        messages.success(
            request,
            f"Рассылка отправлена. Успешно: {success}, неуспешно: {failure}.",
        )
    except MailingSendError as exc:
        messages.error(request, str(exc))

    return redirect("mailing:mailing_list")


@login_required
@require_POST
def mailing_disable(request, pk):
    if not is_manager(request.user):
        messages.error(request, "Недостаточно прав.")
        return redirect("mailing:mailing_list")

    mailing = get_object_or_404(Mailing, pk=pk)
    mailing.is_active = False
    mailing.save(update_fields=["is_active"])
    messages.success(request, f"Рассылка #{mailing.pk} отключена.")
    return redirect("mailing:mailing_list")
