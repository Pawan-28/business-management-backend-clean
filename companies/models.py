from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


class CompanyManager(BaseUserManager):
    def create_company(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        
        email = self.normalize_email(email)
        company = self.model(email=email, **extra_fields)
        
        if password:
            company.set_password(password)
        
        company.save(using=self._db)
        return company
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        
        return self.create_company(email, password, **extra_fields)

class Company(AbstractBaseUser, PermissionsMixin):
    # Basic Company Information
    company_id = models.AutoField(primary_key=True)
    company_name = models.CharField(max_length=255, verbose_name="Company Name")
    registration_number = models.CharField(max_length=50, unique=True, verbose_name="Registration Number")
    
    # GST Information
    gst_number = models.CharField(
        max_length=15, 
        unique=True, 
        verbose_name="GST Number",
        validators=[
            RegexValidator(
                regex='^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$',
                message='Enter a valid GST number'
            )
        ]
    )
    
    # Contact Information
    email = models.EmailField(unique=True, verbose_name="Email Address")
    mobile = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Mobile Number",
        validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message='Enter a valid 10-digit mobile number'
            )
        ]
    )
    alternate_mobile = models.CharField(max_length=10, blank=True, null=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, verbose_name="Address Line 1")
    address_line2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Address Line 2")
    city = models.CharField(max_length=100, verbose_name="City")
    state = models.CharField(max_length=100, verbose_name="State")
    pincode = models.CharField(max_length=6, verbose_name="Pincode")
    country = models.CharField(max_length=100, default="India", verbose_name="Country")
    
    # Business Information
    BUSINESS_TYPES = [
        ('essential', 'Essential'),
        ('non_essential', 'Non-Essential'),
        ('services', 'Services'),
        ('manufacturing', 'Manufacturing'),
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('other', 'Other'),
    ]
    
    business_type = models.CharField(
        max_length=50, 
        choices=BUSINESS_TYPES, 
        verbose_name="Business Type"
    )
    business_subtype = models.CharField(max_length=100, verbose_name="Business Subtype")
    
    # Company Details
    website = models.URLField(blank=True, null=True, verbose_name="Website")
    industry = models.CharField(max_length=100, blank=True, null=True, verbose_name="Industry")
    company_size = models.CharField(max_length=50, blank=True, null=True, verbose_name="Company Size")
    established_year = models.PositiveIntegerField(blank=True, null=True, verbose_name="Established Year")
    
    # Verification
    is_verified = models.BooleanField(default=False, verbose_name="Verified")
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    
    # Company Logo
    logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        verbose_name="Company Logo"
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name="Active")
    is_staff = models.BooleanField(default=False, verbose_name="Staff Status")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Login fields
    last_login = models.DateTimeField(blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['company_name', 'mobile', 'gst_number']
    
    objects = CompanyManager()
    
    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        db_table = 'companies'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['mobile']),
            models.Index(fields=['gst_number']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.company_name} ({self.company_id})"
    
    @property
    def full_address(self):
        address_parts = [self.address_line1]
        if self.address_line2:
            address_parts.append(self.address_line2)
        address_parts.extend([self.city, self.state, self.pincode, self.country])
        return ', '.join(filter(None, address_parts))
    
    


