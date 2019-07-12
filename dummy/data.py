import mysql.connector
import numpy as np
import os.path
import json


def fetch_data(critical_ui, **kwargs):
	if 'host' not in kwargs or 'database' not in kwargs:
		raise ValueError("Missing hostname and database. Check help and try again.")
	connection = mysql.connector.connect(**kwargs)
	print("Connected.")
	cursor = connection.cursor(buffered=True)
	query = """SELECT 
		md.ui as 'descriptor_ui',
		mq.ui as 'qualifier_ui',
		c.journal_id as 'journal',
		YEAR(c.date_completed) as 'year'
	FROM
		citation_mesh_topics AS cmt,
		mesh_topics AS mt,
		mesh_descriptors AS md,
		citations AS c,
		mesh_qualifiers AS mq
	WHERE
		cmt.citation_id = c.id
			AND cmt.mesh_topic_id = mt.id
			AND mt.mesh_descriptor_id = md.id
			AND mt.mesh_qualifier_id = mq.id
			AND YEAR(c.date_completed) >= 2015
			AND c.indexing_method = 'Human'"""
	descriptors_count = dict()
	critical_count = dict()
	cursor.execute(query)
	entries = list()
	for descriptor_ui, qualifier_ui, journal, year in cursor.fetchall():
		if qualifier_ui in critical_ui:
			entries.append((descriptor_ui, qualifier_ui, journal, year))
	cursor.close()
	connection.close()
	print("Saving Data")
	with open("data/data.json", 'w') as f:
		json.dump(entries, f)
		f.close()
	return entries


def make_datasets(entries, training_path, testing_path, ratio=0.85, save=True):
	training_dataset = make_training_dataset(entries[:int(ratio * len(entries))])
	testing_dataset = make_testing_dataset(entries[int(ratio * len(entries)):])
	if save:
		parent, _ = os.path.split(training_path)
		if not os.path.exists(parent):
			os.mkdirs(parent)
		with open(training_path, 'w') as f:
			json.dump(training_dataset, f)
			f.close()
		with open(testing_path, 'w') as f:
			json.dump(testing_dataset, f)
			f.close()
	return training_dataset, testing_dataset


def make_training_dataset(entries):
	return make_probabilities_with_journals(entries)


def make_probabilities_with_journals(entries):
	descriptors_count = dict()
	critical_count = dict()
	for descriptor_ui, qualifier_ui, journal, year in entries:
		if journal not in critical_count:
			critical_count[journal] = dict()
		if descriptor_ui in critical_count[journal]:
			if qualifier_ui in critical_count[journal][descriptor_ui]:
				critical_count[journal][descriptor_ui][qualifier_ui] += 1
			else:
				critical_count[journal][descriptor_ui][qualifier_ui] = 1
		else:
			critical_count[journal][descriptor_ui] = {qualifier_ui : 1}
		if journal not in descriptors_count:
			descriptors_count[journal] = dict()
		if descriptor_ui in descriptors_count[journal]:
			descriptors_count[journal][descriptor_ui] += 1
		else:
			descriptors_count[journal][descriptor_ui] = 1
	probabilities = dict()
	for journal, descriptors in critical_count.items():
		for descriptor_ui in descriptors:
			for qualifier_ui in descriptors[descriptor_ui]:
				if journal not in probabilities:
					probabilities[journal] = {}
				if descriptor_ui not in probabilities[journal]:
					probabilities[journal][descriptor_ui] = dict()
				probabilities[journal][descriptor_ui][qualifier_ui] = np.random.binomial(1, descriptors[descriptor_ui][qualifier_ui] / descriptors_count[journal][descriptor_ui])
	return probabilities


def make_probabilities_without_journals(entries):
	descriptors_count = dict()
	critical_count = dict()
	for descriptor_ui, qualifier_ui, journal, year in entries:
		if descriptor_ui in critical_count:
			if qualifier_ui in critical_count[descriptor_ui]:
				critical_count[descriptor_ui][qualifier_ui] += 1
			else:
				critical_count[descriptor_ui][qualifier_ui] = 1
		else:
			critical_count[descriptor_ui] = {qualifier_ui : 1}
		
		if descriptor_ui in descriptors_count:
			descriptors_count[descriptor_ui] += 1
		else:
			descriptors_count[descriptor_ui] = 1
	probabilities = dict()
	for descriptor_ui, qualifiers in critical_count.items():
		for qualifier_ui in qualifiers:
			if descriptor_ui not in probabilities:
				probabilities[descriptor_ui] = dict()
			probabilities[descriptor_ui][qualifier_ui] = np.random.binomial(1, qualifiers[qualifier_ui] / descriptors_count[descriptor_ui])
	return probabilities


def make_testing_dataset(entries):
	dataset = list()
	for pmid, descriptor_ui, qualifier_ui, journal, year in entries:
		dataset.append((descriptor_ui, qualifier_ui, journal))
	return dataset
		

def load(critical_ui, use_journals, directory, **kwargs):
	if use_journals:
		directory = os.path.join(directory, "journals")	
	training_path = os.path.join(directory, "training.json")
	testing_path = os.path.join(directory, "testing.json")
	if os.path.exists(training_path) and os.path.exists(testing_path):
		with open(training_path) as f:
			training_dataset = json.load(f)
			f.close()
		with open(testing_path) as f:
			testing_dataset = json.load(f)
			f.close()
		return training_dataset, testing_dataset
	else:
		if os.path.exists("data/data.json"):
			print("Recreating training and testing data from \"data/data.json\"")
			with open(os.path.join(directory, "data.json")) as f:
				entries = json.load(f)
				f.close()
			return make_datasets(entries, training_path, testing_path, save=True)
		else:
			print("Fetching data from database.")
			return make_datasets(fetch_data(critical_ui, **{i: j for i, j in kwargs.items() if j is not None}),
								 training_path, testing_path, save=True)
