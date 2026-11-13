import math
import numpy as np

def score(values,segments,threshold=3.5,noise_floor=.02,weights=None,weighting="equal"):
 if weighting not in ["equal","output"]:raise ValueError("加权方式应为equal或output")
 if weighting=="output":
  if weights is None:raise ValueError("按产量加权评分需要每条观测的产量")
  w=np.asarray(weights,dtype=float)
  if w.shape!=(len(values),) or not np.isfinite(w).all() or not (w>0).all():raise ValueError("产量权重必须为与观测一一对应的正有限值")
  if not np.isfinite(w.sum()) or w.sum()<=0:raise ValueError("产量权重合计无效")
 else:w=np.ones(len(values))
 if not math.isfinite(noise_floor) or noise_floor<=0:raise ValueError("噪声下限必须正且有限")
 x=np.asarray(values,dtype=float);scores=np.zeros(len(x));baselines=np.zeros(len(x));details=[]
 for segment in segments:
  a,b=segment["start_index"],segment["end_index"];residual=x[a:b]-segment["mean"]
  # MAD stays on the raw residuals so anomaly detection still flags single-hour deviations.
  median_res=float(np.median(residual));mad=float(np.median(np.abs(residual-median_res)))
  scale=max(1.4826*mad,noise_floor);scores[a:b]=np.abs(residual-median_res)/scale;baselines[a:b]=segment["mean"]+median_res
  details.append({"start_index":a,"end_index":b,"median":float(baselines[a]),"mad":mad,"scale_used":scale,"floor_used":1.4826*mad<noise_floor,"weight_sum":float(w[a:b].sum())})
 return {"scores":scores.tolist(),"baselines":baselines.tolist(),"anomaly_indices":[int(i) for i in np.where(scores>threshold)[0]],"threshold":threshold,"noise_floor":noise_floor,"weighting":weighting,"segments":details,"formula":"abs(residual - segment median residual) / max(1.4826 × MAD, noise_floor)"}
