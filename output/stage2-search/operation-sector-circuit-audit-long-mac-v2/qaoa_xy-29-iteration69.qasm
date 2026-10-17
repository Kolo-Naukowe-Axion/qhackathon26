OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-1.4805152786543831) q[0];
rz(1.1441991447397954) q[1];
rz(-0.0014003447630031405) q[2];
cx q[0],q[1];
rz(-1.1441991447397954) q[1];
cx q[0],q[1];
rx(12.351875677823616) q[0];
rx(12.351875677823616) q[1];
rz(-2.6860646858106447) q[0];
rz(2.0758940893968112) q[1];
rz(-0.002540613170356002) q[2];
cx q[0],q[1];
rz(-2.0758940893968112) q[1];
cx q[0],q[1];
rx(4.6551817454956126) q[0];
rx(4.6551817454956126) q[1];
measure q -> c;
