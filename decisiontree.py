import collections
import random
import copy
import bisect
from scipy.stats import wasserstein_distance
from utils import turnbull

class decisionTree:

    def __init__(self, attribute, sc, is_leaf, is_discrete, dist):
        self.attribute = attribute
        self.sc = sc
        self.left = None
        self.right = None
        self.is_leaf = is_leaf
        self.is_discrete = is_discrete
        self.dist = dist


    # Print decision tree
    def printTree(self):
        self.__printTreeHelper("", "")


    # Helper function for printing decision tree
    def __printTreeHelper(self, prefix, childrenPrefix):
        if self.is_leaf:
            print(prefix + str(self.dist[:3])[:-1] + " ... " + str(self.dist[-3:])[1:])
        else:
            if self.is_discrete:
                print(prefix + str(self.attribute) + " " + str(self.sc)[:5] + " ... " + str(self.sc)[-3:])
            else:
                print(prefix + str(self.attribute) + " " + str(self.sc[1])[:5] + " ... " + str(self.sc[1])[-3:])
            self.left.__printTreeHelper(childrenPrefix + "├── ", childrenPrefix + "│   ")
            self.right.__printTreeHelper(childrenPrefix + "└── ", childrenPrefix + "    ")

    def inference(self, data):
        '''
        Input type:
            attributes(list)
            ...
        '''
        if self.is_leaf:
            return self.dist
        if self.is_discrete:
            next_node = self.left if data[0][self.attribute] in self.sc else self.right
        else:
            next_node = self.left if self.sc[1][bisect.bisect_left(self.sc[0], data[0][self.attribute])] else self.right
        return next_node.inference(data)


