import re


#TODO: This function is unused. Either delete or to support manual input.
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


# hard-coded indices for table columns. information-schema.columns doesn't give the columns in expected order
def get_indices():
    return {'cust': 0, 'prod': 1, 'day': 2, 'month': 3, 'year': 4, 'state': 5, 'quant': 6, 'date': 7}


# parse input file to a table. Not yet mf-structure, just parsing...
def parse_input(file_path):
    input_table = {}

    try:
        with open(file_path, 'r') as file:
            contents = file.read().split('\n')

        for index, line in enumerate(contents):
            line = line.strip()
            if line.startswith('SELECT ATTRIBUTE(S):'):
                input_table['selectedAttribute'] = contents[index + 1].replace('SELECT ATTRIBUTE(S):', "").split(', ')
            elif line.startswith('NUMBER OF GROUPING VARIABLES(n):'):
                input_table['groupingVariables'] = int(
                    contents[index + 1].replace('NUMBER OF GROUPING VARIABLES(n):', "").strip())
            elif line.startswith('GROUPING ATTRIBUTES(V):'):
                input_table['groupingAttributes'] = [attr.strip() for attr in
                                                     contents[index + 1].replace('GROUPING ATTRIBUTES(V):', "").split(
                                                         ',')]
            elif line.startswith('F-VECT([F]):'):
                input_table['listOfAggregateFuncs'] = contents[index + 1].replace('F-VECT([F]):', "").strip().split(',')
            elif line.startswith('SELECT CONDITION-VECT([SIGMA]):'):
                conditions = []
                index += 1
                while index < len(contents) and not contents[index].strip().startswith('HAVING_CONDITION(G):'):
                    condition_line = contents[index].strip().split(",")[0]
                    if condition_line:
                        conditions.append(condition_line)
                    index += 1
                input_table['selectConditionVector'] = conditions
            elif line == 'HAVING_CONDITION(G):':
                input_table['havingCondition'] = contents[index + 1].strip()

    except FileNotFoundError:
        print(f"Error: File '{file}' not found.")
    except ValueError:
        print("Error: Invalid data format. Ensure numeric fields are correct.")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
    return input_table


def generate_MF_table(file_path):
    inputs = parse_input(file_path)
    # build string of grouping attribute
    indentation = "    "
    class_content = """mf_structure = {
    """

    groupingAttr = ""
    for item in inputs["groupingAttributes"]:
        groupingAttr += "\"" + item + "\","
    groupingAttr = groupingAttr[:-1]
    groupingAttr = "{" + groupingAttr + "}"

    selectedAttributes = inputs['selectedAttribute']
    numOfAttributes = inputs["groupingVariables"]
    havingCondition = inputs['havingCondition']
    class_content += f"{indentation}'selectedAttribute' : {selectedAttributes},\n"
    class_content += f"{indentation * 2}'groupingAttribute' : {groupingAttr},\n"
    class_content += f"{indentation * 2}'groupAggValue' : {{}},\n"
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

    selectAttr = """[
        """
    conditions = []
    for condition in inputs["selectConditionVector"]:
        parsed_condition = parse_condition(condition)
        if parsed_condition:
            conditions.append(parsed_condition)

    for condition in conditions:
        if isinstance(condition, list) and len(condition) > 1:
            temp = """    [   
                     """
            for index, con in enumerate(condition):
                if index == len(condition) - 1:
                    temp += f"""
                {{
                    "number": "{con['number']}",
                    "target": "{con['target']}",
                    "sign": "{con['sign']}",
                    "value": "{con['value']}",
                }},
                    """
                    temp += "\n            ],\n"
                    break
                else:
                    temp += f"""
                {{
                    "number": "{con['number']}",
                    "target": "{con['target']}",
                    "sign": "{con['sign']}",
                    "value": "{con['value']}",
                    "logical_operator": "{con['logical_operator']}",
                    "extra_value": "{con['extra_value']}",
                }},           
                """
            selectAttr += temp
        else:
            for con in condition:
                temp = f"""
            {{
                    "number": "{con['number']}",
                    "target": "{con['target']}",
                    "sign": "{con['sign']}",
                    "value": "{con['value']}",
            }},
                """
            selectAttr += temp
    selectAttr += "\n       ]"
    class_content += f"{indentation * 2}'selectConditionVector' : {selectAttr},\n"
    class_content += f"{indentation * 2}'havingCondition' : {{'{havingCondition}'}}\n"
    class_content += """
    }
        """

    file_path = "H_Table.py"
    with open(file_path, "w") as file:
        file.write(class_content)
    print(f"File written: {file_path}")
    return file_path


