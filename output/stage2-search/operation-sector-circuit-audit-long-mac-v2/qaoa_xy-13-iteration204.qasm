OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.059349254459096557) q[0];
rz(-0.00062808891776628903) q[2];
cx q[0],q[1];
rz(-1.009576397698019) q[1];
cx q[0],q[1];
rx(10.508417688120405) q[0];
rx(10.508417688120405) q[1];
rz(-0.13208154593500851) q[0];
rz(-0.0013978095596869397) q[2];
cx q[0],q[1];
rz(-2.2468085330263672) q[1];
cx q[0],q[1];
rx(5.0617634762395811) q[0];
rx(5.0617634762395811) q[1];
measure q -> c;
