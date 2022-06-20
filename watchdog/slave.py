import os
import time
import shutil
import xml.etree.ElementTree as ET
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

def on_modified(event):
	print(f'slave: hey, {event.src_path} has been updated!')
	item_name = event.src_path
	if not item_name.endswith('.xml'): return
	try:
		ET.parse(item_name)
	except Exception as exception:
		print(f'Could not parse {item_name}: {exception}')
		return
	shutil.copy(item_name, f'{item_name[:-4]}.sml')

if __name__ == '__main__':
	patterns = ['*']
	ignore_patterns = None
	ignore_directories = False
	case_sensitive = True
	event_handler = PatternMatchingEventHandler()
	event_handler.on_modified = on_modified

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
