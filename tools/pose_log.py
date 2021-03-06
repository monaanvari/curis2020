"""Logging object poses.
"""

import random
import string
import mlflow

from robovat.math import Pose 
from robovat.simulation.body import Body


def random_string(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

class logger:

    def __init__(self):
        self.experiment_name = random_string()
        self.experiment_id = mlflow.create_experiment(self.experiment_name) 
        self.uri = mlflow.tracking.get_tracking_uri()
    

    def start(self):
        mlflow.start_run(experiment_id=self.experiment_id)
        #mlflow.set_tracking_uri()
        #run = mlflow.tracking.MlflowClient.create_run(experiment_id)
        #run_id = run.info.run_id

    def end(self):
        mlflow.end_run()


    def log(self,info, objs, action):
        #experiment = mlflow.get_experiment_by_name('random')
        #experiment_id = experiment.experiment_id
        print('\n\n action:')
        print(action)

        mlflow.log_metric("start_X" , action[0][0], step = info)
        mlflow.log_metric("start_Y" , action[0][1], step = info)
        mlflow.log_metric("motion_X" , action[0][2], step = info)
        mlflow.log_metric("motion_Y" , action[0][3], step = info)
        for body in objs:

            mlflow.log_metric(body.name+"_X" , body.pose.x, step = info)
            mlflow.log_metric(body.name+"_Y" , body.pose.y, step = info)
            mlflow.log_metric(body.name+"_Z" , body.pose.z, step = info)
            mlflow.log_metric(body.name+"_roll" , body.pose.euler[0], step = info)
            mlflow.log_metric(body.name+"_pitch" , body.pose.euler[1], step = info)
            mlflow.log_metric(body.name+"_yaw" , body.pose.euler[2], step = info)





