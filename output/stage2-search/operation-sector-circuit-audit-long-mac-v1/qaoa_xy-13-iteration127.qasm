OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-3.3540445542751707) q[0];
rz(2.3762202758346627) q[1];
rz(-0.0029566412701928697) q[2];
cx q[0],q[1];
rz(-2.3762202758346627) q[1];
cx q[0],q[1];
rx(3.4637591845036226) q[0];
rx(3.4637591845036226) q[1];
rz(-1.3823397314210313) q[0];
rz(0.97933812289632804) q[1];
rz(-0.0012185534906318477) q[2];
cx q[0],q[1];
rz(-0.97933812289632804) q[1];
cx q[0],q[1];
rx(5.030996582434593) q[0];
rx(5.030996582434593) q[1];
measure q -> c;
