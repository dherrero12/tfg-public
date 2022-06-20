import os
import sys
import time
import shutil
import openpyxl
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
sys.path.insert(0, '..')
from utils.hash import hash_md5
from utils.cos import upload_file
from utils.auth import generate_token

def on_modified(event, iam_token):
	print(f'main: hey, {event.src_path} has been updated!')
	item_name = event.src_path
	if item_name.endswith('.xlsx'):
		workbook = openpyxl.load_workbook(item_name, data_only=True)
		worksheet = workbook[workbook.get_sheet_names()[0]]
		values = worksheet.values
		columns = next(values)[0:]
		data = pd.DataFrame(values, columns=columns)
		data['ID'] = data['Nombre'].apply(hash_md5)
		data.drop(['Codigo', 'Nombre'], axis=1, inplace=True)
		data.to_csv(os.path.join('..', 'data', f'{int(time.time())}-tests.csv'), index=False)
		return
	if not item_name.endswith('.sml') and not item_name.endswith('.csv'): return
	upload_file(item_name, iam_token, proxy=True)

if __name__ == '__main__':
	patterns = ['*']
	ignore_patterns = None
	ignore_directories = False
	case_sensitive = True
	event_handler = PatternMatchingEventHandler()
	iam_token = generate_token()
	event_handler.on_modified = lambda event: on_modified(event, iam_token)

	path = os.path.join('..', 'data')
	recursive = True
	observer = Observer()
	observer.schedule(event_handler, path, recursive=recursive)
	observer.start()
	try:
		while True:
			time.sleep(1)
	finally:
		observer.stop()
		observer.join()
