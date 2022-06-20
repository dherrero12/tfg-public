import os
import sys
import time
import queue
import scipy
import asyncpg
import asyncio
import threading
import pandas as pd
sys.path.insert(0, '..')
from utils.cos import upload_file
from utils.auth import generate_token
from utils.stats import mode, hmean, variation

async def create_pool():
	pool = await asyncpg.create_pool(PG_ENDPOINT, min_size=32, max_size=32)
	return pool

class Dataset:
	def __init__(self, loop, pool, percent_sample=100, batch_size=32):
		self.loop = loop
		self.batch_size = batch_size
		self.pool = pool
		self.percent_sample = percent_sample

	async def iter_start_point_cursor(self):
		def to_date(column):
			return f"TO_DATE({column}, 'DD.MM.YYYY HH24:MI:SS')" if column.endswith('starttime') else f"TO_DATE({column}, 'YYYY-MM-DD')"

		async with self.pool.acquire() as connection:
			async with connection.transaction():
				async for record in connection.cursor(f'''
SELECT *
FROM public.log 
TABLESAMPLE SYSTEM ({self.percent_sample})
JOIN public.user
ON public.log.user_id = public.user.id
LEFT JOIN public.test AS previous
ON previous.id = (
	SELECT id
	FROM public.test
	WHERE public.test.user_id = public.log.user_id
	AND {to_date("public.log.starttime")} > {to_date("public.test.fergo")}
	ORDER BY {to_date("public.test.fergo")} DESC
	LIMIT 1)
JOIN public.test AS upcoming
ON upcoming.id = (
	SELECT id
	FROM public.test
	WHERE public.test.user_id = public.log.user_id
	AND {to_date("public.log.starttime")} < {to_date("public.test.fergo")}
	ORDER BY {to_date("public.test.fergo")}
	LIMIT 1)'''):
					yield record
	async def get_sequence(self, start_point):
		log_id = start_point[0]
		async with self.pool.acquire() as connection:
			result = await connection.fetch(f'''
SELECT *
FROM public.sample
WHERE sample.log_id = {log_id}''')

		def convert_result(result):
			if not result: return
			log = dict()
			for index, (key, value) in enumerate(start_point.items()):
				if index < 58 or index == 59:
					prefix = 'log'
				elif index < 59: 
					prefix = ''
				elif index < 63:
					prefix = 'user'
				elif index < 104:
					prefix = 'previous'
				elif index < 105:
					prefix = ''
				else:
					prefix = 'next'
				log[f'{prefix}_{key}' if prefix else key] = value
			del log['next_user_id']
			log = pd.Series(log).to_frame().T		

			columns = [f'sample_{key}' for key in result[0].keys()]
			samples = pd.DataFrame(result, columns=columns)
			aggregated = samples.drop(['sample_id', 'sample_tm', 'sample_st', 'sample_log_id'], axis=1).agg(['std', 'var', 'min', 'max', mode, 'median', 'mean', 'mad', 'kurt', 'skew', 'sem', hmean, variation])
			aggregated = aggregated.unstack().to_frame().sort_index(level=1).T
			aggregated.columns = aggregated.columns.map('_'.join)
			return pd.concat([log, aggregated], axis=1, join='inner')

		return convert_result(result) 

	async def __aiter__(self):
		start_points = list() 
		async def map_start_points():
			tasks = map(self.get_sequence, start_points)
			batch = await asyncio.gather(*tasks)
			start_points.clear()
			return batch

		async for start_point in self.iter_start_point_cursor():
			start_points.append(start_point)
			if len(start_points) == self.batch_size:
				batch = await map_start_points()
				yield batch
		batch = await map_start_points()
		if len(batch) > 0:
			yield batch
	
	def __iter__(self):
		return wrap_async_iter(self, self.loop)

def wrap_async_iter(ait, loop):
	dequeue = queue.Queue()
	_END = object()

	def yield_queue_items():
		while True:
			next_item = dequeue.get()
			if next_item is _END:
				break
			yield next_item
		#async_result.result()

	async def aiter_to_queue():
		try:
			async for item in ait:
				dequeue.put(item)
		finally:
			dequeue.put(_END)

	async_result = asyncio.run_coroutine_threadsafe(aiter_to_queue(), loop)
	return yield_queue_items()

PG_HOSTNAME = os.getenv('PG_HOSTNAME')
PG_PORT = os.getenv('PG_PORT')
PG_USER	= os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_SSL_MODE = os.getenv('PG_SSL_MODE')
PG_SSL_ROOT_CERT = os.getenv('PG_SSL_ROOT_CERT')
PG_DATABASE = os.getenv('PG_DATABASE')
PG_ENDPOINT = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOSTNAME}:{PG_PORT}/{PG_DATABASE}?sslmode={PG_SSL_MODE}'

if __name__ == '__main__':
	pg_path = os.path.join(os.path.expanduser('~'), '.postgresql')
	if not os.path.exists(pg_path):
		os.mkdir(pg_path)
	with open(os.path.join(pg_path, 'root.crt'), mode='w') as file:
		file.writelines([f'{line}\n' for line in PG_SSL_ROOT_CERT.split('\\n')])

	loop = asyncio.get_event_loop()
	threading.Thread(target=loop.run_forever, daemon=True).start()

	pool = asyncio.run_coroutine_threadsafe(create_pool(), loop=loop).result()
	database = Dataset(percent_sample=100, loop=loop, pool=pool)
	dataset = pd.concat(row for batch in database for row in batch)
	item_name = f'{int(time.time())}-dataset.csv'
	dataset.to_csv(item_name, index=False)
	
	iam_token = generate_token()
	upload_file(item_name, iam_token)
