from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import datetime

from bakery_management.db import get_mongo_db
from .serializers import PerformanceLogSerializer
from users.api_views import IsAdminOrManager
from django.contrib.auth.models import User

class PerformanceLogListCreateAPIView(APIView):
    """
    List all performance logs for a specific user, or create a new one.
    Requires user_id in the request data for POST.
    Requires user_id as a query parameter for GET.
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request, format=None):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        db = get_mongo_db()
        logs = list(db.performance_logs.find({'user_id': int(user_id)}).sort("created_at", -1))
        for log in logs:
            log['_id'] = str(log['_id'])
        serializer = PerformanceLogSerializer(logs, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = PerformanceLogSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            data = serializer.validated_data
            try:
                user = User.objects.get(id=data['user_id'])
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            log_doc = {
                "user_id": user.id,
                "user_name": user.get_full_name() or user.username,
                "logged_by_id": request.user.id,
                "logged_by_name": request.user.get_full_name() or request.user.username,
                "log_type": data['log_type'],
                "notes": data['notes'],
                "created_at": datetime.datetime.utcnow()
            }
            db.performance_logs.insert_one(log_doc)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

