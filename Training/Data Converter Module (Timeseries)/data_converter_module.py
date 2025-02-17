import pymongo
from pymongo import MongoClient
import pprint
import sys
from random import shuffle

# mongodb connection setup
client = MongoClient("localhost", 27017, maxPoolSize=50)
db = client['INDIVIDUAL_SEGMENTED']

# user modifable variables
collection_name_prefix = None
num_tags = 232
unified_sequence_length = 30
train_test_ratio = 0.7

def get_collection(collection_name):
    collection = db[collection_name]
    pointer = collection.find({}).sort("_id", 1)

    return collection, pointer

def get_all_collection_names():
    collections = db.collection_names()

    shuffle(collections)

    num_collections = len(collections)

    return num_collections, collections

def get_collection_names():
    collections = db.collection_names()

    shuffle(collections)

    num_collections = len(collections)

    num_train_collections = train_test_ratio * num_collections
    num_train_collections = round(num_train_collections)
    num_test_collections = (num_collections-num_train_collections)

    train_collections = []
    test_collections = []

    for i in range(0, num_collections):
        if i < num_train_collections:
            train_collections.append(collections[i])
        else:
            test_collections.append(collections[i])

    return num_collections, collections, num_train_collections, num_test_collections, train_collections, test_collections

def split_tags():
    num_collections, collection_names = get_all_collection_names()
    for collection in collection_names:
        split_static_and_object_tags(collection)

def split_static_and_object_tags(collection_name):
    collection, pointer = get_collection(collection_name)

    for document in pointer:
        query = {"_id": document["_id"]}

        object_tags = []
        for i in range(0, len(document['tags'])):
            if '9999' in document['tags'][i]['_id']:
                object_tags.append(document['tags'][i])
                
                document_id = document['tags'][i]['_id']
                remove = {"$pull": {"tags": {"_id": document_id}}}
                # comment out line below to delete copy of object tags in original tag pool
                collection.update_one(query, remove)
        
        new_array = {"$set": {"object_tags": object_tags}}

        collection.update_one(query, new_array)

def progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')

    if iteration == total: 
        print()

def read_tag_epcs():
    with open("static.txt") as f:
        tag_epcs = f.read().splitlines() 
    f.close()

    return tag_epcs

def print_collection(pointer):
    for document in pointer:
        pprint.pprint(document)

def get_label(full_label):
    label = 0

    if full_label == "bedroom_location_bed":
        label = 0
    elif full_label == "bedroom_location_drawers":
        label = 1
    elif full_label == "bedroom_location_mirror":
        label = 2
    elif full_label == "bedroom_location_wardrobe":
        label = 3
    elif full_label == "kitchen_location_table":
        label = 4
    elif full_label == "kitchen_location_worktop_corner":
        label = 5
    elif full_label == "kitchen_location_worktop_sink":
        label = 6
    elif full_label == "TRA":
        label = 7

    # if full_label == "bedroom_location_bed":
    #     label = 0
    # elif full_label == "bedroom_location_drawers":
    #     label = 1
    # elif full_label == "bedroom_location_mirror":
    #     label = 2
    # elif full_label == "bedroom_location_wardrobe":
    #     label = 3
    # elif full_label == "TRA":
    #     label = 4

    # if full_label == "activity_dressing":
    #     label = 0
    # elif full_label == "activity_brushing_teeth":
    #     label = 1
    # elif full_label == "activity_brushing_hair":
    #     label = 2
    # elif full_label == "activity_prepare_te":
    #     label = 3
    # elif full_label == "activity_prepare_coffee":
    #     label = 4
    # elif full_label == "activity_prepare_sandwich":
    #     label = 5
    # elif full_label == "activity_eating_drinking":
    #     label = 6
    # elif full_label == "activity_wash_dishes":
    #     label = 7
    # elif full_label == "activity_sleeping":
    #     label = 8
    # elif full_label == "activity_reading":
    #     label = 9
    # elif full_label == "activity_prepare_cake":
    #     label = 10
    # elif full_label == "TRA":
    #     label = 10

    # if full_label == "bedroom_location_bed":
    #     label = 0
    # elif full_label == "bedroom_location_chair":
    #     label = 0
    # elif full_label == "bedroom_location_drawers":
    #     label = 0
    # elif full_label == "bedroom_location_mirror":
    #     label = 0
    # elif full_label == "bedroom_location_wardrobe":
    #     label = 0
    # elif full_label == "kitchen_location_table":
    #     label = 1
    # elif full_label == "kitchen_location_worktop_corner":
    #     label = 1
    # elif full_label == "kitchen_location_worktop_sink":
    #     label = 1
    # elif full_label == "kitchen_location_worktop_stove":
    #     label = 1
    # elif full_label == "TRA":
    #     label = 2

    label = str(label)

    return label

def create_dataset_files(tag_epcs):
    # training set
    for tag in tag_epcs:
        with open("dataset/train/input/{}_peakRSSI.txt".format(tag), "w") as f:
            f.write("")
            f.close

    with open("dataset/train/y_train.txt".format(), "w") as f:
            f.write("")
            f.close

    # test set
    for tag in tag_epcs:
        with open("dataset/test/input/{}_peakRSSI.txt".format(tag), "w") as f:
            f.write("")
            f.close

    with open("dataset/test/y_test.txt".format(), "w") as f:
            f.write("")
            f.close

