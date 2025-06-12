# Django imports for handling views, sessions, auth, database and error handling
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.db import DatabaseError, IntegrityError, transaction
from django.core.exceptions import ObjectDoesNotExist

# Importing models and utility functions
from .models import InventoryCapture, UserMaster, NextupNumber, DownloadInventory
from .utils import add_inventory
from .export_excel import export_datas_to_excel
import logging

logger = logging.getLogger(__name__)

# Status constants for tracking inventory processing
STATUS_NEW = 0
STATUS_PENDING = 1
STATUS_PROCESSED = 2

# Handles user login with optional auto-creation in UserMaster
def login_view(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            request.session['username'] = username

            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                if not UserMaster.objects.filter(username=username).exists():
                    hashed_password = make_password(password)
                    UserMaster.objects.create(username=username, password=hashed_password)
                else:
                    user_obj = UserMaster.objects.get(username=username)
                    user_obj.save()

                return redirect('main')
            else:
                messages.error(request, 'Invalid Username/Password')
        except Exception as e:
            messages.error(request, f"Login Error: {str(e)}")
            logger.exception("Login error")

    return render(request, 'login.html')


# Handles new user registration
def register_view(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            # Check password match
            if password1 != password2:
                messages.error(request, 'Passwords do not match')
            else:
                from django.contrib.auth.models import User
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'Username already taken')
                else:
                    User.objects.create_user(username=username, password=password1)
                    messages.success(request, 'User created! Please login.')
                    return redirect('login')
        except Exception as e:
            messages.error(request, f"Registration Error: {str(e)}")
            logger.exception("Registration error")
    return render(request, 'register.html')

# Renders the main landing page after login
def main_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'main.html')

# Handles owner name input and sets it in session
def owner_view(request):
    try:
        if not request.user.is_authenticated:
            return redirect('login')

        if request.method == "POST":
            owner = request.POST.get('owner')
            if not owner:
                messages.error(request, "Sorry,Invalid Owner Name")
                return render(request, 'owner.html')
            request.session['owner'] = owner
            return redirect('inventory')
        return render(request, 'owner.html')

    except Exception as e:
        messages.error(request, f"Owner View Error: {str(e)}")
        logger.exception("Owner view error")
        return render(request, 'owner.html')

# Handles capturing inventory item details
def inventory_view(request):
    try:
        if not request.user.is_authenticated:
            return redirect('login')

        if request.method == "POST":
            owner = request.session.get('owner')
            username = request.user.username
            location = request.POST.get('location')
            sku = request.POST.get("sku")
            uom = request.POST.get('uom')
            case = request.POST.get('case', '')

            # Validate and convert status and quantity
            try:
                status = int(request.POST.get('status', STATUS_NEW))
            except (TypeError, ValueError):
                status = STATUS_NEW

            try:
                quantity = int(request.POST.get("quantity"))
            except (TypeError, ValueError):
                messages.error(request, "Please enter a valid quantity number")
                return render(request, "Inventory.html")

            # Save inventory record
            InventoryCapture.objects.create(
                owner=owner,
                location=location,
                sku=sku,
                uom=uom,
                case=case,
                quantity=quantity,
                username=username,
                status=status
            )

            messages.success(request, "Inventory Captured Successfully!")
            return redirect("inventory")

        return render(request, "Inventory.html")

    except Exception as e:
        messages.error(request, f"Something went wrong: {str(e)}")
        logger.exception("Inventory error")
        return render(request, "Inventory.html")

# Logs out the user and redirects to login page
def logout_view(request):
    try:
        logout(request)
        return redirect('login')
    except Exception as e:
        messages.error(request, f"Logout failed: {str(e)}")
        logger.exception("Logout error")
        return redirect('login')

# Returns ASN number details as JSON
def nextup_number_view(request):
    try:
        nextup = NextupNumber.objects.first()
        if nextup:
            data = {
                "Starting_Number": nextup.Starting_Number,
                "Ending_Number": nextup.Ending_Number,
                "Current_Number": nextup.Current_Number,
                "Next_Number": nextup.Next_Number,
                "Created_Date_IST": nextup.get_created_date_ist(),
                "Updated_Date_IST": nextup.get_updated_date_ist(),
            }
        else:
            data = {"message": "No ASN record found"}
        return JsonResponse(data)

    except ObjectDoesNotExist:
        return JsonResponse({"error": "ASN record does not exist"}, status=404)

    except Exception as e:
        logger.exception("ASN JSON error")
        return JsonResponse({"error": str(e)}, status=500)

# Returns all download inventory data as JSON
def download_inventory_view(request):
    try:
        records = DownloadInventory.objects.all().values()
        return JsonResponse(list(records), safe=False)
    except Exception as e:
        logger.exception("Download inventory error")
        return JsonResponse({"error": str(e)}, status=500)

# Exports current download data into Excel format
def download_excel_view(request):
    try:
        return export_datas_to_excel(request)
    except Exception as e:
        messages.error(request, f"Download Excel Error: {str(e)}")
        logger.exception("Excel download error")
        return render(request, "main.html")

# Generates ASN numbers from new inventory records and exports as Excel
def generate_asn_and_download(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                new_records = InventoryCapture.objects.filter(status=STATUS_NEW)

                # No records found for processing
                if not new_records.exists():
                    messages.warning(request, "No new records to generate ASN.")
                    return render(request, "main.html")

                # Add each new record to download table
                for record in new_records:
                    success = add_inventory(
                        owner=record.owner,
                        location=record.location,
                        case=record.case,
                        sku=record.sku,
                        uom=record.uom,
                        record_count=1,
                        quantity=record.quantity,
                        status=STATUS_PENDING,
                        username=request.user.username
                    )
                    if not success:
                        messages.error(request, "Error generating ASN for records.")
                        return render(request, "main.html")

                # Update status to processed after successful ASN generation
                new_records.update(status=STATUS_PROCESSED)

            # Export updated records as Excel file
            return export_datas_to_excel(request)

        except Exception as e:
            messages.error(request, f"Failed: {e}")
            logger.exception("ASN generation failed")
            return render(request, "main.html")

    return redirect("main")
