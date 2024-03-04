from textwrap import indent
from collections import defaultdict
import numpy as np
from scipy.sparse import lil_array

class FPNode:

    def __init__(self, parent, item):
    
        self.support = 1
        self.parent = parent
        self.item = item
        self.children = {}


class FPTree:

    def __init__(self, transactions: list, min_sup: float, conditional: list = []):
    
        self.min_sup = min_sup
        self.T = len(transactions)
        self.header = defaultdict(list)
        self.root = FPNode(None, None)
        self.conditional = conditional
        self.items_support = {}

        self.__build_tree(transactions)
        

    def __build_tree(self, transactions: list):

        transactions = [set(transaction) for transaction in transactions]
        supports = self.__get_support(transactions)
        reduced_transactions = self.__prune(transactions, supports)
        
        # Insert the transactions into the tree
        for transaction in reduced_transactions:
            self.__insert(self.root, transaction)
    
    
    def __insert(self, node: FPNode, itemset: list):
    
        if len(itemset) == 0:
            return
            
        item = itemset[0]
        if item in node.children:
            # support increment
            node.children[item].support += 1
        else:
            new_node = FPNode(node, item)
            node.children[item] = new_node
            # new node to the header list
            self.header[item].append(node.children[item])
            
        # add the rest of the transaction
        self.__insert(node.children[item], itemset[1:])

    def combinations(self, transaction: list):
    
        ans = {}

        for i in range(1, 2 ** len(transaction)):
        
            comb = []
            index = 0

            comb_support = self.T + 1  
            
            # check all bits turned on
            while i:
            
                if i % 2:
                
                    # Add corresponding transaction to the combination
                    comb.append(transaction[index])
                    # Update support of the combination
                    comb_support = min(
                        comb_support,
                        self.items_support[transaction[index]]
                    )
                index += 1
                i //= 2
            # Add combination if support is high enough
            if comb_support >= self.min_sup:
                ans[tuple(comb + self.conditional)] = comb_support
                
        return ans

    def cond_base(self, cond_item):
    
        new_transactions = []
        for node in self.header[cond_item]:
        
            support = node.support
            transaction = []
            node = node.parent
            while node.parent:
            
                transaction.append(node.item)
                node = node.parent
            # Add to the db the transaction support amount of times
            new_transactions.extend([transaction for _ in range(support)])
        return new_transactions

    def is_single_path(self, node: FPNode):
    
        if len(node.children) == 0:
            return True
        elif len(node.children) > 1:
            return False

        child = list(node.children.values())
        
        return self.is_single_path(child[0])

    
    def __get_support(self, transactions: list):
    
        supports = {}
        for transaction in transactions:
            for item in transaction:
                if supports.get(item) == None:
                    supports[item] = 0
                supports[item] += 1
        return supports

    def __prune(self, transactions: list, supports: dict):
        to_remove = set()
        for item, support in supports.items():
            if support < self.min_sup:
                to_remove.add(item)
            else:
                self.items_support[item] = support
        new_transactions = []
        for transaction in transactions:
            new_row = transaction.difference(to_remove)
            if new_row:
                new_transactions.append(
                    list(sorted(new_row, key=lambda x: supports[x], reverse=True)))
