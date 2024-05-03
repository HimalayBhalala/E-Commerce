from django.shortcuts import render,get_object_or_404,redirect,HttpResponseRedirect
from django.urls import reverse
from .models import Item,Order,OrderItem
from django.views.generic import ListView,DetailView,View
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from .forms import CheckOutForm,CouponForm,RefundForm
from .models import Address,Payment,Coupon,Refund
import stripe
from django.conf import settings
import string
import random
from rest_framework import viewsets
from django.http import HttpResponse
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken


class HomeView(ListView):
    model = Item
    paginate_by = 8
    template_name = 'home.html'
    queryset = Item.objects.all()

#product,category
def get_product_category(request,category):
    items = Item.objects.filter(category=category)
    context = {
        'items':items
    }
    return render(request,'product_category.html',context)

def search_products(request):
    query = request.GET.get('q')
    if query:
        object_list = Item.objects.filter(Q(description__icontains=query) | Q(title__icontains=query))
        return render(request,'home.html',{'object_list':object_list})
    else:
        return HttpResponse(request,"No item found....")


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("ecom:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("ecom:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("ecom:order-summary")

@login_required
def remove_to_cart(request,slug):
    item = get_object_or_404(Item,slug=slug)
    order_qs = Order.objects.filter(user=request.user,ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            messages.info(request,"Item successfully remove from your cart")
            order.items.remove(order_item)
        else:
            messages.info(request,'Item Does not exists in your cart')
            return redirect("ecom:product",slug=slug)
    else:
        messages.info(request,'No active product in your cart')
        return redirect("ecom:product",slug=slug)
    return redirect('ecom:product',slug=slug)

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("ecom:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("ecom:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("ecom:product", slug=slug)


class OrderSummaryView(LoginRequiredMixin,View):
     def get(self,request,*args,**kwargs):
         try:
             order = Order.objects.get(user=request.user,ordered=False)
             context = {
                 'object':order
             }
             return render(request,'order_summary.html',context)
         except ObjectDoesNotExist:
             return redirect('/')
         
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_ref_code():
    return ''.join(random.choices(string.ascii_letters + string.digits,k=10))

class PaymentView(View):
    def get(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLIC_KEY,
                'DISPLAY_COUPON_FORM':False
            }
            return render(request, 'payment.html', context)
        else:
            messages.warning(request, "You have not added billing address.")
            return redirect('ecom:checkout')

    def post(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        token = request.POST['stripeToken']
        amount = order.get_total()
        try:
            # Charge the customer using the Stripe token
            charge = stripe.Charge.create(
                amount=int(amount),
                currency='usd',
                source=token,
            )
            # Create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = request.user
            payment.amount = amount
            payment.save()

            order_item = order.items.all()
            order_item.update(ordered=True)
            for item in order_item:
                item.save()

            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()

            messages.success(request, "Payment successful! Your order has been placed.")
            return redirect('ecom:home')  # Redirect to the home page upon successful payment
        
        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, f"{err.get('message')}")
            return redirect("/")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, "Rate limit error")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            print(e)
            messages.warning(self.request, "Invalid parameters")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, "Not authenticated")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, "Network error")
            return redirect("/")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(
                self.request, "Something went wrong. You were not charged. Please try again.")
            return redirect("/")

        except Exception as e:
            # send an email to ourselves
            messages.warning(
                self.request, "A serious error occurred. We have been notifed.")
            return redirect("/")
        