def write_dataset_input_files(tag_epcs, num_collections, num_train_collections, num_test_collections, train_collections, test_collections):
    # write to training set
    print("[write_dataset_input_files][INFO] Writing training set...")
    progress_bar(0, num_train_collections, prefix = 'Progress:', suffix = 'Complete', length = 50)

    for i in range(0, num_train_collections):
        progress_bar(i + 1, num_train_collections, prefix = 'Progress:', suffix = 'Complete', length = 50)
        collection, pointer = get_collection(train_collections[i])

        labelled = 0
        sequence_length = 0

        # for every snapshot in sample (collection)
        for document in pointer:
            sequence_length = sequence_length + 1

            if labelled == 0:
                label = get_label(document["location_label"])

                with open("dataset/train/y_train.txt".format(), "a") as f:
                    f.write(label)
                    f.write('\n')
                    f.close()

                labelled = 1

            # appends value from current snapshot to every vector
            for j in range(0, num_tags):
                epc = document["tags"][j]["_id"]
                antenna = document["tags"][j]["antenna"]
                peakRSSI = document["tags"][j]["peakRSSI"]
                phaseAngle = document["tags"][j]["phaseAngle"]
                velocity = document["tags"][j]["velocity"]

                with open("dataset/train/input/{}_peakRSSI.txt".format(epc), "a") as f:
                    f.write(peakRSSI)
                    f.write("  ")
                    f.close()

            if sequence_length == unified_sequence_length:
                break

        # pad timeseries and add new lines at end of every sample
        if sequence_length < unified_sequence_length:
            sequence_length_diff = unified_sequence_length - sequence_length
            for tag in tag_epcs:
                for j in range(0, sequence_length_diff):
                    with open("dataset/train/input/{}_peakRSSI.txt".format(tag), "a") as f:
                        f.write("0")
                        f.write("  ")
                        f.close()

        for tag in tag_epcs:
            with open("dataset/train/input/{}_peakRSSI.txt".format(tag), "a") as f:
                f.write('\n')
                f.close()

    print()

    # write to test set
    print("[write_dataset_input_files][INFO] Writing test set...")
    progress_bar(0, num_test_collections, prefix = 'Progress:', suffix = 'Complete', length = 50)

    for i in range(0, num_test_collections):
        progress_bar(i + 1, num_test_collections, prefix = 'Progress:', suffix = 'Complete', length = 50)
        collection, pointer = get_collection(test_collections[i])

        labelled = 0
        sequence_length = 0

        for document in pointer:
            sequence_length = sequence_length + 1

            if labelled == 0:
                label = get_label(document["location_label"])

                with open("dataset/test/y_test.txt".format(), "a") as f:
                    f.write(label)
                    f.write('\n')
                    f.close()

                labelled = 1

            for j in range(0, num_tags):
                epc = document["tags"][j]["_id"]
                antenna = document["tags"][j]["antenna"]
                peakRSSI = document["tags"][j]["peakRSSI"]
                phaseAngle = document["tags"][j]["phaseAngle"]
                velocity = document["tags"][j]["velocity"]

                with open("dataset/test/input/{}_peakRSSI.txt".format(epc), "a") as f:
                    f.write(peakRSSI)
                    f.write("  ")
                    f.close()

            if sequence_length == unified_sequence_length:
                break

        # add new lines at end of every sample
        if sequence_length < unified_sequence_length :
            sequence_length_diff = unified_sequence_length - sequence_length
            for tag in tag_epcs:
                for j in range(0, sequence_length_diff):
                    with open("dataset/test/input/{}_peakRSSI.txt".format(tag), "a") as f:
                        f.write("0")
                        f.write("  ")
                        f.close()

        for tag in tag_epcs:
            with open("dataset/test/input/{}_peakRSSI.txt".format(tag), "a") as f:
                f.write('\n')
                f.close()

    print()

def main():
    # clear the terminal
    print(chr(27) + "[2J")
    print("* * * * * * * * * * * * *")
    print("* Data Converter Module *")
    print("* * * * * * * * * * * * *")
    print("- Version 1.0")
    print("- Developed by Ronnie Smith")
    print("- github: @ronsm | email: ronnie.smith@ed.ac.uk | web: ronsm.com")
    print()

    num_arguments = len(sys.argv)

    global database_name

    if num_arguments != 1:
        print("[MAIN][INFO] Invalid arguments. Usage: python3 data_converter_module.py")
        exit()

    # read in tag EPCs
    print("[MAIN][STAT] Reading in tag EPCs from tags.txt...", end="", flush=True)
    tag_epcs = read_tag_epcs()
    print("[DONE]")

    # print("[MAIN][STAT] Splitting static and objects tags...", end="", flush=True)
    # split_tags()
    # print("[DONE]")

    # get the names of all collections (sessions) in the given database
    print("[MAIN][STAT] Getting all collection (session) names from database...", end="", flush=True)
    num_collections, collections, num_train_collections, num_test_collections, train_collections, test_collections = get_collection_names()
    print("[DONE]")

    # create output files in 'Dataset' folder
    print("[MAIN][STAT] Creating (overwriting) output files in dataset folder...", end="", flush=True)
    create_dataset_files(tag_epcs)
    print("[DONE]")

    # write to dataset input files from database
    print("[MAIN][INFO] Dataset will be split at a ratio of", train_test_ratio, "for train/test sets.")
    print("[MAIN][STAT] Writing to dataset files with database (MongoDB) data...")
    write_dataset_input_files(tag_epcs, num_collections, num_train_collections, num_test_collections, train_collections, test_collections)

if __name__== "__main__":
  main()