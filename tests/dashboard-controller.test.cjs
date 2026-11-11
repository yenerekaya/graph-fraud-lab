// Controller smoke checks with DOM/canvas stubs; this is not a visual browser test.
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const path=require('node:path');
const base=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(base,'artifacts/index.html'),'utf8');
const payload=JSON.parse(html.match(/<script type="application\/json" id="data">([\s\S]*?)<\/script>/)[1]);
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
function setup(data){
 const nodes=new Map();
 const ctx=new Proxy({}, {get:()=>()=>{},set:()=>true});
 const defaults=new Map([...html.matchAll(/<input id="([^"]+)"([^>]+)>/g)].map(m=>[m[1],m[2].match(/value="([^"]*)"/)?.[1]??'']));
 function element(id=''){
  return {id,value:defaults.get(id)??'',textContent:'',innerHTML:'',disabled:false,dataset:{},children:[],
   append(n){this.children.push(n)},querySelectorAll(){return []},setAttribute(){},click(){},
   getContext(){return ctx},getBoundingClientRect(){return {width:800,height:480,left:0,top:0}}};
 }
 const document={getElementById(id){if(!nodes.has(id))nodes.set(id,element(id));return nodes.get(id)},createElement:()=>element()};
 document.getElementById('data').textContent=JSON.stringify(data);
 const sandbox={document,console,Intl,Date,Set,Map,Blob,URL,devicePixelRatio:1,requestAnimationFrame(){},setTimeout(){},ResizeObserver:class{observe(){}}};
 vm.createContext(sandbox);
 for(const script of scripts)vm.runInContext(script,sandbox);
 return {nodes,sandbox};
}
const {nodes:n}=setup(payload);
assert.ok(n.get('stats').innerHTML.includes('444'));
assert.ok(n.get('txStatus').textContent.includes('444 of 444'));
assert.equal(n.get('prevTx').disabled,true);
n.get('routeForm').onsubmit({preventDefault(){}});
assert.ok(n.get('routeOutput').innerHTML.includes('R0 → R1 → R2 → R3 → R4'));
n.get('txQuery').value='missing';n.get('txQuery').oninput();
assert.equal(n.get('txStatus').textContent.startsWith('0 of 444'),true);
assert.ok(n.get('routeOutput').textContent.includes('Filters changed'));
n.get('routeForm').onsubmit({preventDefault(){}});
assert.ok(n.get('routeOutput').textContent.includes('No chronological route'));
n.get('resetTx').onclick();
assert.ok(n.get('txStatus').textContent.includes('444 of 444'));
n.get('txFrom').value='2026-01-03';n.get('txTo').value='2026-01-01';n.get('txFrom').oninput();
assert.equal(n.get('downloadCSV').disabled,true);
assert.equal(n.get('txStatus').textContent,'Start must precede end.');
const empty={...payload,nodes:[],edges:[],transactions:[],evaluation:null,summary:{accounts:0,transactions:0,flagged:0,edges:0}};
const {nodes:e}=setup(empty);
assert.equal(e.get('detail').textContent,'No accounts in this dataset.');
assert.ok(e.get('txStatus').textContent.includes('0 of 0'));
console.log('Dashboard controller: 13 smoke assertions passed (no visual verification)');
