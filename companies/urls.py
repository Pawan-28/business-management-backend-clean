from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'items', views.ItemViewSet, basename='item')
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'vendors', views.VendorViewSet, basename='vendor')
router.register(r'create-employees', views.CreateEmployeeViewSet, basename='createemployee')
router.register(r'vehicles', views.VehicleViewSet, basename='vehicle')

router.register(r'item-pricing', views.ItemPricingViewSet, basename='item-pricing')
router.register(r'customer-pricing', views.CustomerPricingViewSet, basename='customer-pricing')

router.register(r'vendor-orders', views.VendorOrderViewSet, basename='vendor-order')
router.register(r'vendor-order-items', views.VendorOrderItemViewSet, basename='vendor-order-item')

router.register(r'stocks', views.StockViewSet, basename='stock')
router.register(r'stock-transactions', views.StockTransactionViewSet, basename='stock-transaction')

urlpatterns = [
    

    ## create urls
     path('item-pricing/current/', 
         views.ItemPricingViewSet.as_view({'get': 'current_pricing'}), 
         name='item-pricing-current'),
    path('item-pricing/history/', 
         views.ItemPricingViewSet.as_view({'get': 'item_history'}), 
         name='item-pricing-history'),
    path('item-pricing/bulk-create/', 
         views.ItemPricingViewSet.as_view({'post': 'bulk_create'}), 
         name='item-pricing-bulk-create'),
    
    path('customer-pricing/active/', 
         views.CustomerPricingViewSet.as_view({'get': 'active_customers'}), 
         name='customer-pricing-active'),
    path('customer-pricing/<int:pk>/update-discount/', 
         views.CustomerPricingViewSet.as_view({'patch': 'update_discount'}), 
         name='customer-pricing-update-discount'),
    path('customer-pricing/<int:pk>/update-commission/', 
         views.CustomerPricingViewSet.as_view({'patch': 'update_commission'}), 
         name='customer-pricing-update-commission'),
    
      
   path('', include(router.urls)),
   path('api/items/types/', views.ItemViewSet.as_view({'get': 'item_types'}), name='item-types'),
   #  path('api/employees/designations/', views.EmployeeViewSet.as_view({'get': 'designations'}), name='employee-designations'),
   path('api/vehicles/expired-documents/', views.VehicleViewSet.as_view({'get': 'expired_documents'}), name='expired-documents'),
    # Authentication URLs


    path('register/', views.CompanyRegisterView.as_view(), name='company-register'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend-otp'),
    path('login/', views.CompanyLoginView.as_view(), name='company-login'),
    path('logout/', views.CompanyLogoutView.as_view(), name='company-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Company URLs
    path('dashboard/', views.CompanyDashboardView.as_view(), name='company-dashboard'),
    path('profile/', views.CompanyProfileView.as_view(), name='company-profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Employee URLs
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employees/add/', views.AddEmployeeView.as_view(), name='add-employee'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    path('employees/<int:employee_id>/reset-password/', 
         views.ResetEmployeePasswordView.as_view(), 
         name='reset-employee-password'),
    
    # Warehouse URLs
  path('warehouses/', views.WarehouseListCreateView.as_view(), name='warehouse-list-create'),
    path('warehouses/<int:warehouse_id>/', views.WarehouseDetailView.as_view(), name='warehouse-detail'),
    path('warehouses/count/', views.WarehouseCountView.as_view(), name='warehouse-count'),
    path('warehouses/search/', views.WarehouseSearchView.as_view(), name='warehouse-search'),
   #  path('warehouses/bulk-delete/', views.WarehouseBulkDeleteView.as_view(), name='warehouse-bulk-delete'),


     path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),

       path('verify-forgot-password-otp/', views.VerifyForgotPasswordOTPView.as_view(), name='verify-forgot-password-otp'),
    path('resend-forgot-password-otp/', views.ResendForgotPasswordOTPView.as_view(), name='resend-forgot-password-otp'),
    
    # ✅ reset-password भी ADD करें
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),

       # Employee Authentication URLs
    path('employee/login/', views.EmployeeLoginView.as_view(), name='employee-login'),
    path('employee/profile/', views.EmployeeProfileView.as_view(), name='employee-profile'),
    path('employee/dashboard/', views.EmployeeDashboardView.as_view(), name='employee-dashboard'),
    path('employee/change-password/', views.EmployeeChangePasswordView.as_view(), name='employee-change-password'),
    # Utility URLs
    path('check-exists/', views.CheckCompanyExistsView.as_view(), name='check-company-exists'),
 # Debug URL (remove in production)
    path('debug/auth-info/', views.DebugAuthInfoView.as_view(), name='debug-auth-info'),

      # Employee Warehouse API
    path('employee/warehouses/', views.EmployeeWarehouseListView.as_view(), name='employee-warehouses'),

    # Vendor Order URLs

     path('vendor-orders/stats/', 
         views.VendorOrderViewSet.as_view({'get': 'stats'}), 
         name='vendor-order-stats'),
    path('vendor-orders/by-vendor/', 
         views.VendorOrderViewSet.as_view({'get': 'by_vendor'}), 
         name='vendor-order-by-vendor'),
    
    # Individual order actions
    path('vendor-orders/<int:pk>/approve/', 
         views.VendorOrderViewSet.as_view({'post': 'approve'}), 
         name='vendor-order-approve'),
    path('vendor-orders/<int:pk>/complete/', 
         views.VendorOrderViewSet.as_view({'post': 'complete'}), 
         name='vendor-order-complete'),
    path('vendor-orders/<int:pk>/cancel/', 
         views.VendorOrderViewSet.as_view({'post': 'cancel'}), 
         name='vendor-order-cancel'),

#          path('vendor-orders/bulk-import/', VendorOrderBulkImportView.as_view(), name='vendor-order-bulk-import'),
#     path('vendor-orders/download-template/', DownloadVendorOrderTemplateView.as_view(), name='download-vendor-order-template'),

  
    
    # Stock Management URLs
    path('stocks/dashboard/', 
         views.StockDashboardAPIView.as_view(), 
         name='stock-dashboard'),
    
    path('stocks/initialize/', 
         views.InitializeStockAPIView.as_view(), 
         name='stock-initialize'),
    
    path('stocks/stats/', 
         views.StockViewSet.as_view({'get': 'stats'}), 
         name='stock-stats'),
    
    path('stocks/low-stock/', 
         views.StockViewSet.as_view({'get': 'low_stock'}), 
         name='stock-low'),
    
    path('stocks/<int:pk>/update-stock/', 
         views.StockViewSet.as_view({'put': 'update_stock'}), 
         name='stock-update'),
    
    path('stock-transactions/by-item/', 
         views.StockTransactionViewSet.as_view({'get': 'by_item'}), 
         name='stock-transactions-by-item'),
    
    path('stock-transactions/summary/', 
         views.StockTransactionViewSet.as_view({'get': 'summary'}), 
         name='stock-transactions-summary'),


]


