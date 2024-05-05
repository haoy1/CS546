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
                                                contents[index + 1].replace('GROUPING ATTRIBUTES(V):', "").split(',')]
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
    class_content += f"{indentation * 2}'output' : {{}},\n"
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
    for condition in inputs["selectConditionVector"]:
        pattern = r'(\d+)\.(\w+)\s*([<>!=]+)\s*(\'[A-Za-z]+\'|\d+)'
        if ' and ' in condition:
            parts = condition.split(' and ')
            logical_operator = 'and'
        elif ' or ' in condition:
            parts = condition.split(' or ')
            logical_operator = 'or'
        else:
            parts = [condition]
            logical_operator = None

        for index in range(len(parts)):
            part = parts[index].strip()
            match = re.match(pattern, part)
            if match:
                if match.group(4).isdigit():
                    fourth_group = int(match.group(4))
                else:
                    fourth_group = match.group(4)

                other_parts = parts[:index] + parts[index + 1:]
                if other_parts:
                    temp = f"""{indentation}{{
                "number": {int(match.group(1))},
                "target": "{match.group(2)}",
                "sign": "{match.group(3)}",
                "value": "{fourth_group}",
                "extra_value": {other_parts},
                "logical_operator": "{logical_operator}"
            }},
        """
                else:
                    temp = f"""
            {{
                "number": {int(match.group(1))},
                "target": "{match.group(2)}",
                "sign": "{match.group(3)}",
                "value": "{fourth_group}",
            }},
                """
            selectAttr += temp
            if(index == len(parts) - 2): break
    selectAttr += "]"
    class_content += f"{indentation * 2}'selectConditionVector' : [{selectAttr},\n"
    class_content += f"{indentation * 2}'havingCondition' : {{'{havingCondition}'}}\n"
    class_content += """
    }
        """

    file_path = "H_Table.py"
    with open(file_path, "w") as file:
        file.write(class_content)
    print(f"File written: {file_path}")
    return file_path

def generate_MF_struct(file_path):

    # retrive the paresd input from file
    inputs = parse_input(file_path)

    # initialize mf-structure
    mf_struct = {}
    mf_struct["groupingAttributes"] = {item for item in inputs["groupingAttributes"]}
    mf_struct["output"] = {}
    mf_struct["numOfGroupingVariables"] = inputs["groupingVariables"]


    mf_struct["listOfAggregateFuncs"] = []
    for item in inputs["listOfAggregateFuncs"]:
        number, agg, target = item.split('_')
        mf_struct["listOfAggregateFuncs"].append({
            "number": int(number),
            "agg": agg,
            "target": target,
        })

    mf_struct["selectConditionVector"] = []
    for condition in inputs["selectConditionVector"]:
        condition = condition.strip()

        if ' and ' in condition:
            parts = condition.split(' and ')
            logical_operator = 'and'
        elif ' or ' in condition:
            parts = condition.split(' or ')
            logical_operator = 'or'
        else:
            parts = [condition]
            logical_operator = None

        for index, part in enumerate(parts):
            part = part.strip()
            pattern = r'(\d+)\.(\w+)\s*([<>!=]+)\s*(\'[A-Za-z]+\'|\d+)'
            match = re.match(pattern, part)
            if match:
                if match.group(4).isdigit():
                    fourth_group = int(match.group(4))
                else:
                    fourth_group = match.group(4)
                condition_entry = {
                    "number": int(match.group(1)),
                    "target": match.group(2),
                    "sign": match.group(3),
                    "value": fourth_group
                }
                other_parts = parts[:index] + parts[index + 1:]

                if other_parts:
                    condition_entry["extra_value"] = other_parts
                    condition_entry["logical_operator"] = logical_operator

                mf_struct["selectConditionVector"].append(condition_entry)
    mf_struct["havingCondition"] = inputs["havingCondition"]
    return mf_struct

