#!/usr/bin/env python

"""
Worker class for the Actor Critic

Modified code from GitHub stefanbo92/A3C-Continuous
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import mlflow
import socket
import time
import traceback

#import tools.curious_agent

from robovat.simulation.body import Body
from robovat.utils import time_utils
from robovat.utils.logging import logger
from pose_log import logger as Plogger
from pose_estimation import find_forward_error as forward_r

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from robovat import envs
from robovat import policies
#from tools.pose_log import log_pose
import A3C_network
import run_A3C
import A3C_config as config


MAX_GLOBAL_EP = 2000        # total number of episodes

# worker class that inits own environment, trains on it and updloads weights to global net
class Worker(object):
    def __init__(self, name, globalAC, sess, env):            
        self.env = env._reset()  # make environment for each worker
        self.name = name
        self.AC = A3C_network.ACNet(name, sess, env, globalAC) # create ACNet for each worker
        self.sess=sess
        #self.coord = coord


    def work(self, *tup):
        (coord, number) = tup
        total_step = 1
        buffer_s, buffer_a, buffer_r = [], [], []
        while not coord.should_stop() and config.global_episodes < MAX_GLOBAL_EP:
            print('\n\n\n %s \n\n\n', self.name)
            s = self.env._reset()

            #self.env._reset_scene()
            ep_r = 0
            for ep_t in range(MAX_EP_STEP):

                bodies_i = env.movable_bodies() 

                if self.name == 'W_0':
                    pose_logger = Plogger()
                    pose_logger.end()
                    pose_logger.start()
                    #self.env.render()
                a = self.AC.choose_action(s)         # estimate stochastic action based on policy 
                s_, r, done, info = self.env.step(a) # make step in environment
                bodies_f = env.movable_bodies() 

                r += forward_r('mlruns', bodies_i, bodies_f, a)
                #TODO:learn how to normalize the clearing reward
                r = r/2

                pose_logger.log(info, env.movable_bodies, a)
                #logger.info(
                #'Episode %d finished in %.2f sec. '
                #'In average each episode takes %.2f sec',
                #episode_index, toc - tic, total_time / (episode_index + 1))
                done = True if ep_t == MAX_EP_STEP - 1 else False

                ep_r += r
                logger.info('Worker %s Episode reward: %f', self.name[-1], ep_r) 
                # save actions, states and rewards in buffer
                buffer_s.append(s)          
                buffer_a.append(a)
                buffer_r.append(r) 
                #buffer_r.append((r+8)/8)    # normalize reward
                #TODO:figure out reward and change this

                if total_step % UPDATE_GLOBAL_ITER == 0 or done:   # update global and assign to local net
                    if done:
                        pose_logger.end()
                        v_s_ = 0   # terminal
                    else:
                        v_s_ = self.sess.run(self.AC.v, {self.AC.s: s_[np.newaxis, :]})[0, 0]
                    buffer_v_target = []
                    for r in buffer_r[::-1]:    # reverse buffer r
                        v_s_ = r + GAMMA * v_s_
                        buffer_v_target.append(v_s_)
                    buffer_v_target.reverse()

                    buffer_s, buffer_a, buffer_v_target = np.vstack(buffer_s), np.vstack(buffer_a), np.vstack(buffer_v_target)
                    feed_dict = {
                        self.AC.s: buffer_s,
                        self.AC.a_his: buffer_a,
                        self.AC.v_target: buffer_v_target,
                    }
                    self.AC.update_global(feed_dict) # actual training step, update global ACNet
                    buffer_s, buffer_a, buffer_r = [], [], []
                    self.AC.pull_global() # get global parameters to local ACNet

                s = s_
                total_step += 1
                if done:
                    if len(config.global_rewards) < 5:  # record running episode reward
                        config.global_rewards.append(ep_r)
                    else:
                        config.global_rewards.append(ep_r)
                        config.global_rewards[-1] =(np.mean(config.global_rewards[-5:])) # smoothing 
                    print(
                        self.name,
                        "Ep:", global_episodes,
                        "| Ep_r: %i" % config.global_rewards[-1],
                          )
                    global_episodes += 1
                    break



#TODO:!
