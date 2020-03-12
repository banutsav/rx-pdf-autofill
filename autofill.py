#! /usr/bin/python

import os
import time
from datetime import datetime
import pdfrw
import pandas as pd

INVOICE_TEMPLATE_PATH = 'input/form-cms-1500-template.pdf'

ANNOT_KEY = '/Annots'
ANNOT_FIELD_KEY = '/T'
ANNOT_VAL_KEY = '/V'
ANNOT_RECT_KEY = '/Rect'
SUBTYPE_KEY = '/Subtype'
WIDGET_SUBTYPE_KEY = '/Widget'

# second version
def writeFillablePDF(input_pdf_path, output_pdf_path, data_dict):
	# Read Input PDF
	template_pdf = pdfrw.PdfReader(input_pdf_path)
	# Set Apparences ( Make Text field visible )
	template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))

	# Loop all Annotations
	for annotation in template_pdf.pages[0]['/Annots']:

		# Custome/Fields and Checkboxes
		if annotation['/Subtype'] == '/Widget' and ('/Parent' in annotation):
			key = annotation['/Parent']['/T'][1:-1] # Remove parentheses
			if key in data_dict.keys():
				# custom fields
				if '/V' in annotation['/Parent']:
					annotation['/Parent'].update(pdfrw.PdfDict(V=f'{data_dict[key]}'))
					#print(annotation)
				# checkbox
				elif '/AS' in annotation:
					annotation.update(pdfrw.PdfDict(AS=pdfrw.PdfName('Yes')))
				#if data_dict[key] in annotation['/AP']['/N']:
				#	annotation.update( pdfrw.PdfDict(AS=pdfrw.PdfName('Yes'), V=pdfrw.PdfName('On')))

		# Text fields
		if annotation['/Subtype'] == '/Widget' and annotation['/T']: 
			key = annotation['/T'][1:-1] # Remove parentheses
			#print(key)
			if key in data_dict.keys():
				annotation.update( pdfrw.PdfDict(V=f'{data_dict[key]}'))
				#print(f'={key}={data_dict[key]}=')

	pdfrw.PdfWriter().write(output_pdf_path, template_pdf)


