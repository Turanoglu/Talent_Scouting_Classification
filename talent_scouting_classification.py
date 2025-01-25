import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

from pandas.core.common import random_state
#from sklearn.exceptions import ConvergenceWarning
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import GridSearchCV, cross_validate, RandomizedSearchCV, validation_curve
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import MinMaxScaler, LabelEncoder, StandardScaler, RobustScaler

warnings.simplefilter(action='ignore', category=FutureWarning)
#warnings.simplefilter("ignore", category=ConvergenceWarning)

pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.float_format', lambda x: '%.3f' % x)



df1 = pd.read_csv("scoutium_attributes.csv", delimiter=";")
df2 = pd.read_csv("scoutium_potential_labels.csv", delimiter=";")

df = pd.merge(df1,df2, on=['task_response_id',"match_id","evaluator_id","player_id"])

df.head()

def check_df(dataframe):
    print("##################### Shape #####################")
    print(dataframe.shape)
    print("##################### Types #####################")
    print(dataframe.dtypes)
    print("##################### Head #####################")
    print(dataframe.head(3))
    print("##################### Tail #####################")
    print(dataframe.tail(3))
    print("##################### NA #####################")
    print(dataframe.isnull().sum())
    print("##################### Quantiles #####################")
    print(dataframe.quantile([0, 0.05, 0.50, 0.95, 0.99, 1], numeric_only=True))


check_df(df)


df = df[df["position_id"] != 1]

df["position_id"].value_counts()

df["potential_label"].value_counts() / len(df) # below_average tüm verisetinden sadece %1'lik bir alana sahip olduğu için kaldırıyoruz.

df = df[~(df["potential_label"].isin(["below_average"]))]
df["potential_label"].unique()

# Adım 5: Oluşturduğunuz veri setinden “pivot_table” fonksiyonunu
# kullanarak bir tablo oluşturunuz. Bu pivot table'da her satırda bir oyuncu
# olacak şekilde manipülasyon yapınız.
# Adım 5.1: İndekste “player_id”,“position_id” ve “potential_label”,
# sütunlarda “attribute_id” ve değerlerde scout’ların oyunculara verdiği puan
# “attribute_value” olacak şekilde pivot table’ı oluşturunuz.
# Adım 2: “reset_index” fonksiyonunu kullanarak indeksleri değişken olarak
# atayınız ve “attribute_id” sütunlarının isimlerini stringe çeviriniz.

df_table = df.pivot_table(index=["player_id", "position_id", "potential_label"], columns="attribute_id", values="attribute_value")

df_table = df_table.reset_index()

df_table.columns = df_table.columns.map(str)

df_table.head() # artık her satırda bir oyuncu olacak şekilde düzenledik tablomuzu.


def get_col_names(dataframe, cat_th=10, car_th=20):

    cat_cols = [col for col in dataframe.columns if dataframe[col].dtypes == "O"]

    num_but_cat = [col for col in dataframe.columns if dataframe[col].nunique() < cat_th and
                   dataframe[col].dtypes != "O"]

    cat_but_car = [col for col in dataframe.columns if dataframe[col].nunique() > car_th and
                   dataframe[col].dtypes == "O"]

    cat_cols = cat_cols + num_but_cat
    cat_cols = [col for col in cat_cols if col not in cat_but_car]

    num_cols = [col for col in dataframe.columns if dataframe[col].dtypes != "O"]
    num_cols = [col for col in num_cols if col not in num_but_cat]

    print(f"Observations: {dataframe.shape[0]}")
    print(f"Variables: {dataframe.shape[1]}")
    print(f'cat_cols: {len(cat_cols)}')
    print(f'num_cols: {len(num_cols)}')
    print(f'cat_but_car: {len(cat_but_car)}')
    print(f'num_but_cat: {len(num_but_cat)}')

    # cat_cols + num_cols + cat_but_car = değişken sayısı.
    # num_but_cat cat_cols'un içerisinde zaten.
    # Yani tüm şu 3 liste ile tüm değişkenler seçilmiş olacaktır: cat_cols + num_cols + cat_but_car
    

    return cat_cols, cat_but_car, num_cols

