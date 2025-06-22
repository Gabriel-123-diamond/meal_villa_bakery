from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from datetime import datetime

from bakery_management.db import get_mongo_db
from .serializers import ShiftSerializer
from users.api_views import IsAdminOrManager
from django.contrib.auth.models import User

class ShiftListCreateAPIView(APIView):
    """
    List all shifts within a date range, or create a new shift.
    Requires start_date and end_date query params for GET.
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request, format=None):
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')
        if not (start_str and end_str):
            return Response({"error": "start_date and end_date are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.fromisoformat(start_str)
            end_date = datetime.fromisoformat(end_str)
        except ValueError:
            return Response({"error": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)

        db = get_mongo_db()
        shifts = list(db.shifts.find({
            "start_time": {"$gte": start_date},
            "end_time": {"$lte": end_date}
        }))
        for shift in shifts:
            shift['_id'] = str(shift['_id'])
        serializer = ShiftSerializer(shifts, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ShiftSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            data = serializer.validated_data
            try:
                user = User.objects.get(id=data['user_id'])
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            shift_doc = {
                "user_id": user.id,
                "user_name": user.get_full_name() or user.username,
                "start_time": data['start_time'],
                "end_time": data['end_time'],
                "notes": data.get('notes', '')
            }
            db.shifts.insert_one(shift_doc)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShiftDetailAPIView(APIView):
    """
    Retrieve, update or delete a shift instance.
    """
    permission_classes = [IsAdminOrManager]
    
    def delete(self, request, pk, format=None):
        db = get_mongo_db()
        try:
            result = db.shifts.delete_one({"_id": ObjectId(pk)})
            if result.deleted_count == 0:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Invalid ID format."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


