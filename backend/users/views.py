from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserProfileSerializer
from .models import BlacklistedToken
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache
from .tasks import send_welcome_email

User = get_user_model()

# Function to generate JWT tokens
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@ratelimit(key='ip',rate='5/m',method='POST',block=True)
@api_view(['POST'])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = get_tokens_for_user(user)  # Generate JWT tokens
        return Response({
            "message": "User registered successfully",
            "tokens": tokens  # Return access & refresh tokens
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    cache_key = f"user_profile_{request.user.id}"
    data = cache.get(cache_key)

    if request.method == 'GET':
        if not data:
            serializer = UserProfileSerializer(request.user)
            data = serializer.data
            cache.set(cache_key, data, timeout=300)
        return Response(data)

    elif request.method == 'PUT':
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Invalidate old cache
            cache.delete(cache_key)
            cache.set(cache_key, serializer.data, timeout=300) #UpdateCache

            return Response({"message": "Profile updated successfully", "data": serializer.data})
        return Response(serializer.errors, status=400)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error":"Refresh token is required"},status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        token.blacklist()

        BlacklistedToken.objects.create(token=refresh_token)
        return Response({"message":"User Logged out successfully"},status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error":str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
