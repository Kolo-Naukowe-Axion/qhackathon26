OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-1.446159555544275) q[0];
rz(1.0463411779839624) q[1];
rz(-0.001301922865060538) q[2];
cx q[0],q[1];
rz(-1.0463411779839624) q[1];
cx q[0],q[1];
rx(11.797888384849207) q[0];
rx(11.797888384849207) q[1];
rz(-2.4422158720925196) q[0];
rz(1.7670187378008047) q[1];
rz(-0.0021986347724227097) q[2];
cx q[0],q[1];
rz(-1.7670187378008047) q[1];
cx q[0],q[1];
rx(11.014914501885205) q[0];
rx(11.014914501885205) q[1];
measure q -> c;
