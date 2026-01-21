import django_filters
from .models import Item, Customer, Vendor, Employee, Vehicle

class ItemFilter(django_filters.FilterSet):
    item_code = django_filters.CharFilter(lookup_expr='icontains')
    item_name = django_filters.CharFilter(lookup_expr='icontains')
    item_type = django_filters.ChoiceFilter(choices=Item.ITEM_TYPES)
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = Item
        fields = ['item_code', 'item_name', 'item_type', 'is_active']


class CustomerFilter(django_filters.FilterSet):
    customer_code = django_filters.CharFilter(lookup_expr='icontains')
    customer_name = django_filters.CharFilter(lookup_expr='icontains')
    gst_number = django_filters.CharFilter(lookup_expr='icontains')
    po_number = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = Customer
        fields = ['customer_code', 'customer_name', 'gst_number', 'po_number', 'is_active']


class VendorFilter(django_filters.FilterSet):
    vendor_code = django_filters.CharFilter(lookup_expr='icontains')
    vendor_name = django_filters.CharFilter(lookup_expr='icontains')
    gst_number = django_filters.CharFilter(lookup_expr='icontains')
    ifsc_code = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = Vendor
        fields = ['vendor_code', 'vendor_name', 'gst_number', 'ifsc_code', 'is_active']


class EmployeeFilter(django_filters.FilterSet):
    employee_code = django_filters.CharFilter(lookup_expr='icontains')
    full_name = django_filters.CharFilter(lookup_expr='icontains')
    # role = django_filters.ChoiceFilter(choices=Employee.ROLE_CHOICES)
    status = django_filters.ChoiceFilter(choices=Employee.STATUS_CHOICES)
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = Employee
        fields = ['employee_code', 'full_name',  'status', 'is_active']


class VehicleFilter(django_filters.FilterSet):
    vehicle_code = django_filters.CharFilter(lookup_expr='icontains')
    vehicle_name = django_filters.CharFilter(lookup_expr='icontains')
    vehicle_number = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = Vehicle
        fields = ['vehicle_code', 'vehicle_name', 'vehicle_number', 'is_active']




from .models import VendorOrder

class VendorOrderFilter(django_filters.FilterSet):
    order_number = django_filters.CharFilter(lookup_expr='icontains')
    invoice_number = django_filters.CharFilter(lookup_expr='icontains')
    vendor_name = django_filters.CharFilter(field_name='vendor__vendor_name', lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=VendorOrder.STATUS_CHOICES)
    load_type = django_filters.ChoiceFilter(choices=VendorOrder.LOAD_TYPE_CHOICES)
    
    # Date filters
    invoice_date_from = django_filters.DateFilter(
        field_name='invoice_date', 
        lookup_expr='gte'
    )
    invoice_date_to = django_filters.DateFilter(
        field_name='invoice_date', 
        lookup_expr='lte'
    )
    
    created_at_from = django_filters.DateFilter(
        field_name='created_at', 
        lookup_expr='date__gte'
    )
    created_at_to = django_filters.DateFilter(
        field_name='created_at', 
        lookup_expr='date__lte'
    )
    
    # Amount filters
    min_amount = django_filters.NumberFilter(
        field_name='total_amount', 
        lookup_expr='gte'
    )
    max_amount = django_filters.NumberFilter(
        field_name='total_amount', 
        lookup_expr='lte'
    )
    
    class Meta:
        model = VendorOrder
        fields = [
            'order_number', 'invoice_number', 'vendor', 'status',
            'load_type', 'transport_required'
        ]        

# filters.py में VendorOrderFilter के बाद जोड़ें

import django_filters
from .models import Stock, StockTransaction

class StockFilter(django_filters.FilterSet):
    item_name = django_filters.CharFilter(field_name='item__item_name', lookup_expr='icontains')
    item_code = django_filters.CharFilter(field_name='item__item_code', lookup_expr='icontains')
    item_type = django_filters.ChoiceFilter(field_name='item__item_type', choices=Item.ITEM_TYPES)
    
    physical_stock_min = django_filters.NumberFilter(field_name='physical_stock', lookup_expr='gte')
    physical_stock_max = django_filters.NumberFilter(field_name='physical_stock', lookup_expr='lte')
    
    empty_with_customers_min = django_filters.NumberFilter(field_name='empty_with_customers', lookup_expr='gte')
    empty_with_customers_max = django_filters.NumberFilter(field_name='empty_with_customers', lookup_expr='lte')
    
    stock_status = django_filters.ChoiceFilter(
        method='filter_by_status',
        choices=[
            ('out_of_stock', 'Out of Stock'),
            ('very_low', 'Very Low'),
            ('low', 'Low Stock'),
            ('high_pending', 'High Pending'),
            ('normal', 'Normal')
        ]
    )
    
    class Meta:
        model = Stock
        fields = ['item', 'item_type']
    
    def filter_by_status(self, queryset, name, value):
        if value == 'out_of_stock':
            return queryset.filter(physical_stock=0)
        elif value == 'very_low':
            return queryset.filter(physical_stock__gt=0, physical_stock__lt=20)
        elif value == 'low':
            return queryset.filter(physical_stock__gte=20, physical_stock__lt=50)
        elif value == 'high_pending':
            return queryset.filter(empty_with_customers__gt=100)
        elif value == 'normal':
            return queryset.filter(
                physical_stock__gte=50,
                empty_with_customers__lte=100
            )
        return queryset


class StockTransactionFilter(django_filters.FilterSet):
    item_name = django_filters.CharFilter(field_name='item__item_name', lookup_expr='icontains')
    item_code = django_filters.CharFilter(field_name='item__item_code', lookup_expr='icontains')
    
    created_at_from = django_filters.DateFilter(
        field_name='created_at', 
        lookup_expr='date__gte'
    )
    
    created_at_to = django_filters.DateFilter(
        field_name='created_at', 
        lookup_expr='date__lte'
    )
    
    quantity_min = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    
    class Meta:
        model = StockTransaction
        fields = ['item', 'transaction_type', 'reference_type']
