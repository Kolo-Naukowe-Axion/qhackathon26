OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.22717909152311772) q[0];
rz(-0.001923376069800164) q[2];
cx q[0],q[1];
rz(-3.0915926535897933) q[1];
cx q[0],q[1];
rx(10.066370614359172) q[0];
rx(10.066370614359172) q[1];
rz(-0.11389844372024903) q[0];
rz(-0.00096430327091397508) q[2];
cx q[0],q[1];
rz(-1.5499999999999998) q[1];
cx q[0],q[1];
rx(0.69999999999999996) q[0];
rx(0.69999999999999996) q[1];
measure q -> c;
