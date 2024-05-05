mf_structure = {
        'selectedAttribute' : ['cust', '1_sum_quant', '2_sum_quant', '3_sum_quant'],
        'groupingAttribute' : {"cust"},
        'groupAggValue' : {},
        'numOfGroupingVariables' : 3,
        'aggregateList' : [
            {

                "number":1,
                "aggregate":"sum",
                "target": "quant",
                "value": 0,
            },
            {

                "number": 1,
                "aggregate":"avg",
                "target": "quant",
                "value": 0,
            },
            {

                "number": 2,
                "aggregate":"sum",
                "target": "quant",
                "value": 0,
            },
            {

                "number": 3,
                "aggregate":"sum",
                "target": "quant",
                "value": 0,
            },
            {

                "number": 3,
                "aggregate":"avg",
                "target": "quant",
                "value": 0,
            }
        ],
        'selectConditionVector' : [
            [   
                     
                {
                    "number": "1",
                    "target": "state",
                    "sign": "=",
                    "value": "NY",
                    "logical_operator": "and",
                    "extra_value": "['1.quant > 100']",
                },           
                
                {
                    "number": "1",
                    "target": "quant",
                    "sign": ">",
                    "value": "100",
                },
                    
            ],

            {
                    "number": "2",
                    "target": "state",
                    "sign": "=",
                    "value": "NJ",
            },
                
            {
                    "number": "3",
                    "target": "state",
                    "sign": "=",
                    "value": "CT",
            },
                
       ],
        'havingCondition' : {'1_sum_quant > 2 * 2_sum_quant or 1_avg_quant > 3_avg_quant'}

    }
        