class Employee(models.Model):
    # ROLE_CHOICES = [
    #     ('admin', 'Administrator'),
    #     ('manager', 'Manager'),
    #     ('supervisor', 'Supervisor'),
    #     ('staff', 'Staff'),
    #     ('viewer', 'Viewer'),
    #     ('accountant', 'Accountant'),
    #     ('hr', 'HR Manager'),
    # ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('on_leave', 'On Leave'),
    ]
    
    # Basic Information
    employee_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='employees',
        verbose_name="Company"
    )
    employee_code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Employee Code"
    )
    
    # Personal Details
    full_name = models.CharField(max_length=255, verbose_name="Full Name")
    email = models.EmailField(verbose_name="Email Address")
    mobile = models.CharField(
        max_length=10,
        verbose_name="Mobile Number",
        validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message='Enter a valid 10-digit mobile number'
            )
        ]
    )
    
    # Job Details
    # role = models.CharField(
    #     max_length=50, 
    #     choices=ROLE_CHOICES, 
    #     verbose_name="Role",
    #     default='staff'
    # )
    # department = models.CharField(max_length=100, blank=True, null=True, verbose_name="Department")
    # designation = models.CharField(max_length=100, blank=True, null=True, verbose_name="Designation")
    # joining_date = models.DateField(verbose_name="Joining Date")
    
    # Employment Details
    # salary = models.DecimalField(
    #     max_digits=10, 
    #     decimal_places=2, 
    #     blank=True, 
    #     null=True, 
    #     verbose_name="Salary"
    # )
    employment_type = models.CharField(
        max_length=50,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('intern', 'Intern'),
        ],
        default='full_time',
        verbose_name="Employment Type"
    )
    
    # Authentication
    

    password = models.CharField(max_length=255, verbose_name="Password")
    temp_password = models.BooleanField(default=True, verbose_name="Temporary Password")
    last_password_change = models.DateTimeField(auto_now_add=True, verbose_name="Last Password Change")
    

    
    
    
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active',
        verbose_name="Status"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    # Additional Information
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    profile_picture = models.ImageField(
        upload_to='employee_profiles/',
        blank=True,
        null=True,
        verbose_name="Profile Picture"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True, verbose_name="Last Login")
    
    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        db_table = 'employees'
        unique_together = ['company', 'email']
        indexes = [
            models.Index(fields=['employee_code']),
            models.Index(fields=['email']),
            models.Index(fields=['company', 'status']),
            # models.Index(fields=['company', 'role']),
            # models.Index(fields=['joining_date']),
        ]
    
   
   
    
    def __str__(self):
        return f"{self.full_name} - {self.employee_code}"
    
    def generate_employee_code(self):
        """Generate unique employee code"""
        if self.employee_code:
            return
        
        company_prefix = self.company.company_name[:3].upper()
        last_employee = Employee.objects.filter(
            company=self.company
        ).order_by('employee_id').last()
        
        if last_employee:
            last_number = int(last_employee.employee_code[3:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        self.employee_code = f"{company_prefix}{new_number:03d}"
    
    def hash_password_if_needed(self):
        """Hash password if it's plain text"""
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
            self.temp_password = False
            self.last_password_change = timezone.now()
    
    def save(self, *args, **kwargs):
        # Generate employee code
        self.generate_employee_code()
        
        # Hash password if needed
        self.hash_password_if_needed()
        
        # Call parent save
        super().save(*args, **kwargs)
    
    def set_password(self, raw_password):
        """Set new password (explicitly)"""
        self.password = make_password(raw_password)
        self.temp_password = False
        self.last_password_change = timezone.now()
        self.save()
    
    def check_password(self, raw_password):
        """Check if password matches"""
        return check_password(raw_password, self.password)

class CompanySettings(models.Model):
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name="Company"
    )
    
    # General Settings
    timezone = models.CharField(max_length=50, default='Asia/Kolkata', verbose_name="Timezone")
    date_format = models.CharField(
        max_length=20,
        default='DD/MM/YYYY',
        choices=[
            ('DD/MM/YYYY', 'DD/MM/YYYY'),
            ('MM/DD/YYYY', 'MM/DD/YYYY'),
            ('YYYY-MM-DD', 'YYYY-MM-DD'),
        ],
        verbose_name="Date Format"
    )
    
    # Security Settings
    password_expiry_days = models.PositiveIntegerField(default=90, verbose_name="Password Expiry (Days)")
    max_login_attempts = models.PositiveIntegerField(default=5, verbose_name="Max Login Attempts")
    session_timeout = models.PositiveIntegerField(default=30, verbose_name="Session Timeout (Minutes)")
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True, verbose_name="Email Notifications")
    sms_notifications = models.BooleanField(default=True, verbose_name="SMS Notifications")
    push_notifications = models.BooleanField(default=True, verbose_name="Push Notifications")
    
    # Employee Settings
    auto_generate_password = models.BooleanField(default=True, verbose_name="Auto Generate Passwords")
    require_employee_activation = models.BooleanField(default=True, verbose_name="Require Employee Activation")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company Settings"
        verbose_name_plural = "Company Settings"
        db_table = 'company_settings'
    
    def __str__(self):
        return f"Settings for {self.company.company_name}"

