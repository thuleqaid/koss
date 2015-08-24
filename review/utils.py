class CSVReader(object):
    CONST_LINETERMINATOR_STRIP = chr(10) + chr(13)
    CONST_LINETERMINATOR_INSERT = "\n"
    def __init__(self, lines):
        self._data=[]
        flag_cell = False
        cell_data = ''
        for line in lines:
            parts=line.rstrip(self.CONST_LINETERMINATOR_STRIP).split("\t")
            if len(parts) > 0:
                if flag_cell:
                    # last cell of the last line startswith a "
                    if len(parts) > 1:
                        # unfinished cell will be finished
                        if parts[0].endswith('"'):
                            cell_data = cell_data+self.CONST_LINETERMINATOR_INSERT+parts[0]
                            self._data[-1].append(cell_data[1:-1])
                        else:
                            self._data[-1].append(cell_data[1:])
                            self._data.append([])
                            self._data[-1].append(parts[0])
                        flag_cell = False
                        cell_data=''
                        self._data[-1].extend(parts[1:])
                    else:
                        if parts[0].endswith('"'):
                            cell_data = cell_data+self.CONST_LINETERMINATOR_INSERT+parts[0]
                            self._data[-1].append(cell_data[1:-1])
                            flag_cell = False
                            cell_data=''
                        else:
                            # unfinished cell continues
                            cell_data=cell_data+self.CONST_LINETERMINATOR_INSERT+parts[0]
                else:
                    self._data.append([])
                    self._data[-1].extend(parts[:-1])
                    if parts[-1].startswith('"'):
                        if len(parts[-1]) > 1 and parts[-1].endswith('"'):
                            self._data[-1].append(parts[-1][1:-1])
                        else:
                            flag_cell = True
                            cell_data = parts[-1]
                    else:
                        self._data[-1].append(parts[-1])
        else:
            if flag_cell:
                cell_data = cell_data+self.CONST_LINETERMINATOR_INSERT
        if flag_cell:
            self._data[-1].append(cell_data)
    def __len__(self):
        return len(self._data)
    def __getitem__(self, idx):
        return self._data[idx]

