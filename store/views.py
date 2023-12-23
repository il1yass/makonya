import logging
import json
import datetime
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.views.generic.edit import FormView
from django.contrib.auth import logout
from .models import Product, Order, OrderItem, ShippingAddress
from .forms import LoginUserForm, RegisterUserForm
from .utils import cartData, guestOrder


# Настройка логгера
logger = logging.getLogger(__name__)

# Обработчик для отображения продуктов в магазине
def store(request):
    try:
        data = cartData(request)

        cartItems = data['cartItems']
        order = data['order']
        items = data['items']

        # Получение всех продуктов из базы данных
        products = Product.objects.all()
        context = {'products': products, 'cartItems': cartItems}
        return render(request, 'store/store.html', context)

    except ObjectDoesNotExist as e:
        # Обработка исключения, например, вывод в консоль или логирование
        logger.error(f'An error occurred: {e}')

        # Возвращение страницы с ошибкой или другого предпочтительного поведения
        return render(request, 'error.html', {'error_message': 'An error occurred.'})


# Обработчик для отображения содержимого корзины
def cart(request):
    try:
        data = cartData(request)

        cartItems = data['cartItems']
        order = data['order']
        items = data['items']

        context = {'items': items, 'order': order, 'cartItems': cartItems}
        return render(request, 'store/cart.html', context)

    except ObjectDoesNotExist as e:
        # Обработка исключения, например, вывод в консоль или логирование
        logger.error(f'An error occurred: {e}')

        # Возвращение страницы с ошибкой или другого предпочтительного поведения
        return render(request, 'error.html', {'error_message': 'An error occurred.'})


# Обработчик для страницы оформления заказа
def checkout(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


# Обновление количества товара в корзине
def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    # Получение текущего пользователя
    customer = request.user
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


# Обработчик для обработки заказа
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment submitted..', safe=False)


# Переопределенный класс для входа в систему с дополнительным функционалом
class LoginUser(LoginView):
    template_name = 'store/login.html'
    form_class = LoginUserForm
    success_url = 'home'

    def form_valid(self, form):
        try:
            print("Start of LoginUser view")  # For debugging

            # Дополнительная логика, если необходимо

            def get_success_url(self):
                logger.info(f'User {self.request.user} logged in')
                return reverse_lazy('home')

            return super().form_valid(form)

        except Exception as e:
            # Обработка исключения, например, вывод в консоль или логирование

            logger.error(f'An error occurred: {e}')

            # Возвращение страницы с ошибкой или другого предпочтительного поведения
            return redirect('error_page')


# Класс для регистрации нового пользователя
class RegisterUser(FormView):
    form_class = RegisterUserForm
    template_name = 'store/registration.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()
        print('User registered successfully')
        return super().form_valid(form)


# Обработчик для выхода пользователя из системы
def logout_user(request):
    logout(request)
    print('User logged out')
    return redirect('/')
