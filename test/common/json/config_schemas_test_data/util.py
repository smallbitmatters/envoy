import copy
import json
import os

# convenience when dealing with json
true, false = True, False


def get_blob(blob):
    return copy.deepcopy(blob)


class TestWriter(object):

    def __init__(self, test_dir):
        self.test_dir = test_dir

    def write_test_file(self, name, schema, data, throws):
        test_filename = os.path.join(self.test_dir, f'schematest-{schema}-{name}.json')
        if os.path.isfile(test_filename):
            raise ValueError(
                f'Test with that name and schema already exists: {test_filename}'
            )

        with open(test_filename, 'w+') as fh:
            json.dump({"schema": schema, "throws": throws, "data": data}, fh, indent=True)
