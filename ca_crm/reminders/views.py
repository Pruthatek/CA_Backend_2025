from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from reminders.models import Reminders
from workflow.views import ModifiedApiview
from clients.models import Customer
from billing.models import Billing
from ca_crm.email_service import send_email

class ReminderCreateView(ModifiedApiview):
    def post(self, request):
        data = request.data
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Required fields
            customer_id = data.get("customer_id")
            
            if not customer_id:
                return Response(
                    {"error": "customer_id is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch related objects
            customer = Customer.objects.get(id=customer_id)
            billing = None
            if data.get("billing_id"):
                billing = Billing.objects.get(id=data.get("billing_id"))
            reminder_title = data.get("reminder_title")
            if not reminder_title:
                return Response(
                    {"error": "reminder_title is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                    )
            # Create the reminder
            content = data.get("content")
            to_email = data.get("to_email")
            if isinstance(to_email, str):
                to_email = to_email.split(',')
            elif isinstance(to_email, list):
                to_email = [email.strip() for email in to_email]
            to_email_string = ', '.join(to_email)
            

            with transaction.atomic():
                email = send_email(subject=reminder_title, body=content, to_emails=to_email)

                if not email:
                    return Response(
                        {"Message":"Error while sending Email"}, status=status.HTTP_400_BAD_REQUEST
                    )
                
                reminder = Reminders.objects.create(
                    customer=customer,
                    billing=billing,
                    type_of_reminder=data.get("type_of_reminder"),
                    reminder_title=reminder_title,
                    content=content,
                    reminder_date=data.get("reminder_date"),
                    to_email=to_email_string,
                    created_by=user,
                    updated_by=user
                )


            return Response(
                {"message": "Reminder created successfully", "id": reminder.id}, 
                status=status.HTTP_201_CREATED
            )
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Billing.DoesNotExist:
            return Response({"error": "Billing not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReminderRetrieveView(ModifiedApiview):
    def get(self, request, reminder_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            reminder = Reminders.objects.get(id=reminder_id)
            data = {
                "id": reminder.id,
                "customer_id": reminder.customer.id,
                "customer_name": reminder.customer.name_of_business,
                "billing_id": reminder.billing.id if reminder.billing else None,
                "type_of_reminder": reminder.type_of_reminder,
                "reminder_title": reminder.reminder_title,
                "content": reminder.content,
                "reminder_date": reminder.reminder_date,
                "to_email": reminder.to_email,
                "created_by": reminder.created_by.id,
                "created_by_user": reminder.created_by.username,
                "created_date": reminder.created_date,
                "updated_by": reminder.updated_by.id if reminder.updated_by else None,
                "updated_by_user": reminder.updated_by.username if reminder.updated_by else None,
                "updated_date": reminder.updated_date
            }
            return Response(data, status=status.HTTP_200_OK)
        except Reminders.DoesNotExist:
            return Response({"error": "Reminder not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
              

class ReminderDeleteView(ModifiedApiview):
    def delete(self, request, reminder_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            reminder = Reminders.objects.get(id=reminder_id)
            reminder.delete()
            
            return Response(
                {"message": "Reminder deleted successfully"}, 
                status=status.HTTP_200_OK
            )
        except Reminders.DoesNotExist:
            return Response({"error": "Reminder not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class ReminderListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            reminders = Reminders.objects.all()
            data = [{
                "id": reminder.id,
                "customer_id": reminder.customer.id,
                "customer_name": reminder.customer.name_of_business,
                "billing_id": reminder.billing.id if reminder.billing else None,
                "type_of_reminder": reminder.type_of_reminder,
                "reminder_title": reminder.reminder_title,
                "content": reminder.content,
                "to_email": reminder.to_email,
                "reminder_date": reminder.reminder_date,
                "created_by": reminder.created_by.id,
                "created_by_user": reminder.created_by.username,
                "created_date": reminder.created_date,
                "updated_by": reminder.updated_by.id if reminder.updated_by else None,
                "updated_by_user": reminder.updated_by.username if reminder.updated_by else None,
                "updated_date": reminder.updated_date
            } for reminder in reminders]
            
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class CustomerReminderListView(ModifiedApiview):
    def get(self, request, customer_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            customer = Customer.objects.get(id=customer_id)
            reminders = Reminders.objects.filter(customer=customer)
            
            data = [{
                "id": reminder.id,
                "billing_id": reminder.billing.id if reminder.billing else None,
                "type_of_reminder": reminder.type_of_reminder,
                "reminder_title": reminder.reminder_title,
                "content": reminder.content,
                "reminder_date": reminder.reminder_date,
                "created_date": reminder.created_date,
                "updated_date": reminder.updated_date
            } for reminder in reminders]
            
            return Response(data, status=status.HTTP_200_OK)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
