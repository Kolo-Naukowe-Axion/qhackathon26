import test from 'node:test';
import assert from 'node:assert/strict';
import {aislePath,transportPose,transportPath,samplePath,activeTransportPath,nearestHeading} from '../presentation/stage2/factory-motion.js';
const locations={RAW:[55,340],HUB_A:[450,260],T1:[150,175],HUB_B:[680,260],QA2:[970,325]};
const point=id=>locations[id];

test('schematic route uses the shared aisle and passes through recorded graph nodes',()=>{
 assert.deepEqual(aislePath(point('RAW'),point('T1')),[[55,340],[55,260],[150,260],[150,175]]);
 const move={legs:[{from:'RAW',to:'HUB_A'},{from:'HUB_A',to:'T1'}]};
 const path=transportPath(move,point);
 assert.deepEqual(path[0],point('RAW'));assert.deepEqual(path.at(-1),point('T1'));
 assert.ok(path.some(p=>p[0]===450&&p[1]===260));
 for(let i=1;i<path.length;i++)assert.ok(path[i][0]===path[i-1][0]||path[i][1]===path[i-1][1]);
});

test('robot motion preserves graph-leg timing, loading waits and pickup/drop boundaries',()=>{
 const move={unit_id:'part-1',start:0,end:10,pickup_tick:4,drop_tick:9,legs:[{from:'T1',to:'HUB_A',start:0,end:2,loaded:false},{from:'HUB_A',to:'RAW',start:2,end:4,loaded:false},{from:'RAW',to:'HUB_A',start:5,end:7,loaded:true},{from:'HUB_A',to:'T1',start:7,end:9,loaded:true}]};
 assert.deepEqual(transportPose(move,0,point),{x:150,y:175,angle:90,loaded:false,moving:true});
 assert.equal(transportPose(move,3.99,point).loaded,false);
 const loading=transportPose(move,4,point);
 assert.deepEqual(loading,{x:55,y:340,angle:0,loaded:true,moving:false});
 const travel=transportPose(move,6,point);
 assert.equal(travel.loaded,true);assert.equal(travel.moving,true);assert.equal(travel.y,260);
 const arrived=transportPose(move,9,point);
 assert.deepEqual(arrived,{x:150,y:175,angle:0,loaded:false,moving:false});
});

test('interpolation is bounded and explicit display paths stay intact',()=>{
 const points=[[0,0],[10,0],[10,10]];
 assert.deepEqual(samplePath(points,-1),{x:0,y:0,angle:0});
 assert.deepEqual(samplePath(points,.75),{x:10,y:5,angle:90});
 assert.deepEqual(samplePath(points,2),{x:10,y:10,angle:90});
 assert.deepEqual(transportPath({path:points},point),points);
 assert.deepEqual(samplePath([[2,3],[2,3]],.5),{x:2,y:3,angle:0});
});

// Recharge records share move intervals but never carry a part.
test('charging and empty repositioning never invent cargo',()=>{
 const charge={unit_id:'',kind:'charge',start:0,end:10,pickup_tick:2,drop_tick:10,legs:[{from:'T1',to:'HUB_A',start:0,end:2,loaded:false}]};
 const pose=transportPose(charge,5,point);
 assert.equal(pose.loaded,false);assert.equal(pose.moving,false);
 assert.deepEqual([pose.x,pose.y],point('HUB_A'));
});

test('route highlights only the current graph leg and disappears during loading waits',()=>{
 const move={start:0,end:10,legs:[{from:'T1',to:'HUB_A',start:0,end:2},{from:'RAW',to:'HUB_A',start:5,end:7},{from:'HUB_A',to:'QA2',start:7,end:9}]};
 assert.deepEqual(activeTransportPath(move,1,point),aislePath(point('T1'),point('HUB_A')));
 assert.deepEqual(activeTransportPath(move,4,point),[]);
 assert.deepEqual(activeTransportPath(move,7,point),aislePath(point('HUB_A'),point('QA2')));
 assert.deepEqual(activeTransportPath(move,9,point),[]);
 assert.equal(nearestHeading(179,-179),181);
 assert.equal(nearestHeading(-179,179),-181);
 assert.equal(nearestHeading(360,90),450);
});