def parse_condition(condition):
    condition = condition.strip()
    conditions = []

    pattern = r'(\d+)\.(\w+)\s*([<>!=]+)\s*(?:\'([A-Za-z0-9\s]+)\'|([A-Za-z0-9]+))'
    match = re.match(pattern, condition)
    if match:
        condition_entry = {
            "number": int(match.group(1)),
            "target": match.group(2),
            "sign": match.group(3),
            "value": match.group(4) or match.group(5)
        }
        remaining_condition = condition[match.end():]

        if remaining_condition:
            if ' and ' in remaining_condition:
                parts = [part.strip() for part in remaining_condition.split(' and ', 1) if part.strip()]
                condition_entry["logical_operator"] = 'and'
                condition_entry["extra_value"] = parts
            elif ' or ' in remaining_condition:
                parts = [part.strip() for part in remaining_condition.split(' or ', 1) if part.strip()]
                condition_entry["logical_operator"] = 'or'
                condition_entry["extra_value"] = parts

        conditions.append(condition_entry)

        for extra_value in condition_entry.get("extra_value", []):
            conditions.extend(parse_condition(extra_value.strip()))

    return conditions


def generate_MF_struct(file_path):
    inputs = parse_input(file_path)
    # build string of grouping attribute

    mf_struct = {}
    mf_struct["groupingAttributes"] = {item for item in inputs["groupingAttributes"]}

    mf_struct["groupAggValue"] = {}
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
        parsed_condition = parse_condition(condition)
        if parsed_condition:
            mf_struct["selectConditionVector"].append(parsed_condition)

    mf_struct["havingCondition"] = inputs["havingCondition"]
    return mf_struct


