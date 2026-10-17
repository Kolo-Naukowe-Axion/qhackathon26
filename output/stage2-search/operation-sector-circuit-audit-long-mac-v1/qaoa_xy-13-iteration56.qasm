OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.20304220976622334) q[0];
rz(-0.0014325207952509394) q[2];
cx q[0],q[1];
rz(-2.3026026143564091) q[1];
cx q[0],q[1];
rx(9.1761296892680093) q[0];
rx(9.1761296892680093) q[1];
rz(-0.224104192895972) q[0];
rz(-0.001581119103244771) q[2];
cx q[0],q[1];
rz(-2.5414562865752464) q[1];
cx q[0],q[1];
rx(6.879414164266155) q[0];
rx(6.879414164266155) q[1];
measure q -> c;
