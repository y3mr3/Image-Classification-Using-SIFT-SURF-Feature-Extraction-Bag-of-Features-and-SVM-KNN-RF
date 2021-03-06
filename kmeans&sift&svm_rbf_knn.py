# -*- coding: utf-8 -*-
"""Kmeans&sift&SVM_Rbf_Knn.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1EHyQShT_QaJJF3x8R0QqZLCFAlezMkop
"""

!apt-get install -y -qq software-properties-common python-software-properties module-init-tools
!add-apt-repository -y ppa:alessandro-strada/ppa 2>&1 > /dev/null
!apt-get update -qq 2>&1 > /dev/null
!apt-get -y install -qq google-drive-ocamlfuse fuse
from google.colab import auth
auth.authenticate_user()
from oauth2client.client import GoogleCredentials
creds = GoogleCredentials.get_application_default()
import getpass
!google-drive-ocamlfuse -headless -id={creds.client_id} -secret={creds.client_secret} < /dev/null 2>&1 | grep URL
vcode = getpass.getpass()
!echo {vcode} | google-drive-ocamlfuse -headless -id={creds.client_id} -secret={creds.client_secret}

!mkdir -p drive
!google-drive-ocamlfuse drive

"""OpenCV Kurulumu"""

!pip install opencv-python==3.4.2.16
!pip install opencv-contrib-python==3.4.2.16

import numpy as np
from sklearn import svm
from sklearn.metrics import accuracy_score
import cv2
import cv2 as cv
from sklearn.externals import joblib

"""**Tüm Datanın Adresini tutan(filename) ve etiketlerini tutan(label) bir DataFrame(data) yapısı oluşturuluyor.**"""

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
import os
filename = os.listdir('/content/drive/ICIAR2018/Data/Benign')
label= [1 for i in filename]
filename=['/content/drive/ICIAR2018/Data/Benign/'+i for i in filename]
data1=pd.DataFrame(list(zip(filename,label)), columns=['filename','label'])

filename = os.listdir('/content/drive/ICIAR2018/Data/Normal')
label= [0 for i in filename]
filename=['/content/drive/ICIAR2018/Data/Normal/'+i for i in filename]
data0=pd.DataFrame(list(zip(filename,label)), columns=['filename','label'])

filename = os.listdir('/content/drive/ICIAR2018/Data/InSitu')
label= [2 for i in filename]
filename=['/content/drive/ICIAR2018/Data/InSitu/'+i for i in filename]
data2=pd.DataFrame(list(zip(filename,label)), columns=['filename','label'])

filename = os.listdir('/content/drive/ICIAR2018/Data/Invasive')
label= [3 for i in filename]
filename=['/content/drive/ICIAR2018/Data/Invasive/'+i for i in filename]
data3=pd.DataFrame(list(zip(filename,label)), columns=['filename','label'])

import pandas as pd
data=pd.concat([data0,data1,data2,data3],ignore_index=True)

"""**Data Setini Random Olarak Train-Test olarak Ayrılıyor(Data boyutunu burdan Değiştirebilirsiniz)**"""

#Data Split train %75 test %25
train_set = data.sample(frac=0.75, random_state=0)
test_set = data.drop(train_set.index)

#Data Split train %80 test %20
#train_set = data.sample(frac=0.80, random_state=0)
#test_set = data.drop(train_set.index)

train_set

"""**Bu Fonksiyon Train Data Setine SIFT Uygularak Elde Edilen Keypoint ve Descriptorleri K-means'le Kümeleyerek Model Databesini Oluşturur.**"""

