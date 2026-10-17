OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(2.407912658055209) q[0];
rz(-2.407912658055209) q[1];
rz(-0.0027504949957761382) q[2];
cx q[0],q[1];
rz(-2.407912658055209) q[1];
cx q[0],q[1];
rx(10.72179601595575) q[0];
rx(10.72179601595575) q[1];
rz(2.1159429763109356) q[0];
rz(-2.1159429763109356) q[1];
rz(-0.0024169857441554495) q[2];
cx q[0],q[1];
rz(-2.1159429763109356) q[1];
cx q[0],q[1];
rx(8.5141328532139529) q[0];
rx(8.5141328532139529) q[1];
measure q -> c;
