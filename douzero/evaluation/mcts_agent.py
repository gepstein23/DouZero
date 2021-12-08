import math
import random
import json
import copy

from douzero.dmc.utils import act
from . import util
from ..env.game import InfoSet

MCTS_DATA_FILE_NAME = 'C:\\Users\\Genevieve\\Desktop\\NEU\\Fall_2021\\ai\\DouZero\\douzero\\evaluation\\mcts_agent_data.txt'  # TODO
VERBOSE = True
TREE_TARGET_DEPTH = 5


def debug(*msgs):
    global VERBOSE
    if VERBOSE:
        result = ""
        for msg in msgs:
            result += str(msg)
        print(result)

# Represents a node of mcts including all children nodes


class MctsState:
    def __init__(self, position, player_action, last_two_moves, all_handcards):
        self.position = position
        self.player_action = action
        self.last_two_moves = last_two_moves
        self.all_handcards = all_handcards

    def getScore(self):
        if self.position == 'landlord':
            return len(self.all_handcards['landlord'])
        else:
            min_cards = len(self.all_handcards['landlord_down']) \
                if len(self.all_handcards['landlord_down']) < len(self.all_handcards['landlord_up']) \
                else len(self.all_handcards['landlord_up'])

            return min_cards


class Node:
    def __init__(self, state=None, is_root=False, parent_key=None):
        self.state = state  # MCTS Object
        self.count = 0
        self.score = 0
        self.is_root = is_root

    def reward(self):
        return self.score / self.count

    def is_terminal(self):
        if self.is_root or self.state == None:
            return

        for hand in self.state.all_handcards:
            print(hand)
            if len(hand) == 0:
                return True

        return False

    def find_random_child(self):
        return random.choice(self.children)

# **Modified** MCTS Agent:
# This agent is called upon each time an action is to be selected.
# Each time it is called upon, it is trained with MCTS a certain number of times
# Each game this agent is used, it will update the saved mcts data to be used


class MctsAgent:
    ######################################################################
    ########################## UTILITIES #################################
    ######################################################################
    def __init__(self, position, depth=2, num_rollouts=10, exploration_weight=0.8):
        self.name = 'MCTS'
        self.position = position
        self.depth = depth
        self.num_rollouts = num_rollouts
        self.children = dict()
        self.exploration_weight = exploration_weight

    # Runs the given number of iterations PER action taken
    # Saves the updated data to the save file
    # Returns the best action
    def act(self, infoset):

        state = MctsState(infoset.player_position, [],
                          infoset.last_two_moves, infoset.all_handcards)

        root_node = Node(state, is_root=True)

        for _ in range(self.num_rollouts):
            self.do_rollout(root_node)

        action = self.choose_best_action(root_node, infoset)

        assert action in infoset.legal_actions

        return action

    def do_rollout(self, root_node):
        path = self.select(root_node)
        self.expand_tree(root_node)
        action_str = util.env_arr2real_card_str(action_tuple[0])
        reward = self.simulate(self.children[root_node])
        self.backpropogate(action_tuple, reward)

    def select(self, node):
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
            node = self.uct_select(node)  # descend a layer deeper

    def uct_select(self, node):
        "Select a child of node, balancing exploration & exploitation"

        # All children of node should already be expanded:
        assert all(n in self.children for n in self.children[node])

        log_N_vertex = math.log(node.count)

        def uct(n):
            "Upper confidence bound for trees"
            return node.score / node.count + self.exploration_weight * math.sqrt(
                log_N_vertex / node.count
            )

        return max(self.children[node], key=uct)

    def expand_tree(self, node):
        if node in self.children:
            return  # already expanded

        state = node.state
        hand_str = util.env_arr2real_card_str(
            state.all_handcards[state.position])
        best_action_tuples = util.get_best_actions(
            hand_str, state.last_two_moves)

        for action_tuple in best_action_tuples:
            self.children[node] = self.build_child_node(
                action_tuple, node.state)

    # New state = our cards after playing the action, the opponents' cards after playing their next best action
    # The opponents right now choose the first action from the heuritic narrowed-down list

    def build_child_node(self, action_tuple, parent_state):
        new_state = copy.deepcopy(parent_state)

        last_move, player_hand = action_tuple

        new_state.player_action = last_move

        # update the last two moves now that we have taken another action
        updated_last_two_moves = [last_move, new_state.last_two_moves[0]]

        # Update the players hand in all_handcards
        new_state.all_handcards[new_state.position] = player_hand

        # choose random actions for the other players and update their state
        for i in range(2):
            # increment to the next player
            next_player_position = util.next_player(parent_state.position)

            best_action_tuples = util.get_best_actions(
                parent_state.all_handcards[next_player_position],
                updated_last_two_moves)

            # make a random choice for the next player based on their best actions
            action, next_hand = random.choice(best_action_tuples)

            # update last moves
            updated_last_two_moves = [action, updated_last_two_moves[0]]

            # update the players hand at this position
            new_state.all_handcards[next_player_position] = next_hand

        # update the state with the players last two moves
        new_state.last_two_moves = updated_last_two_moves

        return Node(new_state)

    def simulate(self, node):
        "Returns the reward for a random simulation (to completion) of `node`"
        cur_depth = 0
        while cur_depth < self.depth:
            if node.is_terminal():
                return node.reward()
            node = node.find_random_child()
            cur_depth += 1
        return node.reward()

    def backpropogate(self, path, reward):
        "Send the reward back up to the ancestors of the leaf"
        for node in reversed(path):
            node.count += 1
            node.score += reward

    def choose_best_action(self, root_node, infoset):
        lowest_num_cards_left = float('inf')
        best_action = None
        for child_node in self.children[root_node]:
            if child_node.getScore() < lowest_num_cards_left:
                lowest_num_cards_left = child_node.getScore()
                best_action = child_node.player_action
        if best_action == None:
            return random.choice(infoset.legal_actions)
        result = list(best_action)

        return result