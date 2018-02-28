import numpy
import json


class Bin(object):
    def __init__(self, shelve_label, row_number, column_number):
        """
        :param shelve_label: A or B
        :param row_number: 1 to 4
        :param column_number: 1 to 3
        """
        self.shelve_label = shelve_label
        self.row_number = row_number
        self.column_number = column_number

    @property
    def tag(self):
        return "%s%s%s" % (self.shelve_label, self.row_number, self.column_number)

    def __eq__(self, other):
        return self.tag == other.tag


def get_bins():
    bins = []
    for shelve_label in ('A', 'B'):
        for row_number in range(1, 5):
            for column_number in range(1, 4):
                bins.append(Bin(shelve_label, row_number, column_number))
    return bins


BINS = get_bins()


def get_source_bins_for_order(n):
    selected_bins = numpy.random.choice(BINS, n, replace=True)
    selected_bins = list(selected_bins)

    source_bins = []

    i = 0
    while i < len(selected_bins):
        current_bin = selected_bins[i]
        count = 1

        j = i + 1
        while j < len(selected_bins):
            if current_bin == selected_bins[j]:
                selected_bins.pop(j)
                count += 1

            j += 1

        i += 1

        source_bins.append({
            'binTag': current_bin.tag,
            'numItems': count
        })

    source_bins.sort(key=lambda sb: sb['binTag'][0])

    return source_bins


def get_orders_for_task(n):
    orders = []

    order_id = 1
    while order_id <= n:
        orders.append({
            'orderId': order_id,
            'sourceBins': get_source_bins_for_order(
                n=numpy.random.randint(4, 7)
            ),
            'receivingBinTag': 'X00',
        })

        order_id += 1

    return orders


def get_tasks_for_method(num_training_tasks, num_testing_tasks):
    tasks = []

    task_id = 1
    while task_id <= num_training_tasks + num_testing_tasks:
        task = {
            'taskId': task_id,
            'isTrainingTask': task_id <= num_training_tasks,
            'orders': get_orders_for_task(
                n=numpy.random.randint(4, 7)
            )
        }
        tasks.append(task)

        task_id += 1

    return tasks


def get_methods_for_subject():
    method_types = ['pick-to-paper', 'pick-to-light', 'pick-to-rfid']

    methods = []
    for method_type in method_types:
        methods.append({
            'methodType': method_type,
            'tasks': get_tasks_for_method(10, 10)
        })

    return methods


if __name__ == '__main__':
    numpy.random.RandomState(42)

    methods_for_one_subject = get_methods_for_subject()
    with open('output.json', mode='w+') as f:
        json.dump(methods_for_one_subject, f, indent=4)
