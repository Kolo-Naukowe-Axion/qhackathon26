OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-3.3946950785653707) q[0];
rz(2.6845331789968481) q[1];
rz(-0.0033402633875919394) q[2];
cx q[0],q[1];
rz(-2.6845331789968481) q[1];
cx q[0],q[1];
rx(10.119382071861475) q[0];
rx(10.119382071861475) q[1];
rz(-2.747762856365235) q[0];
rz(2.1729375938663051) q[1];
rz(-0.0027037042958157694) q[2];
cx q[0],q[1];
rz(-2.1729375938663051) q[1];
cx q[0],q[1];
rx(0.62989410665391987) q[0];
rx(0.62989410665391987) q[1];
measure q -> c;
