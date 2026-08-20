from .serializers import InventorySerializer, ProductSerializer, PurchaseSerializer, SalesSerializer, SalesCreateSerializer
from api.inventory.exception import BusinessException
from api.inventory.models import Status, SalesFile, Sales
from api.inventory.serializers import FileSerializer
from django.core.files.storage import default_storage
from django.conf import settings
from django.db.models import F, Value, Sum
from django.db.models.functions import Coalesce, TruncMonth
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, Purchase, Sales
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework.permissions import IsAuthenticated
import pandas
import logging

logger = logging.getLogger(__name__)

class ProductView(APIView):

    # 商品操作に関する関数で共通で使用する商品取得関数
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise NotFound

    """
    商品操作に関する関数
    """
    def get(self, request, id=None, format=None):
        """
        商品の一覧を取得する
        """
        if id is None :
            queryset = Product.objects.all()
            serializer = ProductSerializer(queryset, many=True)
        else: 
            product = self.get_object(id)
            serializer = ProductSerializer(product)
        return Response(serializer.data, status.HTTP_200_OK)

    def post(self, request, format=None):
        """
        商品を登録する
        """
        serializer = ProductSerializer(data=request.data)
        # validationを通らなかった場合、例外を投げる
        serializer.is_valid(raise_exception=True)
        # 検証したデータを永続化する
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

    def put(self, request, id, format=None):
        """
        商品を更新する
        """
        product = self.get_object(id)
        serializer = ProductSerializer(instance=product, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request, id, format=None):
        """
        商品を削除する
        """
        product = self.get_object(id)
        product.delete()
        return Response(status = status.HTTP_200_OK)

class PurchaseView(APIView):
    def post(self, request, format=None):
        """
        仕入情報を登録する
        """
        serializer = PurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

class SalesView(APIView):
    def post(self, request, format=None):
        """
        売上情報を登録する
        """
        serializer = SalesCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 在庫が売る分の数量を超えないかチェック
        purchase = Purchase.objects.filter(product_id=request.data['product']).aggregate(quantity_sum=Coalesce(Sum('quantity'), 0)) # 在庫テーブルのレコードを取得
        sales = Sales.objects.filter(product_id=request.data['product']).aggregate(quantity_sum=Coalesce(Sum('quantity'), 0)) # 卸しテーブルのレコードを取得

        # 在庫が売る分の数量を超えている場合はエラーレスポンスを返す
        if purchase['quantity_sum'] < (sales['quantity_sum'] + int(request.data['quantity'])):
            raise BusinessException('在庫数量を超過することはできません')

        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)
class InventoryView(APIView):
    # 仕入れ・売上情報を取得する
    def get(self, request, id=None, format=None):
        if id is None :
            # 件数が多くなるので商品IDは必ず指定する
            return Response({"errMsg": "商品IDを指定してください"}, status.HTTP_400_BAD_REQUEST)
        else:
            # UNIONするために、それぞれフィールド名を再定義している
            purchase = Purchase.objects.filter(product_id=id).prefetch_related('product').values("id", "quantity", type=Value('1'), date=F('purchase_date'),unit=F('product__price'))
            sales = Sales.objects.filter(product_id=id).prefetch_related('product').values("id", "quantity", type=Value('2'), date=F('sales_date'),unit=F('product__price'))
            queryset = purchase.union(sales).order_by(F("date"))
            serializer = InventorySerializer(queryset, many=True)
            return Response(serializer.data, status.HTTP_200_OK)

class LoginView(APIView):
    """ユーザーのログイン処理
    Args:
    APIView (class): rest_framework.viewsのAPIViewを受け取る
    """
    # 認証クラスの指定
    # リクエストヘッダーにtokenを差し込むといったカスタム動作をしないので素の認証クラスを使用する
    authentication_classes = []
    # アクセス許可の指定
    permission_classes = []

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"errMsg": "ユーザ名またはパスワードが正しくありません"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        access = serializer.validated_data.get("access", None)
        refresh = serializer.validated_data.get("refresh", None)
        if access:
            response = Response(status=status.HTTP_200_OK)
            max_age = settings.COOKIE_TIME
            response.set_cookie(
                'access',
                access,
                httponly=True,
                max_age=max_age,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE
            )

            response.set_cookie(
                'refresh',
                refresh,
                httponly=True,
                max_age=max_age,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE
            )
            return response
        return Response(
            {'errMsg': 'ユーザーの認証に失敗しました'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

class RetryView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # refresh を Cookie から読む（これが絶対必要）
        refresh_token = request.COOKIES.get('refresh')

        if not refresh_token:
            return Response({'errMsg': 'refresh token がありません'}, status=status.HTTP_401_UNAUTHORIZED)

        # TokenRefreshSerializer に渡す
        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data.get("access")
        refresh = serializer.validated_data.get("refresh")

        if access:
            response = Response(status=status.HTTP_200_OK)
            max_age = settings.COOKIE_TIME
            response.set_cookie(
                'access',
                access,
                httponly=True,
                max_age=max_age,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE
            )

            response.set_cookie(
                'refresh',
                refresh,
                httponly=True,
                max_age=max_age,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE
            )
            return response

        return Response({'errMsg': 'ユーザーの認証に失敗しました'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args):
        response = Response(status=status.HTTP_200_OK)
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response
    
class SalesAsyncView(APIView):
    def post(self, request, format=None):
        serializer = FileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data['file']
        filename = default_storage.save(file.name, file)
        
        sales_file = SalesFile(
            file_name=filename,
            status=Status.ASYNC_UNPROCESSED
        )
        sales_file.save()

        return Response(status=201)

class SalesSyncView(APIView):
    def post(self, request, format=None):
        logger.info("File: %s", request.FILES)
        logger.info("Data: %s", request.data)
        try:
            serializer = FileSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            file = serializer.validated_data['file']
            filename = default_storage.save(file.name, file)
            logger.info("Saved file path: %s", default_storage.path(filename))

            sales_file = SalesFile.objects.create(
                file_name=filename,
                status=Status.ASYNC_UNPROCESSED
            )
            logger.info("SalesFile created: id=%s", sales_file.id)

            df = pandas.read_csv(default_storage.path(filename))
            logger.debug("CSV columns: %s", df.columns)
            logger.debug("CSV head:\n%s", df.head())
            
            for idx, row in df.iterrows():
                logger.debug("Row %s: %s", idx, row)

                try:
                    Sales.objects.create(
                        product_id=row['product'],
                        sales_date=row['date'],
                        quantity=row['quantity'],
                        import_file=sales_file
                    )
                    logger.debug("Row %s saved", idx)
                except Exception as e:
                    logger.exception("Sales error at row %s", idx)
                    raise  # 例外を握りつぶさない

            sales_file.status = Status.SYNC
            sales_file.save()
            logger.info("SalesFile updated to SYNC: id=%s", sales_file.id)

            return Response(status=201)

        except Exception as e:
            logger.exception("SalesSyncView failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class SalesList(ListAPIView):
    serializer_class = SalesSerializer

    def get_queryset(self):
        queryset = Sales.objects.all()

        product_id = self.request.query_params.get('product')

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return (
            queryset
            .annotate(
                monthly_date=TruncMonth('sales_date')
            )
            .values('monthly_date')
            .annotate(
                monthly_price=Sum('quantity')
            )
            .order_by('monthly_date')
        )

# ログイン認証用API
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user_id": request.user.id}, status=200)
