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
	data_dict = {
	'insurance_name': str(row['EmployerName']),
	'insurance_address': str(row['EmployerStreetAddress']),
	'insurance_address2': str(row['EmployerCityAddress']),
	'insurance_city_state_zip': str(str(row['EmployerStateProvinceAddress']) + ' , ' + str(row['EmployerZipPostalCode'])), 
	'pt_name': str(row['PatientLastName'] + ' , ' + row['PatientFirstName']),
	#'insurance_type': '/Other',
	'insurance_id': process_cardholder_id(str(row['CardholderID']), row),
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
	'pt_zip': str(row['MemberZipCode']).split('.')[0],
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
	'fac_location': row['PharmacyLocationCity'] + ',' + row['PharmacyLocationState'] + ',' + str(row['PharmacyLocationZipCode']).split('.')[0],
	'doc_name': str(row['FacilityName']),
	'physician_signature': row['PharmacyLocationName'],
	'physician_date': str(datetime.today().strftime('%m-%d-%Y')),
	'pin1': str(row['ServiceProviderID']),
	}

	# charges
	price = 0
	if isinstance(row['AWP'], float) and isinstance(row['QuantityDispensed'], float):
		# check if NY state
		#if row['MemberState'] == 'NY':
			# different calculation
		#	price = round(row['AWP']*row['QuantityDispensed']*0.8, 2) + 5
		#else:
			# all other states
		price = round(row['AWP']*row['QuantityDispensed'], 2)
		
		# update the charges field
		data_dict['ch1'] = str(price)
		# total charge
		data_dict['t_charge'] = str(price)
		#print(row['PatientLastName'], row['PatientFirstName'], row['AWP'], row['QuantityDispensed'], price)

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
		'local'  + count: str(row['ServiceProviderID']),
	}

	# charges
	price = 0
	if isinstance(row['AWP'], float) and isinstance(row['QuantityDispensed'], float):
		# check if NY state
		#if row['MemberState'] == 'NY':
			# different calculation
		#	price = round(row['AWP']*row['QuantityDispensed']*0.8, 2) + 5
		#else:
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
 
	return result, characters 

# get location for the file based on the required and not-required fields
def get_location(record):
	df = pd.read_csv('input/required-fields.csv')
	required = df[df['status']=='required']
	for index, row in required.iterrows():
		field = row['field']
		if record[field] == '':
			#print('missing field',field)
			return 'missing'
	return 'completed'

# on an extra claim, move to row within the 1-6 section
def multiple_claim_extra_row(obj, index, old_index):
	# get the index as a lowercase alpha
	alphaindex = chr(95 + index)
	datadict = {
		'day' + str(index): obj['day' + str(old_index)],
		'ch' + str(index): obj['ch' + str(old_index)],
		'Suppl' + alphaindex: obj['Suppl' + chr(95 + old_index)],
		'sv'  + str(index) + '_mm_from': obj['sv'  + str(old_index) + '_mm_from'], #month
		'sv'  + str(index) + '_dd_from': obj['sv'  + str(old_index) + '_dd_from'], #day
		'sv'  + str(index) + '_yy_from': obj['sv'  + str(old_index) + '_yy_from'], #year
		'sv'  + str(index) + '_mm_end': obj['sv'  + str(old_index) + '_mm_end'], #month
		'sv'  + str(index) + '_dd_end': obj['sv'  + str(old_index) + '_dd_end'], #day
		'sv'  + str(index) + '_yy_end': obj['sv'  + str(old_index) + '_yy_end'], #year
		'place'  + str(index): obj['place'  + str(old_index)],
		'cpt'  + str(index): obj['cpt'  + str(old_index)],
		'local'  + str(index): obj['local'  + str(old_index)],
	}
	return datadict

# remove the old rows from the person dict which will not be printed on the new claim
def remove_old_rows_from_new_claim(olddict, index):
	newdict = olddict
	# remove the fields
	del newdict['data']['day' + str(index)]
	del newdict['data']['ch' + str(index)]
	del newdict['data']['Suppl' + chr(95 + index)]
	del newdict['data']['sv'  + str(index) + '_mm_from']
	del newdict['data']['sv'  + str(index) + '_dd_from']
	del newdict['data']['sv'  + str(index) + '_yy_from']
	del newdict['data']['sv'  + str(index) + '_mm_end']
	del newdict['data']['sv'  + str(index) + '_dd_end']
	del newdict['data']['sv'  + str(index) + '_yy_end']
	del newdict['data']['place'  + str(index)]
	del newdict['data']['cpt'  + str(index)]
	del newdict['data']['local'  + str(index)]
	return newdict

