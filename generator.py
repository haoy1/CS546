import subprocess
import helper


def main(body):
    """
    This is the generator code. It should take in the MF structure and generate the code
    needed to run the query. That generated code should be saved to a
    file (e.g. _generated.py) and then run.
    """

    # Note: The f allows formatting with variables.
    #       Also, note the indentation is preserved.

    file_path = f'input1.txt'

    tmp = f"""
import os
import psycopg2
import psycopg2.extras
import tabulate
from H_Table import H
import collections
from dotenv import load_dotenv

# DO NOT EDIT THIS FILE, IT IS GENERATED BY generator.py

def query():
    load_dotenv()

    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    dbname = os.getenv('DBNAME')

    conn = psycopg2.connect("dbname="+dbname+" user="+user+" password="+password,
                            cursor_factory=psycopg2.extras.DictCursor)

    cur = conn.cursor()
    cur.execute("SELECT * FROM sales")
    sales = cur.fetchall()
        
    mf_structure = collections.defaultdict(H) 

    _global = []
    {body}

    return tabulate.tabulate(_global,
                        headers="keys", tablefmt="psql")


def main():
    print(query())


if "__main__" == __name__:
    main()
    """

    # Write the generated code to a file
    open("_generated.py", "w").write(tmp)
    # Execute the generated code
    subprocess.run(["python", "_generated.py"])


if "__main__" == __name__:
    mf_structure = helper.get_MF_struct('input1.txt')
    indices = helper.get_indices()
    helper.generate_MF_struct('input1.txt')
    agg_funcs = helper.get_aggregate_functions(mf_structure['listOfAggregateFuncs'])
    body = ""
    body += helper.processing_algorithm(mf_structure, agg_funcs, indices)
    main(body)
