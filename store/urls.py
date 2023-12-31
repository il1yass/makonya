from django.urls import path

from . import views
from .views import logout_user

urlpatterns = [
    path('', views.store, name="store"),
    path('cart/', views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),
    path('login/', views.LoginUser.as_view(), name="login"),
    path('register/', views.RegisterUser.as_view(), name="registration"),
    path('logout/', logout_user, name='logout'),
    path('update_item/', views.updateItem, name="update_item"),
    path('process_order/', views.processOrder, name="process_order"),

]