class EmployeeLoginHistory(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='login_history',
        verbose_name="Employee"
    )
    login_time = models.DateTimeField(auto_now_add=True, verbose_name="Login Time")
    ip_address = models.GenericIPAddressField(verbose_name="IP Address")
    user_agent = models.TextField(verbose_name="User Agent")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Location")
    success = models.BooleanField(default=True, verbose_name="Login Successful")
    
    class Meta:
        verbose_name = "Employee Login History"
        verbose_name_plural = "Employee Login Histories"
        db_table = 'employee_login_history'
        indexes = [
            models.Index(fields=['employee', 'login_time']),
            models.Index(fields=['login_time']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.employee} - {self.login_time} ({status})"
    

#warehouse models 


#warehouse models 


class Warehouse(models.Model):
    warehouse_id = models.AutoField(primary_key=True)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="warehouses"
    )

    warehouse_name = models.CharField(max_length=255)
    address = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "warehouses"

    def __str__(self):
        return self.warehouse_name

# models.py में EmployeeLoginHistory class के बाद ADD करें

class PasswordResetToken(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name="Company",
        null=True,
        blank=True
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(verbose_name="Email Address")
    
    # ✅ User type field add करें
    user_type = models.CharField(
        max_length=20,
        choices=[('company', 'Company'), ('employee', 'Employee')],
        default='company',
        verbose_name="User Type"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=timezone.now)
    used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
        db_table = 'password_reset_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Reset token for {self.email} ({self.user_type})"
    
    def is_valid(self):
        from django.utils import timezone
        return not self.used and self.expires_at > timezone.now()
    


## create modules



from django.db import models
from django.contrib.auth import get_user_model
from .models import Company

User = get_user_model()
from django.core.validators import MinValueValidator, MaxValueValidator

class Item(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    ITEM_TYPES = [
        ('fuel', 'Fuel'),
        ('pipeline', 'Pipeline'),
        ('others', 'Others'),
    ]
    
    item_code = models.CharField(max_length=50, unique=True)
    item_name = models.CharField(max_length=200, unique=True)
    item_description = models.TextField(blank=True, null=True)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='others')
    hsn_code = models.CharField(max_length=50, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='items_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
    
    def __str__(self):
        return f"{self.item_code} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        if not self.item_code:
            prefix = "ITEM"
            company_part = str(self.company.company_id) if self.company else "0"

            if self.company:
                last_item = Item.objects.filter(company=self.company).order_by('-id').first()
            else:
                last_item = Item.objects.order_by('-id').first()

            new_num = 1
            if last_item and last_item.item_code:
                parts = last_item.item_code.split('-')
                try:
                    last_num = int(parts[-1])
                    new_num = last_num + 1
                except Exception:
                    new_num = 1

            self.item_code = f"{prefix}-{company_part}-{new_num:05d}"

        super().save(*args, **kwargs)

    


class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers', null=True, blank=True)
    customer_code = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200,unique=True )
    
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    po_number = models.CharField(max_length=100, blank=True, null=True)
    credit_days = models.IntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(365)])
    emails = models.TextField(blank=True, null=True, help_text="Separate multiple emails with ;")
    contact_persons = models.TextField(blank=True, null=True, help_text="Separate multiple person with ;")
    contact_numbers = models.TextField(blank=True, null=True, help_text="Separate multiple numbers with ;")
    send_price_email = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='customers_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


    
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f"{self.customer_code} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.customer_code:
            prefix = "CUST"
            company_part = str(self.company.company_id) if self.company else "0"

            if self.company:
                last_customer = Customer.objects.filter(company=self.company).order_by('-id').first()
            else:
                last_customer = Customer.objects.order_by('-id').first()

            new_num = 1
            if last_customer and last_customer.customer_code:
                parts = last_customer.customer_code.split('-')
                try:
                    last_num = int(parts[-1])
                    new_num = last_num + 1
                except Exception:
                    new_num = 1

            self.customer_code = f"{prefix}-{company_part}-{new_num:05d}"

        super().save(*args, **kwargs)
    
    def get_emails_list(self):
        if self.emails:
            return [email.strip() for email in self.emails.split(';') if email.strip()]
        return []


