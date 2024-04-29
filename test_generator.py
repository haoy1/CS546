import helper
from generator import main as generator
from _generated import query as _generated

from sql import query as sql


def test_generator():
    # Generate the file

    mf_structure = helper.get_MF_struct('input1.txt')
    indices = helper.get_indices()
    helper.generate_MF_struct('input1.txt')
    agg_funcs = helper.get_aggregate_functions(mf_structure['listOfAggregateFuncs'])
    body = ""
    body += helper.processing_algorithm(mf_structure, agg_funcs, indices)
    generator(body)

    # Compare the output of your generated code to the output of the actual SQL query
    # Note: This only works for standard queries, not ESQL queries.
    assert _generated() == sql()
