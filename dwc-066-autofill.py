#! /usr/bin/python

import os
import time
from datetime import datetime
import pdfrw
import pandas as pd

INVOICE_TEMPLATE_PATH = 'input/dwc-066-template.pdf'

ANNOT_KEY = '/Annots'
ANNOT_FIELD_KEY = '/T'
ANNOT_VAL_KEY = '/V'
ANNOT_RECT_KEY = '/Rect'
SUBTYPE_KEY = '/Subtype'
WIDGET_SUBTYPE_KEY = '/Widget'

# construct a data dictionary from the details row
def getDataDict(row):
	data_dict = {
	'sec_1': row['PharmacyLocationName'] + ',' + row['PharmacyLocationAddress'] + '\n' 
	+ row['PharmacyLocationCity'] + ' , ' + row['PharmacyLocationState'] + '\n'
	+ str(row['PharmacyLocationZipCode']) + ' , ' + str(row['PharmacyLocationPhone'])
	,'sec_2': str(datetime.today().strftime('%m-%d-%Y'))
	,'sec_3': row['ServiceProviderID']
	,'sec_5': row['DateOfBirth']
	,'sec_6': '843330118'
	,'sec_7': row['EmployerName']
	,'sec_8': 'Not On File'
	,'sec_9': row['PatientFirstName'] + ' , ' + row['PatientLastName'] 
	+ '\n' + row['MemberAddress'] + '\n' + row['MemberCity'] + '\n' + row['MemberState'] + ' , ' + str(row['MemberZipCode'])
	,'sec_10': 'Not On File'
	,'sec_11': row['DateOfInjury']
	,'sec_12': row['DateOfBirth']
	,'sec_13': row['PrescriberName'] + ' , ' + row['PrescriberAddress'] + '\n' + row['PrescriberCity'] + ' , ' +
	 row['PrescriberState'] + ' , ' + str(row['PrescriberZipCode'])
	,'sec_14': row['PrescriberID']
	,'sec_15': row['CardholderID']
	,'sec_20_1': str(row['DateOfService'])[4:6] + '/' + str(row['DateOfService'])[6:] + '/' + str(row['DateOfService'])[0:4]
	,'sec_21_1': row['ProductID']
	,'sec_23_1': row['QuantityDispensed']
	,'sec_24_1': row['DaysSupply']
	,'sec_27_1': row['DrugName'] + ' , ' + row['StrengthDescription']
	,'sec_28_1': row['PrescriptionReferenceNumber']
	}

	#charges
	if isinstance(row['AWP'], float) and isinstance(row['QuantityDispensed'], float):
		data_dict['sec_29_1'] = str(round(row['AWP'] + (0.25*row['AWP']*row['QuantityDispensed']) + 4, 2))
	
	return data_dict

# fill out the pdf with the values of the data dictionary
def writeFillablePDF(input_pdf_path, output_pdf_path, data_dict):
	# Read Input PDF
	template_pdf = pdfrw.PdfReader(input_pdf_path)
	# Set Apparences ( Make Text field visible )
	template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))

	# Loop all Annotations
	for annotation in template_pdf.pages[0]['/Annots']:
		# Custom/Fields
		if annotation['/Subtype'] == '/Widget' and ('/Parent' in annotation):
			key = annotation['/Parent']['/T'][1:-1] # Remove parentheses
			if key in data_dict.keys():
				annotation['/Parent'].update(pdfrw.PdfDict(V=f'{data_dict[key]}'))
				
	pdfrw.PdfWriter().write(output_pdf_path, template_pdf)



if __name__ == '__main__':
	t1 = time.time()
	print('Starting the DWC-066 PDF autofill process...')
	print('This might take some time...')
	# iterate over data files in the input directory
	files = [i for i in os.listdir("input") if i.endswith("txt")]

	# iterate over the files
	for file in files:
		# try statement
		try:
			# construct data frame
			df = pd.read_csv('input/' + file, sep="|")
			# replace na's
			df = df.fillna('')

			# iterate across the data
			for index, row in df.iterrows():
				
				# skip if not texas
				if row['MemberState'] != 'TX':
					print('Skipping record (no TX) for ' + row['PatientLastName'] + ',' + row['PatientFirstName'])
					continue

				# not texas
				data_dict = getDataDict(row)
				
				# location address based on facility
				if row['FacilityName'].strip() == 'Elite Rx Facility':
					data_dict['sec_4'] = 'Elite Rx Facility , ' + 'PO BOX 4379, WAYNE NJ 07474 (551 900 2255)'
				elif row['FacilityName'].strip() == 'Rx Solutions':
					data_dict['sec_4'] = 'StreamlineRx , 2861 Executive Dr STE 210, Clearwater, FL 33762 (727 565 0245)'

				# construct filename
				filename = row['PatientLastName'] + ',' + row['PatientFirstName'] + ',' 
				filename += str(row['PharmacyLocationName']) + ',' + str(row['DateOfService']) + ',' 
				filename += row['FacilityName'] + ',' + row['MemberState'] + ',dwc066_' + str(index + 1) + '.pdf'
				# write out first version file
				writeFillablePDF(INVOICE_TEMPLATE_PATH, 'output/' + filename, data_dict)

		# exception
		except Exception as e:
			print('[ERROR] There was an issue with the file ' + file + ' , it will be skipped over')

		else:
			print('Processed data file ' + file)

	# end of writing
	t = time.time()-t1
	print('Completed in:', round(t,2), 'secs')
	input('You can close this window now...')