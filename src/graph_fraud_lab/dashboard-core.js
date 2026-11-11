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
  // Fit free simulation coordinates into the viewport without clamping nodes
  // individually. Clamping had accumulated many nodes on the same border line.
  function projectPositions(nodes,width,height,padding=50){
    if(!nodes.length)return [];
    const pad=Math.min(padding,width/4,height/4);
    const xs=nodes.map(n=>n.x),ys=nodes.map(n=>n.y);
    const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
    const scale=Math.min((width-2*pad)/Math.max(1,maxX-minX),(height-2*pad)/Math.max(1,maxY-minY));
    const cx=(minX+maxX)/2,cy=(minY+maxY)/2;
    return nodes.map(n=>({...n,x:width/2+(n.x-cx)*scale,y:height/2+(n.y-cy)*scale}));
  }
  function advanceLayout(nodes,edges){
    const byId=new Map(nodes.map(n=>[n.id,n]));
    for(let i=0;i<nodes.length;i++){
      const a=nodes[i];
      for(let j=i+1;j<nodes.length;j++){
        const b=nodes[j],dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+40;
        const fx=dx*100/d2,fy=dy*100/d2;
        a.vx+=fx;a.vy+=fy;b.vx-=fx;b.vy-=fy;
      }
      a.vx-=a.x*.0015;a.vy-=a.y*.0015;
    }
    for(const e of edges){
      const a=byId.get(e.source),b=byId.get(e.target),dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1,f=(d-80)*.001;
      a.vx+=dx/d*f;a.vy+=dy/d*f;b.vx-=dx/d*f;b.vy-=dy/d*f;
    }
    for(const n of nodes){n.vx*=.8;n.vy*=.8;n.x+=n.vx;n.y+=n.vy;}
  }
  const api={filterTransactions,traceRoute,toCSV,projectPositions,advanceLayout};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.GraphLab=api;
})(globalThis);