# create multiple claims for a single person if > 6 rows
def multiple_person_claims(persondict):
	print('\nMULTIPLE CLAIMS FOR', persondict['data']['pt_name'])
	records = persondict['records']
	# number of extra files to be made
	extras = int(records/6)
	data_keys = persondict['data'].keys()
	for i in range(extras):
		print('GENERATING EXTRA CLAIM','NUMBER',i + 1, 'FOR', persondict['data']['pt_name'],'\n')
		num = i + 1
		count = 1
		total = 0
		# create new dict to write out new claim
		newdict = persondict
		for j in range(6*num + 1, 6*(num + 1) + 1):
			# check if row is there
			keycheck = 'day' + str(j)
			if keycheck not in data_keys:
				break
			# extra row
			obj = persondict['data']
			extra_row_dict = multiple_claim_extra_row(obj, count, j)
			total += float(persondict['data']['ch' + str(j)])
			newdict['data'] = {**newdict['data'], **extra_row_dict}
			count += 1
		
		# remove rows which appeared in the old claim but not needed in the new claim
		for j in range(count, 7):
			newdict = remove_old_rows_from_new_claim(newdict, j)
		
		# update the total charges
		newdict['data']['t_charge'] = str(round(total, 2))
		# write out PDF
		newdict['filename'] = newdict['filename'].split('.')[0] + '_' + str(num) + '.pdf'
		writeFillablePDF(INVOICE_TEMPLATE_PATH, 'output/' + newdict['folder'] + '/' + newdict['filename'], newdict['data'])


if __name__ == '__main__':
	t1 = time.time()
	print('Starting the PDF autofill process...')
	print('This might take some time...')
	# iterate over data files in the input directory
	files = [i for i in os.listdir("input") if (i.endswith("txt") or i.endswith("xls") or i.endswith("xlsx"))]
	# base template
	print('Ensure that the template file is ' + INVOICE_TEMPLATE_PATH)
	# results dictionary
	results = {}
	# iterate over the files
	for file in files:
		
		# try statement
		try:
			print('Processing data file: ' + file)
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

				# construct filename also serves as results key
				filename = row['PatientLastName'] + ',' + row['PatientFirstName'] + ',' 
				filename += str(row['PharmacyLocationName']) + ',' + str(row['DateOfService']) + ','
				filename += row['MemberState'] + '_' + str(index) + '_cms1500.pdf' #row['FacilityName'] + ',' +

				# construct dictionary key
				person = row['PatientLastName'] + '-' + row['PatientFirstName'] + '-' + str(row['DateOfBirth'])
				
				# check if in result-set
				if person in results:
					#print('Record for: ' + person + ' already exists')
					results[person]['records'] += 1
					newrow, price = add_new_charges_to_dict(row, results[person]['records'])
					results[person]['data'] = {**results[person]['data'], **newrow}
					# check if less than 6 records
					if results[person]['records'] <= 6:
						results[person]['totalprice'] += price
					# diagnosis code alphabet
					if results[person]['code'] != '':
						count = str(results[person]['records'])
						results[person]['data']['diag' + count] = characters
					continue

				# new person to be added

				# skip if texas
				if row['MemberState'] == 'TX' or row['MemberState'] == 'FL':
					print('Skipping record for ' + row['PatientLastName'] + ',' + row['PatientFirstName'] + ', state = ' + row['MemberState'])
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
					data_dict, characters = processDiagnosisCodes(data_dict, row['DiagnosisCodes'])

				# add new person
				results[person] = {'data': data_dict, 'filename': filename, 'records': 1
				, 'totalprice': price, 'code': row['DiagnosisCodes'], 'folder': get_location(row)}

		# exception
		except Exception as e:
			print('[ERROR] There was an issue with the file ' + file + ' , it will be skipped over')

	# iterate over the people in the resultset and create files for them
	disclaimer = '\nDISCLAIMER\n'
	rec_count = 0
	for person in results:
		persondict = results[person]
		# update the total charges
		persondict['data']['t_charge'] = str(round(persondict['totalprice'], 2))
		# write out PDF
		writeFillablePDF(INVOICE_TEMPLATE_PATH, 'output/' + persondict['folder'] + '/' + persondict['filename'], persondict['data'])
		print('Writing out file for',person,'with',persondict['records'])
		if persondict['records'] > 6:
			disclaimer += '\nTHERE ARE ' + str(persondict['records']) + ' RECORDS FOR ' + person + ' THEIR FILE MIGHT HAVE MISSING RECORDS\n'
			multiple_person_claims(persondict)

		rec_count += 1

	# print disclaimer of possibly missing records
	print('Total',rec_count,'records')
	print(disclaimer)

	# end of writing
	t = time.time()-t1
	print('Completed in:', round(t,2), 'secs')
	input('You can close this window now...')
	