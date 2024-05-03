from rest_framework import viewsets
from django.contrib.auth.models import User
# from django.contrib.admin.views.decorators import staff_member_required

from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    UserLoginSerializer,
    ProfileSerializer,
    PasswordChangeSerializer,
    SendPasswordResetEmailSerializer,
    UserPasswordResetSerializer,
    ItemSerializer,
    OrderItemSerializer,
    OrderSerializer,
    AddressSerializer,
    PaymentSerializer,
    CouponSerializer,
    RefundSerializer,
)

from ecom.models import (
    Item,
    OrderItem,
    Order,
    Address,
    Payment,
    Coupon,
    Refund
)

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter

#Genrate Token manually
def get_user_access_token(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access':str(refresh.access_token),
        'refresh':str(refresh)
    }

class RegistartionView(APIView):    
    def post(self,request,*args,**kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = get_user_access_token(user)
            return Response({'msg':"Registration Successfully",'token':token},status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_404_NOT_FOUND)

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(request.data)
        username = serializer.data.get('username')
        password = serializer.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            token = get_user_access_token(user)
            return Response({'token':token,'msg': "Login Successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({'msg': "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,*args,**kwargs):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request,*args,**kwargs):
        serializer = PasswordChangeSerializer(data=request.data,context={'user':request.user})
        if serializer.is_valid(raise_exception=True):
            return Response({'message':"Password Change Successfully"})
        else:
            return Response({'messages':serializer.errors})
        
class SendPasswordResetEmailView(APIView):
    def post(self,request,*args,**kwargs):
        serializer = SendPasswordResetEmailSerializer
        if serializer.is_valid(raise_exception=True):
            return Response({'message':"Password is send on email check Your Email."})
        
class UserPasswordResetView(APIView):
    def post(self,request,uid,token,format=None):
        serializer = UserPasswordResetSerializer(data=request.data,context={'uid':uid,'token':token})
        if serializer.is_valid(raise_exception=True):
            return Response({'message':"Password Reset Successfully..."},status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,status=status.HTTP_404_NOT_FOUND)

class AllAPI(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ('email','^username')
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ItemAPI(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

class OrderItemAPI(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

class OrderAPI(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class AddressAPI(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

class PaymentAPI(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class CouponAPI(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

class RefundAPI(viewsets.ModelViewSet):
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer
