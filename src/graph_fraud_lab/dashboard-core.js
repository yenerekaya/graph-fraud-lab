/* Pure investigation logic, shared by the inline dashboard and Node tests. */
(function(root){
  'use strict';
  function filterTransactions(rows, {query='',start=null,end=null,minAmount=0}={}) {
    const low=start ? Date.parse(start) : -Infinity, high=end ? Date.parse(end) : Infinity;
    if(Number.isNaN(low)||Number.isNaN(high)||low>=high) throw Error('Start must precede end.');
    if(!Number.isFinite(minAmount)||minAmount<0) throw Error('Minimum amount must be non-negative.');
    const q=query.toLowerCase().trim();
    return rows.filter(r=>{const t=Date.parse(r.timestamp);return t>=low&&t<high&&r.amount>=minAmount&&(!q||[r.id,r.source,r.target].some(s=>s.toLowerCase().includes(q)))});
  }
  function traceRoute(rows, accounts, source, target, maxHops=6) {
    if(!accounts.includes(source)||!accounts.includes(target)) throw Error('Choose existing account IDs.');
    if(source===target) throw Error('Choose two different accounts.');
    if(!Number.isInteger(maxHops)||maxHops<1||maxHops>12) throw Error('Max hops must be between 1 and 12.');
    const sorted=[...rows].sort((a,b)=>Date.parse(a.timestamp)-Date.parse(b.timestamp)||a.id.localeCompare(b.id));
    let states=new Map([[source,{at:-Infinity,path:[]}]]),best=null;
    for(let i=0;i<maxHops;i++){
      const next=new Map();
      for(const r of sorted){const prev=states.get(r.source),at=Date.parse(r.timestamp),old=next.get(r.target);if(prev&&prev.at<at&&(!old||at<old.at))next.set(r.target,{at,path:[...prev.path,r]});}
      const hit=next.get(target);if(hit&&(!best||hit.at<best.at||(hit.at===best.at&&hit.path.length<best.path.length)))best=hit;
      states=next;if(!states.size)break;
    }
    return best?best.path:[];
  }
  function toCSV(rows){
    const keys=['id','source','target','amount','timestamp'];
    const cell=value=>{let s=String(value);if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
    return [keys.join(','),...rows.map(r=>keys.map(k=>cell(r[k])).join(','))].join('\r\n');
  }
  const api={filterTransactions,traceRoute,toCSV};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.GraphLab=api;
})(globalThis);
