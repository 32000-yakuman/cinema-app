from rest_framework import serializers
from .models import Product, Purchase, Sales

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'

class SalesCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sales
        fields =  ['product', 'quantity', 'sales_date', 'import_file']

class SalesSerializer(serializers.ModelSerializer):
    monthly_date = serializers.DateTimeField(format='%Y-%m')
    monthly_price = serializers.IntegerField()
    class Meta:
        model = Sales
        fields = ['monthly_date','monthly_price']

# 仕入れ・売上情報の一覧
# Modelに依存しないため、個別にフィールドを定義している
class InventorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    unit = serializers.IntegerField()
    quantity = serializers.IntegerField()
    type = serializers.IntegerField()
    date = serializers.DateTimeField()

class FileSerializer(serializers.Serializer):
    file = serializers.FileField()