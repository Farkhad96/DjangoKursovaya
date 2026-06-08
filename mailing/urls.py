from django.urls import path

from . import views

app_name = "mailing"

urlpatterns = [
    path("", views.home, name="home"),
    path("statistics/", views.statistics, name="statistics"),
    path("recipients/", views.recipient_list, name="recipient_list"),
    path("recipients/create/", views.recipient_create, name="recipient_create"),
    path("recipients/<int:pk>/edit/", views.recipient_update, name="recipient_update"),
    path("recipients/<int:pk>/delete/", views.recipient_delete, name="recipient_delete"),
    path("messages/", views.message_list, name="message_list"),
    path("messages/create/", views.message_create, name="message_create"),
    path("messages/<int:pk>/edit/", views.message_update, name="message_update"),
    path("messages/<int:pk>/delete/", views.message_delete, name="message_delete"),
    path("mailings/", views.mailing_list, name="mailing_list"),
    path("mailings/create/", views.mailing_create, name="mailing_create"),
    path("mailings/<int:pk>/edit/", views.mailing_update, name="mailing_update"),
    path("mailings/<int:pk>/delete/", views.mailing_delete, name="mailing_delete"),
    path("mailings/<int:pk>/send/", views.mailing_send, name="mailing_send"),
    path("mailings/<int:pk>/disable/", views.mailing_disable, name="mailing_disable"),
]