class CustomerContact(models.Model):
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_contact')
    contact_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'contact_name']
        verbose_name = 'Customer Contact'
        verbose_name_plural = 'Customer Contacts'
    
    def __str__(self):
        return f"{self.contact_name} - {self.customer.customer_name}"

    # def save(self, *args, **kwargs):
    #     if not self.customer_code:
    #         prefix = "CUST"
    #         if self.company:
    #             company_prefix = self.company.company_name[:3].upper()
    #             last_customer = Customer.objects.filter(company=self.company).order_by('-id').first()
    #         else:
    #             last_customer = Customer.objects.order_by('-id').first()    


class Vendor(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='vendors', null=True, blank=True)
    vendor_code = models.CharField(max_length=50, unique=True)
    
    vendor_name = models.CharField(max_length=200, unique=True)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    emails = models.TextField(blank=True, null=True, help_text="Separate multiple emails with ;")

    contact_persons=models.TextField(blank=True, null=True, help_text="Separate multiple person with ;")
    contact_numbers=models.TextField(blank=True, null=True, help_text="Separate multiple numbers with ;")
    account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_branch = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='vendors_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
    
    def __str__(self):
        return f"{self.vendor_code} - {self.vendor_name}"
    
    def save(self, *args, **kwargs):
        if not self.vendor_code:
            prefix = "VEND"
            company_part = str(self.company.company_id) if self.company else "0"

            if self.company:
                last_vendor = Vendor.objects.filter(company=self.company).order_by('-id').first()
            else:
                last_vendor = Vendor.objects.order_by('-id').first()

            new_num = 1
            if last_vendor and last_vendor.vendor_code:
                parts = last_vendor.vendor_code.split('-')
                try:
                    last_num = int(parts[-1])
                    new_num = last_num + 1
                except Exception:
                    new_num = 1

            self.vendor_code = f"{prefix}-{company_part}-{new_num:05d}"

        super().save(*args, **kwargs)


class VendorContact(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='vendor_contact')
    contact_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'contact_name']
        verbose_name = 'Vendor Contact'
        verbose_name_plural = 'Vendor Contacts'
    
    def __str__(self):
        return f"{self.contact_name} - {self.vendor.vendor_name}"




