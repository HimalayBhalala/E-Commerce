from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView,TokenVerifyView,TokenRefreshView


router = DefaultRouter()

router.register('all',views.AllAPI,basename='all'),
router.register('item',views.ItemAPI,basename='item'),
router.register('orderitem',views.OrderItemAPI,basename='orderitem'),
router.register('order',views.OrderAPI,basename='order'),
router.register('address',views.AddressAPI,basename='address'),
router.register('payment',views.PaymentAPI,basename='payment'),
router.register('coupon',views.CouponAPI,basename='coupon'),
router.register('refund',views.RefundAPI,basename='refund'),

urlpatterns = [
    path('',include(router.urls)),
    # path('auth/',include('rest_framework.urls',namespace='rest_framework')),
    path('register/',views.RegistartionView.as_view(),name='register'),
    path('login/',views.LoginView.as_view(),name='login'),
    path('profile/',views.ProfileView.as_view(),name='profile'),
    path('password/change/',views.PasswordChangeView.as_view(),name='password_change'),
    path('send-reset-password-email',views.SendPasswordResetEmailView.as_view(),name='send-reset-password-email'),
    path('reset-password/<uid>/<token>/',views.UserPasswordResetView.as_view(),name='reset-password'),
    path('token/',TokenObtainPairView.as_view(),name='token_obtain'),
    path('token/refresh/',TokenRefreshView.as_view(),name='token_refresh'),
    path('token/verify/',TokenVerifyView.as_view(),name='token_verify'),
]
