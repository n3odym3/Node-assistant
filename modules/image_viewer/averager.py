class Averager():
    def __init__(self, frame_size=10):
        self.frame_size = frame_size
        self.sum = 0
        self.last_average = 0 
        self.count = 0

        self.last_list = []
    
    def get_average(self, value):
        new = False
        self.sum += value
        self.count += 1
        if self.count >= self.frame_size:
            self.last_average = round(self.sum / self.count, 2)
            self.sum = 0
            self.count = 0
            new = True
        return self.last_average, new
    
    def get_list_average(self, value):
        self.last_list.extend(value)
        self.count += 1
        if self.count >= self.frame_size:
            self.last_list = []
        if len(self.last_list) > self.frame_size:
            self.last_list.pop(0)
        return round(sum(self.last_list) / len(self.last_list), 2)