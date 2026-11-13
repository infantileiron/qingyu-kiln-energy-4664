from uuid import uuid4
from fastapi import HTTPException
from ..models.run import ChangeRun
from ..models.study import ChangeStudy
from ..models.dataset import MeterDataset
from ..models.window import OperatingWindow
from ..utils.queue import enqueue
from .readings import normalize
from .change_points import detect,resolve_weighting
from .robust_scores import score

def describe_segments(changes,observations,weighting):
 # Adds the segment totals used to cross-check the segment mean on the results page and archive.
 segments=changes["segments"]
 for segment in segments:
  a,b=segment["start_index"],segment["end_index"]
  segment["start_at"]=observations[a]["timestamp"];segment["end_at"]=observations[b-1]["timestamp"]
  segment["energy_kwh"]=sum(o["kwh"] for o in observations[a:b]);segment["output_kg"]=sum(o["output_kg"] for o in observations[a:b])
  segment["mean_intensity"]=segment["energy_kwh"]/segment["output_kg"]
  # With output weighting the DP optimum already equals kWh/output; pin it to the quotient so the
  # displayed mean and totals agree exactly and stay invariant under common energy/output scaling.
  if weighting=="output":segment["mean"]=segment["mean_intensity"]
 return segments

def compute(db,run_id):
 row=db.get(ChangeRun,run_id)
 if row is None or row.status not in ["queued","running"]:return
 row.status="running";db.commit()
 try:
  study=db.get(ChangeStudy,row.study_id);dataset=db.get(MeterDataset,study.dataset_id);window=db.get(OperatingWindow,study.window_id)
  observations,excluded=normalize(dataset.readings,window.start_at,window.end_at);values=[r["intensity"] for r in observations];config=dict(study.config);weighting=resolve_weighting(config);config["weighting"]=weighting
  weights=[r["output"] for r in observations] if weighting=="output" else None
  changes=detect(values,config["penalty"],config["min_segment"],weights,weighting);robust=score(values,changes["segments"],config["anomaly_threshold"],config["noise_floor"],weights,weighting)
  describe_segments(changes,observations,weighting)
  for index,obs in enumerate(observations):obs.update(score=robust["scores"][index],baseline=robust["baselines"][index],anomaly=index in robust["anomaly_indices"])
  row.result={"observations":observations,"excluded":excluded,"changes":changes,"robust":robust,"valid_count":len(observations),"excluded_count":len(excluded),"anomaly_count":len(robust["anomaly_indices"]),"dataset_name":dataset.name,"window_name":window.name,"config":config};row.status="completed"
 except Exception as e:row.status="failed";row.error=str(e)[:1000]
 db.commit()
