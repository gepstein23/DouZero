import copy
from rlcard.games.doudizhu.utils import CARD_TYPE

#from douzero.dmc.utils import act

EnvCard2RealCard = {3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
                    8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q',
                    13: 'K', 14: 'A', 17: '2', 20: 'B', 30: 'R'}
RealCard2EnvCard = {'3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                    '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12,
                    'K': 13, 'A': 14, '2': 17, 'B': 20, 'R': 30}

INDEX = {'3': 0, '4': 1, '5': 2, '6': 3, '7': 4,
         '8': 5, '9': 6, 'T': 7, 'J': 8, 'Q': 9,
         'K': 10, 'A': 11, '2': 12, 'B': 13, 'R': 14}


def get_best_actions(hand_cards, last_two_moves):
    last_move, two_moves_ago = last_two_moves
    lm = last_move

    if len(last_move) == 0:
        lm = two_moves_ago

    combinations = get_combinations(env_arr2real_card_str(hand_cards))
    moves = []
    if len(lm) == 0:
        moves = get_best_leading_moves(hand_cards, combinations)
    else:
        moves = get_best_following_moves(hand_cards, combinations, lm)

    return moves

# Get the best combinations from your hand.
# TODO generate all chains, trios recursively and the solos / pairs that arise from that because
# TODO sometimes these may result in better plays to play a "worse" combos

def get_combinations(hand):
    '''Get optimal combinations of cards in hand
    '''
    comb = {'rocket': [], 'bomb': [], 'trio': [], 'trio_kickers': [], 'trio_chain': [],
            'solo_chain': [], 'pair_chain': [], 'pair': [], 'solo': []}
    # 1. pick rocket
    if hand[-2:] == 'BR':
        comb['rocket'].append('BR')
        hand = hand[:-2]
    # 2. pick bomb
    hand_cp = hand
    for index in range(len(hand_cp) - 3):
        if hand_cp[index] == hand_cp[index + 3]:
            bomb = hand_cp[index: index + 4]
            comb['bomb'].append(bomb)
            hand = hand.replace(bomb, '')
    # 3. pick trio and trio_chain
    hand_cp = hand
    for index in range(len(hand_cp) - 2):
        if hand_cp[index] == hand_cp[index + 2]:
            trio = hand_cp[index: index + 3]
            if len(comb['trio']) > 0 and INDEX[trio[-1]] < 12 and (INDEX[trio[-1]] - 1) == INDEX[comb['trio'][-1][-1]]:
                comb['trio'][-1] += trio
            else:
                comb['trio'].append(trio)
            hand = hand.replace(trio, '')
    only_trio = []
    only_trio_chain = []
    for trio in comb['trio']:
        if len(trio) == 3:
            only_trio.append(trio)
        else:
            only_trio_chain.append(trio)
    comb['trio'] = only_trio
    comb['trio_chain'] = only_trio_chain

    hand_list = card_str2count_list(hand)

    # The following two combos are the change from V1.
    # 4. Pick Non Disruptive Pair Chains
    chains, hand_list = pick_non_disruptive_pair_chains(hand_list)
    comb['pair_chain'] = chains

    # 5. Pick solo chains
    chains, hand_list = pick_chain_v2(hand_list, 1)
    comb['solo_chain'] = chains

    # update hand again with new hand list
    hand = count_list2card_str(hand_list)

    # 6. pick pair and solo
    index = 0
    while index < len(hand) - 1:
        if hand[index] == hand[index + 1]:
            comb['pair'].append(hand[index] + hand[index + 1])
            index += 2
        else:
            comb['solo'].append(hand[index])
            index += 1
    if index == (len(hand) - 1):
        comb['solo'].append(hand[index])

    # 7. Add lowest solo and pairs to trios
    solosAndPairs = comb['solo'] + comb['pair']
    # sort by rank
    solosAndPairs.sort(key=lambda acs: int(
        CARD_TYPE[0][acs][0][1]), reverse=True)

    # reverse trio so we can pop trios we've added kickers to off the back
    comb['trio'].reverse()

    popFromTrioCount = 0
    # add the lowest kickers to each each trio_kicker
    for i in range(len(comb['trio'])):
        if len(solosAndPairs) > 0:
            el = solosAndPairs.pop()
            # sort the trio so that the lower rank cards come first
            new_acs = comb['trio'][i] + el
            popFromTrioCount += 1
            new_ac = real_card_str2env_arr(new_acs)
            new_ac.sort()
            comb['trio_kickers'].append(env_arr2real_card_str(new_ac))

    for i in range(popFromTrioCount):
        comb['trio'].pop()

    # put the lists back in their normal order
    comb['trio'].reverse()
    return comb


