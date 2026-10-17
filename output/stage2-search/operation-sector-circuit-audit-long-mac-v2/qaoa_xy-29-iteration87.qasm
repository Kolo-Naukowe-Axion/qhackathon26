OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
x q[1];
rz(-5.3831853071795868) q[0];
rz(-0.02490485915882298) q[1];
rx(0.69999999999999996) q[0];
rz(-5.3831853071795868) q[0];
rz(-0.02490485915882298) q[1];
rx(0.69999999999999996) q[0];
measure q -> c;
