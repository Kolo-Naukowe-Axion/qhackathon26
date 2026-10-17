OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.076327936058804516) q[0];
rz(-0.00064621847322513198) q[2];
cx q[0],q[1];
rz(-1.0387174488681268) q[1];
cx q[0],q[1];
rx(7.0373799896814848) q[0];
rx(7.0373799896814848) q[1];
rz(-0.10380356605457142) q[0];
rz(-0.00087883657589574692) q[2];
cx q[0],q[1];
rz(-1.4126227025521811) q[1];
cx q[0],q[1];
rx(8.2015052291511861) q[0];
rx(8.2015052291511861) q[1];
measure q -> c;
