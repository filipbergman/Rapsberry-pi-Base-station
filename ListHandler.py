class ListHandler:
    valList = []
    valList.append(['tea', '21', 3.19])

    def addToList(self, val):
        self.valList.append(val)

    def getList(self):
        return self.valList