def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid

        
class CheckoutView(View):
    def get(self,request,*args,**kwargs):
        try:
            order = Order.objects.get(user=request.user,ordered=False)
            form = CheckOutForm()
            context = {
                'form':form,
                'order':order,
                'couponform':CouponForm(),
                'DISPLAY_COUPON_FORM':True                
            }

            shipping_address_qs = Address.objects.filter(
                user = request.user,
                address_type = 'S',
                default = True
            )
            if shipping_address_qs.exists():
                context.update({'default_shipping_address':shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user = request.user,
                address_type = 'B',
                default = True
            )
            if billing_address_qs.exists():
                context.update({'default_billing_address':billing_address_qs[0]})


            return render(request,'checkout.html',context)
        except ObjectDoesNotExist:
            messages.info(request,"You have no any active ordered")
            return redirect('ecom:checkout')
    
    def post(self,request,*args,**kwargs):
        form = CheckOutForm(request.POST)
        try:
            order = Order.objects.get(user=request.user,ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data['use_default_shipping']

                if use_default_shipping:
                    print("Use default shipping Address")
                    address_qs = Address.objects.filter(
                        user = request.user,
                        address_type = 'S',
                        default = True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(request,"No any default street address available.")
                        return redirect('ecom:checkout')
                else:
                    print("User is entering a new shipping address")

                    shipping_address1 = form.cleaned_data['shipping_address']
                    shipping_address2 = form.cleaned_data['shipping_address2']
                    shipping_country = form.cleaned_data['shipping_country']
                    shipping_zip = form.cleaned_data['shipping_zip']

                    if is_valid_form([shipping_address1,shipping_address2,shipping_country,shipping_zip]):
                        shipping_address = Address(
                            user = self.request.user,
                            street_address = shipping_address1,
                            apartment_address = shipping_address2,
                            country = shipping_country,
                            zip = shipping_zip,
                            address_type = 'S'
                        )
                        shipping_address.save()
                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data['set_default_shipping']
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(request,"Fillup all required fields for shipping")

                use_default_billing = form.cleaned_data['use_default_billing']

                same_billing_address = form.cleaned_data['same_billing_address']

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()  
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Use default billing address")
                    address_qs = Address.objects.filter(
                        user = request.user,
                        address_type = 'B',
                        default = True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info("No any default billing address available.")
                        return redirect('ecom:checkout')
                else:
                    print("adding new billing address")

                    billing_address1 = form.cleaned_data['billing_address']
                    billing_address2 = form.cleaned_data['billing_address2']
                    billing_country = form.cleaned_data['billing_country']
                    billing_zip = form.cleaned_data['billing_zip']

                    if is_valid_form([billing_address1,billing_address2,billing_country,billing_zip]):
                        billing_address = Address(
                            user = request.user,
                            street_address = billing_address1,
                            apartment_address = billing_address2,
                            country = billing_country,
                            zip = billing_zip,
                            address_type = 'B'
                        )
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data['set_default_billing']
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.info(request,"Add all required fields for adding billing")

                payment_option = form.cleaned_data['payment_option']

                if payment_option == 'S':
                    return redirect('ecom:payment',payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('ecom:payment',payment_option='paypal')
                else:
                    messages.warning(request,"Select a valid payment Option")
                    return redirect('ecom:checkout')
            else:
                print(form.errors)
        except ObjectDoesNotExist:
            messages.error(request,'You do not have an active account.')
            return redirect('ecom:order-summary')
        

def get_coupon(request,code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request,'Your enter coupon does not exists.')
        return redirect('ecom:checkout')

class AddCouponView(View):

    def post(self,request,*args,**kwargs):
        if request.method == "POST":
            form = CouponForm(request.POST or None)
            if form.is_valid():
                try:
                    code = form.cleaned_data.get('code')
                    order = Order.objects.get(user=request.user,ordered=False)
                    order.coupon = get_coupon(request,code)
                    order.save()
                    messages.success(request,"hurray your coupon is accepted")
                    return redirect('ecom:checkout')
                except ObjectDoesNotExist:
                    messages.info(request,"You have no any active ordered")
                    return redirect('ecom:order-summary')
        return None
    

class RequestRefundView(View):
    def get(self,request,*args,**kwargs):
        form = RefundForm()
        context = {
            'form':form
        }
        return render(request,'request_refund.html',context)

    def post(self,request,*args,**kwargs):
        form = RefundForm(request.POST or None)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data['message']
            email = form.cleaned_data['email']
            #Edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                #Store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.success(request,'Your request is received')
                return redirect('ecom:request-refund')
            except ObjectDoesNotExist:
                messages.warning(request,'This order is not exists')
                return redirect('ecom:request-refund')
                                    