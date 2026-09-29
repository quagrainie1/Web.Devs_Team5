import json
import time
import os

# load the transactions from the json file
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(base_dir, "data", "transactions.json")

with open(file_path, "r", encoding="utf-8") as f:
    transactions = json.load(f)


# Method 1: linear search - check every record one by one
def linear_search(transactions, target_id):
    for t in transactions:
        if t["id"] == target_id:
            return t
    return None


# Method 2: dictionary lookup - id is the key, so we find it directly
def build_dictionary(transactions):
    lookup = {}
    for t in transactions:
        lookup[t["id"]] = t
    return lookup


def dictionary_search(lookup, target_id):
    return lookup.get(target_id)


# time both methods on the first "size" records
def compare(size):
    data = transactions[:size]
    lookup = build_dictionary(data)
    ids = [t["id"] for t in data]

    # make sure both methods give the same answer
    for i in ids:
        assert linear_search(data, i) == dictionary_search(lookup, i)

    runs = 1000  # repeat the search many times so the time is measurable

    start = time.perf_counter()
    for _ in range(runs):
        linear_search(data, ids[-1])  # last id = worst case for linear search
    linear_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(runs):
        dictionary_search(lookup, ids[-1])
    dict_time = time.perf_counter() - start

    print(f"{size:<10}{linear_time:<20.6f}{dict_time:<20.6f}{linear_time / dict_time:<10.1f}")


print("Searching for the last record, 1000 times each (time in seconds)")
print(f"{'Records':<10}{'Linear search':<20}{'Dictionary':<20}{'Faster by (x)':<10}")
compare(20)
compare(100)
compare(500)
compare(len(transactions))