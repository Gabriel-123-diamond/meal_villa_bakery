from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
import datetime

from bakery_management.db import get_mongo_db
from .serializers import ComplianceTaskSerializer, ComplianceLogSerializer
from users.api_views import IsAdminOrManager
from django.contrib.auth.models import User

class ComplianceTaskListCreateAPIView(APIView):
    """
    List all compliance tasks or create a new one (staff only).
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request, format=None):
        db = get_mongo_db()
        tasks = list(db.compliance_tasks.find({}))
        for task in tasks:
            task['_id'] = str(task['_id'])
        serializer = ComplianceTaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ComplianceTaskSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            db.compliance_tasks.insert_one(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ComplianceLogCreateAPIView(APIView):
    """
    Log the completion of a compliance task. Accessible by any authenticated user.
    """
    def post(self, request, format=None):
        serializer = ComplianceLogSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            log_data = serializer.validated_data
            
            try:
                task = db.compliance_tasks.find_one({"_id": ObjectId(log_data['task_id'])})
                if not task:
                    return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception:
                return Response({"error": "Invalid task_id."}, status=status.HTTP_400_BAD_REQUEST)

            db_object = {
                "task_id": log_data['task_id'],
                "task_name": task.get('task_name'),
                "completed_by_id": request.user.id,
                "completed_by_name": request.user.get_full_name() or request.user.username,
                "completed_at": datetime.datetime.utcnow(),
                "notes": log_data.get('notes', '')
            }
            db.compliance_logs.insert_one(db_object)
            return Response({"success": "Task logged successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ComplianceLogListAPIView(APIView):
    """
    View a history of all compliance logs. For staff only.
    """
    permission_classes = [IsAdminOrManager]
    
    def get(self, request, format=None):
        db = get_mongo_db()
        logs = list(db.compliance_logs.find({}).sort("completed_at", -1))
        for log in logs:
            log['_id'] = str(log['_id'])
        serializer = ComplianceLogSerializer(logs, many=True)
        return Response(serializer.data)


