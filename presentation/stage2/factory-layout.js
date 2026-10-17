// Schematic display coordinates. Trace intervals and resource IDs stay unchanged.
export const positions={T1:[150,165],T2:[285,165],F1:[150,335],F2:[285,335],WASH1:[150,460],H1:[285,460],QA1:[415,460],F3:[700,165],S1:[835,165],S2:[970,165],WASH2:[700,335],H2:[835,335],QA2:[970,335],A1:[835,460],A2:[970,460],STOCK:[55,340],RAW_A:[55,340],SHIPPING:[1120,430],SHIP_B:[1120,430],CHARGE_A:[55,145],CHARGE_B:[1120,145],HUB_A:[450,260],HUB_B:[680,260],TOOL_A:[450,390],TOOL_B:[766,450]};
const machines=new Set(['T1','T2','F1','F2','F3','S1','S2','WASH1','WASH2','H1','H2','QA1','QA2','A1','A2']);
const docks={RAW_A:[55,275],STOCK:[55,275],SHIP_B:[1120,350],SHIPPING:[1120,350],CHARGE_A:[55,220],CHARGE_B:[1120,220]};
export const point=id=>positions[id]??[580,300];
export function dockPoint(id){const p=point(id);return machines.has(id)?[p[0]+66,p[1]-10]:docks[id]??p;}
export const processLabel=process=>({T:'TURNING',F:'MILLING',S:'WELDING',WASH:'WASH',HEAT:'HEAT',QA:'INSPECTION',ASSEMBLY:'ASSEMBLY'}[process]??process??'PROCESS');
