def read_file(file_path = ''):
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


def generate_MF_struct():
    htable = get_MF_struct('input1.txt')

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


def parse_condition(condition_str):
    for operator in [' = ', ' != ', ' < ', ' > ', ' <> ']:
        if operator in condition_str:
            left, right = condition_str.split(operator)
            left = "_".join(left.split('_')[:-1])
            right = "_".join(right.split('_')[:-1])
            return left, right, operator
    return None, None, None


def evaluate_having(having_str, mapper):
    left, right, operator = parse_condition(having_str.lower())
    if operator:
        left_mapped = mapper.get(left, f"Unknown mapping for {left}")
        right_mapped = mapper.get(right, f"Unknown mapping for {right}")
        operator = operator.replace(' = ', '==').replace('<>', '!=')
        return f"sales_gb_group[({left_mapped})]['{left}'] {operator} sales_gb_group[({right_mapped})]['{right}']"
    return ""


def get_aggregate_functions(aggregate_funcs):
    agg_dict = {}
    for func in aggregate_funcs:
        key, agg, col = func.split('_')
        if key not in agg_dict:
            agg_dict[key] = []
        agg_dict[key].append((agg, col))
    return agg_dict


def parse_such_that(such_that):
    groups, conditions = [], []
    for condition in such_that.split(' and '):
        left, right, operator = parse_condition(condition)
        if operator == ' = ' and left and right:
            groups.append(right)
        else:
            conditions.append(condition.replace('=', '=='))
    conditions = [c.replace('quant', 'quantC') for c in conditions]
    return ", ".join(groups), " and ".join(conditions)


def generate_algorithm_logic(mf_struct):
    output = ""
    agg_funcs = get_aggregate_functions(mf_struct['listOfAggregateFuncs'])

    for i, such_that in enumerate(mf_struct['selectConditionVector']):
        groups, where = parse_such_that(such_that)
        agg_func = agg_funcs[f"{i + 1}"]

        output += f"\nif {where}:" if where else ""
        for agg, col in agg_func:
            agg_method = {
                'avg': '+', 'sum': '+', 'max': 'max', 'min': 'min', 'count': '+='
            }.get(agg, '+')
            action = f"{agg_method} quantC" if agg in ['avg', 'sum',
                                                       'count'] else f"{agg_method}(current_value, quantC)"
            output += f"\nsales_gb_group[({groups})]['{i + 1}_{agg}'] = {action}"
        output += "\nelse:\nsales_gb_group[({groups})] = {initialization logic}"

    having_clause = mf_struct.get('havingClause')
    if having_clause and having_clause != '-':
        condition_eval = evaluate_having(having_clause, {func: group for group, func in agg_funcs.items()})
        output += f"\nif {condition_eval}:"
        output += "\n    # Add to output or perform other actions"

    return output


