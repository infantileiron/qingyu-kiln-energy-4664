import math
import numpy as np

WEIGHTING_MODES=("equal","output")


def resolve_weighting(config):
    # Runs archived before the weighting option existed carry no mode and keep equal weighting.
    mode=(config or {}).get("weighting","equal")
    if mode not in WEIGHTING_MODES:raise ValueError("加权方式应为equal或output")
    return mode


def detect(values,penalty=6.,min_segment=24,weights=None,weighting="equal"):
 x=np.asarray(values,dtype=float);n=len(x)
 if weighting not in WEIGHTING_MODES:raise ValueError("加权方式应为equal或output")
 weighted=weighting=="output"
 if weighted:
  if weights is None:raise ValueError("按产量加权需要每条观测的产量")
  w=np.asarray(weights,dtype=float)
  if w.shape!=x.shape or not np.isfinite(w).all() or not (w>0).all():raise ValueError("产量权重必须为与观测一一对应的正有限值")
  total=float(w.sum())
  if not math.isfinite(total) or total<=0:raise ValueError("产量权重合计无效")
  # Scale weights to an average of one so the penalty term stays comparable across datasets.
  w=w*(n/total)
 else:w=np.ones(n)
 if n<min_segment or min_segment<3 or not np.isfinite(x).all() or not math.isfinite(penalty) or penalty<=0:raise ValueError("分段参数或观测数量无效")
 # Center first to reduce cancellation in the prefix-sum SSE calculation.
 y=x-float(x.mean())
 if not np.isfinite(y).all() or float(np.max(np.abs(y)))>1e140:raise ValueError("观测量级过大，无法可靠计算平方误差")
 S=np.concatenate(([0.],np.cumsum(w)))
 S1=np.concatenate(([0.],np.cumsum(w*y)))
 S2=np.concatenate(([0.],np.cumsum(w*y*y)))
 dp=np.full(n+1,np.inf);back=np.full(n+1,-1,dtype=int);dp[0]=-penalty
 for end in range(min_segment,n+1):
  starts=np.arange(0,end-min_segment+1)
  candidates=(starts==0)|(starts>=min_segment);starts=starts[candidates]
  # Weighted SSE of y[starts:end]: Σw·y² − (Σw·y)²/Σw. For output weights the weighted
  # segment mean Σoutput·x/Σoutput therefore equals segment kWh divided by segment output.
  sw=S[end]-S[starts];swy=S1[end]-S1[starts]
  cost=np.maximum(0.,S2[end]-S2[starts]-(swy*swy)/sw)
  objective=dp[starts]+cost+penalty
  j=int(np.argmin(objective));dp[end]=objective[j];back[end]=starts[j]
 if back[n]<0:raise ValueError("无法满足最小段长")
 bounds=[n];end=n
 while end>0:end=int(back[end]);bounds.append(end)
 bounds=sorted(bounds);segments=[]
 for a,b in zip(bounds,bounds[1:]):
  segment=x[a:b];seg_w=w[a:b];wsum=float(seg_w.sum())
  if weighted:
   mean=float((seg_w*segment).sum()/wsum);sse=max(0.,float((seg_w*segment*segment).sum()-wsum*mean*mean))
  else:
   mean=float(segment.mean());sse=float(((segment-mean)**2).sum())
  segments.append({"start_index":a,"end_index":b,"count":b-a,"mean":mean,"sse":sse,"weight_sum":wsum})
 criterion=("sum(output_i × (x_i − segment_mean)²) + penalty × number of change points" if weighted else "sum(within-segment SSE) + penalty × number of change points")
 return {"change_indices":bounds[1:-1],"segments":segments,"objective":float(dp[n]),"penalty":penalty,"min_segment":min_segment,"weighting":weighting,"total_sse":sum(s["sse"] for s in segments),"criterion":criterion}
