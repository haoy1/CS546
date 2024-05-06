import subprocess
import helper


def main(body):
    """
    This is the generator code. It should take in the MF structure and generate the code
    needed to run the query. That generated code should be saved to a
    file (e.g. _generated.py) and then run.
    """

    tmp = f"""
import os
import psycopg2
import psycopg2.extras
import tabulate
from mf_structure import mf_structure
from dotenv import load_dotenv
import csv

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
    table = cur.fetchall()

    indices = {{'cust': 0, 'prod': 1, 'day': 2, 'month': 3, 'year': 4, 'state': 5, 'quant': 6, 'date': 7}}
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
    body = ""
    mf_structure = helper.generate_MF_struct('input1.txt')
    helper.generate_MF_table('input1.txt')
    body += helper.processor_algorithm(mf_structure)
    body += helper.having_condition(mf_structure)
    body += helper.generate_output()

    main(body)
