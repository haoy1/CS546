import re


def read_file(file_path=''):
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


def get_MF_struct(file_path):
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
                    condition = contents[index_x].strip()
                    if condition:
                        condition = condition.rstrip(',').strip()
                        conditions.append(condition)
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


def generate_MF_struct(file_path):
    htable = get_MF_struct(file_path)

    # Start the class definition
    class_content = """class H:
    def __init__(self):
        self.mf_structure = {}
    """
    indentation = "    "
    # Handle grouping attributes
    if 'groupingAttributes' in htable:
        grouping_attributes = htable['groupingAttributes'].split(', ')
        for attribute in grouping_attributes:
            attr_key = attribute.replace(' ', '_').replace('-', '_').lower()
            class_content += f"{indentation}self.mf_structure['{attr_key}'] = None\n"

    # Handle aggregate functions
    if 'listOfAggregateFuncs' in htable:
        for func in htable['listOfAggregateFuncs']:
            func_key = func.strip().replace(' ', '_').replace('-', '_').lower()
            class_content += f"{indentation * 2}self.mf_structure['{func_key}'] = 0\n"

    # Define methods for item access and string representation
    class_content += """
    def __getitem__(self, key):
        return self.mf_structure.get(key, None)

    def __setitem__(self, key, value):
        self.mf_structure[key] = value

    def __repr__(self):
        return f'H({{self.mf_structure}})'

    def __contains__(self, key):
        return key in self.mf_structure
        """

    file_path = "H_Table.py"
    with open(file_path, "w") as file:
        file.write(class_content)
    print(f"File written: {file_path}")
    return file_path


def get_indices():
    return {'cust': 0, 'prod': 1, 'day': 2, 'month': 3, 'year': 4, 'state': 5, 'quant': 6, 'date': 7}


def parse_condition(condition_str):
    indices = get_indices()
    pattern = re.compile(r"(\w+)\s*([<>=!]{1,2})\s*(\d+|'[^']*')")

    match = pattern.match(condition_str.strip())
    if match:
        left, operator, right = match.groups()

        match = pattern.match(condition_str.strip())
        if match:
            left, operator, right = match.groups()

            if operator == '=':
                operator = '=='
            elif operator == '<>':
                operator = '!='

            left_index = indices.get(left, f"Unknown index for column {left}")
            condition_expression = f"row[{left_index}] {operator} {right}"
            return condition_expression
    return None


def evaluate_having(having_str, mapper):
    left, right, operator = parse_condition(having_str.lower())
    if operator:
        left_mapped = mapper.get(left, f"Unknown mapping for {left}")
        right_mapped = mapper.get(right, f"Unknown mapping for {right}")
        operator = operator.replace(' = ', '==').replace('<>', '!=')
        return f"sales_gb_group[({left_mapped})]['{left}'] {operator} sales_gb_group[({right_mapped})]['{right}']"
    return ""


def handle_having_clause(output, mf_structure, agg_funcs, indentation):
    having_clause = mf_structure.get('havingClause')
    if having_clause and having_clause != '-':
        condition_eval = evaluate_having(having_clause, agg_funcs)
        output.append(f"{indentation * 2}if {condition_eval}:")
        output.append(f"{indentation * 3}# Add to output or perform other actions based on having condition")

    output.append(f"{indentation}print(mf_structure)")


def get_aggregate_functions(aggregate_funcs):
    agg_dict = {}
    for func in aggregate_funcs:
        key, agg, col = func.split('_')
        if key not in agg_dict:
            agg_dict[key] = []
        agg_dict[key].append((func, key, agg, col))
    return agg_dict


def parse_such_that(such_that):
    conditions = []
    for condition in such_that.split(' and '):
        parsed_condition = parse_condition(condition.strip())
        if parsed_condition:
            conditions.append(parsed_condition)
        else:
            print(f"Failed to parse condition: {condition}")

    return " and ".join(conditions)


def processing_algorithm(mf_structure, agg_funcs, indices):
    output = []
    indentation = "    "

    grouping_attributes = mf_structure['groupingAttributes'].split(', ')
    group_keys = ", ".join([f"sales_{attr}" for attr in grouping_attributes])
    group_dict = f"mf_structure[({group_keys})]"

    if 0 in agg_funcs:
        for funcs in agg_funcs.values():
            for func in funcs:
                if "avg" in func[2]:
                    output.append(f"{indentation}count_{func[3]} = collections.defaultdict(int)")

    output.append("for row in sales:")
    for attribute in grouping_attributes:
        output.append(f"{indentation * 2}sales_{attribute} = row[{indices[attribute]}]")

    for key, funcs in agg_funcs.items():
        conditions = mf_structure['selectConditionVector'][int(key) - 1].split('.')[1]
        where_clause = parse_such_that(conditions)

        if where_clause:
            output.append(f"{indentation * 2}if {where_clause}:")
            grouping_conditions = " and ".join([f"{group_dict}['{attr}']" for attr in grouping_attributes])
            output.append(f"{indentation * 3}if not ({grouping_conditions}):")
            for attribute in grouping_attributes:
                output.append(f"{indentation * 4}{group_dict}['{attribute}'] = sales_{attribute}")

            for agg_name, _, agg_type, agg_attr in funcs:
                agg_line = f"{group_dict}['{agg_name}']"
                if agg_type == "sum":
                    output.append(f"{indentation * 3}{agg_line} += row[{indices[agg_attr]}]")
                elif agg_type == "avg":
                    output.append(f"{indentation * 3}if '{agg_name}_sum' not in {group_dict}:")
                    output.append(f"{indentation * 4}{group_dict}['{agg_name}_sum'] = 0")
                    output.append(f"{indentation * 4}{group_dict}['{agg_name}_count'] = 0")
                    output.append(f"{indentation * 3}{group_dict}['{agg_name}_sum'] += row[{indices[agg_attr]}]")
                    output.append(f"{indentation * 3}{group_dict}['{agg_name}_count'] += 1")
                elif agg_type in ["max", "min"]:
                    condition = ">" if agg_type == "max" else "<"
                    output.append(
                        f"{indentation * 3}if '{agg_name}' not in {group_dict} or row[{indices[agg_attr]}] {condition} {agg_line}:")
                    output.append(f"{indentation * 4}{agg_line} = row[{indices[agg_attr]}]")
                elif agg_type == "count":
                    output.append(f"{indentation * 3}{agg_line} = {group_dict}.get('{agg_name}', 0) + 1")

    having_clause = mf_structure.get('havingClause')
    if having_clause and having_clause != '-':
        condition_eval = evaluate_having(having_clause, agg_funcs)
        output.append(f"{indentation}if {condition_eval}:")
        output.append(f"{indentation * 2}# Add to output or perform other actions based on having condition")

    output.append(f"{indentation}print(mf_structure)")

    return "\n".join(output)


def handle_aggregation(output, agg_type, agg_line, target_index):
    indentation = "    "
    if agg_type == "sum":
        output.append(f"{indentation * 3}{agg_line} += row[{target_index}]")
    elif agg_type == "avg":
        output.extend([
            f"{indentation * 3}{agg_line}_sum += row[{target_index}]",
            f"{indentation * 3}{agg_line}_count += 1"
        ])
    elif agg_type == "max" or agg_type == "min":
        comparator = '>' if agg_type == "max" else '<'
        output.append(
            f"{indentation * 3}if row[{target_index}] {comparator} {agg_line}:")
        output.append(f"{indentation * 4}{agg_line} = row[{target_index}]")
    elif agg_type == "count":
        output.append(f"{indentation * 3}{agg_line} += 1")
