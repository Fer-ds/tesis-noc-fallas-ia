#!/usr/bin/env python
"""Sprint 9 - Error slicing reproducible.
Uso esperado dentro del repo: python src/run_sprint9_error_slicing.py
"""
import pathlib
import numpy as np
import pandas as pd
import joblib
from sklearn.base import clone
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, average_precision_score, brier_score_loss
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_CANDIDATES = [ROOT/'data'/'processed'/'incidents_noc_tx_ip_hpo_sprint7.csv', ROOT/'data'/'processed'/'incidents_noc_tx_ip_clean_sprint7.csv']
MODEL_CANDIDATES = [ROOT/'artifacts'/'sprint8_demo_model.joblib', ROOT/'artifacts'/'best_hpo_model_sprint7.joblib']
OUT = ROOT/'results'; OUT.mkdir(exist_ok=True)
THRESHOLD = 0.2303932323558283
MIN_N = 60; MIN_POS = 10

def find_existing(paths):
    for p in paths:
        if p.exists(): return p
    raise FileNotFoundError('No se encontró archivo esperado: ' + ', '.join(map(str, paths)))

def point_metrics(g):
    y = g['y_true'].values.astype(int); p = g['y_pred'].values.astype(int); prob = g['y_prob'].values
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0,1]).ravel()
    return {'n':len(g),'positives':int(y.sum()),'positive_rate':float(y.mean()),'pred_pos':int(p.sum()),'pred_rate':float(p.mean()),'tp':int(tp),'fp':int(fp),'fn':int(fn),'tn':int(tn),'precision':precision_score(y,p,zero_division=0),'recall':recall_score(y,p,zero_division=0),'f1':f1_score(y,p,zero_division=0),'ap':average_precision_score(y,prob) if len(np.unique(y))>1 else np.nan,'brier':brier_score_loss(y,prob),'fp_rate_neg':fp/(fp+tn) if (fp+tn)>0 else np.nan,'fn_rate_pos':fn/(fn+tp) if (fn+tp)>0 else np.nan}

def prf_from_counts(tp,fp,fn):
    precision = tp/(tp+fp) if tp+fp>0 else 0.0
    recall = tp/(tp+fn) if tp+fn>0 else 0.0
    f1 = 2*precision*recall/(precision+recall) if precision+recall>0 else 0.0
    return precision, recall, f1

def bootstrap_ci(g, B=800, seed=123):
    rng=np.random.default_rng(seed); y=g['y_true'].values.astype(int); p=g['y_pred'].values.astype(int); idx=np.arange(len(g)); vals=np.empty((B,3))
    for b in range(B):
        s=rng.choice(idx,size=len(idx),replace=True); yy=y[s]; pp=p[s]
        tp=int(((yy==1)&(pp==1)).sum()); fp=int(((yy==0)&(pp==1)).sum()); fn=int(((yy==1)&(pp==0)).sum())
        vals[b]=prf_from_counts(tp,fp,fn)
    ci=np.nanpercentile(vals,[2.5,97.5],axis=0)
    return {'precision_ci_low':ci[0,0],'precision_ci_high':ci[1,0],'recall_ci_low':ci[0,1],'recall_ci_high':ci[1,1],'f1_ci_low':ci[0,2],'f1_ci_high':ci[1,2]}

def main():
    data_path=find_existing(DATA_CANDIDATES); model_path=find_existing(MODEL_CANDIDATES)
    df=pd.read_csv(data_path); df['date_start']=pd.to_datetime(df['date_start']); df=df.sort_values('date_start').reset_index(drop=True)
    base_model=joblib.load(model_path); X=df[list(base_model.feature_names_in_)]; y=df['label_over_ola'].astype(int).values
    oof=[]
    for fold,(tr,va) in enumerate(TimeSeriesSplit(n_splits=3).split(X),1):
        model=clone(base_model); model.fit(X.iloc[tr],y[tr]); prob=model.predict_proba(X.iloc[va])[:,1]; pred=(prob>=THRESHOLD).astype(int)
        part=df.iloc[va].copy(); part['fold']=fold; part['y_true']=y[va]; part['y_prob']=prob; part['y_pred']=pred; oof.append(part)
    pred_df=pd.concat(oof,ignore_index=True); pred_df['month']=pred_df['date_start'].dt.month
    pred_df['hour_bin']=pd.cut(pred_df['hour'],bins=[-1,5,11,17,23],labels=['00-05','06-11','12-17','18-23'])
    pred_df['duration_missing']=np.where(pred_df['duration_hours_evidence'].isna(),'duration_missing','duration_present')
    slice_cols=['priority','type_of_incident','trouble_type','incident_type','network_type','branch_id','reason_group','year','quarter','month','week_of_year','day_of_week','hour_bin','is_weekend','is_night','duration_missing']
    rows=[]
    for col in slice_cols:
        for val,g in pred_df.groupby(col,dropna=False):
            if len(g)<MIN_N or g['y_true'].sum()<MIN_POS: continue
            rows.append({'slice_var':col,'slice_value':str(val),**point_metrics(g)})
    all_slices=pd.DataFrame(rows); global_metrics=point_metrics(pred_df); all_slices['delta_f1_global']=all_slices['f1']-global_metrics['f1']
    all_slices.to_csv(OUT/'slice_metrics_all_candidates_sprint9.csv', index=False)
    selected=[('GLOBAL','OOF TimeSeriesSplit n_splits=3'),('incident_type','CABLE BROKEN ACCESS'),('network_type','AGG-SRT'),('branch_id','BRANCH_034'),('reason_group','MISSING'),('month','6')]
    selected_rows=[]
    for var,val in selected:
        g=pred_df.copy() if var=='GLOBAL' else pred_df[pred_df[var].astype(str)==str(val)].copy()
        selected_rows.append({'slice_var':var,'slice_value':val,**point_metrics(g),**bootstrap_ci(g)})
    selected_df=pd.DataFrame(selected_rows)
    for col in ['f1','precision','recall','ap','brier']:
        selected_df[f'delta_{col}_global']=selected_df[col]-selected_df.loc[0,col]
    selected_df.to_csv(OUT/'slice_metrics_problematic_sprint9.csv', index=False)
    print('OK - resultados en results/slice_metrics_*_sprint9.csv')
if __name__ == '__main__':
    main()
