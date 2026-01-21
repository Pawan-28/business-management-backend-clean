from django.shortcuts import render
import json
from companies.utils import  send_twilio_otp




# Create your views here.
import random
from rest_framework.permissions import AllowAny

from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate, logout
from rest_framework.exceptions import ValidationError
from .models import Company, Employee, CompanySettings, PasswordResetToken, Warehouse, EmployeeLoginHistory,VendorOrder
from .serializers import (
    CompanyRegistrationSerializer,
    CompanyLoginSerializer,
    CompanyProfileSerializer,
    EmployeeSerializer,
    AddEmployeeSerializer,
    ChangePasswordSerializer,
    OTPSerializer,
    WarehouseSerializer,
    EmployeeProfileSerializer,
    EmployeeLoginSerializer,
    EmployeeChangePasswordSerializer,
    VendorOrderSerializer
)
from companies import serializers

# companies/views.py me CompanyRegisterView update karein
class CompanyRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        print("="*50)
        print("REGISTRATION REQUEST RECEIVED")
        print("Request data:", request.data)
        print("Request content type:", request.content_type)
        print("="*50)
        
        mobile = request.data.get('mobile')
        if not mobile:
            return Response({
                    'success': False,
                    'error': 'Mobile number is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ **IMPORTANT NEW LOGIC STARTS HERE**
        # Step 1: पहले चेक करें कि इस मोबाइल से कोई VERIFIED कंपनी तो नहीं है
        existing_verified_company = Company.objects.filter(
            mobile=mobile,
            is_verified=True
        ).first()
        
        if existing_verified_company:
            return Response({
                'success': False,
                'error': 'A verified company already exists with this mobile number. Please login.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: अगर इस मोबाइल से कोई UNVERIFIED कंपनी है, तो उसे डिलीट कर दें
        existing_unverified_company = Company.objects.filter(
            mobile=mobile,
            is_verified=False
        ).first()
        
        if existing_unverified_company:
            print(f"[DEBUG] Found old unverified company. Deleting ID: {existing_unverified_company.company_id}")
            try:
                # पहले कंपनी से जुड़े settings डिलीट करें (अगर हैं तो)
                CompanySettings.objects.filter(company=existing_unverified_company).delete()
                # फिर कंपनी को डिलीट करें
                existing_unverified_company.delete()
                print(f"[DEBUG] Successfully deleted old unverified company.")
            except Exception as e:
                print(f"[DEBUG] Error deleting old company: {e}")
        # ✅ **NEW LOGIC ENDS HERE**

        # Step 3: अब नई कंपनी को रजिस्टर करें
        serializer = CompanyRegistrationSerializer(data=request.data)
        
        print("Validating serializer...")
        is_valid = serializer.is_valid()
        print(f"Serializer valid: {is_valid}")
        
        if not is_valid:
            print("SERIALIZER ERRORS:")
            print(json.dumps(serializer.errors, indent=2))
            print("="*50)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print("Serializer is valid, creating company...")
        
        try:
            company = serializer.save()
            print(f"Company created: {company.company_id}")
            
            # Send OTP via SMS
            # if company.mobile:
            #    otp = send_twilio_otp(company.mobile)
            #    if not otp:
            #        raise Exception("OTP sending failed")
            #    otp_expiry = timezone.now() + timedelta(minutes=10)


            if company.mobile:
    # ✅ YEH NAYA CODE DAAL DO
   
                otp = str(random.randint(100000, 999999))  # 6-digit OTP
                otp_expiry = timezone.now() + timedelta(minutes=10)
    
    # Terminal par OTP print karo
                print("\n" + "="*50)
                print(f"📱 OTP FOR MOBILE: {company.mobile}")
                print(f"🔑 OTP CODE: {otp}")
                print(f"⏰ OTP EXPIRES AT: {otp_expiry}")
                print("="*50 + "\n")
    
    # Save OTP to company
                company.otp = otp
                company.otp_expiry = otp_expiry
                company.save()
            
               # Save OTP to company
            #    company.otp = otp
            #    company.otp_expiry = otp_expiry
            #    company.save()

            # Create company settings
            CompanySettings.objects.create(company=company)
            
            # print(f"OTP generated: {otp} for mobile: {company.mobile}")
            print(f"Company created successfully. OTP: {otp}")
            
            return Response({
                'success': True,
                'message': 'Company registered successfully. OTP sent to mobile.',
                'company_id': company.company_id,
                'mobile': company.mobile,
                'requires_otp_verification': True
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error creating company: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            mobile = serializer.validated_data['mobile']
            otp = serializer.validated_data['otp']
            
            try:
                company = Company.objects.get(mobile=mobile)
                
                # Check OTP
                if company.otp != otp or company.otp_expiry < timezone.now():
                    return Response({
                        'success': False,
                        'error': 'Invalid or expired OTP'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Mark company as verified
                company.is_verified = True
                company.otp = None
                company.otp_expiry = None
                company.save()
                
                # Generate tokens
                refresh = RefreshToken.for_user(company)
                
                return Response({
                    'success': True,
                    'message': 'Company verified successfully',
                    'company_id': company.company_id,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token)
                    },
                    'company': {
                        'company_id': company.company_id,
                        'company_name': company.company_name,
                        'email': company.email,
                        'mobile': company.mobile
                    }
                })
                
            except Company.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Company not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class CompanyLoginView(TokenObtainPairView):
    serializer_class = CompanyLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Customize response
            data = response.data
            return Response({
                'success': True,
                'message': 'Login successful',
                'tokens': {
                    'refresh': data['refresh'],
                    'access': data['access']
                },
                'company': data['company']
            })
        
        return response

class CompanyLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logout(request)
            
            return Response({
                'success': True,
                'message': 'Logged out successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class CompanyDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user
        employees = company.employees.all()
        
        # Calculate statistics
        total_employees = employees.count()
        active_employees = employees.filter(is_active=True, status='active').count()
        inactive_employees = employees.filter(is_active=False).count()
        suspended_employees = employees.filter(status='suspended').count()
        on_leave_employees = employees.filter(status='on_leave').count()
        
        # Recent employees
        recent_employees = employees.order_by('-created_at')[:5]
        recent_employees_data = EmployeeSerializer(recent_employees, many=True).data
        
        # Company info
        company_info = {
            'company_id': company.company_id,
            'company_name': company.company_name,
            'email': company.email,
            'mobile': company.mobile,
            'gst_number': company.gst_number,
            'is_verified': company.is_verified,
            'created_at': company.created_at
        }
        
        return Response({
            'success': True,
            'dashboard': {
                'stats': {
                    'total_employees': total_employees,
                    'active_employees': active_employees,
                    'inactive_employees': inactive_employees,
                    'suspended_employees': suspended_employees,
                    'on_leave_employees': on_leave_employees
                },
                'company_info': company_info,
                'recent_employees': recent_employees_data
            }
        })

class CompanyDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user
        employees = company.employees.all()
        
        # Calculate statistics
        total_employees = employees.count()
        active_employees = employees.filter(is_active=True, status='active').count()
        
        # Recent employees
        recent_employees = employees.order_by('-created_at')[:5]
        recent_employees_data = EmployeeSerializer(recent_employees, many=True).data
        
        # Company info
        company_info = {
            'company_id': company.company_id,
            'company_name': company.company_name,
            'email': company.email,
            'mobile': company.mobile,
            'gst_number': company.gst_number,
            'is_verified': company.is_verified,
            'created_at': company.created_at
        }
        
        return Response({
            'success': True,
            'dashboard': {
                'stats': {
                    'total_employees': total_employees,
                    'active_employees': active_employees,
                    'inactive_employees': total_employees - active_employees
                },
                'company_info': company_info,
                'recent_employees': recent_employees_data
            }
        })

class CompanyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CompanyProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        # Handle logo upload separately if needed
        return super().update(request, *args, **kwargs)

class EmployeeListView(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        company = self.request.user
        return Employee.objects.filter(company=company)

class AddEmployeeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = AddEmployeeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            employee = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Employee added successfully',
                'employee': EmployeeSerializer(employee).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        company = self.request.user
        return Employee.objects.filter(company=company)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.status = 'inactive'
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Employee deactivated successfully'
        })

class ResetEmployeePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, employee_id):
        try:
            employee = Employee.objects.get(
                employee_id=employee_id,
                company=request.user
            )
            
            # Generate new password
            import secrets
            new_password = secrets.token_urlsafe(8)
            
            # Update password
            employee.password = new_password  # In production, hash this
            employee.temp_password = True
            employee.last_password_change = timezone.now()
            employee.save()
            
            # Send email with new password
            # send_password_reset_email(employee.email, new_password)
            
            return Response({
                'success': True,
                'message': 'Password reset successfully. New password sent to employee.',
                'new_password': new_password  # Remove in production
            })
            
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            company = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            # Verify old password
            if not company.check_password(old_password):
                return Response({
                    'success': False,
                    'error': 'Old password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update password
            company.set_password(new_password)
            company.save()
            
            # Blacklist all tokens
            tokens = RefreshToken.objects.filter(user=company)
            for token in tokens:
                token.blacklist()
            
            return Response({
                'success': True,
                'message': 'Password changed successfully. Please login again.'
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Resend OTP for verification (registration or forgot password)
        """
        print("="*50)
        print("RESEND OTP REQUEST")
        print("Request data:", request.data)
        print("="*50)
        
        mobile = request.data.get('mobile')
        
        if not mobile:
            return Response({
                'success': False,
                'error': 'Mobile number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if company exists
            company = Company.objects.filter(mobile=mobile).first()
            
            if not company:
                return Response({
                    'success': False,
                    'error': 'No account found with this mobile number'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check OTP cooldown (prevent too many requests)
            # You can implement rate limiting here if needed
            
            # Generate new OTP
            otp = send_twilio_otp(mobile)
            
            if not otp:
                # Fallback to random OTP if Twilio fails
                otp = str(random.randint(100000, 999999))
                print(f"[DEBUG] Twilio failed, using random OTP: {otp}")
            
            # Save OTP to company
            otp_expiry = timezone.now() + timedelta(minutes=10)
            
            company.otp = otp
            company.otp_expiry = otp_expiry
            company.save()
            
            print(f"[DEBUG] OTP resent for {mobile}: {otp}")
            print(f"[DEBUG] OTP expires at: {otp_expiry}")
            
            return Response({
                'success': True,
                'message': 'OTP sent successfully to your mobile number',
                'mobile': mobile,
                'company_id': company.company_id,
                'is_verified': company.is_verified,
                'debug_otp': otp  # Remove this in production
            })
            
        except Exception as e:
            print(f"Error in ResendOTPView: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return Response({
                'success': False,
                'error': 'Failed to send OTP. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckCompanyExistsView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """
        Check if company details already exist (for registration validation)
        """
        email = request.query_params.get('email')
        mobile = request.query_params.get('mobile')
        gst_number = request.query_params.get('gst_number')
        
        response = {
            'exists': False,
            'details': {}
        }
        
        try:
            if email:
                email_company = Company.objects.filter(email=email).first()
                if email_company:
                    response['exists'] = True
                    response['details']['email'] = {
                        'exists': True,
                        'company_name': email_company.company_name,
                        'is_verified': email_company.is_verified,
                        'company_id': email_company.company_id
                    }
                else:
                    response['details']['email'] = {'exists': False}
            
            if mobile:
                mobile_company = Company.objects.filter(mobile=mobile).first()
                if mobile_company:
                    response['exists'] = True
                    response['details']['mobile'] = {
                        'exists': True,
                        'company_name': mobile_company.company_name,
                        'is_verified': mobile_company.is_verified,
                        'company_id': mobile_company.company_id
                    }
                else:
                    response['details']['mobile'] = {'exists': False}
            
            if gst_number:
                gst_company = Company.objects.filter(gst_number=gst_number).first()
                if gst_company:
                    response['exists'] = True
                    response['details']['gst_number'] = {
                        'exists': True,
                        'company_name': gst_company.company_name,
                        'is_verified': gst_company.is_verified,
                        'company_id': gst_company.company_id
                    }
                else:
                    response['details']['gst_number'] = {'exists': False}
            
            return Response(response)
            
        except Exception as e:
            print(f"Error in CheckCompanyExistsView: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    

#warehouse views 
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Warehouse
from .serializers import WarehouseSerializer

# ===================== WAREHOUSE VIEWS =====================

class WarehouseListCreateView(generics.ListCreateAPIView):
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Since request.user is already a Company object (from your authentication),
        we can use it directly
        """
        try:
            # request.user is already a Company object
            company = self.request.user
            print(f"DEBUG: Getting warehouses for company: {company.company_name}")
            return Warehouse.objects.filter(company=company).order_by('-created_at')
        except Exception as e:
            print(f"DEBUG Error in get_queryset: {e}")
            return Warehouse.objects.none()
    
    def perform_create(self, serializer):
        """
        Save warehouse with the authenticated company
        """
        try:
            # request.user is already the Company object
            company = self.request.user
            print(f"DEBUG: Creating warehouse for company: {company.company_name}")
            serializer.save(company=company)
        except Exception as e:
            print(f"DEBUG Error in perform_create: {e}")
            raise
    
    def list(self, request, *args, **kwargs):
        """
        Custom list response with company info
        """
        try:
            response = super().list(request, *args, **kwargs)
            company = request.user  # Already a Company object
            
            response.data = {
                "success": True,
                "company": {
                    "company_id": company.company_id,
                    "company_name": company.company_name,
                    "email": company.email,
                },
                "warehouses": response.data,
                "count": len(response.data),
                "timestamp": timezone.now().isoformat()
            }
            return response
        except Exception as e:
            print(f"DEBUG Error in list: {e}")
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'warehouse_id'
    
    def get_queryset(self):
        """
        Get warehouses for authenticated company
        """
        try:
            # request.user is Company object
            company = self.request.user
            return Warehouse.objects.filter(company=company)
        except:
            return Warehouse.objects.none()
    
    def get_object(self):
        """
        Get warehouse with permission check
        """
        queryset = self.get_queryset()
        warehouse_id = self.kwargs['warehouse_id']
        
        try:
            obj = queryset.get(warehouse_id=warehouse_id)
            print(f"DEBUG: Found warehouse: {obj.warehouse_name}")
            return obj
        except Warehouse.DoesNotExist:
            print(f"DEBUG: Warehouse {warehouse_id} not found")
            from django.http import Http404
            raise Http404("Warehouse not found or you don't have permission")
    
    def perform_update(self, serializer):
        """
        Update warehouse - company remains same
        """
        try:
            # Keep the same company (request.user is the company)
            company = self.request.user
            print(f"DEBUG: Updating warehouse for company: {company.company_name}")
            serializer.save(company=company)
        except Exception as e:
            print(f"DEBUG Error in perform_update: {e}")
            raise
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete warehouse with proper response
        """
        try:
            instance = self.get_object()
            warehouse_name = instance.warehouse_name
            company_name = instance.company.company_name
            
            self.perform_destroy(instance)
            
            print(f"DEBUG: Deleted warehouse '{warehouse_name}' from company '{company_name}'")
            
            return Response({
                "success": True,
                "message": f"Warehouse '{warehouse_name}' deleted successfully",
                "deleted_id": kwargs['warehouse_id'],
                "company": company_name,
                "timestamp": timezone.now().isoformat()
            })
            
        except Exception as e:
            print(f"DEBUG Error in destroy: {e}")
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# Additional warehouse views

class WarehouseCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            # request.user is Company object
            company = request.user
            count = Warehouse.objects.filter(company=company).count()
            
            return Response({
                "success": True,
                "company_id": company.company_id,
                "company_name": company.company_name,
                "warehouse_count": count,
                "timestamp": timezone.now().isoformat()
            })
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class WarehouseSearchView(generics.ListAPIView):
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            # request.user is Company object
            company = self.request.user
            queryset = Warehouse.objects.filter(company=company)
            
            # Search by name or address
            search_query = self.request.query_params.get('search', '')
            if search_query:
                queryset = queryset.filter(
                    warehouse_name__icontains=search_query
                ) | queryset.filter(
                    address__icontains=search_query
                )
            
            return queryset.order_by('-created_at')
        except Exception as e:
            print(f"DEBUG Error in search: {e}")
            return Warehouse.objects.none()
    
    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            company = request.user
            
            return Response({
                "success": True,
                "company": company.company_name,
                "search_results": response.data,
                "count": len(response.data),
                "search_query": request.query_params.get('search', ''),
                "timestamp": timezone.now().isoformat()
            })
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Bulk operations for warehouse
class WarehouseBulkDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request):
        """
        Delete multiple warehouses at once
        """
        try:
            warehouse_ids = request.data.get('warehouse_ids', [])
            
            if not warehouse_ids:
                return Response({
                    "success": False,
                    "error": "No warehouse IDs provided"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            company = request.user
            warehouses = Warehouse.objects.filter(
                warehouse_id__in=warehouse_ids,
                company=company
            )
            
            count = warehouses.count()
            
            if count == 0:
                return Response({
                    "success": False,
                    "error": "No warehouses found to delete"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get names before deleting
            warehouse_names = list(warehouses.values_list('warehouse_name', flat=True))
            
            # Delete warehouses
            warehouses.delete()
            
            return Response({
                "success": True,
                "message": f"Deleted {count} warehouse(s)",
                "deleted_count": count,
                "deleted_names": warehouse_names,
                "company": company.company_name,
                "timestamp": timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# Debug view to check authentication
class DebugAuthInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Debug endpoint to check what request.user contains
        """
        user = request.user
        
        data = {
            "success": True,
            "authentication_info": {
                "user_type": str(type(user)),
                "is_authenticated": request.user.is_authenticated,
                "user_id": getattr(user, 'id', None),
                "company_id": getattr(user, 'company_id', None),
                "company_name": getattr(user, 'company_name', None),
                "email": getattr(user, 'email', None),
                "attributes": [attr for attr in dir(user) if not attr.startswith('_')][:15]
            },
            "request_info": {
                "method": request.method,
                "content_type": request.content_type,
                "has_auth_header": 'Authorization' in request.headers,
                "user_agent": request.META.get('HTTP_USER_AGENT', '')
            }
        }
        
        # Check if it's a Company object
        if hasattr(user, 'company_name'):
            data["authentication_info"]["object_type"] = "Company"
            data["authentication_info"]["warehouse_count"] = Warehouse.objects.filter(company=user).count()
        
        return Response(data)




# Employee Authentication Views
# views.py में EmployeeLoginView

class EmployeeLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        print("="*50)
        print("EMPLOYEE LOGIN REQUEST RECEIVED")
        print("Data:", request.data)
        print("="*50)
        
        serializer = EmployeeLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                validated_data = serializer.validated_data
                
                # ✅ Employee object लें
                employee = validated_data.get('employee_object')
                
                if not employee:
                    return Response({
                        'success': False,
                        'error': 'Employee object not found in response'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                print(f"DEBUG: Employee login successful - {employee.full_name}")
                
                # Track login history
                EmployeeLoginHistory.objects.create(
                    employee=employee,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=True
                )
                
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'tokens': {
                        'refresh': validated_data.get('refresh'),
                        'access': validated_data.get('access')
                    },
                    'employee': validated_data.get('employee_data', {}),
                    'company': validated_data.get('company_data', {})
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                print(f"DEBUG: Employee login processing error: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        print("DEBUG: Employee login validation failed")
        print("Errors:", serializer.errors)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class EmployeeProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Get employee profile - Requires employee token
        """
        # Get employee from token or request
        try:
            # This needs custom authentication to get employee from token
            # For now, get from email in token
            email = request.user.email
            employee = Employee.objects.get(email=email, is_active=True)
            
            return Response({
                'success': True,
                'employee': EmployeeProfileSerializer(employee).data
            })
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class EmployeeChangePasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Custom validation for employee
        email = request.data.get('email')
        company_id = request.data.get('company_id')
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Manual validation
        if not all([email, company_id, old_password, new_password, confirm_password]):
            return Response({
                'success': False,
                'error': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                'success': False,
                'error': 'New passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password == old_password:
            return Response({
                'success': False,
                'error': 'New password must be different from old password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            employee = Employee.objects.get(
                email=email,
                company_id=company_id,
                is_active=True
            )
            
            if not employee.check_password(old_password):
                return Response({
                    'success': False,
                    'error': 'Old password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            employee.set_password(new_password)
            employee.save()
            
            return Response({
                'success': True,
                'message': 'Password changed successfully'
            })
            
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class EmployeeDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Employee dashboard with stats based on role
        """
        try:
            # Get employee
            email = request.user.email
            employee = Employee.objects.get(email=email, is_active=True)
            
            # Basic employee info
            employee_data = EmployeeProfileSerializer(employee).data
            
            # Role-based dashboard data
            dashboard_data = {
                'employee': employee_data,
                'company': {
                    'company_id': employee.company.company_id,
                    'company_name': employee.company.company_name,
                },
                'stats': {}
            }
            
            # Add role-specific data
            if employee.role in ['admin', 'manager']:
                # Managers can see employee count
                total_employees = Employee.objects.filter(
                    company=employee.company,
                    is_active=True
                ).count()
                dashboard_data['stats']['total_employees'] = total_employees
            
            # Add warehouse count if applicable
            if employee.role in ['admin', 'manager', 'supervisor']:
                warehouse_count = Warehouse.objects.filter(
                    company=employee.company
                ).count()
                dashboard_data['stats']['warehouse_count'] = warehouse_count
            
            return Response({
                'success': True,
                'dashboard': dashboard_data
            })
            
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
# Simplified version for both company and employee
from datetime import timedelta

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        identifier = (
            request.data.get('email_or_mobile')
            or request.data.get('email')
            or request.data.get('mobile')
        )

        if not identifier:
            return Response({
                'success': False,
                'error': 'Email or mobile number is required'
            }, status=400)

        identifier = str(identifier).strip()
        is_email = '@' in identifier

        company = None

        if is_email:
            company = Company.objects.filter(email=identifier).first()
            if not company:
                employee = Employee.objects.filter(email=identifier, is_active=True).first()
                if employee:
                    company = employee.company
        else:
            mobile = identifier.replace(' ', '')
            if mobile.startswith('+91'):
                mobile = mobile[3:]
            company = Company.objects.filter(mobile=mobile).first()
            if not company:
                employee = Employee.objects.filter(mobile=mobile, is_active=True).first()
                if employee:
                    company = employee.company
            identifier = mobile  # normalize

        if not company:
            return Response({
                'success': False,
                'error': 'No account found with this email/mobile'
            }, status=404)

        otp = str(random.randint(100000, 999999))

        print("\n" + "🔑"*20)
        print("🔑 FORGOT PASSWORD OTP")
        if is_email:
            print(f"📧 EMAIL: {identifier}")
        else:
            print(f"📱 MOBILE: {identifier}")
        print(f"🏢 COMPANY: {company.company_name if company else 'Employee Account'}")
        print(f"🔢 OTP: {otp}")
        print("🔑"*20 + "\n")

        from django.utils import timezone
        token = PasswordResetToken.objects.create(
            company=company,
            email=identifier,  # NOTE: yahan mobile bhi store kar rahe hain (simple approach)
            expires_at=timezone.now() + timedelta(hours=24)
        )

        reset_link = f"http://localhost:5173/reset-password/{token.token}/"

        return Response({
            'success': True,
            'message': 'OTP generated (check console)',
            'debug_link': reset_link,
            'otp': otp,
            'reset_token': str(token.token),
        })
    
class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not all([token, new_password]):
            return Response({
                'success': False,
                'error': 'Token and new password required'
            }, status=400)
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if reset_token.used or not reset_token.is_valid():
                return Response({
                    'success': False,
                    'error': 'Invalid or expired token'
                }, status=400)
            
            identifier = reset_token.email  # can be email OR mobile
            user_type = reset_token.user_type
            print(f"\n🔑 RESET PASSWORD REQUEST")
            print(f"🆔 Identifier: {identifier}")
            print(f"👤 User type: {user_type}")
            print(f"🏢 Company: {reset_token.company}")

            # COMPANY USER
            if user_type == "company":
                user = Company.objects.filter(email=identifier).first()
                if not user:
                    user = Company.objects.filter(mobile=identifier).first()

                if user:
                    user.set_password(new_password)
                    user.save()
                    print(f"✅ Company password reset: {user.company_name}")
                else:
                    return Response({
                        'success': False, 
                        'error': 'Company not found'
                    }, status=404)

            # EMPLOYEE USER
            elif user_type == "employee":
                employee = Employee.objects.filter(email=identifier, is_active=True).first()
                if not employee:
                    employee = Employee.objects.filter(mobile=identifier, is_active=True).first()

                if not employee:
                    return Response({
                        'success': False, 
                        'error': 'Employee not found'
                    }, status=404)

                # Check if employee belongs to the correct company (optional warning)
                if employee.company != reset_token.company:
                    print(f"⚠️ Warning: Employee {identifier} doesn't belong to company {reset_token.company}")

                employee.set_password(new_password)
                employee.save()
                print(f"✅ Employee password reset: {employee.full_name}")

            # INVALID USER TYPE
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid user type'
                }, status=400)
            
            # Mark token as used
            reset_token.used = True
            reset_token.save()
            
            return Response({
                'success': True,
                'message': 'Password reset successful'
            })
            
        except PasswordResetToken.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid token'
            }, status=400)
        except Exception as e:
            print(f"❌ Reset password error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


# views.py में नया view add करें (अन्य views के साथ)
from .serializers import OTPSerializer  # या नया serializer बनाएं

class VerifyForgotPasswordOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        print("="*50)
        print("VERIFY FORGOT PASSWORD OTP REQUEST")
        print("Data:", request.data)
        print("="*50)
        
        identifier = request.data.get('email_or_mobile')
        otp = request.data.get('otp')

        if not identifier or not otp:
            return Response({
                'success': False,
                'error': 'Email/Mobile and OTP are required'
            }, status=400)

        identifier = str(identifier).strip()
        is_email = '@' in identifier

        # ✅ TERMINAL पर PRINT करें
        print("\n" + "🔑"*20)
        print("🔑 VERIFY FORGOT PASSWORD OTP")
        if is_email:
            print(f"📧 EMAIL: {identifier}")
        else:
            print(f"📱 MOBILE: {identifier}")
        print(f"🔢 ENTERED OTP: {otp}")
        print("🔑"*20 + "\n")

        company = None
        user_type = "company"
        email = identifier if is_email else None

        if is_email:
            # Email के लिए search
            company = Company.objects.filter(email=identifier).first()
            if not company:
                employee = Employee.objects.filter(email=identifier, is_active=True).first()
                if employee:
                    company = employee.company
                    user_type = "employee"
                    print(f"✅ Found employee: {employee.full_name}, Company: {company.company_name}")
        else:
            # Mobile के लिए search
            mobile = identifier.replace(' ', '')
            if mobile.startswith('+91'):
                mobile = mobile[3:]
            
            company = Company.objects.filter(mobile=mobile).first()
            if not company:
                employee = Employee.objects.filter(mobile=mobile, is_active=True).first()
                if employee:
                    company = employee.company
                    user_type = "employee"
                    print(f"✅ Found employee: {employee.full_name}, Company: {company.company_name}")

        if not company:
            return Response({
                'success': False,
                'error': 'No account found with this email/mobile'
            }, status=404)

        print(f"✅ User type: {user_type}, Company: {company.company_name}")
        
        # ✅ OTP validation
        if len(str(otp)) != 6 or not str(otp).isdigit():
            return Response({
                'success': False,
                'error': 'Invalid OTP format. Must be 6 digits.'
            }, status=400)
        
        # ✅ यहाँ actual OTP verification logic add करें
        # उदाहरण:
        # stored_otp = cache.get(f'forgot_otp_{identifier}')
        # if str(otp) != str(stored_otp):
        #     return Response({'success': False, 'error': 'Invalid OTP'}, status=400)
        
        try:
            # Generate reset token
            token = PasswordResetToken.objects.create(
                company=company,
                email=identifier,
                user_type=user_type,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            
            print(f"✅ Reset token created: {token.token}")
            
            return Response({
                'success': True,
                'message': 'OTP verified successfully',
                'reset_token': token.token,
                'email_or_mobile': identifier,
                'user_type': user_type
            })
            
        except Exception as e:
            print(f"❌ Error creating reset token: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return Response({
                'success': False,
                'error': f'Failed to create reset token: {str(e)}'
            }, status=500)

class ResendForgotPasswordOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email_or_mobile')
        
        if not email:
            return Response({
                'success': False,
                'error': 'Email is required'
            }, status=400)
        
        # Generate new OTP
        otp = str(random.randint(100000, 999999))
        
        # ✅ TERMINAL पर PRINT करें
        print("\n" + "🔄"*20)
        print(f"🔄 RESEND FORGOT PASSWORD OTP")
        print(f"📧 EMAIL/MOBILE: {email}")
        print(f"🔢 NEW OTP: {otp}")
        print("🔄"*20 + "\n")
        
        return Response({
            'success': True,
            'message': 'OTP resent successfully',
            'email_or_mobile': email,
            'otp': otp  # Testing के लिए
        })  


## create modules



from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Item, Customer, Vendor, Employee, Vehicle,VendorOrderItem
from .serializers import (
    ItemSerializer, CustomerSerializer, 
    VendorSerializer, EmployeeSerializer, VehicleSerializer,VendorOrderItemSerializer
)
from .filters import ItemFilter, CustomerFilter, VendorFilter, EmployeeFilter, VehicleFilter,VendorOrderFilter

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ItemFilter
    search_fields = ['item_code', 'item_name', 'item_description', 'hsn_code']
    ordering_fields = ['item_code', 'item_name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Item.objects.filter(company=self.request.user)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user, created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def item_types(self, request):
        return Response(Item.ITEM_TYPES)



# Customer ViewSet - SABSE IMPORTANT
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CustomerFilter
    search_fields = ['customer_code', 'customer_name', 'gst_number', 'po_number', 'emails']
    ordering_fields = ['customer_code', 'customer_name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        # IMPORTANT: self.request.user Company object है
        # क्योंकि आपका AUTH_USER_MODEL = Company है
        user_company = self.request.user
        
        # CustomerContact के लिए prefetch_related करें
        return Customer.objects.filter(company=user_company).prefetch_related('customer_contact')

    def perform_create(self, serializer):
        # self.request.user Company object है
        serializer.save(company=self.request.user, created_by=self.request.user)


# Vendor ViewSet - SABSE IMPORTANT
class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VendorFilter
    search_fields = ['vendor_code', 'vendor_name', 'gst_number', 'emails', 'account_number', 'ifsc_code']
    ordering_fields = ['vendor_code', 'vendor_name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        # IMPORTANT: self.request.user Company object है
        user_company = self.request.user
        
        # VendorContact के लिए prefetch_related करें
        return Vendor.objects.filter(company=user_company).prefetch_related('vendor_contact')

    def perform_create(self, serializer):
        # self.request.user Company object है
        serializer.save(company=self.request.user, created_by=self.request.user)
# IMPORTANT: delete/remove this old EmployeeViewSet completely (it's broken and not needed for Create screen)


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VehicleFilter
    search_fields = ['vehicle_code', 'vehicle_name', 'vehicle_number']
    ordering_fields = ['vehicle_code', 'vehicle_name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Vehicle.objects.filter(company=self.request.user)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user, created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def expired_documents(self, request):
        from django.utils import timezone
        today = timezone.now().date()

        qs = self.get_queryset()
        expired_insurance = qs.filter(vehicle_insurance_expiry__lt=today, is_active=True)
        expired_pollution = qs.filter(pollution_cert_expiry__lt=today, is_active=True)

        return Response({
            'expired_insurance': VehicleSerializer(expired_insurance, many=True).data,
            'expired_pollution': VehicleSerializer(expired_pollution, many=True).data
        })

    @action(detail=False, methods=['get'])
    def upcoming_expiry_alerts(self, request):
        """API endpoint to list vehicles with documents expiring soon."""
        days_ahead = request.query_params.get('days', 7)
        try:
            days_ahead = int(days_ahead)
        except ValueError:
            days_ahead = 7

        target_date = timezone.now().date() + timedelta(days=days_ahead)
        vehicles = self.get_queryset().filter(
            vehicle_insurance_expiry=target_date
        ) | self.get_queryset().filter(
            pollution_cert_expiry=target_date
        )

        serializer = self.get_serializer(vehicles.distinct(), many=True)
        return Response(serializer.data)    

# views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import CreateEmployee
from .serializers import CreateEmployeeSerializer
from .permissions import IsSameCompany

class CreateEmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = CreateEmployeeSerializer
    permission_classes = [IsAuthenticated, IsSameCompany]

    def get_queryset(self):
        # Because request.user IS Company (AUTH_USER_MODEL = Company)
        return CreateEmployee.objects.filter(company=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user,
            created_by=self.request.user
        )
    
    def get_serializer_context(self):
        """
        Pass request context to serializer
        """
        context = super().get_serializer_context()
        context.update({
            'request': self.request
        })
        return context




# Pricing views के लिए views.py में जोड़ें

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import ItemPricing, CustomerPricing
from .serializers import ItemPricingSerializer, CustomerPricingSerializer

class ItemPricingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Item Pricing
    """
    serializer_class = ItemPricingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['item', 'year', 'month', 'is_active']
    search_fields = ['item__item_code', 'item__item_name']
    ordering_fields = ['year', 'month', 'item__item_name', 'created_at']
    ordering = ['-year', '-month']
    
    def get_queryset(self):
        # Only show pricings for user's company
        if self.request.user.is_authenticated:
            return ItemPricing.objects.filter(
                company=self.request.user
            ).select_related('item', 'company', 'created_by')
        return ItemPricing.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user,
            created_by=self.request.user
        )
    
    @action(detail=False, methods=['get'])
    def current_pricing(self, request):
        """
        Get current pricing for all items
        """
        from django.utils import timezone
        
        current_year = timezone.now().year
        current_month = timezone.now().month
        
        pricings = ItemPricing.objects.filter(
            company=request.user,
            year=current_year,
            month=current_month,
            is_active=True
        ).select_related('item')
        
        serializer = self.get_serializer(pricings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def item_history(self, request):
        """
        Get pricing history for a specific item
        """
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        history = ItemPricing.objects.filter(
            company=request.user,
            item_id=item_id
        ).order_by('-year', '-month')
        
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create multiple item pricings
        """
        pricings_data = request.data.get('pricings', [])
        if not isinstance(pricings_data, list):
            return Response(
                {'error': 'pricings should be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_pricings = []
        errors = []
        
        for idx, pricing_data in enumerate(pricings_data):
            try:
                # Add company and created_by to each pricing
                pricing_data['company'] = request.user.pk
                pricing_data['created_by'] = request.user.pk
                
                serializer = self.get_serializer(data=pricing_data)
                if serializer.is_valid():
                    pricing = serializer.save()
                    created_pricings.append(pricing)
                else:
                    errors.append({
                        'index': idx,
                        'data': pricing_data,
                        'errors': serializer.errors
                    })
            except Exception as e:
                errors.append({
                    'index': idx,
                    'data': pricing_data,
                    'error': str(e)
                })
        
        if errors:
            return Response({
                'created': len(created_pricings),
                'failed': len(errors),
                'errors': errors
            }, status=status.HTTP_207_MULTI_STATUS)
        
        return Response({
            'message': f'Successfully created {len(created_pricings)} pricings',
            'created': ItemPricingSerializer(created_pricings, many=True).data
        }, status=status.HTTP_201_CREATED)

class CustomerPricingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Customer Pricing (FIXED AMOUNT version)
    """
    serializer_class = CustomerPricingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'is_active']
    search_fields = ['customer__customer_code', 'customer__customer_name']
    ordering_fields = ['customer__customer_name', 'created_at', 'valid_from']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Only show pricings for user's company
        if self.request.user.is_authenticated:
            return CustomerPricing.objects.filter(
                company=self.request.user
            ).select_related('customer', 'company', 'created_by')
        return CustomerPricing.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user,
            created_by=self.request.user
        )
    
    @action(detail=False, methods=['get'])
    def active_customers(self, request):
        """
        Get active customer pricings
        """
        from django.utils import timezone
        
        today = timezone.now().date()
        pricings = CustomerPricing.objects.filter(
            company=request.user,
            is_active=True,
            valid_from__lte=today,
            valid_to__gte=today
        ).select_related('customer')
        
        serializer = self.get_serializer(pricings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_discount(self, request, pk=None):
        """
        Update only discount amount
        """
        pricing = self.get_object()
        discount_amount = request.data.get('discount_amount')
        
        if discount_amount is not None:
            try:
                discount_amount = float(discount_amount)
                if discount_amount < 0:
                    return Response(
                        {'error': 'Discount amount cannot be negative'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                pricing.discount_amount = discount_amount
                pricing.save()
                
                return Response(self.get_serializer(pricing).data)
            except ValueError:
                return Response(
                    {'error': 'Invalid discount amount'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': 'discount_amount is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['patch'])
    def update_commission(self, request, pk=None):
        """
        Update only sales commission amount
        """
        pricing = self.get_object()
        commission_amount = request.data.get('sales_commission_amount')
        
        if commission_amount is not None:
            try:
                commission_amount = float(commission_amount)
                if commission_amount < 0:
                    return Response(
                        {'error': 'Commission amount cannot be negative'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                pricing.sales_commission_amount = commission_amount
                pricing.save()
                
                return Response(self.get_serializer(pricing).data)
            except ValueError:
                return Response(
                    {'error': 'Invalid commission amount'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': 'sales_commission_amount is required'},
            status=status.HTTP_400_BAD_REQUEST
        )


# companies/views.py mein yeh view add karein

class EmployeeWarehouseListView(APIView):
    """
    Employee ke liye warehouse list
    Employee token se uska company pata karke uss company ke warehouses return karega
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            # Employee ka email auth token se lein
            user_email = request.user.email
            
            # 1. Pehle employee ko find karein
            employee = Employee.objects.filter(
                email=user_email, 
                is_active=True
            ).first()
            
            if not employee:
                # 2. Agar employee nahi mila, toh company check karein
                # (company login ke liye bhi kaam karega)
                company = Company.objects.filter(email=user_email, is_verified=True).first()
                if not company:
                    return Response({
                        'success': False,
                        'error': 'User not found or inactive'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Company ke warehouses
                warehouses = Warehouse.objects.filter(company=company)
            else:
                # Employee ki company ke warehouses
                warehouses = Warehouse.objects.filter(company=employee.company)
            
            serializer = WarehouseSerializer(warehouses, many=True)
            
            return Response({
                'success': True,
                'warehouses': serializer.data,
                'count': warehouses.count(),
                'is_employee': bool(employee),
                'company_id': employee.company.company_id if employee else company.company_id,
                'company_name': employee.company.company_name if employee else company.company_name
            })
            
        except Exception as e:
            print(f"Error in EmployeeWarehouseListView: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


# views.py में यह views add करें



class VendorOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Vendor Orders
    """
    serializer_class = VendorOrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VendorOrderFilter
    search_fields = ['order_number', 'invoice_number', 'vendor__vendor_name', 'cylinder_place']
    ordering_fields = ['created_at', 'invoice_date', 'total_amount', 'status']
    ordering = ['-created_at']
    
    
    def get_queryset(self):
        # Only show orders for user's company
        if self.request.user.is_authenticated:
            return VendorOrder.objects.filter(
                company=self.request.user
            ).select_related(
                'vendor', 'employee', 'warehouse', 'created_by'
            ).prefetch_related('order_items')
        return VendorOrder.objects.none()
    
    def perform_create(self, serializer):
        # Company and created_by are set in serializer
        order = serializer.save()
        # Apply stock impact immediately after creation (idempotent)
        self._apply_stock_changes(order)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a vendor order
        """
        order = self.get_object()
        
        if order.status not in ['draft', 'pending']:
            return Response({
                'success': False,
                'error': f'Order cannot be approved in {order.status} status.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'approved'
        order.approved_at = timezone.now()
        order.save()
        
        # Apply stock if not already applied
        self._apply_stock_changes(order)
        
        return Response({
            'success': True,
            'message': 'Order approved successfully.',
            'order': VendorOrderSerializer(order).data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark order as completed
        """
        order = self.get_object()
        
        if order.status != 'approved':
            return Response({
                'success': False,
                'error': f'Only approved orders can be completed.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()
        
        # Ensure stock is applied
        self._apply_stock_changes(order)
        
        return Response({
            'success': True,
            'message': 'Order marked as completed.',
            'order': VendorOrderSerializer(order).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a vendor order
        """
        order = self.get_object()
        
        if order.status not in ['draft', 'pending', 'approved']:
            return Response({
                'success': False,
                'error': f'Order cannot be cancelled in {order.status} status.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'cancelled'
        order.save()
        
        return Response({
            'success': True,
            'message': 'Order cancelled successfully.',
            'order': VendorOrderSerializer(order).data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get vendor order statistics
        """
        company = request.user
        queryset = self.get_queryset()
        
        total_orders = queryset.count()
        total_amount = queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        status_counts = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        monthly_stats = queryset.filter(
            created_at__year=timezone.now().year
        ).values('created_at__month').annotate(
            count=Count('id'),
            amount=Sum('total_amount')
        ).order_by('created_at__month')
        
        return Response({
            'success': True,
            'stats': {
                'total_orders': total_orders,
                'total_amount': total_amount,
                'status_counts': list(status_counts),
                'monthly_stats': list(monthly_stats),
            }
        })
    
    @action(detail=False, methods=['get'])
    def by_vendor(self, request):
        """
        Get orders grouped by vendor
        """
        company = request.user
        vendor_id = request.query_params.get('vendor_id')
        
        if vendor_id:
            orders = VendorOrder.objects.filter(
                company=company,
                vendor_id=vendor_id
            ).order_by('-created_at')
        else:
            # Group by vendor
            vendors = Vendor.objects.filter(company=company)
            result = []
            
            for vendor in vendors:
                vendor_orders = VendorOrder.objects.filter(
                    company=company,
                    vendor=vendor
                )
                
                total_orders = vendor_orders.count()
                total_amount = vendor_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
                
                result.append({
                    'vendor': {
                        'id': vendor.id,
                        'vendor_code': vendor.vendor_code,
                        'vendor_name': vendor.vendor_name,
                    },
                    'total_orders': total_orders,
                    'total_amount': total_amount,
                    'orders': VendorOrderSerializer(vendor_orders[:5], many=True).data
                })
            
            return Response({
                'success': True,
                'vendors': result
            })
        
        serializer = self.get_serializer(orders, many=True)
        return Response({
            'success': True,
            'orders': serializer.data
        })

    # ---------------- Internal helpers ----------------
    def _apply_stock_changes(self, order):
        """
        Apply stock adjustments for a vendor order based on load_type.
        Idempotent per order+item via reference_number check.
        """
        load_type = order.load_type
        for item in order.order_items.all():
            # Skip if already applied for this order+item
            if StockTransaction.objects.filter(
                reference_number=order.order_number,
                reference_type='vendor_order',
                item=item.item
            ).exists():
                continue

            qty = Decimal(item.quantity or 0)
            empty_cyl = Decimal(item.empty_cylinders or 0)

            delta_physical = Decimal('0')
            delta_empty = Decimal('0')

            if load_type == 'emr':
                # Incoming filled stock
                delta_physical = qty
            elif load_type == 'empty':
                # Sending out physical stock
                delta_physical = -qty
            elif load_type == 'refill':
                # Refill cycle:
                # Total cylinders same; only movement from Physical -> With Customers
                # Example: qty=30, empty_returned=20 => with_customers +10, physical -10
                empty_with_customer = qty - empty_cyl
                delta_physical = -empty_with_customer
                delta_empty = empty_with_customer
            # Other load types can be extended later

            # Get or create stock record
            stock, _ = Stock.objects.get_or_create(
                company=order.company,
                item=item.item,
                defaults={
                    'physical_stock': Decimal('0'),
                    'empty_with_customers': Decimal('0')
                }
            )

            new_physical = stock.physical_stock + delta_physical
            new_empty = stock.empty_with_customers + delta_empty

            # Prevent negative physical stock
            if new_physical < 0:
                raise ValidationError(
                    {'stock': f'Insufficient physical stock for item {item.item_name}.'}
                )

            previous_physical = stock.physical_stock
            previous_empty = stock.empty_with_customers

            stock.physical_stock = new_physical
            stock.empty_with_customers = new_empty
            stock.save()

            StockTransaction.objects.create(
                company=order.company,
                stock=stock,
                item=item.item,
                transaction_type='VENDOR_ORDER',
                previous_physical_stock=previous_physical,
                previous_empty_customers=previous_empty,
                new_physical_stock=new_physical,
                new_empty_customers=new_empty,
                quantity=qty,
                reference_number=order.order_number,
                reference_type='vendor_order',
                notes=f'Vendor order {order.order_number} ({load_type})',
                created_by=order.created_by
            )


class VendorOrderItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Vendor Order Items (separate from order)
    """
    serializer_class = VendorOrderItemSerializer
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return VendorOrderItem.objects.filter(
                order__company=self.request.user
            ).select_related('order', 'item')
        return VendorOrderItem.objects.none()
    
    def perform_create(self, serializer):
        # Validate that order belongs to user's company
        order = serializer.validated_data.get('order')
        if order.company != self.request.user:
            raise serializers.ValidationError({
                'order': 'Invalid order.'
            })
        
        # Validate order is editable
        if not order.is_editable:
            raise serializers.ValidationError({
                'order': 'Cannot add items to order in current status.'
            })
        
        serializer.save()
    
    def perform_update(self, serializer):
        instance = self.get_object()
        
        # Validate order is editable
        if not instance.order.is_editable:
            raise serializers.ValidationError({
                'order': 'Cannot update items for order in current status.'
            })
        
        serializer.save()
    
    def perform_destroy(self, instance):
        # Validate order is editable
        if not instance.order.is_editable:
            raise serializers.ValidationError({
                'order': 'Cannot delete items from order in current status.'
            })
        
        super().perform_destroy(instance)




# views.py में VendorOrderViewSet के बाद जोड़ें

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from decimal import Decimal
from .models import Stock, StockTransaction
from .serializers import (
    StockSerializer, StockTransactionSerializer,
    StockUpdateSerializer, StockTransactionCreateSerializer,
    StockStatsSerializer
)

class StockViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Stock
    """
    serializer_class = StockSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['item', 'item__item_type']
    search_fields = ['item__item_code', 'item__item_name']
    ordering_fields = ['physical_stock', 'empty_with_customers', 'last_updated']
    ordering = ['-last_updated']
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Stock.objects.filter(
                company=self.request.user
            ).select_related('item', 'company')
        return Stock.objects.none()
    
    def perform_create(self, serializer):
        # Stock creation is handled by stock transactions
        serializer.save(company=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get stock statistics
        """
        stocks = self.get_queryset()
        
        # Calculate totals
        total_items = stocks.count()
        total_physical_stock = stocks.aggregate(
            total=Sum('physical_stock')
        )['total'] or Decimal('0')
        
        total_empty_with_customers = stocks.aggregate(
            total=Sum('empty_with_customers')
        )['total'] or Decimal('0')
        
        total_overall_stock = total_physical_stock + total_empty_with_customers
        
        # Calculate stock status counts
        out_of_stock_items = stocks.filter(physical_stock=0).count()
        very_low_stock_items = stocks.filter(
            physical_stock__gt=0,
            physical_stock__lt=20
        ).count()
        
        low_stock_items = stocks.filter(
            physical_stock__gte=20,
            physical_stock__lt=50
        ).count()
        
        high_pending_items = stocks.filter(
            empty_with_customers__gt=100
        ).count()
        
        # Get lists for each category
        out_of_stock_list = stocks.filter(physical_stock=0)
        very_low_stock_list = stocks.filter(
            physical_stock__gt=0,
            physical_stock__lt=20
        )
        low_stock_list = stocks.filter(
            physical_stock__gte=20,
            physical_stock__lt=50
        )
        high_pending_list = stocks.filter(
            empty_with_customers__gt=100
        )
        
        data = {
            'total_items': total_items,
            'total_physical_stock': total_physical_stock,
            'total_empty_with_customers': total_empty_with_customers,
            'total_overall_stock': total_overall_stock,
            'out_of_stock_items': out_of_stock_items,
            'very_low_stock_items': very_low_stock_items,
            'low_stock_items': low_stock_items,
            'high_pending_items': high_pending_items,
            'out_of_stock_list': StockSerializer(out_of_stock_list, many=True).data,
            'very_low_stock_list': StockSerializer(very_low_stock_list, many=True).data,
            'low_stock_list': StockSerializer(low_stock_list, many=True).data,
            'high_pending_list': StockSerializer(high_pending_list, many=True).data,
        }
        
        serializer = StockStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """
        Get low stock items (physical stock < 50)
        """
        stocks = self.get_queryset().filter(
            Q(physical_stock__lt=50)
        ).order_by('physical_stock')
        
        serializer = self.get_serializer(stocks, many=True)
        return Response({
            'success': True,
            'count': stocks.count(),
            'stocks': serializer.data
        })
    
    @action(detail=True, methods=['put'])
    def update_stock(self, request, pk=None):
        """
        Manual stock update
        """
        stock = self.get_object()
        
        serializer = StockUpdateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            item = serializer.validated_data.get('item')
            
            # Verify item matches stock item
            if item != stock.item:
                return Response({
                    'success': False,
                    'error': 'Item mismatch'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save previous values
            previous_physical_stock = stock.physical_stock
            previous_empty_customers = stock.empty_with_customers
            
            # Update stock
            stock.physical_stock = serializer.validated_data.get('physical_stock')
            stock.empty_with_customers = serializer.validated_data.get('empty_with_customers')
            stock.save()
            
            # Create transaction record
            StockTransaction.objects.create(
                company=request.user,
                stock=stock,
                item=stock.item,
                transaction_type='MANUAL_ADJUSTMENT',
                previous_physical_stock=previous_physical_stock,
                previous_empty_customers=previous_empty_customers,
                new_physical_stock=stock.physical_stock,
                new_empty_customers=stock.empty_with_customers,
                quantity=abs(stock.physical_stock - previous_physical_stock),
                notes=serializer.validated_data.get('notes', 'Manual stock adjustment'),
                created_by=request.user
            )
            
            return Response({
                'success': True,
                'message': 'Stock updated successfully',
                'stock': StockSerializer(stock).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StockTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Stock Transactions
    """
    serializer_class = StockTransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['item', 'transaction_type', 'reference_type']
    search_fields = ['item__item_code', 'item__item_name', 'reference_number', 'notes']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return StockTransaction.objects.filter(
                company=self.request.user
            ).select_related('item', 'stock', 'company', 'created_by')
        return StockTransaction.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StockTransactionCreateSerializer
        return StockTransactionSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                transaction = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Transaction recorded successfully',
                    'transaction': StockTransactionSerializer(transaction).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_item(self, request):
        """
        Get transactions for a specific item
        """
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response({
                'success': False,
                'error': 'item_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            transactions = self.get_queryset().filter(item_id=item_id)
            serializer = self.get_serializer(transactions, many=True)
            
            # Get item details
            from .models import Item
            item = Item.objects.filter(
                id=item_id,
                company=request.user
            ).first()
            
            # Get current stock
            stock = Stock.objects.filter(
                company=request.user,
                item_id=item_id
            ).first()
            
            return Response({
                'success': True,
                'item': {
                    'id': item.id if item else None,
                    'item_code': item.item_code if item else None,
                    'item_name': item.item_name if item else None,
                },
                'current_stock': StockSerializer(stock).data if stock else None,
                'transactions': serializer.data,
                'count': transactions.count()
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get transaction summary by type and date range
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Date filters
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        transactions = self.get_queryset().filter(
            created_at__gte=start_date
        )
        
        # Summary by transaction type
        type_summary = transactions.values('transaction_type').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('-count')
        
        # Summary by item
        item_summary = transactions.values(
            'item__item_code',
            'item__item_name'
        ).annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:10]
        
        # Daily summary
        daily_summary = transactions.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('date')
        
        return Response({
            'success': True,
            'summary': {
                'total_transactions': transactions.count(),
                'total_quantity': transactions.aggregate(total=Sum('quantity'))['total'] or 0,
                'by_type': list(type_summary),
                'top_items': list(item_summary),
                'daily_summary': list(daily_summary),
                'date_range': {
                    'start_date': start_date.date(),
                    'end_date': timezone.now().date(),
                    'days': days
                }
            }
        })


class StockDashboardAPIView(APIView):
    """
    API for stock dashboard data
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user
        
        # Get stocks
        stocks = Stock.objects.filter(company=company).select_related('item')
        
        # Calculate statistics
        total_items = stocks.count()
        total_physical_stock = stocks.aggregate(
            total=Sum('physical_stock')
        )['total'] or Decimal('0')
        
        total_empty_with_customers = stocks.aggregate(
            total=Sum('empty_with_customers')
        )['total'] or Decimal('0')
        
        total_overall_stock = total_physical_stock + total_empty_with_customers
        
        # Stock status counts
        stock_status = {
            'out_of_stock': stocks.filter(physical_stock=0).count(),
            'very_low': stocks.filter(
                physical_stock__gt=0,
                physical_stock__lt=20
            ).count(),
            'low': stocks.filter(
                physical_stock__gte=20,
                physical_stock__lt=50
            ).count(),
            'high_pending': stocks.filter(
                empty_with_customers__gt=100
            ).count(),
            'normal': stocks.filter(
                physical_stock__gte=50,
                empty_with_customers__lte=100
            ).count()
        }
        
        # Recent transactions
        recent_transactions = StockTransaction.objects.filter(
            company=company
        ).select_related('item', 'created_by')[:10]
        
        # Low stock alerts
        low_stock_items = stocks.filter(
            Q(physical_stock__lt=50) | Q(physical_stock=0)
        ).order_by('physical_stock')[:5]
        
        # High pending alerts
        high_pending_items = stocks.filter(
            empty_with_customers__gt=100
        ).order_by('-empty_with_customers')[:5]
        
        return Response({
            'success': True,
            'dashboard': {
                'stats': {
                    'total_items': total_items,
                    'total_physical_stock': total_physical_stock,
                    'total_empty_with_customers': total_empty_with_customers,
                    'total_overall_stock': total_overall_stock,
                    'stock_status': stock_status
                },
                'recent_transactions': StockTransactionSerializer(recent_transactions, many=True).data,
                'alerts': {
                    'low_stock_items': StockSerializer(low_stock_items, many=True).data,
                    'high_pending_items': StockSerializer(high_pending_items, many=True).data,
                    'total_alerts': low_stock_items.count() + high_pending_items.count()
                },
                'company_info': {
                    'company_id': company.company_id,
                    'company_name': company.company_name
                }
            }
        })


class InitializeStockAPIView(APIView):
    """
    API to initialize stock for all items (if not exists)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        company = request.user
        
        # Get all items for company
        items = Item.objects.filter(company=company, is_active=True)
        
        created_count = 0
        updated_count = 0
        
        for item in items:
            # Check if stock exists
            stock_exists = Stock.objects.filter(
                company=company,
                item=item
            ).exists()
            
            if not stock_exists:
                # Create initial stock
                Stock.objects.create(
                    company=company,
                    item=item,
                    physical_stock=100,  # Default initial stock
                    empty_with_customers=0
                )
                created_count += 1
            else:
                updated_count += 1
        
        return Response({
            'success': True,
            'message': f'Stock initialized for {items.count()} items',
            'details': {
                'total_items': items.count(),
                'stocks_created': created_count,
                'stocks_already_exist': updated_count
            }
        })