class Vehicle(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='vehicles', null=True, blank=True)
    vehicle_code = models.CharField(max_length=50, unique=True)
   
    vehicle_name = models.CharField(max_length=200)
    vehicle_number = models.CharField(max_length=50, unique=True)
    fc_expiry_date = models.DateField(blank=True, null=True)
    transit_insurance_expiry = models.DateField(blank=True, null=True)
    vehicle_insurance_expiry = models.DateField(blank=True, null=True)
    # road_tax_expiry = models.DateField(blank=True, null=True)
    road_tax = models.JSONField(
    default=list,
    blank=True,
    help_text="State-wise road tax expiry dates in format: [{'state': 'MH', 'expiry_date': '2024-12-31'}, ...]"
)
    state_permits = models.JSONField(
        default=list,
        blank=True,
        help_text="State-wise permits in format: [{'state': 'MH', 'expiry_date': '2024-12-31'}, ...]"
    )
    pollution_cert_expiry = models.DateField(blank=True, null=True)
    tn_permit_expiry = models.DateField(blank=True, null=True)
    ka_permit_expiry = models.DateField(blank=True, null=True)
    # National permit
    has_national_permit = models.BooleanField(default=False)
    national_permit_expiry = models.DateField(blank=True, null=True)

    # Notification / reminder settings (emails and SMS)
    notification_emails = models.TextField(
        blank=True,
        null=True,
        help_text="Separate multiple emails with ;"
    )
    notification_phone_numbers = models.TextField(
        blank=True,
        null=True,
        help_text="Separate multiple numbers with ;"
    )
    enable_7day_reminder = models.BooleanField(default=True)
    enable_3day_reminder = models.BooleanField(default=True)
    enable_expiry_day_reminder = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='vehicles_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
    
    def __str__(self):
        return f"{self.vehicle_code} - {self.vehicle_name} ({self.vehicle_number})"
    
    @property
    def is_insurance_expired(self):
        """
        Helper property for serializers:
        True when vehicle_insurance_expiry is in the past.
        """
        from django.utils import timezone
        if self.vehicle_insurance_expiry:
            return self.vehicle_insurance_expiry < timezone.now().date()
        return False

    @property
    def is_pollution_cert_expired(self):
        """
        Helper property for serializers:
        True when pollution_cert_expiry is in the past.
        """
        from django.utils import timezone
        if self.pollution_cert_expiry:
            return self.pollution_cert_expiry < timezone.now().date()
        return False

    def save(self, *args, **kwargs):
        if not self.vehicle_code:
            prefix = "VEH"
            company_part = str(self.company.company_id) if self.company else "0"

            if self.company:
                last_vehicle = Vehicle.objects.filter(company=self.company).order_by('-id').first()
            else:
                last_vehicle = Vehicle.objects.order_by('-id').first()

            new_num = 1
            if last_vehicle and last_vehicle.vehicle_code:
                parts = last_vehicle.vehicle_code.split('-')
                try:
                    last_num = int(parts[-1])
                    new_num = last_num + 1
                except Exception:
                    new_num = 1

            self.vehicle_code = f"{prefix}-{company_part}-{new_num:05d}"

        super().save(*args, **kwargs)


from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()

class CreateEmployee(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='created_employees'   # ✅ UNIQUE
    )


    DESIGNATION_CHOICES = [
        ('manager', 'Manager'),
        ('transporter', 'Transporter'),
        ('asst_manager', 'Assistant Manager'),
        ('driver', 'Driver'),
        ('md', 'MD'),
        ('other', 'Other'),
    ]

    employee_code = models.CharField(max_length=50)
    employee_name = models.CharField(max_length=200)
    designation = models.CharField(
        max_length=20,
        choices=DESIGNATION_CHOICES,
        default='manager'
    )

    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_branch = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)

    transport_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    dl_number = models.CharField(max_length=50, blank=True, null=True)
    dl_expiry_date = models.DateField(null=True, blank=True)
    hazardous_cert_number = models.CharField(max_length=100, blank=True, null=True)
    hazardous_license_expiry = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='employees_created'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'employee_code'],
                name='unique_employee_code_per_company'
            )
        ]

    def __str__(self):
        return f"{self.employee_code} - {self.employee_name}"

    def save(self, *args, **kwargs):
        if not self.company:
            raise ValueError("Company is required")

        if not self.employee_code:
            prefix = "EMP"
            company_emps = CreateEmployee.objects.filter(company=self.company)

            max_num = 0
            for emp in company_emps:
                if emp.employee_code and emp.employee_code.startswith(prefix):
                    try:
                        num = int(emp.employee_code.split('-')[-1])
                        max_num = max(max_num, num)
                    except:
                        pass

            self.employee_code = f"{prefix}-{max_num + 1:05d}"

        if self.designation != 'driver':
            self.transport_amount = None

        super().save(*args, **kwargs)