class buildDecisionTree:

    def __init__(self, data, second_price_auction = True, num_categories = 100, num_price_bins = 100, is_discrete = [True, True, True, False, False, False, False, False, False, False]):
        '''
        Input type:
            data(list): Training data
                win or lose: 1 is win, 0 is lose
                winning_price: -1 if lose
                bidprice: float
                attributes: list
            num_categories(int): The number of bins for each continuous value
            num_price_bins(int): The number of bins for the price
            is_discrete(list of Boolean): Length is equal to the number of attributes. It is used to indicate if each attribute is discrete or not.
        '''
        self.root = None
        self.data = data
        self.second_price_auction = second_price_auction
        self.flatten_data = [k[-1] + k[:-1] for k in data]
        self.attributes_size = len(data[0][-1])
        self.num_categories = num_categories
        self.num_price_bins = num_price_bins
        self.is_discrete = is_discrete
        self.attribute_bins = self.findAttributeBins()
        self.price_bins = self.findPriceBins()


    def findAttributeBins(self):
        '''
        Function to find the bins for each attributes
        For discrete attribute, the bins are all distinct values
        For continuous attribute, the bins are intervals that are divided equally

        Return type: list of list
        '''
        attribute_bins = []
        for attribute_idx in range(self.attributes_size):
            if self.is_discrete[attribute_idx]:
                attribute_bins.append(list(set([k[attribute_idx] for k in self.flatten_data])))
            else:
                attribute_values = [k[attribute_idx] for k in self.flatten_data]
                min_attribute_value = min(attribute_values)
                max_attribute_value = max(attribute_values)
                bin_width = (max_attribute_value - min_attribute_value) / self.num_categories
                bins = [min_attribute_value + bin_width]
                for _ in range(1, self.num_categories - 1):
                    bins.append(bins[-1] + bin_width)
                attribute_bins.append(bins)
        return attribute_bins


    def findPriceBins(self):
        '''
        Function to find the bins for each price
        The bins are intervals that are divided equally

        Return type: list(length = self.num_price_bins - 1)
        represents the interval (-inf, x1], (x1, x2], ..., (xn, +inf)
        '''
        prices = [k[-1] if not k[-3] else k[-2] for k in self.flatten_data]
        min_price = min(prices)
        max_price = max(prices)
        bin_width = (max_price - min_price) / self.num_price_bins
        bins = [min_price + bin_width]
        for _ in range(1, self.num_price_bins - 1):
            bins.append(bins[-1] + bin_width)
        return bins


    def train(self, max_height = 5, min_leaf_size = 100, wasserstein = False):
        '''
        Function to train with the given stop conditions: max_height and min_leaf_size
        Save the built tree to self.root

        Return type: decisionTree
        '''
        self.root = self.build(self.flatten_data, 1, max_height, min_leaf_size, wasserstein)
        return self.root


    def build(self, data, current_height, max_height, min_leaf_size, wasserstein):
        '''
        Function to use recursion to build decision tree

        Return type: decisionTree
        '''
        if len(data) < min_leaf_size or current_height == max_height:
            return decisionTree(-1, -1, True, True, self.computeDataDistribution(data))
        else:
            tf, attribute, sc, left_data, right_data = self.findSplittingCriteria(data, wasserstein)
            if not tf:
                return decisionTree(-1, -1, True, True, self.computeDataDistribution(data))
            node = decisionTree(attribute, sc, False, self.is_discrete[attribute], -1)
            node.left = self.build(left_data, current_height + 1, max_height, min_leaf_size, wasserstein)
            node.right = self.build(right_data, current_height + 1, max_height, min_leaf_size, wasserstein)
            return node
            

    def findSplittingCriteria(self, data, wasserstein):
        '''
        Function to find the largest divergence among all attributes
        
        Return type: tuple
            find_or_not(Boolean): Whether we find a best criteria. If False, stop splitting the tree.
            attribute_idx(int): The index of the best attribute. -1 if find_or_not is False
            splittingcriteria:
                If the attribute is discrete, it is a set whose keys are the possible attribute values and values are 0 or 1
                If the attribute is continuous, it is a list of length self.num_attribute_bins[attribute_idx] and the values of this list are 0 or 1
                0 indicates right child and 1 indicates left child
                -1 if find_or_not is False
            left_data(list): Data of left child. [] if find_or_not is False
            right_data(list): Data of right child. [] if find_or_not is False
        '''
        kl_values = []
        for attribute_idx in range(self.attributes_size):
            tf, kl_attribute, splittingcriteria, left_data, right_data = self.computeAttributeKL(data, attribute_idx, wasserstein)
            if tf:
                kl_values.append((kl_attribute, attribute_idx, splittingcriteria, left_data, right_data))
        if kl_values:
            max_kl_value = max(kl_values)
            return True, max_kl_value[1], max_kl_value[2], max_kl_value[3], max_kl_value[4]
        else:
            return False, -1, -1, [], []


    def computeAttributeKL(self, data, attribute_idx, wasserstein):
        '''
        Function to find the best splitting criteria for attribute attribute_idx.

        Return type: tuple
            find_or_not(Boolean): Whether we find a best criteria. If False, stop splitting the tree.
            divergence(float): The max divergence value. -1 if find_or_not is False
            splittingcriteria:
                If the attribute is discrete, it is a set whose keys are the possible attribute values and values are 0 or 1
                If the attribute is continuous, it is a list of length self.num_attribute_bins[attribute_idx] and the values of this list are 0 or 1
                0 indicates right child and 1 indicates left child
                -1 if find_or_not is False
            left_data(list): Data of left child. [] if find_or_not is False
            right_data(list): Data of right child. [] if find_or_not is False
        '''
        if self.is_discrete[attribute_idx]:
            this_attribute_bins = self.attribute_bins[attribute_idx]
            val_data = collections.defaultdict(list)
            for k in data:
                val_data[k[attribute_idx]].append(k)
            left_or_right = [random.randint(0, 1) for _ in range(len(this_attribute_bins))]
            left = set()
            for i in range(len(this_attribute_bins)):
                if left_or_right[i]:
                    left.add(this_attribute_bins[i])
            
            not_converge = True
            while not_converge:
                preleft = copy.deepcopy(left)
                left_data, right_data = [], []
                for k in this_attribute_bins:
                    if k in left:
                        left_data.extend(val_data[k])
                    else:
                        right_data.extend(val_data[k])
                left_distribution, right_distribution = self.computeDataDistribution(left_data), self.computeDataDistribution(right_data)

                for val in this_attribute_bins:
                    bin_data = val_data[val]
                    bin_distribution = self.computeDataDistribution(bin_data)
                    left_div = self.computeKLDivergence(left_distribution, bin_distribution, wasserstein)
                    right_div = self.computeKLDivergence(right_distribution, bin_distribution, wasserstein)
                    if left_div < right_div and val not in left:
                        left.add(val)
                    elif left_div > right_div and val in left:
                        left.remove(val)
                
                not_converge = (left != preleft)

            # Decide if split succeed
            if (len(left) == 0) or (len(left) == len(self.attribute_bins[attribute_idx])):
                return False, -1, -1, [], []

            kl_div = self.computeKLDivergence(left_distribution, right_distribution, wasserstein)
            return True, kl_div, left, left_data, right_data
        else:
            this_attribute_bins = self.attribute_bins[attribute_idx]
            left_or_right = [random.randint(0, 1) for _ in range(len(this_attribute_bins) + 1)]
            val_data = [[] for _ in range(len(left_or_right))]
            for k in data:
                pos = bisect.bisect_left(this_attribute_bins, k[attribute_idx])
                val_data[pos].append(k)
            not_converge = True

            while not_converge:
                pre_left_or_right = copy.deepcopy(left_or_right)
                left_data, right_data = [], []
                for i in range(len(left_or_right)):
                    if left_or_right[i]:
                        left_data.extend(val_data[i])
                    else:
                        right_data.extend(val_data[i])
                left_distribution, right_distribution = self.computeDataDistribution(left_data), self.computeDataDistribution(right_data)

                for i in range(len(left_or_right)):
                    bin_data = val_data[i]
                    bin_distribution = self.computeDataDistribution(bin_data)
                    left_div = self.computeKLDivergence(left_distribution, bin_distribution, wasserstein)
                    right_div = self.computeKLDivergence(right_distribution, bin_distribution, wasserstein)
                    if left_div < right_div and left_or_right[i] == 0:
                        left_or_right[i] = 1
                    elif left_div > right_div and left_or_right[i] == 1:
                        left_or_right[i] = 0
                
                not_converge = (left_or_right != pre_left_or_right)

            # Decide if split succeed
            if all(left_or_right) or (not any(left_or_right)):
                return False, -1, -1, [], []

            kl_div = self.computeKLDivergence(left_distribution, right_distribution, wasserstein)
            return True, kl_div, (this_attribute_bins, left_or_right), left_data, right_data


    def computeDataDistribution(self, data):
        if self.second_price_auction:
            return self.computeDataDistributionByKME(data)
        else:
            return self.computeDataDistributionByTurnbull(data)

    def computeDataDistributionByKME(self, data):
        '''
        Function to find the PDF distribution of the input data based on price bins in self.price_bins
        TODO: determine whether to use PDF or CDF

        Return type: list of length self.num_price_bins
        '''
        count = [[0, 0] for _ in range(self.num_price_bins)]
        for k in data:
            price = k[-2] if k[-3] else k[-1]
            pos = bisect.bisect_left(self.price_bins, price)
            count[pos][0] += int(k[-3])
            count[pos][1] += 1 - int(k[-3])
        loseprob = [1]
        ni = len(data)
        for i in range(len(count)):
            di = count[i][0]
            if i:
                ni -= count[i - 1][0] + count[i - 1][1]
            if ni != 0:
                loseprob.append(loseprob[-1] * (1 - di / ni))
            else:
                loseprob.append(loseprob[-1])
        winprob = [1 - k for k in loseprob]

        # Use CDF instead
        dist = winprob[1:]
        # dist = []
        # for i in range(1, len(loseprob)):
        #     dist.append(winprob[i] - winprob[i - 1])
        return dist


    def computeDataDistributionByTurnbull(self, data):
        modified_data = []
        for k in data:
            price = k[-2] if k[-3] else k[-1]
            modified_data.append([price, k[-3]])
        return turnbull(modified_data, bins = self.price_bins)[1]


    def computeKLDivergence(self, dist1, dist2, wasserstein):
        '''
        Function to compute the divergence
        Right now we use Euclid divergence here to avoid q = 0
        TODO: How to change back to KL divergence? Substitute 0 with a very small epsilon?

        Return type: float
        '''
        if wasserstein:
            div = wasserstein_distance(dist1, dist2)
        else:
            div = sum([(dist1[i] - dist2[i]) * (dist1[i] - dist2[i]) for i in range(len(dist1))])
        return div