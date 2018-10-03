from __future__ import print_function
from collections import Counter, deque
import struct
import sys
import time

import pandas as pd
import numpy as np
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.externals import joblib

from common import *
from myo_raw_jonathan import MyoRaw

SUBSAMPLE = 3
K = 15



class CLassificador(object):
    
    clusters = 9
    clf = joblib.load('modeloEntrenado.pkl')
    
    def __init__(self):
        for i in range(10):
            with open('vals%d.dat' % i, 'ab') as f: pass
        #self.read_data()
        #knn = KNeighborsClassifier(n_neighbors=10)
    
    def store_data(self, vals):
        with open("setDataCompleta.csv","w") as f:
            f.write(pack('8H', *vals))
            f.close()
        #colocar Daros en los archivos
        #self.train(np.vstack([self.X, vals]), np.hstack([self.Y, [cls]]))   
    
    
    
    def entrenar(self):
        archivo = "setDataCompleta.csv"
        df = pd.read_csv(archivo)
        
        arregloX = df[df.columns[:-1]].values
        arregloy = df[df.columns[-1]].values  #as_matrix()
        
        X_train,X_test,y_train,y_test = train_test_split(arregloX, arregloy)
        clf = KNeighborsClassifier(self.clusters)
        clf.fit(X_train, y_train)      
        
        

    def classify(self, d):
        return self.clf.predict([d])
    

class Myo(MyoRaw):
    hist_len = 35

    def __init__(self, cls, tty=None):
        MyoRaw.__init__(self, tty)
        self.cls = cls

        self.history = deque([0] * Myo.hist_len, Myo.hist_len)
        self.history_cnt = Counter(self.history)
        self.add_emg_handler(self.emg_handler)
        self.last_pose = None

        self.pose_handlers = []

    def emg_handler(self, emg, moving):
        y = self.cls.classify(emg)
        #Quita un dato 
        self.history_cnt[self.history[0]] -= 1
        #Coloca el siguiente
        #y[] = dato entero que importa
        self.history_cnt[y[0]] += 1    
        self.history.append(y[0])
        #Tamaño del array siempre sera 25
        
        ##Desempaqueta el mas comun en el historial
        r, n = self.history_cnt.most_common(1)[0]
        
        if self.last_pose is None or (n > self.history_cnt[self.last_pose] + 5 and n > Myo.hist_len / 2):
            self.on_raw_pose(r)
            self.last_pose = r
        
    

    def add_raw_pose_handler(self, h):
        self.pose_handlers.append(h)

    def on_raw_pose(self, pose):
        for h in self.pose_handlers:
            h(pose)


if __name__ == '__main__':
    import subprocess
    m = Myo(CLassificador(), sys.argv[1] if len(sys.argv) >= 2 else None)
    m.add_raw_pose_handler(print)
  
   

    
    m.connect()

    try:
        while True:
            m.run()
        
    except KeyboardInterrupt:
        pass
        
    finally:
        m.disconnect()
        print()