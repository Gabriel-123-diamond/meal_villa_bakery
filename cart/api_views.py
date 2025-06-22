from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .cart import Cart
from bakery_management.db import get_mongo_db
from bson import ObjectId

class CartAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        cart = Cart(request)
        cart_data = list(cart) # __iter__ is called
        for item in cart_data:
            item['product']['_id'] = str(item['product']['_id'])
        return Response({
            "items": cart_data,
            "total_price": cart.get_total_price()
        })

    def post(self, request, format=None): # Add item
        cart = Cart(request)
        product_id = request.data.get('product_id')
        db = get_mongo_db()
        try:
            product = db.products.find_one({'_id': ObjectId(product_id)})
            if product:
                cart.add(product=product)
                return Response({'success': f"Added {product['name']} to cart.", 'cart_item_count': len(cart)})
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({'error': 'Invalid product ID'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, format=None): # Remove item
        cart = Cart(request)
        product_id = request.data.get('product_id')
        cart.remove(product_id)
        return Response({'success': 'Item removed from cart.', 'cart_item_count': len(cart)})

