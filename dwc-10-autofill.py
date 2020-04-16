#! /usr/bin/python

import os
import time
from datetime import datetime
import pdfrw
import pandas as pd

INVOICE_TEMPLATE_PATH = 'input/fl-dwc-10-template.pdf'

ANNOT_KEY = '/Annots'
ANNOT_FIELD_KEY = '/T'
ANNOT_VAL_KEY = '/V'
ANNOT_RECT_KEY = '/Rect'
SUBTYPE_KEY = '/Subtype'
WIDGET_SUBTYPE_KEY = '/Widget'

# construct date of birth
def getDate(date):
	return (str(date)[4:6] + '/' + str(date)[6:8] + '/' + str(date)[0:4])

# processing the card holder ID
def process_cardholder_id(id, row):
	# check if 7 digit numeric data type starting with the number 6
	if (len(id) == 7) and (id[0] == '6'):
		# see if claim reference id can be used
		if str(row['ClaimReferenceID']) != '':
			return str(row['ClaimReferenceID'])
		# see if carrier id can be used
		elif str(row['CarrierID']) != '':
			return str(row['CarrierID'])
		# return blank
		return ''
	else:
		return id

# construct a data dictionary from the details row
def getDataDict(row):
	#charges
	price = 0
	if isinstance(row['AWP'], float) and isinstance(row['QuantityDispensed'], float):	
		price = round(row['AWP']*row['QuantityDispensed'],2) + 4.18

	data_dict = {
	'8 EMPLOYERS NAME  ADDRESS': row['ClaimReferenceID'],
	'5 GENDER': row['PatientFirstName'] + ' ' + row['PatientLastName'],
	'2 EMPLOYEES SOCIAL SECURITY  OR DIVISION ASSIGNED': process_cardholder_id(str(row['CardholderID']), row), #row['CardholderID']
	'7 INSURERCARRIER NAME  ADDRESS': getDate(row['DateOfInjury']),
	'4 EMPLOYEES DOB': getDate(row['DateOfBirth']),
	'7 INSURERCARRIER NAME  ADDRESS_2': row['EmployerName'] + '\n' + row['EmployerStreetAddress'] 
	+ '\n' + row['EmployerCityAddress'] + '\n' + row['EmployerStateProvinceAddress'] 
	+ '\n' + str(row['EmployerZipPostalCode']),
	'9a1': row['ProductID'],
	'10 QUANTITY': row['QuantityDispensed'],
	'11 DAYS': row['DaysSupply'],
	'12 MEDICATION  STRENGTH': row['TherapeuticClass14'],
	'16_1_date-filled': getDate(row['DateOfService']),
	'17a_1_prescriber_name': row['PrescriberName'],
	'13 USUAL CHARGE': str(price),
	'26 PHYSICAL ADDRESS OF PHARMACY OR MEDICAL SUPPLIER': row['PharmacyLocationName'],
	'25 REMITTANCE RECIPIENTS FEIN': '84-4771022',
	'26 PHYSICAL ADDRESS OF PHARMACY OR MEDICAL SUPPLIER_2': row['PharmacyLocationAddress'] 
	+ '\n' + row['PharmacyLocationCity'] + '\n' + row['PharmacyLocationState'] + '\n' + str(row['PharmacyLocationZipCode']).split('.')[0],
	'27 REMITTANCE ADDRESS if different from Field 26 Check if Same': 'StreamlineRx\n2861 Executive Dr STE 210\nClearwater, FL 33762\nNPI1184257743',
	}
	
	# for a specific pharmacy in FL
	if row['PharmacyLocationName'] == 'PRECISIONMED PHARMACY':
		data_dict['FOR INSURERCARRIER USE'] = 'Zenaida Quinn'
		data_dict['29 PHARMACISTS DOH LICENSE  MED SUPPLIERS LICENSE'] = 'PS34350'

	return data_dict

