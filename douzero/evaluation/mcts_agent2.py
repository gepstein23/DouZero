"""
A minimal implementation of Monte Carlo tree search (MCTS) in Python 3
Luke Harold Miles, July 2019, Public Domain Dedication
See also https://en.wikipedia.org/wiki/Monte_Carlo_tree_search
https://gist.github.com/qpwo/c538c6f73727e254fdc7fab81024f6e1
"""
from collections import deque
from collections import namedtuple

from douzero.dmc.utils import act
from . import util
import random
from abc import ABC, abstractmethod
from collections import defaultdict
import math

# Much of this file was taken from: https://gist.github.com/qpwo/c538c6f73727e254fdc7fab81024f6e1
# after much attempt to try to write our own implementation of MCTS


class MCTS:
    "Monte Carlo tree searcher. First rollout the tree then choose a move."

    def __init__(self, exploration_weight=.5, depth=4):
        self.Q = defaultdict(int)  # total reward of each node
        self.N = defaultdict(int)  # total visit count for each node
        self.children = dict()  # children of each node
        self.exploration_weight = exploration_weight
        self.depth = depth

    def choose(self, node):
        "Choose the best successor of node. (Choose a move in the game)"
        if node.is_terminal():
            raise RuntimeError(f"choose called on terminal node {node}")

        if node not in self.children:
            return node.find_random_child()
        
        def score(n):
            if self.N[n] == 0:
                return float("-inf")  # avoid unseen moves

            print((n.player_action, n.all_handcards[n.position]), self.Q[n] / self.N[n])
            return self.Q[n] / self.N[n]  # average reward

        print('------------\n')
        print('Last Two Moves: ', node.last_two_moves)
        
        return max(self.children[node], key=score)

    def do_rollout(self, node):
        "Make the tree one layer better. (Train for one iteration.)"
        path = self._select(node)
        leaf = path[-1]
        self._expand(leaf)
        reward = self._simulate(leaf)
        self._backpropagate(path, reward)

    def _select(self, node):
        "Find an unexplored descendent of `node`"
        path = []
        while True:
            path.append(node)
            if node not in self.children or not self.children[node]:
                # node is either unexplored or terminal
                return path
            unexplored = self.children[node] - self.children.keys()
            if unexplored:
                n = unexplored.pop()
                path.append(n)
                return path
            node = self._uct_select(node)  # descend a layer deeper

    def _expand(self, node):
        "Update the `children` dict with the children of `node`"
        if node in self.children:
            return  # already expanded
        self.children[node] = node.find_children()

    def _simulate(self, node):
        "Returns the reward for a random simulation (to completion) of `node`"
        cur_depth = 0
        while cur_depth < self.depth:
            if node.is_terminal():
                return node.reward()
            node = node.find_random_child()
            cur_depth += 1
        return node.reward()

    def _backpropagate(self, path, reward):
        "Send the reward back up to the ancestors of the leaf"
        for node in reversed(path):
            self.N[node] += 1
            self.Q[node] += reward
            reward = reward 

    def _uct_select(self, node):
        "Select a child of node, balancing exploration & exploitation"

        # All children of node should already be expanded:
        assert all(n in self.children for n in self.children[node])

        log_N_vertex = math.log(self.N[node])

        def uct(n):
            avg_score = self.Q[n] / self.N[n]
            explore_val = math.sqrt(log_N_vertex / self.N[n])
            "Upper confidence bound for trees"
            return avg_score + self.exploration_weight * explore_val

        return max(self.children[node], key=uct)


class Node(ABC):
    """
    A representation of a single board state.
    MCTS works by constructing a tree of these Nodes.
    Could be e.g. a chess or checkers board state.
    """

    @abstractmethod
    def find_children(self):
        "All possible successors of this board state"
        return set()

    @abstractmethod
    def find_random_child(self):
        "Random successor of this board state (for more efficient simulation)"
        return None

    @abstractmethod
    def is_terminal(self):
        "Returns True if the node has no children"
        return True

    @abstractmethod
    def reward(self):
        "Assumes `self` is terminal node. 1=win, 0=loss, .5=tie, etc"
        return 0

    @abstractmethod
    def __hash__(self):
        "Nodes must be hashable"
        return 123456789

    @abstractmethod
    def __eq__(node1, node2):
        "Nodes must be comparable"
        return node1 == node2


# TODO UPDATE STATE HERE FOR V2
# TODO POTENTIALLY ADD UNPLAYED CARD LIST AND PLAYER_HAND CARDS
_DD = namedtuple(
    "DouDizhuNode", "position player_action last_two_moves all_handcards is_root")

