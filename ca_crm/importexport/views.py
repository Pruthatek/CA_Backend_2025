from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Location, Inward, Outward
from custom_auth.models import CustomUser
from clients.models import Customer
from workflow.models import ClientWorkCategoryAssignment
import uuid
import time
from datetime import date, datetime
import traceback
from django.conf import settings
import os
import posixpath
from django.core.files.storage import FileSystemStorage
from workflow.views import ModifiedApiview


def generate_short_unique_filename(extension):
    # Shortened UUID (6 characters) + Unix timestamp for uniqueness
    unique_id = uuid.uuid4().hex[:6]  # Get the first 6 characters of UUID
    timestamp = str(int(time.time()))  # Unix timestamp as a string
    return f"{unique_id}_{timestamp}{extension}"


class LocationCreateView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error":"You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Extract data from the request
            location = request.data.get('location')
            description = request.data.get('description', None)
            photo = request.data.get('photo', None)
            is_active = request.data.get('is_active', True)

            # Validate required fields
            if not location or not description:
                return Response(
                    {"error": "Location and modified_by are required fields."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if photo:
                extension = os.path.splitext(photo.name)[1]  # Get the file extension
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'photos'))
                photo_path = fs.save(short_unique_filename, photo)
                photo_url = posixpath.join('media/location/photos', photo_path)
            else:
                photo_url = ""

            # Create the Location object
            location_obj = Location.objects.create(
                location=location,
                description=description,
                photo=photo_url,
                is_active=is_active,
                modified_by=user
            )

            # Return the created object as a response
            return Response(
                {
                    "id": location_obj.id,
                    "location": location_obj.location,
                    "description": location_obj.description,
                    "photo": location_obj.photo,
                    "is_active": location_obj.is_active,
                    "modified_by": location_obj.modified_by.id,
                    "modified_date": location_obj.modified_date
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LocationRetrieveView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error":"You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Location object
            location_data = Location.objects.filter(is_active=True)

            # Return the object as a response
            res_data = []
            for location in location_data:
                res_data.append({
                    "id": location.id,
                    "location": location.location,
                    "description": location.description,
                    "photo": location.photo,
                    "is_active": location.is_active
                })

            return Response(
                {"data":res_data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LocationUpdateView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error":"You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            # Fetch the Location object
            location_obj = Location.objects.get(id=id)
            photo = request.data.get('photo')
            if photo:
                extension = os.path.splitext(photo.name)[1]  # Get the file extension
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'photos'))
                photo_path = fs.save(short_unique_filename, photo)
                photo_url = posixpath.join('media/location/photos', photo_path)
            else:
                photo_url = ""

            # Update fields if provided in the request
            location_obj.location = request.data.get('location', location_obj.location)
            location_obj.description = request.data.get('description', location_obj.description)
            location_obj.photo = photo_url
            location_obj.is_active = request.data.get('is_active', location_obj.is_active)

            # Update modified_by if provided
            location_obj.modified_by = user

            # Save the updated object
            location_obj.save()

            # Return the updated object as a response
            return Response(
                {
                    "id": location_obj.id,
                    "location": location_obj.location,
                    "description": location_obj.description,
                    "photo": location_obj.photo,
                    "is_active": location_obj.is_active,
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LocationDeleteView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error":"You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Location object
            location_obj = Location.objects.get(id=id)

            # Delete the object
            location_obj.is_active = False
            location_obj.modified_by = user
            location_obj.save()

            # Return a success response
            return Response(
                {"message": "Location deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InwardCreateView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            file = request.FILES.get('file')

            # Extract data from the request
            company = request.data.get('company')
            inward_for = request.data.get('inward_for')
            inward_type = request.data.get('inward_type')
            customer_id = request.data.get('customer')
            reference_to = request.data.get('reference_to')
            inward_title = request.data.get('inward_title')
            description = request.data.get('description')
            location_id = request.data.get('location')
            through = request.data.get('through')
            task = request.data.get('assigned_task', None)

            # Validate required fields
            if not all([company, inward_for, inward_type, customer_id, reference_to, inward_title, description, through]):
                return Response(
                    {"error": "All fields are required except file and location."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch related objects
            customer = get_object_or_404(Customer, id=customer_id)
            location = get_object_or_404(Location, id=location_id) if location_id else None
            if task:
                assigned_task = ClientWorkCategoryAssignment.objects.filter(assignment_id=task, is_active=True).first()
                if not assigned_task:
                    return Response({"Error":"Selected Task not found"}, status=status.HTTP_400_BAD_REQUEST)

            # Handle file upload
            file_url = ""
            if file:
                extension = os.path.splitext(file.name)[1]  # Get the file extension
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'inward_files'))
                file_path = fs.save(short_unique_filename, file)
                file_url = posixpath.join('media/inward_files', file_path)

            # Create the Inward object
            inward_obj = Inward.objects.create(
                company=company,
                inward_for=inward_for,
                inward_type=inward_type,
                customer=customer,
                reference_to=reference_to,
                inward_title=inward_title,
                description=description,
                task=assigned_task,
                location=location,
                file=file_url,
                through=through,
                created_by=user,
                modified_by=user
            )

            # Return the created object as a response
            return Response(
                {
                    "id": inward_obj.id,
                    "company": inward_obj.company,
                    "inward_for": inward_obj.inward_for,
                    "inward_type": inward_obj.inward_type,
                    "customer": inward_obj.customer.id,
                    "reference_to": inward_obj.reference_to,
                    "inward_title": inward_obj.inward_title,
                    "task":inward_obj.task.assignment_id if inward_obj.task else None,
                    "task_name":inward_obj.task.task_name if inward_obj.task else None,
                    "description": inward_obj.description,
                    "location": inward_obj.location.id if inward_obj.location else None,
                    "file": inward_obj.file,
                    "through": inward_obj.through,
                    "created_by": inward_obj.created_by.id,
                    "modified_by": inward_obj.modified_by.id,
                    "created_date": inward_obj.created_date,
                    "modified_date": inward_obj.modified_date
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InwardListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Inward object
            inward_list = []
            inward_data = Inward.objects.all()
            for inward in inward_data:
                inward_list.append(                {
                    "id": inward.id,
                    "company": inward.company,
                    "inward_for": inward.inward_for,
                    "inward_type": inward.inward_type,
                    "customer": inward.customer.id,
                    "reference_to": inward.reference_to,
                    "inward_title": inward.inward_title,
                    "description": inward.description,
                    "location_id": inward.location.id if inward.location else None,
                    "location": inward.location.location if inward.location else None,
                    "through": inward.through,
                    "created_date": inward.created_date
                },)
            # Return the object as a response
            return Response({"inward_data":inward_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InwardRetrieveView(ModifiedApiview):
    def get(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Inward object
            inward_obj = Inward.objects.get(id=id)

            # Return the object as a response
            return Response(
                {
                    "id": inward_obj.id,
                    "company": inward_obj.company,
                    "inward_for": inward_obj.inward_for,
                    "inward_type": inward_obj.inward_type,
                    "customer": inward_obj.customer.id,
                    "customer_name": inward_obj.customer.name_of_business,
                    "reference_to": inward_obj.reference_to,
                    "inward_title": inward_obj.inward_title,
                    "assigned_task": inward_obj.task.assignment_id if inward_obj.task else None,
                    "assigned_task_name": inward_obj.task.task_name if inward_obj.task else None,
                    "description": inward_obj.description,
                    "location": inward_obj.location.id if inward_obj.location else None,
                    "file": inward_obj.file,
                    "through": inward_obj.through
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InwardUpdateView(ModifiedApiview):
    def put(self, request, pk):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Inward object
            inward_obj = get_object_or_404(Inward, id=pk)

            # Update fields if provided in the request
            inward_obj.company = request.data.get('company', inward_obj.company)
            inward_obj.inward_for = request.data.get('inward_for', inward_obj.inward_for)
            inward_obj.inward_type = request.data.get('inward_type', inward_obj.inward_type)
            inward_obj.reference_to = request.data.get('reference_to', inward_obj.reference_to)
            inward_obj.inward_title = request.data.get('inward_title', inward_obj.inward_title)
            inward_obj.description = request.data.get('description', inward_obj.description)
            inward_obj.through = request.data.get('through', inward_obj.through)
            task_id = request.data.get("assignment_id", None)

            if task_id:
                assigned_task = ClientWorkCategoryAssignment.objects.filter(assignment_id=task_id, is_active=True).first()
                if not assigned_task:
                    return Response({"Error":"Assigned task not found"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    inward_obj.task = assigned_task


            # Update related fields if provided
            customer_id = request.data.get('customer')
            if customer_id:
                inward_obj.customer = get_object_or_404(Customer, id=customer_id)

            location_id = request.data.get('location')
            if location_id:
                inward_obj.location = get_object_or_404(Location, id=location_id)

            # Handle file upload if provided
            file = request.FILES.get('file')
            if file:
                extension = os.path.splitext(file.name)[1]  # Get the file extension
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'inward_files'))
                file_path = fs.save(short_unique_filename, file)
                inward_obj.file = posixpath.join('media/inward_files', file_path)

            # Update modified_by and save
            inward_obj.modified_by = user
            inward_obj.save()

            # Return the updated object as a response
            return Response(
                {
                    "id": inward_obj.id,
                    "company": inward_obj.company,
                    "inward_for": inward_obj.inward_for,
                    "inward_type": inward_obj.inward_type,
                    "customer": inward_obj.customer.id,
                    "reference_to": inward_obj.reference_to,
                    "inward_title": inward_obj.inward_title,
                    "description": inward_obj.description,
                    "location": inward_obj.location.id if inward_obj.location else None,
                    "file": inward_obj.file,
                    "task": inward_obj.task.task_name,
                    "task_id": inward_obj.task.assignment_id,
                    "through": inward_obj.through,
                    "created_by": inward_obj.created_by.id,
                    "modified_by": inward_obj.modified_by.id,
                    "created_date": inward_obj.created_date,
                    "modified_date": inward_obj.modified_date
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InwardDeleteView(ModifiedApiview):
    def delete(self, request, pk):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Inward object
            inward_obj = get_object_or_404(Inward, id=pk)

            # Delete the object
            inward_obj.delete()

            # Return a success response
            return Response(
                {"message": "Inward deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class OutwardCreateView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Extract data from the request
            customer_id = request.data.get('customer')
            outward_reference = request.data.get('outward_reference')
            inward_id = request.data.get('inward', None)
            company = request.data.get('company')
            outward_title = request.data.get('outward_title')
            about_outward = request.data.get('about_outward')
            outward_through = request.data.get('outward_through')
            outward_date = request.data.get('outward_date')
            avb_no = request.data.get('avb_no', None)
            courier_name = request.data.get('courier_name', None)
            name_of_person = request.data.get('name_of_person', None)

            # Validate required fields
            if not all([customer_id, outward_reference, company, outward_title, about_outward, outward_through, outward_date]):
                return Response(
                    {"error": "All fields are required except inward (if outward_reference is non-inward-entry)."},
                    status=status.HTTP_400_BAD_REQUEST
                )


            if outward_through not in ["hand_over_to_client", "sent_via_office_boy", "by_courier"]:
                return Response({"error":"Outward through option incorrect"}, status=status.HTTP_400_BAD_REQUEST)

            if outward_through == "by_courier" and not avb_no or not courier_name:
                return Response({"error":"AVB no and Courier name is required in case of sent through courier"}, status=status.HTTP_400_BAD_REQUEST)
            
            if outward_through in ["hand_over_to_client", "sent_via_office_boy"] and not name_of_person:
                return Response({"error":"person name is required in case of out ward given to client or send via office boy"}, status=status.HTTP_400_BAD_REQUEST)


            # Fetch related objects
            customer = get_object_or_404(Customer, id=customer_id)
            inward = get_object_or_404(Inward, id=inward_id) if outward_reference == 'inward-entry' and inward_id else None

            # Create the Outward object
            outward_obj = Outward.objects.create(
                customer=customer,
                outward_reference=outward_reference,
                inward=inward,
                company=company,
                outward_title=outward_title,
                about_outward=about_outward,
                outward_through=outward_through,
                outward_date=outward_date,
                avb_no=avb_no,
                courier_name=courier_name,
                name_of_person=name_of_person,
                created_by=user,
                modified_by=user,
            )

            # Return the created object as a response
            return Response(
                {
                    "id": outward_obj.id,
                    "customer": outward_obj.customer.id,
                    "outward_reference": outward_obj.outward_reference,
                    "inward": outward_obj.inward.id if outward_obj.inward else None,
                    "company": outward_obj.company,
                    "outward_title": outward_obj.outward_title,
                    "about_outward": outward_obj.about_outward,
                    "outward_through": outward_obj.outward_through,
                    "outward_date": outward_obj.outward_date,
                    },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OutwardListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Outward object
            outward_list = []
            outward_obj = Outward.objects.all()
            for outward in outward_obj:
                outward_list.append({
                    "id": outward.id,
                    "customer": outward.customer.id,
                    "outward_reference": outward.outward_reference,
                    "inward": outward.inward.id if outward.inward else None,
                    "company": outward.company,
                    "outward_title": outward.outward_title,
                    "about_outward": outward.about_outward,
                    "outward_through": outward.outward_through,
                    "outward_date": outward.outward_date,
                    "avb_no": outward.avb_no,
                    "courier_name": outward.courier_name,
                    "name_of_person": outward.name_of_person,
                })
            # Return the object as a response
            return Response({"outward-data":outward_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OutwardRetrieveView(ModifiedApiview):
    def get(self, request, pk):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Outward object
            outward_obj = get_object_or_404(Outward, id=pk)

            # Return the object as a response
            return Response(
                {
                    "id": outward_obj.id,
                    "customer": outward_obj.customer.id,
                    "outward_reference": outward_obj.outward_reference,
                    "inward": outward_obj.inward.id if outward_obj.inward else None,
                    "company": outward_obj.company,
                    "outward_title": outward_obj.outward_title,
                    "about_outward": outward_obj.about_outward,
                    "outward_through": outward_obj.outward_through,
                    "outward_date": outward_obj.outward_date,
                    "avb_no": outward_obj.avb_no,
                    "courier_name": outward_obj.courier_name,
                    "name_of_person": outward_obj.name_of_person,
                    "created_by": outward_obj.created_by.id,
                    "modified_by": outward_obj.modified_by.id,
                    "created_date": outward_obj.created_date,
                    "modified_date": outward_obj.modified_date
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OutwardUpdateView(ModifiedApiview):
    def put(self, request, pk):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Outward object
            outward_obj = get_object_or_404(Outward, id=pk)

            # Extract data from the request
            outward_through = request.data.get('outward_through', outward_obj.outward_through)
            avb_no = request.data.get('avb_no', outward_obj.avb_no)
            courier_name = request.data.get('courier_name', outward_obj.courier_name)
            name_of_person = request.data.get('name_of_person', outward_obj.name_of_person)

            # Validate outward_through logic
            if outward_through not in ["hand_over_to_client", "sent_via_office_boy", "by_courier"]:
                return Response({"error": "Outward through option incorrect"}, status=status.HTTP_400_BAD_REQUEST)

            if outward_through == "by_courier" and (not avb_no or not courier_name):
                return Response({"error": "AVB no and Courier name are required in case of sent through courier"}, status=status.HTTP_400_BAD_REQUEST)

            if outward_through in ["hand_over_to_client", "sent_via_office_boy"] and not name_of_person:
                return Response({"error": "Person name is required in case of outward given to client or sent via office boy"}, status=status.HTTP_400_BAD_REQUEST)

            # Update fields if provided in the request
            outward_obj.customer = get_object_or_404(Customer, id=request.data.get('customer', outward_obj.customer.id))
            outward_obj.outward_reference = request.data.get('outward_reference', outward_obj.outward_reference)
            outward_obj.company = request.data.get('company', outward_obj.company)
            outward_obj.outward_title = request.data.get('outward_title', outward_obj.outward_title)
            outward_obj.about_outward = request.data.get('about_outward', outward_obj.about_outward)
            outward_obj.outward_through = outward_through
            outward_obj.outward_date = request.data.get('outward_date', outward_obj.outward_date)
            outward_obj.avb_no = avb_no
            outward_obj.courier_name = courier_name
            outward_obj.name_of_person = name_of_person

            # Update inward if outward_reference is 'inward-entry'
            if outward_obj.outward_reference == 'inward-entry':
                inward_id = request.data.get('inward')
                if inward_id:
                    outward_obj.inward = get_object_or_404(Inward, id=inward_id)
            else:
                outward_obj.inward = None

            # Update modified_by and save
            outward_obj.modified_by = user
            outward_obj.save()

            # Return the updated object as a response
            return Response(
                {
                    "id": outward_obj.id,
                    "customer": outward_obj.customer.id,
                    "outward_reference": outward_obj.outward_reference,
                    "inward": outward_obj.inward.id if outward_obj.inward else None,
                    "company": outward_obj.company,
                    "outward_title": outward_obj.outward_title,
                    "about_outward": outward_obj.about_outward,
                    "outward_through": outward_obj.outward_through,
                    "outward_date": outward_obj.outward_date,
                    "avb_no": outward_obj.avb_no,
                    "courier_name": outward_obj.courier_name,
                    "name_of_person": outward_obj.name_of_person,
                    "created_by": outward_obj.created_by.id,
                    "modified_by": outward_obj.modified_by.id,
                    "created_date": outward_obj.created_date,
                    "modified_date": outward_obj.modified_date
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OutwardDeleteView(ModifiedApiview):
    def delete(self, request, pk):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Outward object
            outward_obj = get_object_or_404(Outward, id=pk)

            # Delete the object
            outward_obj.delete()

            # Return a success response
            return Response(
                {"message": "Outward deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )