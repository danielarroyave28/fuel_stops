from django.urls import path
from . import views
urlpatterns = [
  #path('fuel/', views.fuel),
  path('fuel/', views.FuelList.as_view()),
]


