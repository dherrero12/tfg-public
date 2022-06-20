import numpy as np

def mode(data):
	return data.value_counts().index[0]

def hmean(data, axis=0):
	return data.shape[axis] / np.sum(1.0 / data, axis=axis)

def variation(data, axis=0):
	return data.std(axis) / data.mean(axis)
