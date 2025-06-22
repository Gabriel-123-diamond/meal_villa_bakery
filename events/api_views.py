from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from bson import ObjectId
import datetime

from bakery_management.db import get_mongo_db
from .serializers import EventSerializer, EventRegistrationSerializer
from users.api_views import IsAdminOrManager

class EventListCreateAPIView(APIView):
    """
    Publicly list upcoming events, or allow staff to create a new event.
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsAdminOrManager()]
        return [permissions.AllowAny()]

    def get(self, request, format=None):
        db = get_mongo_db()
        # Find events where the start time is in the future
        events = list(db.events.find({'start_time': {'$gte': datetime.datetime.utcnow()}}).sort("start_time", 1))
        for event in events:
            event['_id'] = str(event['_id'])
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            event_data = serializer.validated_data
            event_data['registered_attendees'] = [] # Initialize
            result = db.events.insert_one(event_data)
            event_data['_id'] = str(result.inserted_id)
            return Response(event_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventDetailAPIView(APIView):
    """
    Retrieve, update or delete an event instance.
    GET is public, PUT/DELETE are for staff only.
    """
    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [permissions.IsAuthenticated(), IsAdminOrManager()]
        return [permissions.AllowAny()]

    def get_object(self, pk):
        db = get_mongo_db()
        try:
            return db.events.find_one({"_id": ObjectId(pk)})
        except: return None

    def get(self, request, pk, format=None):
        event = self.get_object(pk)
        if event:
            event['_id'] = str(event['_id'])
            serializer = EventSerializer(event)
            return Response(serializer.data)
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    def put(self, request, pk, format=None):
        event = self.get_object(pk)
        if not event: return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EventSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            db = get_mongo_db()
            db.events.update_one({"_id": ObjectId(pk)}, {"$set": serializer.validated_data})
            updated_event = self.get_object(pk)
            updated_event['_id'] = str(updated_event['_id'])
            return Response(EventSerializer(updated_event).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk, format=None):
        event = self.get_object(pk)
        if not event: return Response(status=status.HTTP_404_NOT_FOUND)
        db = get_mongo_db()
        db.events.delete_one({"_id": ObjectId(pk)})
        return Response(status=status.HTTP_204_NO_CONTENT)

class EventRegistrationAPIView(APIView):
    """
    Public endpoint for customers to register for an event.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk, format=None):
        serializer = EventRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        db = get_mongo_db()
        try:
            event_oid = ObjectId(pk)
            event = db.events.find_one({"_id": event_oid})
            if not event:
                return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({"error": "Invalid event ID."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if event is full
        max_attendees = event.get('max_attendees', 0)
        current_attendees = len(event.get('registered_attendees', []))
        if current_attendees >= max_attendees:
            return Response({"error": "This event is already full."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if user is already registered
        registrant_email = serializer.validated_data['email']
        if any(attendee['email'] == registrant_email for attendee in event.get('registered_attendees', [])):
            return Response({"error": "This email is already registered for the event."}, status=status.HTTP_400_BAD_REQUEST)

        new_attendee = {
            "name": serializer.validated_data['name'],
            "email": registrant_email,
            "registered_at": datetime.datetime.utcnow()
        }
        
        db.events.update_one({"_id": event_oid}, {"$push": {"registered_attendees": new_attendee}})
        
        return Response({"success": "You have been successfully registered for the event!"}, status=status.HTTP_200_OK)

