
from game import DominosGame
from domino import Domino
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Activation
from copy import copy
from collections import deque

'''
    QLearning
'''

class Agent:

    def __init__(self):
        self.MAX_POSS_MOVES = 60
        self.ACTION_SPACE = 30
        self.NUM_DOMINOS = 28
        self.NUM_LAYERS = 5
        self.NUM_OUTPUT_UNITS = 1  # arbitrary
        self.STATE_SPACE = self.ACTION_SPACE*self.MAX_POSS_MOVES+self.NUM_DOMINOS
        self.GAMMA = 0.9
        self.NUM_ITERS = 10
        self.NUM_EPOCHS = 20

        model = Sequential()
        self.model = model
        state_action_space = self.STATE_SPACE + self.ACTION_SPACE
        print('stateactionspace', state_action_space)
        model.add(Dense(units=self.NUM_OUTPUT_UNITS, input_dim=state_action_space, activation='relu'))  # units is arbitrary
        for i in range(self.NUM_LAYERS): 
            model.add(Dense(units=self.NUM_OUTPUT_UNITS, activation='relu'))  
        model.add(Activation('linear')) # add additional layer for neg values
        model.compile(loss='mse',
                  optimizer='adam')
        self.model = model
        self.domino_dict = {}

        all_dominoes = [ Domino(a, b) for a in range(7) for b in range(a, 7)]
        for i, domino in enumerate(all_dominoes):
            self.domino_dict[domino] = i

        self.memory = deque(maxlen=10000)


    '''
        Model represents Q values of [s_hot,a_hot] inputs
        Build training inputs X as list of np array [s_hot, a_hot] tuples and 
        fit to output Y with updated q values (gamma * Q(sp,ap))
    '''

    def train(self, batch_size=120):
        X = []
        Y = []
        perspective_player = 0 # perspective of player 0 
        memory = copy(self.memory) # copy if you want multiple iterations
        sa = None # [s_hot,a_hot]
        r = None
        spap = None # [sp_hot, ap_hot]
        count = 0
        while memory: # scan memory sequentially
            count+=1
            board_state, best_a, is_end_state, scores, curr_hand, curr_player = memory.pop()
            if curr_player == perspective_player:  # considers actions of perspective player
                print('memory count', count)
                if sa is None:  # first time
                    sa = np.r_[self.state_to_one_hot(board_state, curr_hand), self.action_to_one_hot(best_a)]
                    print('perspective player', perspective_player)

                    r = scores[perspective_player] if len(scores) != 0 else 0
                else:
                    spap = np.r_[self.state_to_one_hot(board_state, curr_hand), self.action_to_one_hot(best_a)].reshape(-1,1).T 
                    X.append(sa)
                    if is_end_state:    # only use r
                        Y.append(r)
                    else:   # take q into account
                        q = self.model.predict(spap)
                        Y.append(r+self.GAMMA*q)
                    sa = spap

                    r = scores[perspective_player] if len(scores) != 0 else 0
        print('length of input X', len(X))
        for i,x in enumerate(X):    
            self.model.fit(np.array(x).reshape(-1,1).T,np.array(Y[i]).reshape(-1,1).T,batch_size, epochs=self.NUM_EPOCHS)
       

    def state_to_one_hot(self, board_state, hand):
        state = np.zeros(self.STATE_SPACE)
        for move_idx, domino in enumerate(board_state):
            if domino is None:
                state[move_idx*self.ACTION_SPACE + self.NUM_DOMINOS] = 1
            else:
                l = [key for key in self.domino_dict]
             
                domino_idx = self.domino_dict[domino[0]]
                state[move_idx*self.ACTION_SPACE + domino_idx] = 1
                state[move_idx*self.ACTION_SPACE + self.ACTION_SPACE-1] = domino[1]

        # hand = game.get_player_hand()
        for domino in hand:
            state[self.ACTION_SPACE*self.MAX_POSS_MOVES + self.domino_dict[domino]] = 1

        return state


    def action_to_one_hot(self, action):
        action_v = np.zeros(self.ACTION_SPACE)
        if action is not None:
            domino, side = action
            l = [key for key in self.domino_dict]
            
            domino_idx = self.domino_dict[domino]
          
            action_v[domino_idx] = 1
            action_v[-1] = side
        return action_v

    def selfplay(self, num_games):
        print('range games', range(num_games))
        for i in range(num_games): # play multiple games
            print("Game "+str(i))
            game = DominosGame()
            is_end_state = game.is_end_state()
            while(not is_end_state):    # play game
                poss_actions = game.get_possible_actions()
                curr_player = game.curr_player
                curr_player_hand = game.get_player_hand(curr_player)
                best_a = None
                best_a_score = float('-inf')
                if poss_actions[0] is not None:
                    s_hot = self.state_to_one_hot(game.board, curr_player_hand)
                    for action in poss_actions:
                        a_hot = self.action_to_one_hot(action)
                        curr_score = self.model.predict(np.r_[s_hot, a_hot].reshape(-1,1).T)
                        if curr_score > best_a_score:
                            best_a_score = curr_score
                            best_a = action
                # take best_a and get reward
                game.move(best_a)
                is_end_state = game.is_end_state()
                scores = []
                if is_end_state:
                    for player_idx in range(4):
                        scores.append(game.get_score(player_idx))
                    
                # s', a, is_end, scores, hand, curr_player
                sa = (copy(game.board), best_a, is_end_state, scores, curr_player_hand, curr_player)
                self.memory.append(sa)
       
    






        

