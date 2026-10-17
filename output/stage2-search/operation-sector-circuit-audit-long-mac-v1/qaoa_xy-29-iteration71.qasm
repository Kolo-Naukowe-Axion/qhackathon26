OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(2.8915926535897931) q[0];
rz(-2.8915926535897931) q[1];
rz(-0.0035389177205805934) q[2];
cx q[0],q[1];
rz(-2.8915926535897931) q[1];
cx q[0],q[1];
rx(0.69999999999999996) q[0];
rx(0.69999999999999996) q[1];
rz(2.4915926535897932) q[0];
rz(-2.4915926535897932) q[1];
rz(-0.0030493719035116261) q[2];
cx q[0],q[1];
rz(-2.4915926535897932) q[1];
cx q[0],q[1];
rx(0.69999999999999996) q[0];
rx(0.69999999999999996) q[1];
measure q -> c;