# This algorithm is a modified version of Algorithm 3.1.
# Instead of scanning the table once for every grouping variable, it scans the table for only once and update aggregate values for grouping variables.
# However, the worst-case runtime is still O(N^2) since it still needs to look for matching grouping variables in the new h-table for each row in the origional table.
# This is the first scan of the whole table.
def is_number(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def processor_algorithm(mf_struct):
    header = f"""

    for row in table:
    """
    for condition in mf_struct["selectConditionVector"]:
        numbers = []
        targets = []
        signs = []
        values = []
        current_grouping_variable = 0
        logical_operators = []
        if len(condition) > 1:
            for con in condition:
                numbers.append(con["number"])
                targets.append(con["target"])
                if con["sign"] == '=':
                    signs.append('==')
                else:
                    signs.append(con["sign"])

                values.append(con["value"])
                logical_operators.append(con.get("logical_operator", None))
            current_grouping_variable = numbers[0]
        else:
            for con in condition:
                numbers = con["number"]
                targets = con["target"]
                if con["sign"] == '=':
                    signs.append('==')
                else:
                    signs.append(con["sign"])
                values.append(con["value"])
            current_grouping_variable = numbers
        temp_header = "    if "

        if len(logical_operators) != 0:
            for num, target, sign, value, logic in zip(numbers, targets, signs, values, logical_operators):
                if is_number(value):
                    int(value)
                    temp_header += f"row[{get_indices()[target]}] {sign} {value}"
                else:
                    temp_header += f"row[{get_indices()[target]}] {sign} '{value}'"
                if logic:
                    temp_header += f" {logic} "
            if temp_header.endswith(' and ') or temp_header.endswith(' or '):
                temp_header = temp_header.rstrip(' and ').rstrip(' or ')
        else:
            temp_header += f"row[{get_indices()[targets]}] {signs[0]} '{values[0]}'"
        temp_header += ":"
        header += temp_header

        res = f"""    
            group_keys = ", ".join([f"{{row[indices[k]]}}" for k in mf_structure['groupingAttribute']])
            if group_keys not in mf_structure['groupAggValue']:
                mf_structure['groupAggValue'][group_keys] = {{}}
            for selectedAttribute in mf_structure["selectedAttribute"]:
                if not selectedAttribute[0].isdigit() and selectedAttribute not in mf_structure['groupingAttribute']:
                    mf_structure['groupAggValue'][group_keys][selectedAttribute] = row[indices[selectedAttribute]]
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

                if aggregate == "count":
                        mf_structure["groupAggValue"][group_keys][key] += 1
                elif aggregate == "sum":
                        mf_structure["groupAggValue"][group_keys][key] += row[targetIndex]                       
                elif aggregate == "min":
                        mf_structure["groupAggValue"][group_keys][key] = min(row[targetIndex], mf_structure["groupAggValue"][group_keys][key])
                elif aggregate == "max":
                        mf_structure["groupAggValue"][group_keys][key] = max(row[targetIndex], mf_structure["groupAggValue"][group_keys][key])

                elif aggregate == "avg":
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


# This is the second and the last scan of the whole table.
# It checks if existing rows in the h-table satisfy the predicates in the having clause. 
def having_condition(mf_struct):
    predicate = str(parse_having_condition(mf_struct['havingCondition'], "row"))
    output = f"""

    for group_key in mf_structure["output"].keys():
        for f_vect in mf_structure["aggregateList"]:
            number = f_vect["number"]
            aggregate = f_vect["aggregate"]
            target = f_vect["target"]
            key = str(number) + "_" + aggregate + "_" + target
            targetIndex = indices[target]
            
            # initialize value for each aggregate of each distinct groups of grouping attributes
            if key not in mf_structure["output"][group_key]:
                        mf_structure["output"][group_key][key] = "NULL"

    newTable = {{}}
    for key, row in mf_structure["output"].items():
        if ({predicate}):
            newTable[key] = row
    """

    return output


def parse_having_condition(input_string, prefix):
    # Define a regular expression pattern to match substrings like "1_x_x"
    pattern = r'\b\d+_\w+_\w+\b'
    # Find all matches in the input string
    matches = re.findall(pattern, input_string)
    # Create a dictionary to keep track of processed matches
    processed_matches = {}
    # Replace each match with the prefix followed by the match enclosed in square brackets
    for match in matches:
        if match not in processed_matches:
            input_string = input_string.replace(match, f'{prefix}[\'{match}\']')
            processed_matches[match] = True
    return input_string
    # Example usage:
    input_string = '1_sum_quant > 2 * 2_sum_quant or 1_avg_quant > 3_avg_quant'
    prefix = "row"
    output_string = "row['1_sum_quant'] > row['2_sum_quant'] and row['1_avg_quant'] > row['3_avg_quant']"


def generate_output():
    first_scan_output = f""""""

    first_scan_output += f"""
    output = []
    header = mf_structure['selectedAttribute']
    output.append(header)
    for group, aggregates in newTable.items():
        new_row = []
        for key in group.split(", "):
            new_row.append(key)
        for col_name in header:
            if col_name in aggregates:
                new_row.append(aggregates[col_name])
        output.append(new_row)

    # Path to the CSV file
    csv_file_path = 'new_file.csv'

    with open(csv_file_path, 'w', newline='') as csvfile:
        # Create a CSV writer object
        csv_writer = csv.writer(csvfile)
        
        # Write the data to the CSV file
        csv_writer.writerows(output)
    """
    return first_scan_output
