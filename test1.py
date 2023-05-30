import win32com.client as win32

excel_file = r"F:\Code\Python-Projects\Laser-Quote-Generator\quotes\2023-05-29-22-23-08.xlsm"  # Replace with the path to your Excel file
pdf_file = "path_to_save_pdf_file.pdf"  # Specify the path to save the PDF file

# Create an instance of Excel application
excel_app = win32.gencache.EnsureDispatch("Excel.Application")

# Open the Excel file
workbook = excel_app.Workbooks.Open(excel_file)

# Save the Excel file as PDF
workbook.ExportAsFixedFormat(0, excel_file.replace(".xlsm", ".pdf"))

# Close the Excel file and quit the application
workbook.Close()
excel_app.Quit()

print("Excel file converted to PDF.")
