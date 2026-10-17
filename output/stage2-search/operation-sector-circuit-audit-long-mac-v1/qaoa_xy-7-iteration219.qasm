OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.00018542891022096169) q[2];
cx q[0],q[1];
rz(0.32466637516236857) q[1];
cx q[0],q[1];
rx(1.2516214975833122) q[0];
rx(1.2516214975833122) q[1];
rz(-0.0010168043610892219) q[2];
cx q[0],q[1];
rz(1.7803167034242073) q[1];
cx q[0],q[1];
rx(8.5931230888965882) q[0];
rx(8.5931230888965882) q[1];
measure q -> c;
