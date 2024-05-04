import re
import os
import psycopg2
import psycopg2.extras
import tabulate
from dotenv import load_dotenv


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


def get_indices():
    return {'cust': 0, 'prod': 1, 'day': 2, 'month': 3, 'year': 4, 'state': 5, 'quant': 6, 'date': 7}

def parse_input(file_path):
    htable = {}

    try:
        with open(file_path, 'r') as file:
            contents = file.read().split('\n')

        for index, line in enumerate(contents):
            line = line.strip()
            if line.startswith('SELECT ATTRIBUTE(S):'):
                htable['selectedAttribute'] = contents[index + 1].replace('SELECT ATTRIBUTE(S):', "").split(', ')
            elif line.startswith('NUMBER OF GROUPING VARIABLES(n):'):
                htable['groupingVariables'] = int(
                    contents[index + 1].replace('NUMBER OF GROUPING VARIABLES(n):', "").strip())
            elif line.startswith('GROUPING ATTRIBUTES(V):'):
                htable['groupingAttributes'] = [attr.strip() for attr in
                                                contents[index + 1].replace('GROUPING ATTRIBUTES(V):', "").split(',')]
            elif line.startswith('F-VECT([F]):'):
                htable['listOfAggregateFuncs'] = contents[index + 1].replace('F-VECT([F]):', "").strip().split(',')
            elif line.startswith('SELECT CONDITION-VECT([SIGMA]):'):
                conditions = []
                index += 1
                while index < len(contents) and not contents[index].strip().startswith('HAVING_CONDITION(G):'):
                    condition_line = contents[index].strip().split(",")[0]
                    if condition_line:
                        conditions.append(condition_line)
                    index += 1
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
    inputs = parse_input(file_path)
    # build string of grouping attribute

    mf_struct = {}
    mf_struct["groupingAttributes"] = {item: [] for item in inputs["groupingAttributes"]}

    mf_struct["groupAggValue"] = {}
    mf_struct["numOfGroupingAttributes"] = len(inputs["groupingAttributes"])
    mf_struct["numOfGroupingVariables"] = inputs["groupingVariables"]
    # build string of aggregate function list

    mf_struct["listOfAggregateFuncs"] = []
    for item in inputs["listOfAggregateFuncs"]:
        number, agg, target = item.split('_')
        mf_struct["listOfAggregateFuncs"].append({
            "number": int(number),
            "agg": agg,
            "target": target,
            "value": 0
        })
    # --------------------------------------------

    mf_struct["selectConditionVector"] = []

    for condition in inputs["selectConditionVector"]:
        condition = condition.strip()
        sub_conditions = condition.split('and')
        for sub_condition in sub_conditions:
            sub_condition = sub_condition.strip()
            pattern = r'(\d+)\.(\w+)\s*([<>!=]+)\s*\'([A-Za-z0-9\s]+)\''
            match = re.match(pattern, sub_condition)
            if match:
                mf_struct["selectConditionVector"].append({
                    "number": int(match.group(1)),
                    "target": match.group(2),
                    "sign": match.group(3),
                    "value": match.group(4)
                })

    return mf_struct


def generate_MF_table(file_path):
    inputs = parse_input(file_path)
    # build string of grouping attribute
    indentation = "    "
    class_content = """mf_structure = {
    """

    groupingAttr = ""
    for item in inputs["groupingAttributes"]:
        groupingAttr += "\"" + item + "\":[],"
    groupingAttr = groupingAttr[:-1]
    groupingAttr = "{" + groupingAttr + "}"

    length = len(inputs["groupingAttributes"])
    selectedAttributes = inputs['selectedAttribute']
    numOfAttributes = inputs["groupingVariables"]
    class_content += f"{indentation}'selectedAttribute' : {selectedAttributes},\n"
    class_content += f"{indentation * 2}'groupingAttribute' : {groupingAttr},\n"
    class_content += f"{indentation * 2}'groupAggValue' : {{}},\n"
    class_content += f"{indentation * 2}'numOfGroupingAttributes' : {length},\n"
    class_content += f"{indentation * 2}'numOfGroupingVariables' : {numOfAttributes},\n"

    # build string of aggregate function list
    aggregateAttr = ""
    for item in inputs["listOfAggregateFuncs"]:
        number, agg, target = item.split('_')
        stringBuilder = "\n"
        stringA = f"\n{indentation * 4}\"number\":" + number + ",\n"
        stringB = f"{indentation * 4}\"aggregate\":" + "\"" + agg + "\"" + ",\n"
        stringC = f"{indentation * 4}\"target\": \"" + target + "\",\n"
        stringD = f"{indentation * 4}\"value\": " + "0" + ",\n"
        stringBuilder = stringBuilder + stringA + stringB + stringC + stringD
        stringBuilder = f"{indentation * 3}{{{stringBuilder}{indentation * 3}}}"
        aggregateAttr = aggregateAttr + stringBuilder + ",\n"
    aggregateAttr = aggregateAttr.rstrip(',\n')
    aggregateAttr = f"[\n{aggregateAttr}\n{indentation * 2}]"
    # --------------------------------------------
    class_content += f"{indentation * 2}'aggregateList' : {aggregateAttr},\n"

    selectAttr = """
        """
    for v in inputs["selectConditionVector"]:
        pattern = r'(\d+)\.(\w+)\s*([<>!=]+)\s*\'([A-Za-z]+)\''
        match = re.match(pattern, v)
        if match:
            number = int(match.group(1))
            target = match.group(2)
            sign = match.group(3)
            value = match.group(4)
            temp = f"""{indentation}{{
                "number": {number},
                "target": "{target}",
                "sign": "{sign}",
                "value": "{value}",
        {indentation}}},
    {indentation}"""
        selectAttr += temp
    selectAttr += "]"
    class_content += f"{indentation * 2}'selectConditionVector' : [{selectAttr},\n"

    class_content += """
    }
        """

    file_path = "H_Table.py"
    with open(file_path, "w") as file:
        file.write(class_content)
    print(f"File written: {file_path}")
    return file_path


