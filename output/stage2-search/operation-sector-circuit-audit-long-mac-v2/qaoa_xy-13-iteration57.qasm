OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-2.0518815676804083) q[0];
rz(1.6226329671229265) q[1];
rz(-0.0020189810034703056) q[2];
cx q[0],q[1];
rz(-1.6226329671229265) q[1];
cx q[0],q[1];
rx(10.580520898528365) q[0];
rx(10.580520898528365) q[1];
rz(-1.9127093650832281) q[0];
rz(1.5125752485887205) q[1];
rz(-0.0018820403351195128) q[2];
cx q[0],q[1];
rz(-1.5125752485887205) q[1];
cx q[0],q[1];
rx(1.3866471372522793) q[0];
rx(1.3866471372522793) q[1];
measure q -> c;
