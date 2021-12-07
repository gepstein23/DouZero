
from math import inf
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
    def __init__(self, position, last_two_moves, landlord_hand, landlord_down_hand, landlord_up_hand):
        self.position = position
        self.last_two_moves = last_two_moves
        self.landlord_hand = landlord_hand
        self.landlord_down_hand = landlord_down_hand
        self.landlord_up_hand = landlord_up_hand

    def getScore(self):
        if self.position == 'landlord':
            return len(self.landlord_hand)
        else:
            min_cards = len(self.landlord_down_hand) \
                if len(self.landlord_down_hand) < len(self.landlord_up_hand) else len(self.landlord_up_hand)

            return min_cards

class Node:
    def __init__(self):
        self.children = {}  # action: resulting node
        # TODO define class based represenation of this
        self.state = None  # info set object currently

# **Modified** MCTS Agent:
# This agent is called upon each time an action is to be selected.
# Each time it is called upon, it is trained with MCTS a certain number of times
# Each game this agent is used, it will update the saved mcts data to be used


class MctsAgent:
    ######################################################################
    ########################## UTILITIES #################################
    ######################################################################
    def __init__(self, position):
        self.name = 'MCTS'
        self.position = 'position'

    # Runs the given number of iterations PER action taken
    # Saves the updated data to the save file
    # Returns the best action
    def act(self, infoset, num_iterations=10):
        curr_hand = infoset.player_hand_cards

        card_str_list = util.env_arr2real_card_str(curr_hand)
        # print('last_two_moves', infoset.last_two_moves)
        best_action_tuple = util.get_best_actions(
            card_str_list, infoset.last_two_moves)

        # print('bestactiontuple', list(map(lambda x: x[0], best_action_tuple)))
        # print('legal actions', infoset.legal_actions)
        tree = self.create_tree(infoset, best_action_tuple)

        action = self.choose_best_action(tree, infoset)

        if action not in infoset.legal_actions:
            print("ILLEGAL ACTION", action)
            print(infoset.last_two_moves)
            print(infoset.legal_actions)

            # print(curr_hand)
            # print(infoset.all_handcards)
            # print(infoset.num_cards_left_dict)

        assert action in infoset.legal_actions

        return action

    # Returns the best action from the curr_hand based on self.mcts_data
    # (The action that will lead to the child with the highest number of visits)
    # def get_best_action(self, curr_hand, infoset):
    #     legal_moves = infoset.legal_actions
    #     if len(legal_moves[0]) == 0:
    #         return []

    #     # Picks the action that will lead to the child with the highest number of visits
    #     card_str_list = util.env_arr2real_card_str(curr_hand)
    #     best_action_tuple = util.get_best_actions(card_str_list, infoset=infoset)
    #     best_legal_moves = []
    #     for action in best_action_tuple:
    #         action = action[0]
    #         if legal_moves.__contains__(action):
    #             best_legal_moves.append(action)
    #     if len(best_legal_moves) == 0:
    #         if len(legal_moves) == 0:
    #             return []
    #         else:
    #             # we didn't generate an action when there are legal moves
    #             return legal_moves[0]
    #     else:
    #         return best_legal_moves[0]  # MCTS implementation

    # New state = our cards after playing the action, the opponents' cards after playing their next best action
    # The opponents right now choose the first action from the heuritic narrowed-down list
    def build_new_state(self, action_tuple, state):
        infoset = copy.deepcopy(state)
        last_move, new_hand = action_tuple
        # print('last_move', last_move)
        two_moves_ago = infoset.last_move
        # print('two_moves_ago', two_moves_ago)

        # update infoset / state with new hand
        new_all_player_cards = {infoset.player_position: new_hand}

        # update the "cur player" position
        curr_player = util.next_player(infoset.player_position)

        # play one round of play
        while curr_player != infoset.player_position:

            # get the hand of the current player
            hand = util.env_arr2real_card_str(
                infoset.all_handcards[curr_player])

            best_action_tuple = util.get_best_actions(
                hand, [last_move, two_moves_ago])

            # for opponnet, for now pick random suggested move
            new_action, new_hand = random.choice(best_action_tuple)

            new_all_player_cards[curr_player] = new_hand.copy()
            two_moves_ago = last_move.copy()
            last_move = new_action.copy()
            curr_player = util.next_player(curr_player)

        state = InfoSet(infoset.player_position)
        state.all_handcards = new_all_player_cards
        state.last_move = last_move
        node = Node()
        node.state = state
        node.num_team_cards = get_num_teamcards(state)
        return node

    def fill_node(self, root_node, depth):
        pass
        # if depth == 0:
        #   return root_node
        # BROKEN
        # for action_child_pair in root_node.children:
        #
        #   self.fill_node(action_child_pair[1], depth - 1)

    def create_tree(self, infoset, best_action_tuple):
        global TREE_TARGET_DEPTH
        root_node = Node()

        # create a node for each action from the hand
        for action in best_action_tuple:
            child_node = self.build_new_state(action, infoset)
            root_node.children[tuple(action[0])] = child_node

        self.fill_node(root_node, TREE_TARGET_DEPTH)
        root_node.state = infoset
        root_node.num_team_cards = get_num_teamcards(infoset)
        return root_node

    def choose_best_action(self, tree, infoset):
        lowest_num_cards_left = float('inf')
        best_action = None
        for action in tree.children:
            child_node = tree.children[action]
            if child_node.num_team_cards < lowest_num_cards_left:
                lowest_num_cards_left = child_node.num_team_cards
                best_action = action
        if best_action == None:
            return random.choice(infoset.legal_actions)
        result = list(best_action)

        return result

    # def traverse_round_tree(self, infoset):
    #   target_leaf_hand = None  # TODO
    #
    #   # while fully_expanded(node):
    #   #   node = best_uct(node)
    #   #
    #   # # in case no children are present / node is terminal
    #   # return pick_univisted(node.children) or node
    #
    #   return target_leaf_hand
    #
    # def round_rollout_policy(self, legal_actions_from_hand):
    #   return random.choice(legal_actions_from_hand)
    #
    # def rollout_round(self, target_leaf_hand):
    #   simulation_result = None  # TODO
    #   #   while non_terminal(node):
    #   #     node = rollout_policy(node)
    #   #   return result(node)
    #   return simulation_result
    #
    # def backpropagate(self, target_leaf_hand, simulation_result):
    #   # TODO update the mcts data??
    #
    #   #   if is_root(node) return
    #   #   node.stats = update_stats(node, result)
    #   #   backpropagate(node.parent)
    #   return None  # TODO nothing to return