# Inheriting from a namedtuple is convenient because it makes the class
# immutable and predefines __init__, __repr__, __hash__, __eq__, and others
class DouDizhuNode(_DD, Node):
    # TODO UPDATE HASH HERE FOR V2
    def __hash__(self):
        action_str = util.env_arr2real_card_str(self.player_action)
        hand_str = util.env_arr2real_card_str(
            self.all_handcards[self.position])
        return hash(action_str + hand_str)

    def is_terminal(self):
        if self.is_root:
            return False

        for position in self.all_handcards:
            hand = self.all_handcards[position]
            if len(hand) == 0:
                return True

        return False

    def is_player_winner(self):
      landlord_count = len(self.all_handcards['landlord'])
      landlord_down_count = len(self.all_handcards['landlord_down'])
      landlord_up_count = len(self.all_handcards['landlord_up'])

      if self.position == 'landlord':
        return landlord_count == 0
      else:
        return landlord_up_count == 0 or landlord_down_count == 0

    def find_children(self):
        if self.is_terminal():
            return set()

        action_tuples = util.get_best_actions(
            self.all_handcards[self.position], self.last_two_moves)

        children = {
            self.make_action(action_tuple) for action_tuple in action_tuples
        }

        return children

    def find_random_child(self):
        if self.is_terminal():
            return None  # If the game is finished then no moves can be made

        action_tuples = util.get_best_actions(
            self.all_handcards[self.position], self.last_two_moves)

        choice = random.choice(action_tuples)
        return self.make_action(choice)

    # We want the have the largest difference between our cards and their cards
    def reward(self):
        if self.is_terminal():
          return 10 if self.is_player_winner() else -10

        landlord_count = len(self.all_handcards['landlord'])
        landlord_down_count = len(self.all_handcards['landlord_down'])
        landlord_up_count = len(self.all_handcards['landlord_up'])

        min_farmer_count = landlord_down_count if landlord_down_count < landlord_up_count else landlord_up_count

        if self.position == 'landlord':
            return min_farmer_count - landlord_count
        else:
            return landlord_count - min_farmer_count

    # TODO THIS IS BASICALLY OUR HEURISTIC FOR ADDING NODES
    # TODO THIS IS WHERE TO CHANGE HOW OPPONENT HAND IS SELECTED
    def make_action(self, action_tuple):
        all_handcards = dict()
        position = self.position
        # Update the players hand in all_handcards and hand
        last_move, player_hand = action_tuple
        player_action = last_move
        all_handcards[position] = player_hand # update the player hand based on last action

        # update the last two moves now that we have taken another action
        updated_last_two_moves = [last_move, self.last_two_moves[0]]

        # set
        cur_player_position = position
        # choose random actions for the other players and update their state
        for i in range(2):
            # increment to the next player
            cur_player_position = util.next_player(cur_player_position)

            # get the best actions for theis player
            best_action_tuples = util.get_best_actions(
                self.all_handcards[cur_player_position],
                updated_last_two_moves)
            
            # remove passing as an option from opponents if they have other options
            passing_action_tuple = ([], self.all_handcards[cur_player_position])
            if len(best_action_tuples) > 1 and passing_action_tuple in best_action_tuples:
              best_action_tuples.remove(passing_action_tuple)

            # make a random choice for the next player based on their best actions
            action, next_hand = random.choice(best_action_tuples)

            # update last moves
            updated_last_two_moves = [action, updated_last_two_moves[0]]

            # update the players hand at this position
            all_handcards[cur_player_position] = next_hand

        # update the state with the players last two moves
        last_two_moves = updated_last_two_moves

        return DouDizhuNode(position, player_action, last_two_moves, all_handcards, False)

    def pretty_print(self, tree):
        queue = deque()
        deque.append(self)

        while len(queue) > 0:
            level_size = len(queue)

            for i in range(level_size):
                node = queue.popLeft()
                avg_score = tree.Q[node] / tree.N[node]
                print('Prev Hand: %s Action: %s Score: %f' % (util.env_arr2real_card_str(
                    self.all_handcards[self.position]), util.env_arr2real_card_str(self.player_action[0]), avg_score))
                for el in node.children:
                  next_node = node.children[el]
                  queue.append(next_node)

class MctsAgent:
    ######################################################################
    ########################## UTILITIES #################################
    ######################################################################
    def __init__(self, position, depth=5, num_rollouts=1000):
        self.name = 'MCTS'
        self.position = position
        self.depth = depth
        self.num_rollouts = num_rollouts

    # Runs the given number of iterations PER action taken
    # Saves the updated data to the save file
    # Returns the best action
    def act(self, infoset):
        tree = MCTS(depth=self.depth)
        node = DouDizhuNode(infoset.player_position, [],
                            infoset.last_two_moves, infoset.all_handcards, True)

        # You can train as you go, or only at the beginning.
        # Here, we train as we go, doing fifty rollouts each turn.
        for _ in range(self.num_rollouts):
            tree.do_rollout(node)

        # node.pretty_print(tree)

        best_node = tree.choose(node)

        action = best_node.player_action

        #print('CHOSEN ACTION:', action)
        
        if action not in infoset.legal_actions:
            print('ILLEGAL ACTION:', action)
            print('LAST TWO MOVES', infoset.last_two_moves)
            print('LEGAL ACTIONS', infoset.legal_actions)
            print('HAND', infoset.player_hand_cards)
            action = random.choice(infoset.legal_actions)



        assert action in infoset.legal_actions

        return action