# Pricing models के लिए models.py में जोड़ें (Item और CreateEmployee के बाद)
# models.py में TOP पर import करें
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class ItemPricing(models.Model):
    """
    Item-specific pricing for different months and years
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='item_pricings',
        verbose_name="Company"
    )
    
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='pricings',
        verbose_name="Item"
    )
    
    year = models.PositiveIntegerField(
        verbose_name="Year",
        validators=[
            MinValueValidator(2000),
            MaxValueValidator(2100)
        ]
    )
    
    month = models.PositiveIntegerField(
        verbose_name="Month",
        choices=[
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ]
    )
    
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Purchase Price (₹)",
        validators=[MinValueValidator(0)]
    )
    
    mrp = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Maximum Retail Price (MRP) (₹)",
        validators=[MinValueValidator(0)]
    )
    
    # Status and audit
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    # ✅ इसे CHANGE करें (बहुत IMPORTANT!)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ❌ 'auth.User' की जगह ये USE करें ✅
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_item_pricings',
        verbose_name="Created By"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item Pricing"
        verbose_name_plural = "Item Pricings"
        db_table = 'item_pricing'
        ordering = ['-year', '-month', 'item']
        unique_together = ['company', 'item', 'year', 'month']
        indexes = [
            models.Index(fields=['company', 'item']),
            models.Index(fields=['year', 'month']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        month_name = dict(self._meta.get_field('month').choices).get(self.month, str(self.month))
        return f"{self.item.item_name} - {month_name} {self.year}"
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.purchase_price and self.mrp and self.purchase_price > 0:
            return ((self.mrp - self.purchase_price) / self.purchase_price) * 100
        return 0

class CustomerPricing(models.Model):
    """
    Customer-specific pricing (discount and commission)
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='customer_pricings',
        verbose_name="Company"
    )
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='pricings',
        verbose_name="Customer"
    )
    
    # ✅ FIXED AMOUNT (percentage नहीं)
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Discount Amount (₹)",
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Fixed discount amount in rupees"
    )
    
    # ✅ FIXED AMOUNT (percentage नहीं)
    sales_commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Sales Commission Amount (₹)",
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Fixed sales commission amount in rupees"
    )
    
    # Validity period
    valid_from = models.DateField(
        verbose_name="Valid From",
        null=True,
        blank=True
    )
    
    valid_to = models.DateField(
        verbose_name="Valid To",
        null=True,
        blank=True
    )
    
    # Status and audit
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    # ✅ इसे भी CHANGE करें (बहुत IMPORTANT!)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ❌ 'auth.User' की जगह ये USE करें ✅
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_customer_pricings',
        verbose_name="Created By"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Customer Pricing"
        verbose_name_plural = "Customer Pricings"
        db_table = 'customer_pricing'
        ordering = ['-created_at', 'customer']
        unique_together = ['company', 'customer']
        indexes = [
            models.Index(fields=['company', 'customer']),
            models.Index(fields=['valid_from', 'valid_to']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.customer.customer_name} - Discount: ₹{self.discount_amount}, Commission: ₹{self.sales_commission_amount}"
    
    @property
    def is_valid(self):
        """Check if pricing is currently valid"""
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.valid_from and self.valid_to:
            return self.valid_from <= today <= self.valid_to
        return True  # If no dates specified, always valid
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate date range
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValidationError({
                'valid_to': 'Valid To date must be after Valid From date.'
            })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)



## vendor-order models

# models.py  models add 

