from django.db import models
from django.conf import settings
from django.urls import reverse
from django.conf import settings
from django_countries.fields import CountryField
from django.contrib.auth.models import AbstractUser

# Create your models here.


#First add item into cart
#Second add billing address

CATEGORY_CHOICES = (
    ('S','Shirt'),
    ('SW','Sport Wear'),
    ('OW','Outwear')
)

LABEL_CHOICES = (
    ('P','primary'),
    ('S','secondary'),
    ('D','danger')
)

ADDRESS_CHOICES = (
    ('S','Shipping'),
    ('B','Billing')
)
    

class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    image = models.ImageField(upload_to='product/',null=False,blank=False)
    discount_price = models.FloatField(blank=False,null=False)
    category = models.CharField(choices=CATEGORY_CHOICES,max_length=2)
    label = models.CharField(choices=LABEL_CHOICES,max_length=1)
    slug = models.SlugField()
    description = models.TextField(default="No description...")

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('ecom:product',kwargs={
            'slug':self.slug
        })
    
    def add_to_cart_url(self):
        return reverse('ecom:add-to-cart',kwargs={
            'slug':self.slug
        })
    
    def remove_from_cart_url(self):
        return reverse('ecom:remove-to-cart',kwargs={'slug':self.slug})

class OrderItem(models.Model):
    item = models.ForeignKey(Item,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item.title} - {self.quantity}"
    
    def get_total_item_price(self):
        return self.quantity * self.item.price
    
    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price
    
    def get_amount_saving(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()
    
    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()
    
    
class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,related_name='order',on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20,blank=True,null=True)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey('Address',related_name='billing_address',on_delete=models.SET_NULL,blank=True,null=True)
    shipping_address = models.ForeignKey('Address',related_name='shipping_address',on_delete=models.SET_NULL,blank=True,null=True)
    payment = models.ForeignKey('Payment',on_delete=models.SET_NULL,blank=True,null=True)
    coupon = models.ForeignKey('Coupon',on_delete=models.SET_NULL,blank=True,null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    
    def get_total(self):
        total = 0
        for object_item in self.items.all():
            total += object_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,related_name='address',on_delete=models.CASCADE)
    street_address = models.CharField(max_length=200)
    apartment_address = models.CharField(max_length=200)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1,choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    
    class Meta:
        verbose_name_plural = 'Addresses'

class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,related_name='payment',on_delete=models.SET_NULL,blank=True,null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    
class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code
    
class Refund(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"
    