def grouping_attribute_process(mf_struct):
    body = [""]
    indentation = "    "
    for item in mf_struct["groupingAttributes"]:
        entityName = item
        entityIndex = get_indices()[entityName]
        body.append(f"{indentation}res = set()")
        body.append(f"{indentation}for row in table:")
        body.append(f"{indentation*2}res.add(row[{entityIndex}])")
        body.append(f"{indentation}mf_structure['groupingAttribute']['{entityName}'] = list(res)")
        body.append("")
    body.append("\n# ------ populate mf-struct with distinct values of grouping attribute ------")
    #
    # for number, target,

    return '\n'.join(body)

def processor_algorithm(mf_struct):
    output = ""
    header = f"""

    for row in table:
            """
    for condition in mf_struct["selectConditionVector"]:
        current_grouping_variable = condition['number']
        s = condition['sign']

        if s == "=":
            s = "=="

        column = get_indices()[condition['target']]

        res = f"""    
        if row[{column}] {s} "{condition['value']}":
            group_keys = ", ".join([f"{{row[indices[k]]}}" for k in mf_structure['groupingAttribute'].keys()])
            if group_keys not in mf_structure['groupAggValue']:
                mf_structure['groupAggValue'][group_keys] = {{}}

            for f_vect in mf_structure["aggregateList"]:
                number = f_vect["number"]
                # only care about current grouping_variable, exit if it's not
                if(number != {current_grouping_variable}):
                    continue
                aggregate = f_vect["aggregate"]
                target = f_vect["target"]
                value = f_vect["value"]
  
                key = str(number) + "_" + aggregate + "_" + target
                targetIndex = indices[target]
                
                # initialize value for each aggregate of each distinct groups of grouping attributes
                if key not in mf_structure["groupAggValue"][group_keys]:
                    mf_structure["groupAggValue"][group_keys][key] = 0   

                match aggregate:
                    case "count":
                        mf_structure["groupAggValue"][group_keys][key] += 1
                    case "sum":
                        mf_structure["groupAggValue"][group_keys][key] += row[targetIndex]                       
                    case "min":
                        mf_structure["groupAggValue"][group_keys][key] = min(row[targetIndex], mf_structure["groupAggValue"][group_keys][key])
                    case "max":
                        mf_structure["groupAggValue"][group_keys][key] = max(row[targetIndex], mf_structure["groupAggValue"][group_keys][key])
                                    
                    case "avg":
                        # need to introduce new 'sum' and 'count' keys to calculate average. Those columns can be neglected from output.
                        # TODO: should not need this step if we already have sum calculated
                        if "sum" not in mf_structure["groupAggValue"][group_keys]:
                            mf_structure["groupAggValue"][group_keys]["sum"] = 0
                        if "count" not in mf_structure["groupAggValue"][group_keys]:
                            mf_structure["groupAggValue"][group_keys]["count"] = 0
                        
                        mf_structure["groupAggValue"][group_keys]["sum"] += row[targetIndex]
                        mf_structure["groupAggValue"][group_keys]["count"] += 1
                        mf_structure["groupAggValue"][group_keys][key] = mf_structure["groupAggValue"][group_keys]["sum"] / mf_structure["groupAggValue"][group_keys]["count"]

        #output_cursor_i += 1
        #print(mf_structure["groupAggValue"])
    """
        header += res
    
    return header

def generate_output():
    output = f""""""


    output += f"""
    output = []
    header = mf_structure['selectedAttribute']
    output.append(header)
    for item in (iter(mf_structure["groupAggValue"].items())):
        new_row = []
        for key in item[0].split(", "):
            new_row.append(key)
        for col_name in item[1]:
            if col_name in header:
                new_row.append(item[1][col_name])
        output.append(new_row)

    # Path to the CSV file
    csv_file_path = 'new_file.csv'

    with open(csv_file_path, 'w', newline='') as csvfile:
        # Create a CSV writer object
        csv_writer = csv.writer(csvfile)
        
        # Write the data to the CSV file
        csv_writer.writerows(output)
    """
    return output

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