# construct a data dictionary from the details row
def getDataDict(row):
	data_dict = {
	'insurance_name': str(row['EmployerName']),
	'insurance_address': str(row['EmployerStreetAddress']),
	'insurance_address2': str(row['EmployerCityAddress']),
	'insurance_city_state_zip': str(str(row['EmployerStateProvinceAddress']) + ' , ' + str(row['EmployerZipPostalCode'])), 
	'pt_name': str(row['PatientLastName'] + ' , ' + row['PatientFirstName']),
	#'insurance_type': '/Other',
	'insurance_id': str(row['CardholderID']),
	'birth_mm': str(row['DateOfBirth'])[4:6], #month
	'birth_dd': str(row['DateOfBirth'])[6:], #day
	'birth_yy': str(row['DateOfBirth'])[0:4], #year
	'ins_name': str(row['EmployerName']),
	'pt_street': str(row['MemberAddress']),
	#'rel_to_ins': '/O',
	'ins_street': str(row['EmployerStreetAddress']),
	'pt_city': str(row['MemberCity']),
	'pt_state': str(row['MemberState']),
	'ins_city': str(row['EmployerCityAddress']),
	'ins_state': str(row['EmployerStateProvinceAddress']),
	'pt_zip': str(row['MemberZipCode']),
	'ins_zip': str(row['EmployerZipPostalCode']),
	'ins_policy': '', #str(row['CardholderID']),
	#'employment': '/YES',
	#'pt_auto_accident': '/NO',
	#'other_accident': '/NO',
	#'ins_benefit_plan': '/NO',
	'pt_signature': 'SIGNATURE ON FILE',
	'ins_signature': 'SIGNATURE ON FILE',
	'cur_ill_mm': str(row['DateOfInjury'])[4:6], #month
	'cur_ill_dd': str(row['DateOfInjury'])[6:], #day
	'cur_ill_yy': str(row['DateOfInjury'])[0:4], #year
	'85': 'DN',
	'ref_physician': str(row['PrescriberName']),
	'id_physician': str(row['PrescriberID']),
	#'lab': '/NO',
	'day1': row['QuantityDispensed'],
	'Suppl': str(row['ProductID']) + ',' + str(row['DrugName']) 
	+ ',' + str(row['StrengthDescription']) + '. QTY: '
	 + str(row['QuantityDispensed']) + ', DS: ' + str(row['DaysSupply']) + ', RX# ' + str(row['PrescriptionReferenceNumber']),
	'sv1_mm_from': str(row['DateOfService'])[4:6], #month
	'sv1_dd_from': str(row['DateOfService'])[6:], #day
	'sv1_yy_from': str(row['DateOfService'])[2:4], #year
	'sv1_mm_end': str(row['DateOfService'])[4:6], #month
	'sv1_dd_end': str(row['DateOfService'])[6:], #day
	'sv1_yy_end': str(row['DateOfService'])[2:4], #year
	'place1': '01',
	'cpt1': 'NDC',
	'local1': str(row['ServiceProviderID']),
	#'ssn': '/EIN',
	'pt_account': row['PatientFirstName'][0] + row['PatientLastName'][0] + str(row['DateOfBirth']),
	'amt_paid': '0.00',
	#'assignment': '/YES',
	'31_sp_id': str(row['ServiceProviderID']),
	'fac_name': row['PharmacyLocationName'],
	'fac_street': row['PharmacyLocationAddress'],
	'fac_location': row['PharmacyLocationCity'] + ',' + row['PharmacyLocationState'] + ',' + str(row['PharmacyLocationZipCode']),
	'doc_name': str(row['FacilityName']),
	'physician_signature': row['PharmacyLocationName'],
	'physician_date': str(datetime.today().strftime('%m-%d-%Y')),
	'pin1': str(row['ServiceProviderID']),
	}

	# charges
	price = 0
	if isinstance(row['AWP'], float) and isinstance(row['QuantityDispensed'], float):
		# check if NY state
		if row['MemberState'] == 'NY':
			# different calculation
			price = round(row['AWP']*row['QuantityDispensed']*0.8, 2) + 5
		else:
			# all other states
			price = round(row['AWP']*row['QuantityDispensed'], 2)
		
		# update the charges field
		data_dict['ch1'] = str(price)
		# total charge
		data_dict['t_charge'] = str(price)

	# gender
	if row['Gender'] == 'M':
		data_dict['3_gender_m'] = '/M'
	elif row['Gender'] == 'F':
		data_dict['3_gender_f'] = '/F'

	return data_dict, price

# multiple rows for same person - charges comes on the next form row for section 24
def add_new_charges_to_dict(row, index):
	# get the record number as a string
	count = str(index)
	# get the index as a lowercase alpha
	alphaindex = chr(95 + index)
	datadict = {
		'day' + count: row['QuantityDispensed'],
		'Suppl' + alphaindex: str(row['ProductID']) + ',' + str(row['DrugName']) 
		+ ',' + str(row['StrengthDescription']) + '. QTY: '
	 	+ str(row['QuantityDispensed']) + ', DS: ' + str(row['DaysSupply']) + ', RX# ' + str(row['PrescriptionReferenceNumber']),
		'sv'  + count + '_mm_from': str(row['DateOfService'])[4:6], #month
		'sv'  + count + '_dd_from': str(row['DateOfService'])[6:], #day
		'sv'  + count + '_yy_from': str(row['DateOfService'])[2:4], #year
		'sv'  + count + '_mm_end': str(row['DateOfService'])[4:6], #month
		'sv'  + count + '_dd_end': str(row['DateOfService'])[6:], #day
		'sv'  + count + '_yy_end': str(row['DateOfService'])[2:4], #year
		'place'  + count: '01',
		'cpt'  + count: 'NDC',
		'local'  + count: str(row['ServiceProviderID'])
	}

	# charges
	price = 0
	if isinstance(row['AWP'], float) and isinstance(row['QuantityDispensed'], float):
		# check if NY state
		if row['MemberState'] == 'NY':
			# different calculation
			price = round(row['AWP']*row['QuantityDispensed']*0.8, 2) + 5
		else:
			# all other states
			price = round(row['AWP']*row['QuantityDispensed'], 2)
		
		# update the charges field
		datadict['ch' + count] = str(price)
	
	return datadict, price