def read_and_clusterize(train_set, num_cluster):
    
    sift_keypoints = []

    for index, row in train_set.iterrows():
      
      image = cv2.imread(row.filename,1)
      image =cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
      sift = cv2.xfeatures2d.SIFT_create()
      kp, descriptors = sift.detectAndCompute(image,None)
      sift_keypoints.append(descriptors)
    sift_keypoints=np.asarray(sift_keypoints)
    sift_keypoints=np.concatenate(sift_keypoints, axis=0)
    #with the descriptors detected, lets clusterize them
    print("Training kmeans")    
    kmeans k_labels, k_center= MiniBatchKMeans(n_clusters=num_cluster, random_state=0).fit(sift_keypoints)
    #return the learned model
    return kmeans, k_labels, k_center

def save_model(filename):
  path='/content/drive/ICIAR2018/'+filename
  joblib.dump(model, path)
  print("Model Succesfully Saved")

def load_model(filename):
  path='/content/drive/ICIAR2018/'+filename
  return joblib.load(path)

"""**Bu Fonksiyonda Görüntülerin Kmeans ile Histogramı Çıkarılıp Histogramdan Feature Vektörler Elde Edilirken Etiket Atamasıda Burda Yapılır.**"""

def calculate_centroids_histogram(df, model,num_clusters):

    feature_vectors=[]
    class_vectors=[]
    for index,row in df.iterrows():
        #read image
        image = cv2.imread(row.filename,1)
        #Convert them to grayscale
        image =cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        #SIFT extraction
        sift = cv2.xfeatures2d.SIFT_create()
        kp, descriptors = sift.detectAndCompute(image,None)
        #classification of all descriptors in the model
        predict_kmeans=model.predict(descriptors)
        #calculates the histogram
        hist, bin_edges=np.histogram(predict_kmeans, bins=num_clusters)
        #hist, bin_edges=np.histogram(predict_kmeans)
        #histogram is the feature vector
        feature_vectors.append(hist)
        #class_sample=define_class(row.label)
        class_sample=row.label
        class_vectors.append(class_sample)

    feature_vectors=np.asarray(feature_vectors)
    class_vectors=np.asarray(class_vectors)
    #return vectors and classes we want to classify
    return class_vectors, feature_vectors

model=read_and_clusterize(train_set,200)

save_model('clusterize_model_n_clusters_200_sift_1')

"""**Train Data Setinin Feature Vektörleri Oluşturup Etiketleniyor.**"""

print("Step 2: Extracting histograms of training and testing images")
print("Training")
[train_class,train_featvec]=calculate_centroids_histogram(train_set,model,1000)

"""**Test Data Setinin Feature Vektörleri Oluşturup Etiketleniyor.**"""

print("Testing")
[test_class,test_featvec]=calculate_centroids_histogram(test_set,model,1000)

"""SVM'i  Train Feature Vektör ile Eğitip Test Feature Vektörünün Tahminlenmesi(predict) Yapılmıştır ;

SVM İçin Accuracy-F1Score-Precision-Recal-Kappa Score Confussion Matrix Hesaplanması Yapılmıştır
"""

#find optimal gamma-C-kernel for svm
from sklearn.model_selection import GridSearchCV
svcClassifier = svm.SVC(kernel='rbf', probability=True, C=10, gamma=10)
param_grid = { 
    'C': [0.01,0.1,1, 10, 50],
    'gamma': [0.1, 0.5, 1.0,0.01],
    'kernel':['rbf','linear']
}
CV_rfc = GridSearchCV(estimator=svcClassifier, param_grid=param_grid, cv= 5)
CV_rfc.fit(train_featvec, train_class)
print (CV_rfc.best_params_)

print("Step 4: Testing the SVM classifier")  
predict=CV_rfc.predict(test_featvec)

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report, confusion_matrix

test_set.label.to_numpy()

predict

#accuracy
score=accuracy_score(np.asarray(test_class), predict)
print("Accuracy:" +str(score))

#Confussion Matrix
from sklearn.metrics import confusion_matrix
confusion_matrix(test_set.label.to_numpy(), predict)

#kappa_score
from sklearn.metrics import cohen_kappa_score
cohen_kappa_score(test_set.label.to_numpy(), predict)

