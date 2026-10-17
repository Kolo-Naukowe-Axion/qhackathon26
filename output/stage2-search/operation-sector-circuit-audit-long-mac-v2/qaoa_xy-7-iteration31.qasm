OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
x q[1];
rz(-4.2354515510156787) q[0];
rz(-0.019921547120977438) q[1];
rx(9.7278206084159997) q[0];
rz(-2.4995625846936713) q[0];
rz(-0.011756752075434803) q[1];
rx(8.0530143238131195) q[0];
measure q -> c;
