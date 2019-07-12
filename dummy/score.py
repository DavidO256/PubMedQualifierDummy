from argparse import ArgumentParser
import numpy as np
import dummy.data


def calculate_score(probabilities, testing_dataset, critical_ui, use_journals):
	critical_length = len(critical_ui)
	f1, recall, precision = list(), list(), list()
	for descriptor_ui, qualifier_ui, journal in testing_dataset:
		critical_index = critical_ui.index(qualifier_ui)
		y_pred = np.zeros(critical_length)
		y_true = np.zeros(critical_length)
		y_true[critical_index] = 1
		for i in critical_ui:
			if use_journals:
				if journal in probabilities:
					if descriptor_ui in probabilities[journal]:
						if i in probabilities[journal][descriptor_ui]:
							y_pred[critical_ui.index(i)] = probabilities[journal][descriptor_ui][i]
			else:
				if descriptor_ui in probabilities:
					if i in probabilities[descriptor_ui]:
						y_pred[critical_ui.index(i)] = probabilities[descriptor_ui][i]
		f1_score, precision_score, recall_score = score(y_true, y_pred)
		f1.append(f1_score)
		recall.append(recall_score)
		precision.append(precision_score)
	print("F1 Score:\t%f\nPrecision:\t%f\nRecall:\t\t%f" % (np.average(f1) / critical_length,
															np.average(precision) / critical_length,
															np.average(recall) / critical_length))


def score(y_true, y_pred):
	matches = 0
	predictions = 0
	actual_number = 0
	for i in range(len(y_true)):
		if y_true[i] == y_pred[i]:
			matches += 1
		if y_true[i] == 1:
			actual_number += 1
		if y_pred[i] == 1:
			predictions += 1
	precision = matches / (predictions + 1e-7)
	recall = matches / (actual_number + 1e-7)
	f1 = 2 * precision * recall / (precision + recall + 1e-7)
	return f1, precision, recall


if __name__ == '__main__':
	descriptions = {
		'qualifiers': "List of qualifier unique identifiers to score.\nExample: --qualifiers Q012345 Q543210",
		'directory': "Path to directory for reading and/or writing data.\nExample --directory ~/data",
		'database': "MEDLINE database in the MySQL server to query.\nExample: --database medline",
		'hostname': "Address of the MySQL server to connect to.\nExample: --hostname 127.0.0.1",
		'username': "Username for server authentication.\nExample: --username helloworld",
		'password': "Password for server authentication.\nExample: --password helloworld",
		"journals": "Enable use of journals in probability calculations."
	}
	parser = ArgumentParser()
	parser.add_argument('--qualifiers', nargs='*', required=True, help=descriptions['qualifiers'])
	parser.add_argument('--directory', type=str, default="data", help=descriptions['directory'])
	parser.add_argument('--database', type=str, help=descriptions['database'])
	parser.add_argument('--hostname', type=str, help=descriptions['hostname'])
	parser.add_argument('--username', default=None, type=str, help=descriptions['username'])
	parser.add_argument('--password', default=None, type=str, help=descriptions['password'])
	parser.add_argument('--journals', action='store_true', help=descriptions['journals'])

	arguments = parser.parse_args()
	probabilities, testing_data = dummy.data.load(arguments.qualifiers, arguments.journals, arguments.directory,
												  user=arguments.username, password=arguments.password,
												  database=arguments.database, host=arguments.hostname)
	calculate_score(probabilities, testing_data, arguments.qualifiers, arguments.journals)