#fscore
from sklearn.metrics import precision_recall_fscore_support
precision_recall_fscore_support(test_set.label.to_numpy(), predict, average='macro')#precision
precision_recall_fscore_support(test_set.label.to_numpy(), predict, average='micro')#recall
precision_recall_fscore_support(test_set.label.to_numpy(), predict, average='weighted')#fscore

"""KNN'i Train Feature Vektör ile Eğitip Test Feature Vektörünün Tahminlenmesi(predict) Yapılmıştır ;

KNN İçin Accuracy-F1Score-Precision-Recal-Kappa Score Confussion Matrix Hesaplanması Yapılmıştır
"""

from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score
# Creating odd list K for KNN
neighbors = list(range(2,50,2))
# empty list that will hold cv scores
K=0
cv_scores = [ ]
#perform 10-fold cross-validation
for K in neighbors:
    knn = KNeighborsClassifier(n_neighbors = K)
    scores = cross_val_score(knn,train_featvec,train_class,cv = 10,scoring =
    "accuracy")
    cv_scores.append(scores.mean())

# Changing to mis classification error
mse = [1-x for x in cv_scores]
# determing best k
optimal_k = neighbors[mse.index(min(mse))]
print("The optimal no. of neighbors is {}".format(optimal_k))

"""KNN için The optimal no. of neighbors is 4"""

import matplotlib.pyplot as plt
def plot_accuracy(knn_list_scores):
    pd.DataFrame({"K":[i for i in range(2,50,2)], "Accuracy":knn_list_scores}).set_index("K").plot.bar(figsize= (9,6),ylim=(0.40,0.83),rot=0)
    plt.show()
plot_accuracy(cv_scores)

from sklearn.neighbors import KNeighborsClassifier

model = KNeighborsClassifier(n_neighbors=4)

# Train the model using the training sets
model.fit(train_featvec,train_class)

predicted= model.predict(test_featvec)

#accuracy
score=accuracy_score(np.asarray(test_class), predicted)
print("Accuracy:" +str(score))

#kappa_score
from sklearn.metrics import cohen_kappa_score
cohen_kappa_score(test_set.label.to_numpy(), predicted)

#Confussion Matrix
from sklearn.metrics import confusion_matrix
confusion_matrix(test_set.label.to_numpy(), predicted)

#fscore
from sklearn.metrics import precision_recall_fscore_support
precision_recall_fscore_support(test_set.label.to_numpy(), predicted, average='macro')#precision
precision_recall_fscore_support(test_set.label.to_numpy(), predicted, average='micro')#recall
precision_recall_fscore_support(test_set.label.to_numpy(), predicted, average='weighted')#fscore

"""Random Forest Train Feature Vektör ile Eğitip Test Feature Vektörünün Tahminlenmesi(predict) Yapılmıştır ;

Random Forest İçin Accuracy-F1Score-Precision-Recal-Kappa Score Confussion Matrix Hesaplanması Yapılmıştır
"""

from sklearn import model_selection# random forest model creation
rfc = RandomForestClassifier(n_jobs=4, random_state=0)
rfc.fit(train_featvec,train_class)# predictions
rfc_predict = rfc.predict(test_featvec)

rfc_predict

#accuracy
score=accuracy_score(np.asarray(test_class), rfc_predict)
print("Accuracy:" +str(score))

#kappa_score
from sklearn.metrics import cohen_kappa_score
cohen_kappa_score(test_set.label.to_numpy(), rfc_predict)

#Confussion Matrix
from sklearn.metrics import confusion_matrix
confusion_matrix(test_set.label.to_numpy(), rfc_predict)

#fscore
from sklearn.metrics import precision_recall_fscore_support
precision_recall_fscore_support(test_set.label.to_numpy(), rfc_predict, average='macro')#precision
precision_recall_fscore_support(test_set.label.to_numpy(), rfc_predict, average='micro')#recall
precision_recall_fscore_support(test_set.label.to_numpy(), rfc_predict, average='weighted')#fscore