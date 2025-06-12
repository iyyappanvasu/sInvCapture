from django.db import models
from django.utils import timezone

# Model to store captured inventory data entered by users
class InventoryCapture(models.Model):
    owner = models.CharField(max_length=100, db_column='OWNER')  # Name of the inventory owner
    location = models.CharField(max_length=100, db_column='LOCATION')  # Inventory location
    case = models.CharField(max_length=100, db_column='CASE')  # Case number or ID
    sku = models.CharField(max_length=100, db_column='SKU')  # Stock Keeping Unit
    uom = models.CharField(max_length=20, db_column='UOM')  # Unit of Measure
    quantity = models.IntegerField(default=1, db_column='QUANTITY')  # Quantity of items
    username = models.CharField(max_length=100, default='default_user', db_column='USERNAME')  # Capturing user's name
    created_date = models.DateTimeField(blank=True, null=True, db_column='ADDDATE')  # Record creation time
    status = models.IntegerField(default=0, db_column='STATUS')  # Status (custom logic can apply)

    class Meta:
        db_table = 'INVENTORYCAPTURE'  # Table name in the database

    def save(self, *args, **kwargs):
        # Set created_date automatically if not provided
        if not self.created_date:
            self.created_date = timezone.now().replace(microsecond=0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.owner} - {self.sku}"


# Custom user model (not using Django’s built-in auth model)
class UserMaster(models.Model):
    username = models.CharField(max_length=100, unique=True, db_column='USERNAME')  # Unique username
    password = models.CharField(max_length=100, db_column='PASSWORD')  # Password (can be hashed)
    created_date = models.DateTimeField(blank=True, null=True, db_column='ADDDATE')  # User creation timestamp
    updated_datetime = models.DateTimeField(blank=True, null=True, db_column='LASTLOGIN')  # Last login time

    class Meta:
        db_table = 'USERMASTER'

    def save(self, *args, **kwargs):
        # Set timestamps when saving
        now = timezone.now().replace(microsecond=0)
        if not self.created_date:
            self.created_date = now
        self.updated_datetime = now
        super().save(*args, **kwargs)


# Model to manage ASN number generation and line limits
class NextupNumber(models.Model):
    type = models.CharField(max_length=50, default="ASN", db_column="TYPE")  # Type like ASN, BSN etc.
    Starting_Number = models.CharField(max_length=50, db_column='STARTINGNUMBER')  # Start of the number range
    Ending_Number = models.CharField(max_length=50, db_column='ENDINGNUMBER')  # End of the number range
    Current_Number = models.CharField(max_length=50, db_column='CURRENTNUMBER')  # Last assigned number
    Next_Number = models.CharField(max_length=50, db_column='NEXTNUMBER')  # Next number to be assigned
    prefix = models.CharField(max_length=10, default='ASN', db_column='PREFIX')  # Prefix for numbering (e.g., ASN)
    NUMBEROFLINES = models.IntegerField(default=0, db_column='NUMBEROFLINES')  # Max records allowed per ASN number

    created_date = models.DateTimeField(blank=True, null=True, db_column='ADDDATE')  # Record creation timestamp
    updated_datetime = models.DateTimeField(blank=True, null=True, db_column='LASTLOGIN')  # Last update time
    created_username = models.CharField(max_length=100, blank=True, null=True, db_column='CREATEDUSERNAME')  # Created by
    updated_username = models.CharField(max_length=100, blank=True, null=True, db_column='UPDATEDUSERNAME')  # Updated by

    class Meta:
        db_table = 'NEXTUPNUMBER'

    def __str__(self):
        return f"Current: {self.Current_Number} | Next: {self.Next_Number}"

    def save(self, *args, **kwargs):
        # Set timestamps automatically
        now = timezone.now().replace(microsecond=0)
        if not self.created_date:
            self.created_date = now
        self.updated_datetime = now
        super().save(*args, **kwargs)


# Model to store final records ready for download or export
class DownloadInventory(models.Model):
    owner = models.CharField(max_length=100, db_column='OWNER')  # Owner of the item
    location = models.CharField(max_length=100, db_column='LOCATION')  # Item location
    case = models.CharField(max_length=100, db_column='CASE')  # Case number
    sku = models.CharField(max_length=100, db_column='SKU')  # SKU of the item
    uom = models.CharField(max_length=20, db_column='UOM')  # Unit of Measure
    quantity = models.IntegerField(default=1, db_column='QUANTITY')  # Quantity of the item
    asn_number = models.CharField(max_length=20, db_column='ASNNUMBER')  # ASN number assigned
    line_number = models.CharField(max_length=6, db_column='LINENUMBER')  # Line number under ASN
    status = models.IntegerField(default=1, db_column='STATUS')  # Item status (active, processed, etc.)

    download_status = models.CharField(
        max_length=3,
        choices=[('yes', 'Yes'), ('no', 'No')],
        default='no',
        db_column='DOWNLOADSTATUS'
    )  # Whether the data is downloaded

    updated_username = models.CharField(max_length=100, blank=True, null=True, db_column='UPDATEDUSERNAME')  # Updated by
    updated_datetime = models.DateTimeField(blank=True, null=True, db_column='LASTLOGIN')  # Last update timestamp

    class Meta:
        db_table = 'DOWNLOADINVENTORY'

    def __str__(self):
        return f"{self.asn_number} - {self.line_number}"