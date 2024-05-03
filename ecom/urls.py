from django.urls import path
from . import views

app_name = 'ecom'

urlpatterns = [
    path('',views.HomeView.as_view(),name='home'),
    path('checkout/',views.CheckoutView.as_view(),name='checkout'),
    path('order-summary/',views.OrderSummaryView.as_view(),name='order-summary'),
    path('product/<str:category>/',views.get_product_category,name='pcategory'),
    path('products/<slug>/',views.ItemDetailView.as_view(),name='product'),
    path('add-to-cart/<slug>/',views.add_to_cart,name='add-to-cart'),
    path('add-coupon/',views.AddCouponView.as_view(),name='add-coupon'),
    path('remove-to-cart/<slug>/',views.remove_to_cart,name='remove-to-cart'),
    path('remove-single-item-from-cart/<slug>/',views.remove_single_item_from_cart,name='remove-single-item-from-cart'),
    path('payment/<payment_option>/',views.PaymentView.as_view(),name='payment'),
    path('request-refund/',views.RequestRefundView.as_view(),name='request-refund'),
    path('search/', views.search_products, name='search_products'),
]