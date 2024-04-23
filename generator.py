import subprocess


def read_file():
    S = []
    N = []
    V = []
    F = []
    SIGMA = []
    G = []
    try:
        with open('input1.txt', 'r') as file:
            # Read lines from the file
            for line in file:
                # Split each line at the colon
                parts = line.strip().split(':')
                if len(parts) == 2:
                    # Extract key and value
                    key = parts[0].strip()
                    value = parts[1].strip().split(',')

                    # Assign value to corresponding variable
                    if key == "SELECT ATTRIBUTE(S)":
                        S = value
                    elif key == "NUMBER OF GROUPING VARIABLES(n)":
                        N = value
                    elif key == "GROUPING ATTRIBUTES(V)":
                        V = value
                    elif key == "F-VECT([F])":
                        F = value
                    elif key == "SELECT CONDITION-VECT([SIGMA])":
                        SIGMA = value
                    elif key == "HAVING_CONDITION(G)":
                        G = value

    except FileNotFoundError:
        print("File Not Found")


def read_Inputs():
    print("Please enter all arguments of Phi operator")

    select_attributes = input("Enter SELECT ATTRIBUTE(S) (e.g., cust, 1_sum_quant, 2_sum_quant, 3_sum_quant): ")
    number_of_grouping_variables = input("Enter NUMBER OF GROUPING VARIABLES(n) (e.g., 3): ")
    grouping_attributes = input("Enter GROUPING ATTRIBUTES(V) (e.g., cust): ")
    f_vect = input("Enter F-VECT([F]) (e.g., 1_sum_quant, 1_avg_quant, 2_sum_quant, 3_sum_quant, 3_avg_quant): ")
    select_condition_vect = input("Enter SELECT CONDITION-VECT([σ]) (e.g., 1.state='NY', 2.state='NJ', 3.state='CT'): ")
    having_condition = input(
        "Enter HAVING_CONDITION(G) (e.g., 1_sum_quant > 2 * 2_sum_quant or 1_avg_quant > 3_avg_quant): ")

    return {
        'SELECT_ATTRIBUTE(S)': select_attributes,
        'NUMBER_OF_GROUPING_VARIABLES(n)': number_of_grouping_variables,
        'GROUPING_ATTRIBUTES(V)': grouping_attributes,
        'F-VECT([F])': f_vect,
        'SELECT_CONDITION-VECT([σ])': select_condition_vect,
        'HAVING_CONDITION(G)': having_condition
    }


def get_arguments():
    res = input("Enter type of argument process either from 'file' or 'manually': ")
    if res == 'file':
        return read_file()
    elif res == 'manually':
        return read_Inputs()
    else:
        print("Invalid Input")
        return get_arguments()


def check_arguments():
    phi_args = get_arguments()
    if phi_args is not None:
        print("Phi Arguments: ", phi_args)
        return phi_args


def get_htable(file_path):
    htable = {}

    try:
        with open(file_path, 'r') as file:
            contents = file.read().split('\n')
            class_content = """
            class H_table:
                def __init__(self):
                    self.attributes = {}
                """

        for index, line in enumerate(contents):
            line = line.strip()
            if line == 'SELECT ATTRIBUTE(S):':
                htable['select'] = contents[index + 1].strip()
            elif line == 'NUMBER OF GROUPING VARIABLES(n):':
                htable['groupingVariables'] = int(contents[index + 1].strip())
            elif line == 'GROUPING ATTRIBUTES(V):':
                htable['groupingAttributes'] = contents[index + 1].strip()
            elif line == 'F-VECT([F]):':
                htable['listOfAggregateFuncs'] = [func.strip().lower() for func in contents[index + 1].split(',')]
            elif line == 'SELECT CONDITION-VECT([SIGMA]):':
                conditions = []
                index_x = index + 1
                while index_x < len(contents) and contents[index_x] != 'HAVING_CONDITION(G):':
                    if contents[index_x].strip():
                        conditions.append(contents[index_x].strip())
                    index_x += 1
                htable['selectConditionVector'] = conditions
            elif line == 'HAVING_CONDITION(G):':
                htable['havingCondition'] = contents[index + 1].strip()

    except FileNotFoundError:
        print(f"Error: File '{file}' not found.")
    except ValueError:
        print("Error: Invalid data format. Ensure numeric fields are correct.")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")

    return htable


def generate_htable():
    htable = get_htable('input1.txt')

    class_content = """class MF_Structure:
    def __init__(self):
        self.mf_structure = {}
    """

    if 'groupingAttributes' in htable:
        grouping_attributes = htable['groupingAttributes'].split(', ')
        for attribute in grouping_attributes:
            attr_key = attribute.replace(' ', '_').replace('-', '_').lower()
            class_content += f"    self.mf_structure['{attr_key}'] = None\n"

    if 'listOfAggregateFuncs' in htable:
        for func in htable['listOfAggregateFuncs']:
            func_key = func.strip().replace(' ', '_').replace('-', '_').lower()
            class_content += f"        self.mf_structure['{func_key}'] = None\n"

    class_content += """
        def __getitem__(self, key):
            return self.mf_structure.get(key, None)

        def __setitem__(self, key, value):
            self.mf_structure[key] = value

        def __repr__(self):
            return f'H({{self.mf_structure}})'
        """

    file_path = "MF_structure_generated.py"
    with open(file_path, "w") as file:
        file.write(class_content)
    print(f"File written: {file_path}")
    return file_path


def logic_processing(file_path):
    mf_structure = get_htable(file_path)
    n = mf_structure['groupingVariables']
    lists = mf_structure['listOfAggregateFuncs']
    agg_funcs = {}

    for func in lists:
        parts = func.split('_')
        idx = parts[0]
        agg = parts[1]
        col = parts[2]
        if idx in agg_funcs:
            agg_funcs[idx].append((agg, col))
        else:
            agg_funcs[idx] = [(agg, col)]

    setup_table = """for i in range(mf_structure['groupingVariables']):
    """


        

    


def main():
    """
    This is the generator code. It should take in the MF structure and generate the code
    needed to run the query. That generated code should be saved to a
    file (e.g. _generated.py) and then run.
    """

    file_path = 'input1.txt'
    body = """
    for row in cur:
        if row['quant'] > 10:
            _global.append(row)
    """

    # Note: The f allows formatting with variables.
    #       Also, note the indentation is preserved.
    tmp = f"""
import os
import psycopg2
import psycopg2.extras
import tabulate
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

    input_path = f'{file_path}'
    mf_structure = get_htable(input_path)

    
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
    main()
    generate_htable()
