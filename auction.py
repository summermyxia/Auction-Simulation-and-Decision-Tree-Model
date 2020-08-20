import random

class competitor:

    def __init__(self, competitor_id, num_attributes, is_myself = False, budget = float('inf')):
        self.competitor_id = competitor_id
        self.num_attributes = num_attributes
        self.remaining_budget = budget
        self.attribute_weights = [random.random() for _ in range(num_attributes)]
        self.bidprice_record = []
        self.is_myself = is_myself

    def bidprice(self, attributes):
        running_bid = self.generateRunningBid() if not self.is_myself else self.generateRunningBidSelf()
        pctr = self.generatePctr(attributes)
        price = running_bid * pctr

        # price = max(sum([self.attribute_weights[i] * attributes[i] for i in range(self.num_attributes)]) + self.generateNoise() * self.num_attributes, 0)
        if price > self.remaining_budget:
            price = self.remaining_budget
            self.remaining_budget = 0
        else:
            self.remaining_budget -= price
        self.bidprice_record.append((price, pctr, running_bid))
        return price

    def clearBidPriceRecord(self):
        self.bidprice_record = []

    # TODO: Add other noise type
    def generateNoise(self):
        return random.random()

    def generatePctr(self, attributes):
        return sum([self.attribute_weights[i] * attributes[i] for i in range(self.num_attributes)])
    
    def generateRunningBid(self, range = 10):
        return random.random() * range
    
    def generateRunningBidSelf(self):
        return random.choice([1, 2] * 20 + [4, 7, 10])


class adExchange:

    # TODO: Add time attribute
    # num_competitors >= 2
    def __init__(self, num_competitors = 20, num_integer_attributes = 3, integer_attributes_range = [2, 5, 10], num_float_attributes = 7, float_attributes_range = [], auction_type = 'first', myself_idx = -1):
        if len(integer_attributes_range) == 0:
            integer_attributes_range = [4 for _ in range(num_integer_attributes)]
        elif len(integer_attributes_range) != num_integer_attributes:
            print("Length of integer_attributes_range must match num_integer_attributes!")
            return
        if len(float_attributes_range) == 0:
            average_integer_attribute_range = sum(integer_attributes_range) / num_integer_attributes
            float_attributes_range = [average_integer_attribute_range + 1 for _ in range(num_float_attributes)]
        elif len(float_attributes_range) != num_float_attributes:
            print("Length of float_attributes_range must match num_float_attributes or be equal to 0!")
            return
        
        self.num_competitors = num_competitors
        self.num_integer_attributes = num_integer_attributes
        self.integer_attributes_range = integer_attributes_range
        self.num_float_attributes = num_float_attributes
        self.float_attributes_range = float_attributes_range
        self.num_attributes = num_integer_attributes + num_float_attributes
        self.auction_type = auction_type
        self.competitors = [competitor(i, self.num_attributes) if i != myself_idx else competitor(i, self.num_attributes, is_myself = True) for i in range(self.num_competitors)]
        self.bid_record = []


    def generateOneBid(self):
        '''
        Return type: list
            winning_price: float
            winning_id: int
            attributes: list
            competitor_bidprices: list
        '''
        # Generate attributes
        attributes = []
        for i in range(self.num_attributes):
            if i < self.num_integer_attributes:
                attributes.append(self.generateRandomAttribute(i, "integer"))
            else:
                attributes.append(self.generateRandomAttribute(i - self.num_integer_attributes, "float"))

        # Generate bid price for each competitor
        # TODO: Floor price
        competitor_bidprices = [(k.bidprice(attributes), i) for i, k in enumerate(self.competitors)]
        sorted_bidprice = sorted(competitor_bidprices, reverse = True)
        if self.auction_type == 'first':
            winning_price, winning_id = sorted_bidprice[0]
        elif self.auction_type == 'second':
            winning_price = sorted_bidprice[1][0]
            winning_id = sorted_bidprice[0][1]

        return [winning_price, winning_id, attributes, competitor_bidprices]


    def generateMultipleBidRecord(self, num_records, save = False, save_path = "./bid_record"):
        '''
        Return type: list of list
            winning_price: float
            winning_id: int
            attributes: list
            competitor_bidprices: list
        '''
        for _ in range(num_records):
            self.bid_record.append(self.generateOneBid())

        if save:
            self.saveRecord(self.bid_record, save_path + ".txt")
        return self.bid_record


    def getCensoredRecord(self, competitor_idx, save = False, save_path = "./censored_record_competitor_"):
        '''
        Return type: list of list
            win or lose: 1 is win, 0 is lose
            winning_price: -1 if lose
            bidprice: float
            attributes: list
        '''
        if competitor_idx >= self.num_competitors:
            print("Wrong competitor_idx!")
            return
        censored_record = []
        for winning_price, winning_id, attributes, competitor_bidprices in self.bid_record:
            if competitor_idx == winning_id:
                censored_record.append([1, winning_price, competitor_bidprices[competitor_idx][0], attributes])
            else:
                censored_record.append([0, -1, competitor_bidprices[competitor_idx][0], attributes])
        
        # TODO: Save censored_record
        if save:
            self.saveRecord(censored_record, save_path + str(competitor_idx) + ".txt")
        return censored_record

    
    def getFullInfoOfCompetitor(self, competitor_idx):
        '''
        Return type: list of list
            win or lose: 1 is win, 0 is lose
            winning_price: -1 if lose
            bidprice: float
            attributes: list
            pctr: float
            running_bid: float
        '''
        if competitor_idx >= self.num_competitors:
            print("Wrong competitor_idx!")
            return
        full_info = []
        for i in range(len(self.bid_record)):
            winning_price, winning_id, attributes, competitor_bidprices = self.bid_record[i]
            price, pctr, running_bid = self.competitors[competitor_idx].bidprice_record[i]
            if competitor_bidprices[competitor_idx][0] != price:
                print("Error!")
            if competitor_idx == winning_id:
                full_info.append([1, winning_price, competitor_bidprices[competitor_idx][0], attributes, pctr, running_bid])
            else:
                full_info.append([0, -1, competitor_bidprices[competitor_idx][0], attributes, pctr, running_bid])
        return full_info


    def clearRecord(self):
        self.bid_record = []
        for k in self.competitors:
            k.clearBidPriceRecord()


    def getRecordLength(self):
        return len(self.bid_record)


    # TODO: Save records
    def saveRecord(self, record, path):
        pass


    def generateRandomAttribute(self, attribute_idx, attribute_type):
        if attribute_type == "integer":
            return random.randint(1, self.integer_attributes_range[attribute_idx])
        elif attribute_type == "float":
            return random.random() * self.float_attributes_range[attribute_idx]