class VendorOrder(models.Model):
    """
    Vendor Orders (Vendor Purchase Orders)
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='vendor_orders',
        verbose_name="Company"
    )
    
    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Order Number"
    )
    
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name='vendor_orders',
        verbose_name="Vendor"
    )
    
    employee = models.ForeignKey(
        'CreateEmployee',  # Employee model use 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendor_orders',
        verbose_name="Employee"
    )
    
    invoice_number = models.CharField(
        max_length=100,
        verbose_name="Invoice Number"
    )
    
    invoice_date = models.DateField(
        verbose_name="Invoice Date"
    )
    
    LOAD_TYPE_CHOICES = [
        ('refill', 'Refill'),
        ('emr', 'EMR'),
        ('empty', 'Empty'),
        ('pipeline', 'Pipeline'),
        ('others', 'Others'),
    ]
    
    load_type = models.CharField(
        max_length=20,
        choices=LOAD_TYPE_CHOICES,
        default='refill',
        verbose_name="Load Type"
    )
    
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendor_orders',
        verbose_name="Warehouse"
    )
    
    cylinder_place = models.TextField(
        verbose_name="Cylinder Place/Address"
    )
    
    transport_required = models.BooleanField(
        default=False,
        verbose_name="Transport Required"
    )
    
    total_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Quantity"
    )
    
    total_empty_cylinders = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Empty Cylinders"
    )
    
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Total Amount"
    )
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Status"
    )
    
    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='vendor_orders_created',
        verbose_name="Created By"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Vendor Order"
        verbose_name_plural = "Vendor Orders"
        db_table = 'vendor_orders'
        ordering = ['-created_at']
        unique_together = [['company', 'invoice_number']]
        indexes = [
            models.Index(fields=['company', 'vendor']),
            models.Index(fields=['order_number']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.vendor.vendor_name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Auto-generate order number
            prefix = "VO"
            company_part = str(self.company.company_id) if self.company else "0"
            
            today = timezone.now()
            date_part = today.strftime('%y%m%d')
            
            last_order = VendorOrder.objects.filter(
                company=self.company
            ).order_by('-created_at').first()
            
            seq_num = 1
            if last_order and last_order.order_number:
                try:
                    last_seq = int(last_order.order_number.split('-')[-1])
                    seq_num = last_seq + 1
                except:
                    pass
            
            self.order_number = f"{prefix}-{company_part}-{date_part}-{seq_num:04d}"
        
        super().save(*args, **kwargs)
    
    def update_totals(self):
        """Update order totals from items"""
        items = self.order_items.all()
        self.total_quantity = sum(item.quantity for item in items)
        self.total_empty_cylinders = sum(item.empty_cylinders for item in items)
        self.total_amount = sum(item.total for item in items)
        self.save()
    
    @property
    def is_editable(self):
        """Check if order is editable"""
        return self.status in ['draft', 'pending']


class VendorOrderItem(models.Model):
    """
    Items in Vendor Order
    """
    order = models.ForeignKey(
        VendorOrder,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name="Order"
    )
    
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name='vendor_order_items',
        verbose_name="Item"
    )
    
    item_code = models.CharField(
        max_length=50,
        verbose_name="Item Code"
    )
    
    item_name = models.CharField(
        max_length=200,
        verbose_name="Item Name"
    )
    
    quantity = models.IntegerField(  # ✅ IntegerField use 
        verbose_name="Quantity",
        default=0,
        validators=[MinValueValidator(0)]  # Optional validation
    )
    
    empty_cylinders = models.IntegerField(  
        default=0,
        verbose_name="Empty Cylinders"
    )
    
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Price"
    )
    
    is_transport = models.BooleanField(
        default=False,
        verbose_name="Transport Included"
    )
    
    # Transport specific fields (if applicable)
    transport_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Transport Price"
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Total"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Vendor Order Item"
        verbose_name_plural = "Vendor Order Items"
        db_table = 'vendor_order_items'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calculate total
        if self.is_transport and self.transport_price > 0:
            # Transport price per unit
            self.total = self.quantity * self.transport_price
        else:
            self.total = self.quantity * self.price
        
        super().save(*args, **kwargs)
        
        # Update parent order totals
        self.order.update_totals()
    
    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.update_totals()

# models.py  VendorOrderItem class models add 
from decimal import Decimal
from django.core.validators import MinValueValidator

class Stock(models.Model):
    """
    Real-time stock tracking for items
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name="Company"
    )
    
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='item_stocks',
        verbose_name="Item"
    )
    
    # Stock levels
    physical_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Physical Stock"
    )
    
    empty_with_customers = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Empty Cylinders with Customers"
    )
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        db_table = 'stocks'
        unique_together = ['company', 'item']
        indexes = [
            models.Index(fields=['company', 'item']),
            models.Index(fields=['physical_stock']),
            models.Index(fields=['last_updated']),
        ]
    
    def __str__(self):
        return f"{self.item.item_name} - Physical: {self.physical_stock}, Empty: {self.empty_with_customers}"
    
    @property
    def total_stock(self):
        """Calculate total stock (physical + empty with customers)"""
        return self.physical_stock + self.empty_with_customers
    
    @property
    def stock_status(self):
        """Get stock status based on levels"""
        if self.physical_stock == 0:
            return 'out_of_stock'
        elif self.physical_stock < 20:
            return 'very_low'
        elif self.physical_stock < 50:
            return 'low'
        elif self.empty_with_customers > 100:
            return 'high_pending'
        else:
            return 'normal'
    
    def can_transaction(self, transaction_type, quantity):
        """
        Check if transaction is possible with current stock
        """
        quantity = Decimal(str(quantity))
        
        if transaction_type in ['REMOVE_STOCK', 'CUSTOMER_TAKE']:
            return self.physical_stock >= quantity
        elif transaction_type == 'CUSTOMER_RETURN':
            return self.empty_with_customers >= quantity
        elif transaction_type in ['ADD_STOCK', 'MANUAL_ADJUSTMENT']:
            return True
        
        return False
    
    def update_stock(self, transaction_type, quantity):
        """
        Update stock based on transaction type
        """
        quantity = Decimal(str(quantity))
        
        if transaction_type == 'ADD_STOCK':
            self.physical_stock += quantity
        elif transaction_type == 'REMOVE_STOCK':
            self.physical_stock -= quantity
        elif transaction_type == 'CUSTOMER_RETURN':
            self.physical_stock += quantity
            self.empty_with_customers -= quantity
        elif transaction_type == 'CUSTOMER_TAKE':
            self.physical_stock -= quantity
            self.empty_with_customers += quantity
        # MANUAL_ADJUSTMENT handled separately
        
        self.save()


