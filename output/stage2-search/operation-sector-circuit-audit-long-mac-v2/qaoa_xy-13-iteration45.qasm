OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.0010058505065985901) q[2];
cx q[0],q[1];
rz(-1.616782118503151) q[1];
cx q[0],q[1];
rx(10.288945376253807) q[0];
rx(10.288945376253807) q[1];
rz(-0.00016206326926925538) q[2];
cx q[0],q[1];
rz(-0.26049695665685968) q[1];
cx q[0],q[1];
rx(4.6560298400846749) q[0];
rx(4.6560298400846749) q[1];
measure q -> c;
