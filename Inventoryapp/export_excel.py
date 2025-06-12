# Required libraries for data processing, database connection, file handling, and Django integration
import pandas as pd
import mysql.connector
from io import BytesIO
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from decouple import config


def export_datas_to_excel(request):
    # Initialize database and cursor variables
    mydb = None
    cursor = None

    try:
        # Establish connection to the MySQL database
        mydb = mysql.connector.connect(
        host=config('DB_HOST'),
        user=config('DB_USER'),
        password=config('DB_PASSWORD'),
        database=config('DB_NAME'),
        )
        cursor = mydb.cursor()

        # SQL query to fetch records that are not yet downloaded
        query = """
        SELECT id, ASNNUMBER, SKU, OWNER, LINENUMBER, QUANTITY, UOM, `CASE` AS TOID, LOCATION 
        FROM DOWNLOADINVENTORY 
        WHERE DOWNLOADSTATUS = 'no'
        """
        df = pd.read_sql(query, con=mydb)

        # If no data found, display warning and redirect
        if df.empty:
            messages.warning(request, "Sorry, no data found to export!")
            return redirect("inventory")

        # Prepare the 'Data' sheet with ASN and Owner, setting initial status to 0
        df_data = df[['ASNNUMBER', 'OWNER']].drop_duplicates()
        df_data['STATUS'] = 0
        df_data = df_data[['ASNNUMBER', 'OWNER', 'STATUS']]

        # Define static rows for description and headers in 'Data' sheet
        data_desc = ['Column Name', 'GenericKey', 'RECEIPTKEY', 'STORERKEY', 'STATUS']
        data_headers = ['Messages', 'GenericKey', 'ASN/Receipt', 'Owner', 'Receipt Status']
        data_rows = [data_desc, data_headers]

        # Add data rows to the 'Data' sheet
        for _, row in df_data.iterrows():
            data_rows.append(['', ''] + row.tolist())
        df_data_final = pd.DataFrame(data_rows, columns=data_headers)

        # Prepare the 'Detail' sheet with detailed item information
        df_detail = df[['ASNNUMBER', 'SKU', 'OWNER', 'LINENUMBER', 'QUANTITY', 'UOM', 'TOID', 'LOCATION']]

        # Define static rows for description and headers in 'Detail' sheet
        detail_desc = ['Column Name', 'GenericKey', 'RECEIPTKEY', 'SKU', 'STORERKEY',
                       'RECEIPTLINENUMBER', 'QTYEXPECTED', 'UOM', 'TOID', 'TOLOC']
        detail_headers = ['Messages', 'GenericKey', 'ASN/Receipt', 'Item', 'Owner',
                          'Line #', 'Expected Qty', 'UOM', 'LPN', 'Location']
        detail_rows = [detail_desc, detail_headers]

        # Add data rows to the 'Detail' sheet
        for _, row in df_detail.iterrows():
            detail_rows.append(['', ''] + row.tolist())
        df_detail_final = pd.DataFrame(detail_rows, columns=detail_headers)

        # Prepare the 'Validations' sheet with basic configuration details
        validation_data = [
            ['Date Format', 'M/d/yy h:mm a', 'MM=Month, dd=Day, yy=Year, mm=Minute, hh=Hour'],
            ['Time Zone', '(GMT-05:00) Eastern Time (US & Canada)', 'America/New_York'],
            ['Empty Fields', '[blank]', 'Put [blank] to remove existing values']
        ]
        df_validations = pd.DataFrame(validation_data)

        # Generate the Excel file with multiple sheets and write all data
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_data_final.to_excel(writer, index=False, header=False, sheet_name='Data')
            df_detail_final.to_excel(writer, index=False, header=False, sheet_name='Detail')
            df_validations.to_excel(writer, index=False, header=False, sheet_name='Validations')

        # Set the Excel file name with a timestamp for uniqueness
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename=inventory_data_{timestamp}.xlsx'

        # Update download status for the exported records in the database
        ids = df['id'].tolist()
        if ids:
            update_query = """
                UPDATE DOWNLOADINVENTORY 
                SET DOWNLOADSTATUS = 'yes' 
                WHERE id = %s
            """
            cursor.executemany(update_query, [(i,) for i in ids])
            mydb.commit()

        return response

    # Handle MySQL connection errors
    except mysql.connector.Error as err:
        messages.error(request, f"MySQL Error: {err}")
        return redirect("inventory")

    # Handle errors while fetching data using pandas
    except pd.errors.DatabaseError as db_err:
        messages.error(request, f"Pandas DB Error: {db_err}")
        return redirect("inventory")

    # Handle any unexpected errors
    except Exception as e:
        messages.error(request, f"Unexpected error: {str(e)}")
        return redirect("inventory")

    # Ensure that the database connection is closed after processing
    finally:
        try:
            if cursor:
                cursor.close()
            if mydb and mydb.is_connected():
                mydb.close()
        except Exception:
            pass