# fill out the pdf with the values of the data dictionary
def writeFillablePDF(input_pdf_path, output_pdf_path, data_dict):
	# Read Input PDF
	template_pdf = pdfrw.PdfReader(input_pdf_path)
	# Set Apparences ( Make Text field visible )
	template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))

	# Loop all Annotations
	for annotation in template_pdf.pages[0]['/Annots']:
		
		# new additions to template
		if annotation['/Subtype'] == '/Widget' and ('/Parent' in annotation):
			key = annotation['/Parent']['/T'][1:-1] # Remove parentheses
			#print(key)
			if key in data_dict.keys():
				# custom fields
				if '/V' in annotation['/Parent']:
					annotation['/Parent'].update(pdfrw.PdfDict(V=f'{data_dict[key]}'))
		
		# Text fields
		if annotation['/Subtype'] == '/Widget' and annotation['/T']: 
			key = annotation['/T'][1:-1] # Remove parentheses
			#print(key)
			if key in data_dict.keys():
				annotation.update( pdfrw.PdfDict(V=f'{data_dict[key]}'))
	
	pdfrw.PdfWriter().write(output_pdf_path, template_pdf)

# multiple rows for same person - charges comes on the next form row for section 24
def add_new_charges_to_dict(row, index):
	#charges
	price = 0
	if isinstance(row['AWP'], float) and isinstance(row['QuantityDispensed'], float):	
		price = round(row['AWP']*row['QuantityDispensed'],2) + 4.18
	# construct dictionary
	datadict = {}
	
	return datadict, price

# get location for the file based on the required and not-required fields
def get_location(record):
	df = pd.read_csv('input/required-fields.csv')
	required = df[df['status']=='required']
	for index, row in required.iterrows():
		field = row['field']
		if record[field] == '':
			print('missing field',field)
			return 'missing'
	return 'completed'

if __name__ == '__main__':
	t1 = time.time()
	print('Starting the FL-DWC-10 PDF autofill process...')
	print('This might take some time...')
	# results dictionary
	results = {}
	# iterate over data files in the input directory
	files = [i for i in os.listdir("input") if (i.endswith("txt") or i.endswith("xls") or i.endswith("xlsx"))]

	# iterate over the files
	for file in files:
		# try statement
		try:
			# get file extension
			file_ext = os.path.splitext(file)[1]
			
			# construct data frame based on type of file
			if file_ext == '.txt':
				df = pd.read_csv('input/' + file, sep="|")
			elif file_ext == '.xls' or file_ext == '.xlsx':
				df = pd.read_excel('input/' + file)
			# replace na's
			df = df.fillna('')

			# iterate across the data
			for index, row in df.iterrows():

				# skip based on the isReversal and TransactionResponseStatus fields
				if row['TransactionResponseStatus'] != 'P':
					print('skipping record for ' + row['PatientLastName'] + ',' + row['PatientFirstName'])
					continue
				
				# skip if not florida
				if row['MemberState'] != 'FL':
					#print('Skipping record (no FL) for ' + row['PatientLastName'] + ',' + row['PatientFirstName'])
					continue

				# construct filename
				filename = row['PatientLastName'] + ',' + row['PatientFirstName'] + ',' 
				filename += str(row['PharmacyLocationName']) + ',' + str(row['DateOfService']) + ',' 
				filename += row['MemberState'] + ',dwc066.pdf' #row['FacilityName'] + ',' +

				# construct dictionary key
				person = row['PatientLastName'] + '-' + row['PatientFirstName'] + '-' + str(row['DateOfBirth'])
				
				# check if in result-set
				if person in results:
					print('Record for: ' + person + ' already exists')
					results[person]['records'] += 1
					newrow, price = add_new_charges_to_dict(row, results[person]['records'])
					results[person]['data'] = {**results[person]['data'], **newrow}
					results[person]['totalprice'] += price
					continue

				# construct data dictionary
				data_dict = getDataDict(row)

				# write out first version file
				writeFillablePDF(INVOICE_TEMPLATE_PATH, 'output/' + get_location(row) + '/' + filename, data_dict)
				print('Added ' + row['PatientLastName'] + ',' + row['PatientFirstName']);


		# exception
		except Exception as e:
			print('[ERROR] There was an issue with the file ' + file + ' , it will be skipped over')

		else:
			print('Processed data file ' + file)

	# end of writing
	t = time.time()-t1
	print('Completed in:', round(t,2), 'secs')
	input('You can close this window now...')