class StockTransaction(models.Model):
    """
    Record of all stock transactions
    """
    TRANSACTION_TYPES = [
        ('ADD_STOCK', 'Add Physical Stock'),
        ('REMOVE_STOCK', 'Remove Physical Stock'),
        ('CUSTOMER_RETURN', 'Customer Returns Empty'),
        ('CUSTOMER_TAKE', 'Customer Takes Cylinders'),
        ('MANUAL_ADJUSTMENT', 'Manual Stock Adjustment'),
        ('VENDOR_ORDER', 'Vendor Order'),
        ('CUSTOMER_ORDER', 'Customer Order'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='company_stock_transactions',
        verbose_name="Company"
    )
    
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='stock_transactions',
        verbose_name="Stock",
        null=True,
        blank=True
    )
    
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='item_stock_transactions',
        verbose_name="Item"
    )
    
    transaction_type = models.CharField(
        max_length=50,
        choices=TRANSACTION_TYPES,
        verbose_name="Transaction Type"
    )
    
    # Stock levels before transaction
    previous_physical_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Previous Physical Stock"
    )
    
    previous_empty_customers = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Previous Empty with Customers"
    )
    
    # Stock levels after transaction
    new_physical_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="New Physical Stock"
    )
    
    new_empty_customers = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="New Empty with Customers"
    )
    
    # Transaction details
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantity"
    )
    
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Reference Number"
    )
    
    reference_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Reference Type"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    
    # Performed by
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_stock_transactions',
        verbose_name="Created By"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Stock Transaction"
        verbose_name_plural = "Stock Transactions"
        db_table = 'stock_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'item']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['reference_number']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.item.item_name} - {self.quantity}"
    
    @property
    def physical_stock_change(self):
        """Calculate change in physical stock"""
        return self.new_physical_stock - self.previous_physical_stock
    
    @property
    def empty_customers_change(self):
        """Calculate change in empty with customers"""
        return self.new_empty_customers - self.previous_empty_customers