import numpy as np

from collections import defaultdict
from utils import HashTree, FPTree


class Apriori:

    def __init__(self):
    
        self.min_sup = 1
    
    def fit(self, transactions: list, min_sup: float, alpha: float = 0.0):
    
        self.min_sup = int(len(transactions) * min_sup)
        # frequent set
        L = []
        # candidate set
        candidates = self.__generate_candidate(transactions, L, K=1)
        C, support = candidates['Itemset'], candidates['Support']


        L.append(self.__prune(support))

        k = 1
        while True:
        
            min_sup -= alpha
            if min_sup > 0.0:
                self.min_sup = int(len(transactions) * min_sup)

            candidates = self.__join(transactions, L[k - 1]['Itemset'])
            C = candidates['Itemset']
            support = candidates['Support']
            C = self.__prune(support)
            
            if len(C['Itemset']) == 0:
                break
                
            L.append(C)

            k += 1

        return L

    def __join(self, transactions: list, itemsets: list) -> dict:
    
        L = len(itemsets)

        J = []
        for i in range(L):
            for j in range(i + 1, L):
                if itemsets[i][:-1] == itemsets[j][:-1]:
                
                    new_itemset = frozenset(itemsets[i] + [itemsets[j][-1]])
                    J.append(new_itemset)

        return {'Itemset': J, 'Support': self.__get_support(transactions, J)}

    def __generate_candidate(self, transactions: list, L, K) -> dict:
    
        # frequent 1-itemset
        if K == 1:

            uniqe_items = set(
                [item for transaction in transactions for item in transaction]
            )

            supports = defaultdict(int)
            for transaction in transactions:
                for item in transaction:    
                    if item in uniqe_items:
                        supports[(item, )] += 1
            
            return {
                'Itemset': np.expand_dims(list(uniqe_items), axis=1).tolist(),
                'Support': supports
            }

        # L: frequent (k-1)-itemset
        C = self.__join(L)

        return C


    def __get_support(self, transactions: list, itemsets: list):
    
        supports = defaultdict(int)

        for transaction in transactions:
            for itemset in itemsets:
                if len(itemset & transaction) == len(itemset):
                    supports[itemset] += 1
        
        return supports
    
    def __prune(self, support):
    
        res = {
            'Itemset': [],
            'Support': []
        }
        
        for c, s in support.items():
            if s >= self.min_sup:
            
                res['Itemset'].append(list(c))
                res['Support'].append(s)
        
        return res





class FPGrowth:

    def __init__(self):
    
        self.transactions = None
        self.min_sup = None
        self.confidence = None
        self.tree = None
        self.patterns = None

    def fit(self, transactions: list, min_sup: float):
    
        self.transactions = transactions
        self.min_sup = int(min_sup * len(transactions))
        self.tree = FPTree(transactions, self.min_sup)
        self.frequent_patterns = self.__find_frequent_patterns(self.tree)
        return self.frequent_patterns
    
    def __find_frequent_patterns(self, fptree: FPTree):
    
        if fptree.is_single_path(fptree.root):
        
            transaction = []
            node = fptree.root
            
            while node.children:
            
                child = list(node.children.values())
                node = child[0]
                transaction.append(node.item)
            
            # combinations of the transaction
            return fptree.combinations(transaction)
        else:
        
            patterns = {}
            for item in fptree.header:
                # conditional base for item and suffix
                cond_base = fptree.cond_base(item)
                # Add the patterns generated of item and suffix
                patterns = self.__join_dicts(
                    patterns,
                    {
                        tuple([item] + fptree.conditional): fptree.items_support[item]
                    }
                )
                # Add patterns generated for the conditional tree
                patterns = self.__join_dicts(
                    patterns,
                    self.__find_frequent_patterns(
                        FPTree(cond_base, fptree.min_sup, [item] + fptree.conditional)
                    )
                )  
            return patterns
    
    def __join_dicts(self, d1, d2):
            
        return {
            k: d1.get(k, 0) + d2.get(k, 0) for k in set(d1.keys()).union(set(d2.keys()))
        }



class ECLAT:

    def __init__(self):
    
        self.min_sup = 1
    
    def fit(self, transactions: list, min_sup: float):

        self.min_sup = int(min_sup * len(transactions))
        
        table = self.__get_support(transactions)
        table = self.__prune(table)

        L = [{itemset: len(TIDs)} for itemset, TIDs in table.items()]

        while True:
        
            table = self.__join(table)
            table = self.__prune(table)
            
            if len(table) == 0:
                break
                
            L.extend([{itemset: len(TIDs)} for itemset, TIDs in table.items()])
        
        return L

    def __get_support(self, transactions):
    
        supports = {}
        for i, transaction in enumerate(transactions):
            for item in transaction:
                if supports.get((item, )) == None:
                    supports[(item, )] = set()
                    
                supports[(item, )].add(i)

        return supports
    
    def __prune(self, supports):
    
        keys = tuple(supports.keys())
        for item in keys:
            if len(supports[item]) < self.min_sup:
                supports.pop(item)
                
        return supports
    
    def __join(self, table):
    
        L = len(table)
        itemsets = list(table.keys())
        J = {}
        for i in range(L):
            for j in range(i + 1, L):
                if itemsets[i][:-1] == itemsets[j][:-1]:
                
                    new_itemset = list(itemsets[i][:-1])
                    new_itemset.append(itemsets[i][-1])
                    new_itemset.append(itemsets[j][-1])
                    J[tuple(new_itemset)] = table[itemsets[i]] & table[itemsets[j]]

        return J