cat_cols, cat_but_car, num_cols = get_col_names(df_table)

num_cols = [col for col in num_cols if col not in "player_id"]
num_cols

def label_encod(dataframe, binary_col):
    label_encod = LabelEncoder()
    dataframe[binary_col] = label_encod.fit_transform(dataframe[binary_col])
    return dataframe

binary_cols = [col for col in df_table.columns if col in "potential_label"]

for col in binary_cols:
    label_encod(df_table,col)

df_table["potential_label"].value_counts()

num_cols
df_table.columns
scaler = StandardScaler()
df_table[num_cols] = scaler.fit_transform(df_table[num_cols])
df_table[num_cols].head()

df_table.head()

# Elimizdeki veri seti üzerinden minimum hata ile futbolcuların
# potansiyel etiketlerini tahmin eden bir makine öğrenmesi modeli
# geliştirelim. (Roc_auc, f1, precision, recall, accuracy)
# Değişkenlerin önem düzeyini belirten feature_importance
# fonksiyonunu kullanarak özelliklerin sıralamasını çizdirelim.

y = df_table["potential_label"]

X = df_table.drop(["player_id","position_id","potential_label"],axis=1)

# Random Forest---------------
rf_model = RandomForestClassifier(random_state=17)
rf_model.get_params()

cv_results = cross_validate(rf_model, X, y, cv=10, scoring=["accuracy","f1","roc_auc"])
print(cv_results["test_accuracy"].mean())
print(cv_results["test_f1"].mean())
print(cv_results["test_roc_auc"].mean())

rf_params = {
    "max_depth" : [5,8,None],
    "max_features" : ["sqrt","log2","None"],
    "min_samples_split" : [2,5,8,15,20],
    "n_estimators" : [100,200,300,400,500,800]
}

rf_best_grid = GridSearchCV(rf_model,rf_params,cv=5,n_jobs=-1,verbose=True).fit(X,y)
rf_best_grid.best_params_


rf_final = rf_model.set_params(**rf_best_grid.best_params_, random_state=17).fit(X,y)

cv_results = cross_validate(rf_final, X, y, cv=10, scoring=["accuracy","f1","roc_auc"])
print("İşlem tamamlandı")
print(cv_results["test_accuracy"].mean())
print(cv_results["test_f1"].mean())
print(cv_results["test_roc_auc"].mean())

# Gradien Boosting Machine (GBM)-----

gbm_model = GradientBoostingClassifier(random_state=17)
gbm_model.get_params()

cv_results = cross_validate(gbm_model, X, y, cv=5, scoring=["accuracy","f1","roc_auc"])
print(cv_results["test_accuracy"].mean())
print(cv_results["test_f1"].mean())
print(cv_results["test_roc_auc"].mean())

gbm_params = {"learning_rate": [0.01, 0.1],
              "max_depth": [3, 8, 10],
              "n_estimators": [100, 500, 1000],
              "subsample": [1, 0.5, 0.7]}

gbm_best_grid = GridSearchCV(gbm_model,gbm_params,cv=5,n_jobs=-1,verbose=True).fit(X,y)

gbm_best_grid.best_params_

gbm_final = gbm_model.set_params(**gbm_best_grid.best_params_, random_state=17).fit(X,y)

cv_results = cross_validate(gbm_final, X, y, cv=5, scoring=["accuracy","f1","roc_auc"])
print("İşlem tamamlandı")
print(cv_results["test_accuracy"].mean())
print(cv_results["test_f1"].mean())
print(cv_results["test_roc_auc"].mean())


def plot_importance(model, features, num=len(X), save=False):
    feature_imp = pd.DataFrame({'Value': model.feature_importances_, 'Feature': features.columns})
    plt.figure(figsize=(10, 10))
    sns.set(font_scale=1)
    sns.barplot(x="Value", y="Feature", data=feature_imp.sort_values(by="Value",
                                                                     ascending=False)[0:num])
    plt.title('Features')
    plt.tight_layout()
    plt.show(block=True)
    if save:
        plt.savefig('importances.png')



plot_importance(rf_final, X)
plot_importance(gbm_final, X)






