def getFirstAndLastArr(arr):
    if len(arr) < 2:
        return arr

    return arr[::len(arr) - 1]


def convertActionListArr(arr):
    return list(map(lambda tuple: (real_card_str2env_arr(tuple[0]), real_card_str2env_arr(tuple[1])), arr))


def getNextHandTupleArr(hand, action_strs):
    def filterHand(action_str): 
        hand_str = env_arr2real_card_str(hand)
        for c in action_str:
            hand_str = hand_str.replace(c, '')
        return (action_str, hand_str)
    return list(map(filterHand, action_strs))

def formatResultTuple(hand, action_strs):
    return convertActionListArr(getNextHandTupleArr(hand, action_strs))


# Get a prioritzed array of all the best moves from your combinations
def get_best_leading_moves(hand, combinations):
    action_strs = combinations['trio_chain'] + combinations['pair_chain'] + combinations['solo_chain'] \
        + getFirstAndLastArr(combinations['trio_kickers']) + getFirstAndLastArr(combinations['trio']) \
        + getFirstAndLastArr(combinations['pair']) + getFirstAndLastArr(combinations['solo']) + \
        combinations['bomb'] + combinations['rocket']

    result = formatResultTuple(hand, action_strs)

    return result


TRIO_CHAIN = 'trio_chain'
PAIR_CHAIN = 'pair_chain'
SOLO_CHAIN = 'solo_chain'
TRIO = 'trio'
TRIO_SOLO = 'trio_solo'
TRIO_PAIR = 'trio_pair'
PAIR = 'pair'
SOLO = 'solo'

# the idea behind this is we don't want to break up our best hands, we would rather pass
# Additionally, playing your highest ranked hands may be advantageous over lowest ranked to control
# the board sometimes.


def get_best_following_moves(hand, combinations, last_move):
    last_move_str = env_arr2real_card_str(last_move)
    the_type, last_rank = CARD_TYPE[0][last_move_str][0]
    last_rank = int(last_rank)

    moves = []

    if PAIR_CHAIN in the_type:
        for move in combinations['pair_chain']:
            if len(move) >= len(last_move):
                new_move = move[len(move) - len(last_move):]
                this_rank = int(CARD_TYPE[0][new_move][0][1])
                if this_rank > last_rank:
                    moves.append(new_move)
    elif SOLO_CHAIN in the_type:
        for move in combinations['solo_chain']:
            if len(move) >= len(last_move):
                new_move = move[len(move) - len(last_move):]
                this_rank = int(CARD_TYPE[0][new_move][0][1])
                if this_rank > last_rank:
                    moves.append(new_move)
    elif TRIO == the_type:
        for move in combinations['trio']:
            this_rank = int(CARD_TYPE[0][move][0][1])
            if this_rank > last_rank:
                moves.append(move)
    elif TRIO_SOLO == the_type:
        for move in combinations['trio']:
            this_rank = int(CARD_TYPE[0][move][0][1])
            if this_rank > last_rank and len(combinations['solo']) > 0:
                trio = move + combinations['solo'][0]
                trio_arr = real_card_str2env_arr(trio)
                trio_arr.sort()
                moves.append(env_arr2real_card_str(trio_arr))
    elif TRIO_PAIR == the_type:
        for move in combinations['trio']:
            this_rank = int(CARD_TYPE[0][move][0][1])
            if this_rank > last_rank and len(combinations['pair']) > 0:
                trio = move + combinations['pair'][0]
                trio_arr = real_card_str2env_arr(trio)
                trio_arr.sort()
                moves.append(env_arr2real_card_str(trio_arr))
    elif PAIR == the_type:
        for move in combinations['pair']:
            this_rank = int(CARD_TYPE[0][move][0][1])
            if this_rank > last_rank:
                moves.append(move)
    elif SOLO == the_type:
        for move in combinations['solo']:
            this_rank = int(CARD_TYPE[0][move][0][1])
            if this_rank > last_rank:
                moves.append(move)
    
    legal_bombs = []
    if 'bomb' == the_type:
        for move in combinations['bomb']:
            this_rank = int(CARD_TYPE[0][move][0][1])
            if this_rank > last_rank:
                legal_bombs.append(move)
    elif 'rocket' != the_type:
        legal_bombs = combinations['bomb']

    # prior_moves = copy.copy(moves)
    moves = getFirstAndLastArr(moves) + legal_bombs + combinations['rocket']

    # if env_arr2real_card_str([3, 4, 6, 6, 6, 7, 8, 9, 10, 11, 12, 13, 14]) == env_arr2real_card_str(hand):
    #     print('hand', hand)
    #     print('lm', last_move)
    #     print('type', the_type)
    #     print('combos', combinations)
    #     print('prior_moves', prior_moves)
    #     print('moves', moves)

    if len(moves) > 0:
        # convert to actions arrays and add pass as a valid move
        return formatResultTuple(hand, moves) + [([], hand)]
    
    if the_type == SOLO:
        legal_solos = []
        for i, move in enumerate(env_arr2real_card_str(hand)):
            this_rank = int(CARD_TYPE[0][move][0][1])
            if this_rank > last_rank and move not in legal_solos:
                legal_solos.append(move)

        result = formatResultTuple(hand, legal_solos) + [([], hand)]
        
        return result
    
    if the_type == PAIR:
        legal_pairs = []
        for i, card in enumerate(hand):
            # check if pair
            if i < len(hand) - 1 and card == hand[i + 1]:
                # create move
                move = env_arr2real_card_str([card, card]) 
                this_rank = int(CARD_TYPE[0][move][0][1])
                if this_rank > last_rank and move not in legal_pairs:
                    legal_pairs.append(move)
        
        return formatResultTuple(hand, legal_pairs) + [([], hand)]
    
    # pass this turn since there aren't any legal actions
    return [([], hand)]



