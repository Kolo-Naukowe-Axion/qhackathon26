OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-3.5875104851107236) q[0];
rz(2.595674822068863) q[1];
rz(-0.0032297002853549101) q[2];
cx q[0],q[1];
rz(-2.595674822068863) q[1];
cx q[0],q[1];
rx(0.69999999999999996) q[0];
rx(0.69999999999999996) q[1];
rz(-3.1233470732918871) q[0];
rz(2.2598382338876997) q[1];
rz(-0.0028118314847411226) q[2];
cx q[0],q[1];
rz(-2.2598382338876997) q[1];
cx q[0],q[1];
rx(0.69999999999999996) q[0];
rx(0.69999999999999996) q[1];
measure q -> c;
