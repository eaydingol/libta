import os
from libta.path_analysis import *


def get_xmls(test_dir):
    paths = []
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.endswith(".xml"):
                paths.append(str(os.path.join(root, file)))
    return paths


def path_from_query_comment(nta):
    query = str(nta.queries[0].comment)
    index = int(str(nta.queries[1].comment))
    path = construct_path_from_labels(query.split()[::2], nta.templates[index])

    return path