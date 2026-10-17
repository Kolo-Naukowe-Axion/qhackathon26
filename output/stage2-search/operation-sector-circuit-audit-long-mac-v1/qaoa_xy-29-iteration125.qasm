OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-2.5864188311650045) q[0];
rz(1.8713540398677262) q[1];
rz(-0.0022902838561808946) q[2];
cx q[0],q[1];
rz(-1.8713540398677262) q[1];
cx q[0],q[1];
rx(1.5265379198292597) q[0];
rx(1.5265379198292597) q[1];
rz(-2.2265975131314932) q[0];
rz(1.611012184550642) q[1];
rz(-0.0019716606904847632) q[2];
cx q[0],q[1];
rz(-1.611012184550642) q[1];
cx q[0],q[1];
rx(7.6402025246504861) q[0];
rx(7.6402025246504861) q[1];
measure q -> c;
