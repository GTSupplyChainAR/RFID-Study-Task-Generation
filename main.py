import numpy
import json
import os


STUDY_METHODS = [
    'pick-by-light_button',
    'pick-by-hud_rfid',
    'pick-by-paper_none',
    'pick-by-paper_barcode',
]

NUM_TRAINING_TASKS = 10
NUM_TESTING_TASKS = 10


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

    def __str__(self):
        return self.tag

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


def get_source_bins_for_order(num_source_bins):
    """
    Randomly selects n source bins that subjects will pick from in an order.

    Parameters
    ----------
    num_source_bins: int
        The number of source bins in this order

    Returns
    -------
        A list of dictionaries with keys 'binTag' and 'numItems'.
        Entries are sorted alphabetically by each 'binTag'.

    Examples
    --------
    >>> get_source_bins_for_order(3)
    [
        {
            'binTag': 'A32',
            'numItems': 2
        },
        {
            'binTag': 'B12',
            'numItems': 1
        }
    ]

    """

    # Gets source bins with replacement meaning that there may be duplicate Bin tags
    # When num_source_bins=3, this may return bins with tags 'A32', 'B12', 'A32'.
    randomly_selected_bins = numpy.random.choice(BINS, num_source_bins, replace=True)
    selected_bins = list(randomly_selected_bins)

    # In the loops below, we want to map a source bin tag to the number of times it was selected.
    # See the Examples in the docstring for the output of selecting 'A32', 'B12', 'A32'.

    source_bins = []

    # Group selected bins by bin tag and count instances of that tag in the list
    i = 0
    while i < len(selected_bins):
        current_bin = selected_bins[i]
        count_of_bins_with_tag = 1

        # Start searching for duplicate bin tags after current_bin
        j = i + 1
        while j < len(selected_bins):
            if current_bin.tag == selected_bins[j].tag:
                selected_bins.pop(j)
                count_of_bins_with_tag += 1
                # We removed a bin at j, so don't increment j
            else:
                # The bin at j is fine, so move on
                j += 1

        i += 1

        source_bins.append({
            'binTag': current_bin.tag,
            'numItems': count_of_bins_with_tag
        })

    # Sort (in-place) the source_bins by their tags
    source_bins.sort(key=lambda sb: sb['binTag'])

    assert len(set([sb['binTag'] for sb in source_bins])) == len(source_bins), \
        "There is a duplicated source bin tag which shouldn't happened!"

    return source_bins


def get_orders_for_task():
    receiving_bin_tags = ['C11', 'C12', 'C13']

    orders = []

    for i, receiving_bin_tag in enumerate(receiving_bin_tags):
        orders.append({
            'orderId': i + 1,
            'sourceBins': get_source_bins_for_order(
                num_source_bins=numpy.random.randint(8, 13)
            ),
            'receivingBinTag': receiving_bin_tag,
        })

    return orders


def get_tasks_for_method(num_tasks):
    tasks = []

    task_id = 1
    while task_id <= num_tasks:
        task = {
            'taskId': task_id,
            'orders': get_orders_for_task()
        }
        tasks.append(task)

        task_id += 1

    return tasks


def write_tasks_to_output_file(tasks, output_file_name):
    """ Writes the given tasks to the given output file """
    with open(output_file_name, mode='w+') as f:
        json.dump({'tasks': tasks}, f, indent=4)


def print_task_ordering(tasks):
    """ Simply prints out all task IDs"""
    print([task['taskId'] for task in tasks])


def assign_training_testing_labels_to_tasks(tasks, num_training, num_testing):
    """ Called after shuffling tasks, this method assigned the isTrainingTask label appropriately"""
    assert len(tasks) == num_training + num_testing

    i = 0
    while i < len(tasks):
        tasks[i]['isTrainingTask'] = i < num_training
        i += 1

    # Ensure every task has a isTrainingTask value assigned
    assert all('isTrainingTask' in task_dict for task_dict in tasks)

    # Ensure there isn't a testing task before a training task
    assert not any(tasks[i] is False and tasks[i + 1] is True for i in range(len(tasks) - 1))

    # Ensure the counts expected are achieved
    assert len([task for task in tasks if task['isTrainingTask']]) == num_training
    assert len([task for task in tasks if not task['isTrainingTask']]) == num_testing


if __name__ == '__main__':
    numpy.random.seed(1)

    tasks = get_tasks_for_method(
        num_tasks=NUM_TRAINING_TASKS + NUM_TESTING_TASKS
    )

    # Create an output directory, if it doesn't already exist
    if not os.path.isdir('output'):
        os.mkdir('output')

    # Write the "master" list of tasks
    assign_training_testing_labels_to_tasks(tasks, NUM_TRAINING_TASKS, NUM_TESTING_TASKS)
    print_task_ordering(tasks)
    write_tasks_to_output_file(tasks, 'output/tasks-MASTER.json')

    # For each method, shuffle the tasks and write them to an output file
    for method_name in STUDY_METHODS:
        # Shuffle the tasks, in-place
        numpy.random.shuffle(tasks)

        # Re-assign the training/testing labels and write to an output file
        assign_training_testing_labels_to_tasks(tasks, NUM_TRAINING_TASKS, NUM_TESTING_TASKS)
        print_task_ordering(tasks)
        write_tasks_to_output_file(tasks, 'output/tasks-shuffled-for-%s.json' % (method_name,))
