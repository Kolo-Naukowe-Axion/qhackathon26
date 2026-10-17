OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-3.5459508366360284) q[0];
rz(-3.0915926535897933) q[1];
rz(-0.0035314445871740714) q[2];
cx q[0],q[1];
rz(3.0915926535897933) q[1];
cx q[0],q[1];
rx(11.666370614359172) q[0];
rx(11.666370614359172) q[1];
rz(-0.63083115360791875) q[0];
rz(-0.55000000000000004) q[1];
rz(-0.00062825046523850745) q[2];
cx q[0],q[1];
rz(0.55000000000000004) q[1];
cx q[0],q[1];
rx(11.666370614359172) q[0];
rx(11.666370614359172) q[1];
measure q -> c;
