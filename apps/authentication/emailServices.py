from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response 
from .models import OTP


class EmailService:
    
    @staticmethod
    def send_otp_email(email, otp_code, first_name='User', last_name="User"):
        try:
            send_mail(
                f'Welcome to DocuMind {f"{first_name}  {last_name}"}',
                f'Your OTP is: {otp_code}. Valid for 10 minutes.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False
        

    @staticmethod
    def send_password_change_notification(user):
        try:
            send_mail(
                'Password Updated - DocuMind',
                f'Hello {user.first_name}, your password has been successfully updated.',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False

class OTPService:

    @staticmethod
    def generate_send_otp(email, first_name="User", last_name="User"):
        #delete old otp
        OTP.objects.filter(email = email).delete()

        #generate now otp
        otp_code = OTP.generate_otp()
        OTP.objects.create(email=email, otp=otp_code)

        #send mail
        if EmailService.send_otp_email(email, otp_code, first_name, last_name):
            return Response({
                'message': 'OTP sent to your email successfully',
                'email': email
            }, status=status.HTTP_200_OK)   
        else:
            return Response({
                'message': 'Failed to send OTP. Please again later',
                'email': email
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


    @staticmethod
    def verify_otp(email, otp_code):
        try:
            otp = OTP.objects.get(email=email, otp=otp_code)
            if not otp.is_valid():
                return None, Response({
                    'error': 'OTP expired or already used'
                }, status=status.HTTP_400_BAD_REQUEST)
            return otp, None
        except OTP.DoesNotExist:
            return None, Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)

