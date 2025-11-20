from django.urls import path
from projects.views.presale import crear_presale, pre_sale, presale_edit, presale_delete

urlpatterns = [
    path("create/", crear_presale, name="crear_presale"),
    path("", pre_sale, name="presale_list"),
    path("<str:pk>/edit/", presale_edit, name="presale_edit"),
    path("<str:pk>/delete/", presale_delete, name="presale_delete"),  # ✅ corregido
]

