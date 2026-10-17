OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(3.1353632401229494) q[0];
rz(-3.1353632401229494) q[1];
rz(-0.0038372598979849811) q[2];
cx q[0],q[1];
rz(-3.1353632401229494) q[1];
cx q[0],q[1];
rx(11.704421786323568) q[0];
rx(11.704421786323568) q[1];
rz(2.4830606367386365) q[0];
rz(-2.4830606367386365) q[1];
rz(-0.0030389298706100121) q[2];
cx q[0],q[1];
rz(-2.4830606367386365) q[1];
cx q[0],q[1];
rx(7.2060291207164067) q[0];
rx(7.2060291207164067) q[1];
measure q -> c;
