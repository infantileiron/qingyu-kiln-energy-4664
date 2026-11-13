import type {Segment} from '../types/domain';import {fixed,hour} from '../utils/format';
export default function SegmentTable({rows,weighting}:{rows:Segment[];weighting?:string}){
 const weighted=weighting==='output';
 // Snapshots archived before the weighting option carry no segment kWh/output sums and keep the original columns.
 const showTotals=rows.some(s=>s.energy_kwh!==undefined&&s.energy_kwh!==null);
 return <div className="table-wrap"><table><thead><tr><th>工况段</th><th>起始 UTC</th><th>结束 UTC</th><th>观测数</th><th>均值 kWh/kg</th>{showTotals&&<><th>电量 kWh</th><th>产量 kg</th><th>均能耗 kWh/kg</th></>}</tr></thead><tbody>{rows.map((s,i)=><tr key={s.start_index}><td>{String(i+1).padStart(2,'0')}</td><td>{hour(s.start_at)}</td><td>{hour(s.end_at)}</td><td>{s.count}</td><td>{fixed(s.mean)}</td>{showTotals&&<><td>{s.energy_kwh===undefined||s.energy_kwh===null?'—':fixed(s.energy_kwh,2)}</td><td>{s.output_kg===undefined||s.output_kg===null?'—':fixed(s.output_kg,2)}</td><td>{s.mean_intensity===undefined||s.mean_intensity===null?'—':fixed(s.mean_intensity)}</td></>}</tr>)}</tbody></table>{showTotals&&<p className="table-note">{weighted?'按产量加权：段均值即段电量除以段产量，与段均能耗一致。':'等权研究：段均值为逐条归一能耗的等权均值，均能耗为段电量除以段产量的核对值。'}</p>}</div>
}
