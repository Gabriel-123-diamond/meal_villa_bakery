from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from decimal import Decimal, ROUND_HALF_UP
import datetime

from bakery_management.db import get_mongo_db
from .serializers import ProductSerializer, OrderSerializer, PromotionSerializer
from users.api_views import IsAdminOrManager


def get_recipe_cost(db, product_name):
    """Helper function to calculate the cost of a recipe."""
    recipe = db.recipes.find_one({"name": {"$regex": product_name, "$options": "i"}})
    if not recipe:
        return 0.0

    total_cost = 0.0
    for ingredient in recipe.get('ingredients', []):
        supply_item = db.baker_production_supplies.find_one({"name_lower": ingredient['ingredient_name'].lower()})
        cost_per_unit = float(supply_item.get('cost_per_unit', 0)) if supply_item else 0
        total_cost += float(ingredient.get('quantity', 0)) * cost_per_unit
    return total_cost

class ProductListCreateAPIView(APIView):
    """
    API endpoint to list all products or create a new one.
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request, format=None):
        db = get_mongo_db()
        products = list(db.products.find({}))
        for product in products:
            product['_id'] = str(product['_id'])
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            product_data = serializer.validated_data
            product_data['price'] = float(product_data['price'])
            
            result = db.products.insert_one(product_data)
            product_data['_id'] = str(result.inserted_id)
            return Response(product_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetailAPIView(APIView):
    """
    API endpoint to retrieve, update, or delete a single product.
    """
    permission_classes = [IsAdminOrManager]
    
    def get_object(self, pk):
        db = get_mongo_db()
        try:
            return db.products.find_one({"_id": ObjectId(pk)})
        except Exception:
            return None

    def get(self, request, pk, format=None):
        product = self.get_object(pk)
        if product:
            product['_id'] = str(product['_id'])
            serializer = ProductSerializer(product)
            return Response(serializer.data)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk, format=None):
        product = self.get_object(pk)
        if not product:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProductSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            db = get_mongo_db()
            update_data = serializer.validated_data
            if 'price' in update_data:
                update_data['price'] = float(update_data['price'])

            db.products.update_one({"_id": ObjectId(pk)}, {"$set": update_data})
            
            updated_product = self.get_object(pk)
            updated_product['_id'] = str(updated_product['_id'])
            return Response(ProductSerializer(updated_product).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        product = self.get_object(pk)
        if not product:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        db = get_mongo_db()
        db.products.delete_one({"_id": ObjectId(pk)})
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrderCreateAPIView(APIView):
    """
    API endpoint to create a new order, calculating COGS, applying promotions, and updating stock.
    """
    def post(self, request, format=None):
        order_serializer = OrderSerializer(data=request.data)
        if not order_serializer.is_valid():
            return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        db = get_mongo_db()
        validated_data = order_serializer.validated_data
        items_data = validated_data.get('items')
        
        subtotal = Decimal('0.00')
        total_cogs = Decimal('0.00')
        order_items_for_db = []
        product_updates = []

        for item in items_data:
            try:
                product = db.products.find_one({"_id": ObjectId(item['product_id'])})
                if not product: return Response({"error": f"Product with ID {item['product_id']} not found."}, status=status.HTTP_404_NOT_FOUND)
                if product['current_stock'] < item['quantity']: return Response({"error": f"Not enough stock for {product['name']}."}, status=status.HTTP_400_BAD_REQUEST)
                
                price = Decimal(str(product.get('price', '0.0')))
                subtotal += price * item['quantity']
                
                recipe_cost = Decimal(str(get_recipe_cost(db, product['name'])))
                total_cogs += recipe_cost * item['quantity']

                order_items_for_db.append({"product_id": item['product_id'], "name": product['name'], "quantity": item['quantity'], "price_at_sale": float(price)})
                product_updates.append({"id": product['_id'], "decrement": item['quantity']})
            except Exception:
                return Response({"error": f"Invalid product_id: {item['product_id']}"}, status=status.HTTP_400_BAD_REQUEST)

        promo_code = validated_data.get('promo_code')
        discount_amount = Decimal('0.00')
        applied_promo_code = None
        if promo_code:
            promotion = db.promotions.find_one({"promo_code": promo_code, "is_active": True})
            if promotion:
                usage_limit = promotion.get('usage_limit', 0)
                times_used = promotion.get('times_used', 0)
                if usage_limit > 0 and times_used >= usage_limit:
                    return Response({"error": "This promo code has reached its usage limit."}, status=status.HTTP_400_BAD_REQUEST)
                
                if promotion['discount_type'] == 'percentage': discount_amount = (subtotal * Decimal(str(promotion['value'] / 100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                elif promotion['discount_type'] == 'fixed_amount': discount_amount = Decimal(str(promotion['value'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                applied_promo_code = promo_code
        
        total_price = subtotal - discount_amount

        for update in product_updates:
            db.products.update_one({"_id": update["id"]}, {"$inc": {"current_stock": -update["decrement"]}})
            
        if applied_promo_code:
            db.promotions.update_one({"promo_code": applied_promo_code}, {"$inc": {"times_used": 1}})

        customer_id = validated_data.get('customer_id')
        customer_name = validated_data.get('customer_name', "In-Store Customer")
        customer_oid = None

        if customer_id:
            try:
                customer_oid = ObjectId(customer_id)
                customer = db.customers.find_one({"_id": customer_oid})
                if not customer:
                    return Response({"error": f"Customer with ID {customer_id} not found."}, status=status.HTTP_404_NOT_FOUND)
                customer_name = customer.get('name', customer_name)
            except Exception:
                return Response({"error": f"Invalid customer_id format: {customer_id}"}, status=status.HTTP_400_BAD_REQUEST)

        order_data = {
            "created_by_staff_id": request.user.id if request.user.is_authenticated else None,
            "created_by_staff_name": request.user.get_full_name() or request.user.username if request.user.is_authenticated else "Online Customer",
            "customer_id": str(customer_oid) if customer_oid else None,
            "customer_name": customer_name,
            "items": order_items_for_db,
            "subtotal": float(subtotal),
            "discount_amount": float(discount_amount),
            "total_price": float(total_price),
            "cost_of_goods_sold": float(total_cogs),
            "applied_promo_code": applied_promo_code,
            "payment_method": validated_data.get('payment_method'),
            "status": "pending",
            "created_at": datetime.datetime.utcnow()
        }
        result = db.orders.insert_one(order_data)
        new_order_id = str(result.inserted_id)

        if customer_oid:
            points_to_award = int(total_price / 100)
            db.customers.update_one(
                {"_id": customer_oid},
                {
                    "$push": {"order_history": new_order_id},
                    "$inc": {"loyalty_points": points_to_award}
                }
            )
        
        order_data['_id'] = new_order_id
        final_serializer = OrderSerializer(order_data)
        return Response(final_serializer.data, status=status.HTTP_201_CREATED)

class OrderListAPIView(APIView):
    def get(self, request, format=None):
        db = get_mongo_db()
        orders = list(db.orders.find({}).sort("created_at", -1))
        for order in orders: order['_id'] = str(order['_id'])
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class OrderDetailAPIView(APIView):
    def get_object(self, pk):
        db = get_mongo_db()
        try:
            return db.orders.find_one({"_id": ObjectId(pk)})
        except Exception:
            return None
    def get(self, request, pk, format=None):
        order = self.get_object(pk)
        if order:
            order['_id'] = str(order['_id'])
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        return Response(status=status.HTTP_404_NOT_FOUND)
    def put(self, request, pk, format=None):
        order = self.get_object(pk)
        if not order: return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(instance=order, data=request.data, partial=True)
        if serializer.is_valid():
            db = get_mongo_db()
            new_status = serializer.validated_data.get('status')
            if new_status == 'cancelled' and order.get('status') != 'cancelled':
                for item in order.get('items', []):
                    db.products.update_one({"_id": ObjectId(item['product_id'])},{"$inc": {"current_stock": item['quantity']}})
            db.orders.update_one({"_id": ObjectId(pk)}, {"$set": {"status": new_status}})
            updated_order = self.get_object(pk)
            updated_order['_id'] = str(updated_order['_id'])
            return Response(OrderSerializer(updated_order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PromotionListCreateAPIView(APIView):
    permission_classes = [IsAdminOrManager]
    def get(self, request, format=None):
        db = get_mongo_db()
        promotions = list(db.promotions.find({}))
        for promo in promotions: promo['_id'] = str(promo['_id'])
        serializer = PromotionSerializer(promotions, many=True)
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = PromotionSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            promo_data = serializer.validated_data
            if db.promotions.find_one({"promo_code": promo_data['promo_code']}): return Response({"error": "This promo code already exists."}, status=status.HTTP_400_BAD_REQUEST)
            promo_data['times_used'] = 0
            result = db.promotions.insert_one(promo_data)
            promo_data['_id'] = str(result.inserted_id)
            return Response(promo_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PromotionDetailAPIView(APIView):
    permission_classes = [IsAdminOrManager]
    def get_object(self, pk):
        db = get_mongo_db()
        try: return db.promotions.find_one({"_id": ObjectId(pk)})
        except: return None
    def put(self, request, pk, format=None):
        promo = self.get_object(pk)
        if not promo: return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = PromotionSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            db = get_mongo_db()
            db.promotions.update_one({"_id": ObjectId(pk)}, {"$set": serializer.validated_data})
            updated_promo = self.get_object(pk)
            updated_promo['_id'] = str(updated_promo['_id'])
            return Response(PromotionSerializer(updated_promo).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk, format=None):
        promo = self.get_object(pk)
        if not promo: return Response(status=status.HTTP_404_NOT_FOUND)
        db = get_mongo_db()
        db.promotions.delete_one({"_id": ObjectId(pk)})
        return Response(status=status.HTTP_204_NO_CONTENT)

