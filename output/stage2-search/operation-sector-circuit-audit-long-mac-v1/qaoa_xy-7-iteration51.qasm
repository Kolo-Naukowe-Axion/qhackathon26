OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.036432966774210859) q[0];
rz(-0.00025704498880717817) q[2];
cx q[0],q[1];
rz(-0.41316849653895749) q[1];
cx q[0],q[1];
rx(6.7239267893455024) q[0];
rx(6.7239267893455024) q[1];
rz(-0.11017617194440425) q[0];
rz(-0.00077732436833317833) q[2];
cx q[0],q[1];
rz(-1.2494541989621752) q[1];
cx q[0],q[1];
rx(2.2537729719511037) q[0];
rx(2.2537729719511037) q[1];
measure q -> c;
