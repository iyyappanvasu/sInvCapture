from .models import DownloadInventory, NextupNumber 
from django.db import transaction, DatabaseError
from django.utils import timezone

def add_inventory(owner, location, case, sku, uom, record_count, quantity, status, username, is_export=False):
    try:
        with transaction.atomic():
            nextup = NextupNumber.objects.first()
            if not nextup:
                prefix = "ASN"
                nextup = NextupNumber.objects.create(
                    Starting_Number=f"{prefix}0000001",
                    Ending_Number=f"{prefix}9999999",
                    Current_Number=f"{prefix}0000001",
                    Next_Number=f"{prefix}0000002",
                    prefix=prefix,
                    NUMBEROFLINES=3,
                    created_username=username,
                    updated_username=username,
                    type="ASN"
                )

            prefix = nextup.prefix or ""
            current_number = int(''.join(filter(str.isdigit, nextup.Current_Number)))
            current_prefix = nextup.Current_Number[:len(prefix)]

            if current_prefix != prefix:
                current_number += 1
                nextup.Current_Number = f"{prefix}{current_number:07d}"
                nextup.Next_Number = f"{prefix}{current_number + 1:07d}"

            last_asn_num = current_number
            MAX_RECORDS_PER_ASN = nextup.NUMBEROFLINES
            total_records = record_count

            last_asn_obj = DownloadInventory.objects.filter(
                asn_number=f"{prefix}{last_asn_num:07d}"
            ).order_by('-line_number').first()

            if last_asn_obj:
                last_owner = last_asn_obj.owner
                last_line_number = int(last_asn_obj.line_number or 0)
                if last_owner != owner or last_line_number >= MAX_RECORDS_PER_ASN:
                    last_asn_num += 1
                    last_line_number = 0
            else:
                last_line_number = 0

            while total_records > 0:
                if last_line_number < MAX_RECORDS_PER_ASN:
                    remaining = MAX_RECORDS_PER_ASN - last_line_number
                    to_add = min(total_records, remaining)
                    current_asn = f"{prefix}{last_asn_num:07d}"

                    for i in range(1, to_add + 1):
                        line_number = last_line_number + i
                        DownloadInventory.objects.create(
                            owner=owner,
                            location=location,
                            case=case,
                            sku=sku,
                            uom=uom,
                            quantity=quantity,
                            asn_number=current_asn,
                            line_number=f"{line_number:05d}",
                            status=status,
                            updated_username=username,
                            updated_datetime=timezone.now().replace(microsecond=0),
                        )

                    last_line_number += to_add
                    total_records -= to_add
                else:
                    last_asn_num += 1
                    last_line_number = 0

            if is_export:
                last_asn_num += 1

            nextup.Current_Number = f"{prefix}{last_asn_num:07d}"
            nextup.Next_Number = f"{prefix}{last_asn_num + 1:07d}"
            nextup.updated_username = username
            nextup.save()

    except DatabaseError as e:
        print(f"Database error in add_inventory: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error in add_inventory: {e}")
        return False

    return True
