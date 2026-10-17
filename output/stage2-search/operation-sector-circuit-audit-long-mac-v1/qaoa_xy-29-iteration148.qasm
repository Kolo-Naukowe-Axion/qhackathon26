OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-2.2124657932140379) q[0];
rz(1.6007874480001827) q[1];
rz(-0.0019591469979624893) q[2];
cx q[0],q[1];
rz(-1.6007874480001827) q[1];
cx q[0],q[1];
rx(0.47866588339123251) q[0];
rx(0.47866588339123251) q[1];
rz(-2.8848823598074209) q[0];
rz(2.0873016363467474) q[1];
rz(-0.0025545744625868998) q[2];
cx q[0],q[1];
rz(-2.0873016363467474) q[1];
cx q[0],q[1];
rx(5.369735806872761) q[0];
rx(5.369735806872761) q[1];
measure q -> c;
