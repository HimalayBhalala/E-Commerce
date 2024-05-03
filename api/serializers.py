from rest_framework import serializers
from django.contrib.auth.models import User
from ecom.models import Item,OrderItem,Order,Coupon,Address,Payment,Refund
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.utils.encoding import force_bytes,smart_str,DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from . import utils

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','password']
    
    def create(self,validate_data):
        username = validate_data['username']
        password = validate_data['password']
        user = User.objects.create(username=username,password=password)
        user.set_password(password)
        user.save()
        return user
    
class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','password']

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','password']

class PasswordChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['password']

    def validate(self, attrs):
        password = attrs['password']
        user = self.context.get('user')
        user.set_password(password)
        user.save()
        return user
    
class SendPasswordResetEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']

    def validate(self, attrs):
        email = attrs['email']
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            print("UID",uid)
            token = PasswordResetTokenGenerator().make_token(user)
            print("Token",token)
            link = 'http://127.0.0.1:8000/api/user/reset/'+uid+'/'+token
            print("Link",link)

            #Email Send
            body = 'Click following link for reset your password'+link
            data = {
                'subject':"Reset Password",
                'body':body,
                'to_email':user.email
            }
            utils.Util.send_email()

            return attrs
        else:
            serializers.ValidationError("You have not Register for this features so first Register.")

class UserPasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['password']

        def validate(self,data):
            try:
                password = data['password']
                uid = self.context.get('uid')
                token = self.context.get('token')
                id = smart_str(urlsafe_base64_decode(uid))
                print(id)
                user = User.objects.get(id=id)
                if not PasswordResetTokenGenerator().check_token(user,token):
                    raise serializers.ValidationError("Toke is not valid or expire")
                user.set_password(password)
                user.save()
                return data
            except DjangoUnicodeDecodeError as identifier:
                PasswordResetTokenGenerator().check_token(user,token)
                raise serializers.ValidationError("Token is not valid or expired")

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = serializers.HyperlinkedRelatedField(many=True,read_only=True,view_name='item-detail')
    class Meta:
        model = Order
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    order = serializers.HyperlinkedRelatedField(many=True,read_only=True,view_name='order-detail')
    address = AddressSerializer(many=True,read_only=True)
    payment = PaymentSerializer(many=True,read_only=True)
    class Meta:
        model = User
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(many=True,read_only=True)
    class Meta:
        model = OrderItem
        fields = '__all__'

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'

class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = '__all__'