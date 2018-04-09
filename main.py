import numpy
import json
import os

# This is the version number of the JSON file.
# Use this number to keep all copies of the tasks in sync across the study methods.
VERSION = "1.2"

# The Google Glass HUD client can only fit these number of orders on the screen at once.
MAX_ORDERS_PER_RACK = 6

# These are the names of all of the methods in this study.
# These names should be clean to use as file names in any OS
STUDY_METHODS = [
    'pick-by-light_button',
    'pick-by-hud_rfid',
    'pick-by-paper_none',
    'pick-by-paper_barcode',
]

# This is the number of tasks to include in the training files
NUM_TRAINING_TASKS = 5

# This is the number of tasks to include in testing files
NUM_TESTING_TASKS = 10


class Bin(object):
    """ A simple structure to hold information about a source bin. """

    def __init__(self, rack, row_number, column_number):
        """
        :param rack: A or B
        :param row_number: 1 to 4
        :param column_number: 1 to 3
        """
        self.rack = rack
        self.row_number = row_number
        self.column_number = column_number

    @property
    def tag(self):
        return "%s%s%s" % (self.rack, self.row_number, self.column_number)

    def __str__(self):
        return self.tag

    def __eq__(self, other):
        return self.tag == other.tag


def generate_bins():
    """ Generates all bins in our layout """
    bins = []
    racks = ('A', 'B')
    for rack in racks:
        for row_number in range(1, 5):
            for column_number in range(1, 4):
                bins.append(Bin(rack, row_number, column_number))
    return bins


BINS = generate_bins()


def get_source_bins_for_order(racks_and_num_source_bins):
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
    >>> get_source_bins_for_order({'A': 2, 'B': 1})
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

    source_bins = []
    for rack, num_source_bins in racks_and_num_source_bins.iteritems():
        # Get bins that are in this rack
        bins_in_rack = [bin for bin in BINS if bin.rack == rack]
        # Then, randomly select num_source_bins from that rack
        randomly_selected_bins = numpy.random.choice(
            a=bins_in_rack,
            size=num_source_bins,
            replace=False,                  # select a unique set of bins
        )

        for bin in randomly_selected_bins:
            source_bins.append({
                'binTag': bin.tag,
                'numItems': numpy.random.choice(
                    a=[1, 2, 3],            # the number of items in this bin
                    size=None,              # select one value
                    replace=False,
                    p=[0.87, 0.08, 0.05],   # with this probability distribution
                )
            })

    # Sort (in-place) the source_bins by their tags
    source_bins.sort(key=lambda sb: sb['binTag'])

    assert len(set([sb['binTag'] for sb in source_bins])) == len(source_bins), \
        "There is a duplicated source bin tag which shouldn't happened!"

    for rack in racks_and_num_source_bins:
        bins_in_rack = [bin for bin in source_bins if bin['binTag'][0] == rack]
        assert len(bins_in_rack) <= MAX_ORDERS_PER_RACK, bins_in_rack

    return source_bins


def get_orders_for_task():
    receiving_bin_tags = ['C11', 'C12', 'C13']

    orders = []

    for i, receiving_bin_tag in enumerate(receiving_bin_tags):
        orders.append({
            'orderId': i + 1,
            'sourceBins': get_source_bins_for_order({
                'A': numpy.random.choice(
                    a=[4, 5, 6],
                    p=[0.90, 0.05, 0.05]
                ),
                'B': numpy.random.choice(
                    a=[4, 5, 6],
                    p=[0.90, 0.05, 0.05]
                ),
            }),
            'receivingBinTag': receiving_bin_tag,
        })

    return orders


def get_tasks_for_method(num_training_tasks, num_testing_tasks):
    """ Returns a tuple of training tasks and testing tasks with the specified counts. """

    training_tasks = []

    # Increment this in each loop
    task_id = 1

    while task_id <= num_training_tasks:
        task = {
            'taskId': task_id,
            'orders': get_orders_for_task()
        }
        training_tasks.append(task)
        task_id += 1

    testing_tasks = []
    while task_id <= num_training_tasks + num_testing_tasks:
        task = {
            'taskId': task_id,
            'orders': get_orders_for_task()
        }
        testing_tasks.append(task)
        task_id += 1

    # Ensure the lengths of the tasks lists are as expected. Very important!
    assert len(training_tasks) == num_training_tasks
    assert len(testing_tasks) == num_testing_tasks

    return training_tasks, testing_tasks


def write_tasks_to_output_file(tasks, is_training_task_list, study_method):
    """ Writes the given tasks to the given output file """

    # This is just the name of the file
    output_file_name = "%s-%s-%s.json" % ('tasks', study_method, 'training' if is_training_task_list else 'testing')

    # Create the output directory if it doesn't already exist
    output_file_dir = os.path.join('output', study_method)
    if not os.path.isdir(output_file_dir):
        os.mkdir(output_file_dir)

    # Print out the task IDs
    print_task_ordering(tasks, is_training_task_list=is_training_task_list)

    # Write to the output file
    output_file_name = os.path.join(output_file_dir, output_file_name)
    with open(output_file_name, mode='w+') as f:
        obj = {
            'version': VERSION,
            'tasks': tasks,
        }
        json.dump(obj, f, indent=4)


def print_task_ordering(tasks, is_training_task_list):
    """ Simply prints out all task IDs"""
    task_list_str = str([task['taskId'] for task in tasks])
    if is_training_task_list:
        print("Training: " + task_list_str)
    else:
        print("Testing:  " + task_list_str)


if __name__ == '__main__':
    # Change this seed to alter what pick paths are generated
    numpy.random.seed(1)

    # Generate all the tasks, separated into training and testing tasks
    training_tasks, testing_tasks = get_tasks_for_method(
        num_training_tasks=NUM_TRAINING_TASKS,
        num_testing_tasks=NUM_TESTING_TASKS,
    )

    # Create an output directory, if it doesn't already exist
    if not os.path.isdir('output'):
        os.mkdir('output')

    # Write the "master" list of tasks
    write_tasks_to_output_file(training_tasks, is_training_task_list=True, study_method='MASTER')
    write_tasks_to_output_file(testing_tasks, is_training_task_list=False, study_method='MASTER')

    # For each method, shuffle the tasks and write them to an output file
    for method_name in STUDY_METHODS:

        # Create a folder for each method
        method_dir_name = os.path.join('output', method_name)
        if not os.path.isdir(method_dir_name):
            os.mkdir(method_dir_name)

        # Shuffle the tasks, in-place
        numpy.random.shuffle(training_tasks)
        numpy.random.shuffle(testing_tasks)

        # Write the new tasks
        write_tasks_to_output_file(training_tasks, is_training_task_list=True, study_method=method_name)
        write_tasks_to_output_file(testing_tasks, is_training_task_list=False, study_method=method_name)
