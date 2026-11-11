const assert=require('node:assert/strict');
const data=require('../artifacts/analysis.json');
const {advanceLayout,projectPositions}=require('../src/graph_fraud_lab/dashboard-core.js');
const nodes=data.nodes.map((n,i)=>({...n,x:180*Math.cos(i*2.39996),y:170*Math.sin(i*2.39996),vx:0,vy:0}));
for(let i=0;i<230;i++)advanceLayout(nodes,data.edges);
assert.ok(nodes.every(n=>[n.x,n.y,n.vx,n.vy].every(Number.isFinite)));
for(const [width,height] of [[800,480],[320,400],[1600,700]]){
 const view=projectPositions(nodes,width,height);
 assert.equal(view.length,80);
 assert.ok(view.every(n=>n.x>=49.999&&n.x<=width-49.999&&n.y>=49.999&&n.y<=height-49.999));
 // Regression: border clipping previously accumulated dozens on one straight line.
 assert.ok(view.filter(n=>Math.abs(n.y-50)<.01).length<=2);
 assert.ok(view.filter(n=>Math.abs(n.y-(height-50))<.01).length<=2);
 assert.equal(new Set(view.map(n=>`${n.x.toFixed(3)},${n.y.toFixed(3)}`)).size,80);
 // Preserve pairwise geometry with a uniform scale, including aspect-ratio changes.
 const ratio=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
 assert.ok(Math.abs(ratio(view[0],view[1])/ratio(nodes[0],nodes[1])-ratio(view[2],view[3])/ratio(nodes[2],nodes[3]))<1e-9);
}
assert.deepEqual(projectPositions([],800,480),[]);
const single=projectPositions([{id:'only',x:9000,y:-4000}],800,480)[0];
assert.equal(single.x,400);assert.equal(single.y,240);
console.log('Graph layout regression: 230 simulation steps, 3 viewport sizes, no border accumulation');