# This algorithm is a modified version of Algorithm 3.1. 
# Instead of scanning the table once for every grouping variable, it scans the table for only once and update aggregate values for grouping variables.
# However, the worst-case runtime is still O(N^2) since it still needs to look for matching grouping variables in the new h-table for each row in the origional table.
# This is the first scan of the whole table. 
def processor_algorithm(mf_struct):
    header = f"""
    # table scan
    for row in table:
    """
    for condition in mf_struct["selectConditionVector"]:
        current_grouping_variable = condition['number']
        extra_fields = ' '.join(condition.get('extra_value', []))
        extra_number = None
        extra_target = None
        extra_sign = None
        extra_value = None

        logic_operator = condition.get('logical_operator')

        if extra_fields:
            pattern = r'(\d+)\.(\w+)\s*([<>!=]+)\s*(\'[A-Za-z]+\'|\d+)'
            match = re.match(pattern, extra_fields)
            if match:
                extra_number = int(match.group(1))
                extra_target = match.group(2)
                extra_sign = match.group(3)
                extra_value_str = match.group(4)
                extra_value = int(extra_value_str) if extra_value_str and extra_value_str.isdigit() else extra_value_str

        s = condition['sign']
        if s == "=":
            s = "=="
        if extra_sign == '=':
            extra_sign = "=="

        column = get_indices()[condition['target']]

        if logic_operator:
            if extra_number is not None and extra_number != current_grouping_variable:
                break
            header += f"    if row[{column}] {s} {condition['value']} {logic_operator} row[{get_indices()[extra_target]}] {extra_sign} {extra_value}:"
        else:
            header += f"    if row[{column}] {s} {condition['value']}: "

        res = f"""    
            group_keys = ", ".join([f"{{row[indices[k]]}}" for k in mf_structure['groupingAttribute']])
            if group_keys not in mf_structure['output']:
                mf_structure['output'][group_keys] = {{}}
            for selectedAttribute in mf_structure["selectedAttribute"]:
                if not selectedAttribute[0].isdigit() and selectedAttribute not in mf_structure['groupingAttribute']:
                    mf_structure['output'][group_keys][selectedAttribute] = row[indices[selectedAttribute]]
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
                if key not in mf_structure["output"][group_keys]:
                    mf_structure["output"][group_keys][key] = 0   
                    if aggregate == "min":
                        mf_structure["output"][group_keys][key] = float('inf')
                    elif aggregate == "max":
                        mf_structure["output"][group_keys][key] = float('-inf')
                if aggregate == "count":
                        mf_structure["output"][group_keys][key] += 1
                elif aggregate == "sum":
                        mf_structure["output"][group_keys][key] += row[targetIndex]                       
                elif aggregate == "min":
                        mf_structure["output"][group_keys][key] = min(row[targetIndex], mf_structure["output"][group_keys][key])
                elif aggregate == "max":
                        mf_structure["output"][group_keys][key] = max(row[targetIndex], mf_structure["output"][group_keys][key])
                                    
                elif aggregate == "avg":
                        # need to introduce new 'sum' and 'count' keys to calculate average. Those columns can be neglected from output.
                        # TODO: should not need this step if we already have sum calculated
                        if "sum" not in mf_structure["output"][group_keys]:
                            mf_structure["output"][group_keys]["sum"] = 0
                        if "count" not in mf_structure["output"][group_keys]:
                            mf_structure["output"][group_keys]["count"] = 0
                        
                        mf_structure["output"][group_keys]["sum"] += row[targetIndex]
                        mf_structure["output"][group_keys]["count"] += 1
                        mf_structure["output"][group_keys][key] = mf_structure["output"][group_keys]["sum"] / mf_structure["output"][group_keys]["count"]

                        
    """
        header += res

    return header


# This is the second and the last scan of the whole table.
# It checks if existing rows in the h-table satisfy the predicates in the having clause. 
def having_condition(mf_struct):
    predicate = str(parse_having_condition(mf_struct['havingCondition'],"row"))
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
