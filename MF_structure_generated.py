class MF_Structure:
    def __init__(self):
        self.mf_structure = {}
        self.mf_structure['cust'] = None
        self.mf_structure['1_sum_quant'] = None
        self.mf_structure['1_avg_quant'] = None
        self.mf_structure['2_sum_quant'] = None
        self.mf_structure['3_sum_quant'] = None
        self.mf_structure['3_avg_quant'] = None

        def __getitem__(self, key):
            return self.mf_structure.get(key, None)

        def __setitem__(self, key, value):
            self.mf_structure[key] = value

        def __repr__(self):
            return f'H({{self.mf_structure}})'
        