# break up and add diagnosis codes
def processDiagnosisCodes(data_dict ,codes):
	result = data_dict
	# check if string before splitting
	if type(codes) is not str:
		return result
	# is string, then split
	codelist = codes.split('^')
	#print(codelist)
	# iterate over list of diagnosis codes
	for i in range(len(codelist)):
		data_dict['diagnosis' + str(i + 1)] = codelist[i]
	# add entry to 24E
	characters = ''
	for i in range(len(codelist)):
		characters += chr(65 + i)
	data_dict['diag1'] = characters 
	return result 

if __name__ == '__main__':
	t1 = time.time()
	print('Starting the PDF autofill process...')
	print('This might take some time...')
	# iterate over data files in the input directory
	files = [i for i in os.listdir("input") if i.endswith("txt")]
	# base template
	print('Ensure that the template file is ' + INVOICE_TEMPLATE_PATH)
	# results dictionary
	results = {}
	# iterate over the files
	for file in files:
		
		# try statement
		try:
			print('Processing data file: ' + file)
			# construct data frame
			df = pd.read_csv('input/' + file, sep="|")
			# replace na's
			df = df.fillna('')

			# iterate across the data
			for index, row in df.iterrows():

				# construct filename also serves as results key
				filename = row['PatientLastName'] + ',' + row['PatientFirstName'] + ',' 
				filename += str(row['PharmacyLocationName']) + ',' + str(row['DateOfService']) + ',' 
				filename += row['FacilityName'] + ',' + row['MemberState'] + ',cms1500.pdf'

				# construct dictionary key
				person = row['PatientLastName'] + '-' + row['PatientFirstName'] + '-' + str(row['DateOfBirth'])
				
				# check if in result-set
				if person in results:
					#print('Record for: ' + person + ' already exists')
					results[person]['records'] += 1
					newrow, price = add_new_charges_to_dict(row, results[person]['records'])
					results[person]['data'] = {**results[person]['data'], **newrow}
					results[person]['totalprice'] += price
					continue

				# new person to be added

				# skip if texas
				if row['MemberState'] == 'TX' or row['MemberState'] == 'FL':
					print('Skipping record for ' + row['PatientLastName'] + ',' + row['PatientFirstName'])
					continue
				
				# construct dictionary to populate fields
				data_dict, price = getDataDict(row)

				# location address based on facility
				'''if row['FacilityName'].strip() == 'Elite Rx Facility':
					data_dict['doc_phone area'] = '551'
					data_dict['doc_phone'] = '900 2255'
					data_dict['doc_street'] = 'PO BOX 4379'
					data_dict['doc_location'] = 'WAYNE NJ 07474'
					data_dict['pin'] = '1982240735'
					data_dict['tax_id'] = '84-3330118'
				elif row['FacilityName'].strip() == 'Rx Solutions':'''

				# only streamline rx addresses to be shown
				data_dict['doc_name'] = 'StreamlineRx'
				data_dict['tax_id'] = '84-4771022'
				data_dict['doc_phone area'] = '727'
				data_dict['doc_phone'] = '565 0245'
				data_dict['doc_street'] = '2861 Executive Dr STE 210'
				data_dict['doc_location'] = 'Clearwater, FL 33762'
				data_dict['pin'] = '1184257743'

				# check diagnosis codes
				if row['DiagnosisCodes'] != '':
					data_dict = processDiagnosisCodes(data_dict, row['DiagnosisCodes'])

				# add new person
				results[person] = {'data': data_dict, 'filename': filename, 'records': 1, 'totalprice': price}

		# exception
		except Exception as e:
			print('[ERROR] There was an issue with the file ' + file + ' , it will be skipped over')

	# iterate over the people in the resultset and create files for them
	for person in results:
		persondict = results[person]
		# update the total charges
		persondict['data']['t_charge'] = str(round(persondict['totalprice'], 2))
		# write out PDF
		writeFillablePDF(INVOICE_TEMPLATE_PATH, 'output/' + persondict['filename'], persondict['data'])
		print('Writing out file for',person,'with',persondict['records']
			,'records with total cost',persondict['totalprice'],'location',row['PharmacyLocationName'])

	# end of writing
	t = time.time()-t1
	print('Completed in:', round(t,2), 'secs')
	input('You can close this window now...')
	