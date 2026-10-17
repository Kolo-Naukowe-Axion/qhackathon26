OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.47779606505628808) q[0];
rz(-0.47779606505628808) q[1];
rz(-0.00058475766265079436) q[2];
cx q[0],q[1];
rz(0.47779606505628808) q[1];
cx q[0],q[1];
rx(7.3296352415593367) q[0];
rx(7.3296352415593367) q[1];
rz(-0.34215792117796145) q[0];
rz(-0.34215792117796145) q[1];
rz(-0.00041875494772421071) q[2];
cx q[0],q[1];
rz(0.34215792117796145) q[1];
cx q[0],q[1];
rx(10.719775961445089) q[0];
rx(10.719775961445089) q[1];
measure q -> c;