# Pick pair chains which results in removing more cards from hand than by playing the solo straight
# surrounding it.
def pick_non_disruptive_pair_chains(hand_list):
    solo_chains, solo_handlist = pick_chain_v2(hand_list, 1)
    pair_chains, pair_handlist = pick_chain_v2(hand_list, 2)

    if sum(pair_handlist) < sum(solo_handlist):
        return (pair_chains, pair_handlist)

    # Return original handlist if there are no good pair chains to pick
    return ([], hand_list)


def card_str2count_list(hand):
    hand_list = [0 for _ in range(15)]
    for card in hand:
        hand_list[INDEX[card]] += 1
    return hand_list


def count_list2card_str(hand_list):
    card_str = ''
    # print('v1', hand_list)
    cards = [card for card in INDEX]
    for index, count in enumerate(hand_list):
        card_str += cards[index] * count
    return card_str


def env_arr2real_card_str(ac):
    _ac = ac.copy()
    for i, c in enumerate(_ac):
        _ac[i] = EnvCard2RealCard[c]
    return ''.join(_ac)


def real_card_str2env_arr(ac):
    _ac = []
    for c in ac:
        _ac.append(RealCard2EnvCard[c])
    return _ac


def pick_chain(hand_list, count):
    chains = []
    str_card = [card for card in INDEX]
    hand_list = [str(card) for card in hand_list]
    hand = ''.join(hand_list[:12])
    chain_list = hand.split('0')
    add = 0
    for index, chain in enumerate(chain_list):
        if len(chain) > 0:
            if len(chain) >= 5:
                start = index + add
                min_count = int(min(chain)) // count
                if min_count != 0:
                    str_chain = ''
                    for num in range(len(chain)):
                        str_chain += str_card[start + num]
                        hand_list[start +
                                  num] = int(hand_list[start + num]) - int(min(chain))
                    for _ in range(min_count):
                        chains.append(str_chain)
            add += len(chain)
    hand_list = [int(card) for card in hand_list]

    return (chains, hand_list)


def pick_chain_v2(hand_list, count):
    chains = []
    str_card = [card for card in INDEX]
    hand_list = [str(card) for card in hand_list]
    hand = ''.join(hand_list[:12])

    formatted_hand = hand

    # based on count, turn all cards that break chain to 0 so we can split up chains.lower()
    # example, one Jack breaks a pair chain for 2 10's, 1 J and 2 Q's.
    if count == 2:
        formatted_hand = hand.replace('1', '0')
    elif count == 3:
        formatted_hand = hand.replace('2', '0')
    elif count == 4:
        formatted_hand = hand.replace('4', '0')

    chain_list = formatted_hand.split('0')

    add = 0
    for index, chain in enumerate(chain_list):
        if len(chain) > 0:
            # pair chain needs to be 3 long, trio needs to be 2 long
            if len(chain) >= (5 / count):
                start = index + add
                min_count = int(min(chain)) // count
                if min_count != 0:
                    str_chain = ''
                    for num in range(len(chain)):
                        # push 2 jacks to result if pair chain
                        str_chain += (str_card[start + num] * count)
                        hand_list[start +
                                  num] = int(hand_list[start + num]) - int(min(chain))
                    for _ in range(min_count):
                        chains.append(str_chain)
            add += len(chain)

    hand_list = [int(card) for card in hand_list]

    return (chains, hand_list)


def next_player(player):
    if player == 'landlord':
        return 'landlord_down'
    elif player == 'landlord_down':
        return 'landlord_up'
    else:
        return 'landlord'
