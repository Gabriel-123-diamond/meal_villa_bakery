from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from bson import ObjectId
import datetime

from bakery_management.db import get_mongo_db
from .serializers import FeedbackSerializer
from users.api_views import IsAdminOrManager

class FeedbackSubmitAPIView(APIView):
    """
    A public API endpoint for anyone to submit feedback.
    """
    permission_classes = [permissions.AllowAny] # No login required

    def post(self, request, format=None):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            feedback_data = serializer.validated_data
            feedback_data['submitted_at'] = datetime.datetime.utcnow()
            feedback_data['is_resolved'] = False
            
            db.feedback.insert_one(feedback_data)
            return Response({"success": "Thank you for your feedback!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FeedbackListAPIView(APIView):
    """
    An admin-only endpoint to view all submitted feedback.
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request, format=None):
        db = get_mongo_db()
        feedback_list = list(db.feedback.find({}).sort("submitted_at", -1))
        for feedback in feedback_list:
            feedback['_id'] = str(feedback['_id'])
        serializer = FeedbackSerializer(feedback_list, many=True)
        return Response(serializer.data)

class FeedbackDetailAPIView(APIView):
    """
    An admin-only endpoint to update or delete a feedback entry.
    """
    permission_classes = [IsAdminOrManager]

    def put(self, request, pk, format=None):
        db = get_mongo_db()
        try:
            feedback_oid = ObjectId(pk)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        update_data = {"$set": {"is_resolved": request.data.get('is_resolved', False)}}
        db.feedback.update_one({"_id": feedback_oid}, update_data)
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, pk, format=None):
        db = get_mongo_db()
        try:
            feedback_oid = ObjectId(pk)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
        db.feedback.delete_one({"_id": feedback_oid})
        return Response(status=status.HTTP_204_NO_CONTENT)

