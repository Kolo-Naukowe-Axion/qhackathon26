OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-2.6786130096565608) q[0];
rz(2.0701351474896872) q[1];
rz(-0.0025335650055525625) q[2];
cx q[0],q[1];
rz(-2.0701351474896872) q[1];
cx q[0],q[1];
rx(1.5458420782022362) q[0];
rx(1.5458420782022362) q[1];
rz(-3.3576439955084041) q[0];
rz(2.5949164074099862) q[1];
rz(-0.0031758261822279741) q[2];
cx q[0],q[1];
rz(-2.5949164074099862) q[1];
cx q[0],q[1];
rx(11.04148396923091) q[0];
rx(11.04148396923091) q[1];
measure q -> c;
