OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
x q[1];
rz(-1.8553390249610746) q[0];
rz(-0.0071399710127200526) q[1];
rx(11.476019707453721) q[0];
rz(-5.5731085763733201) q[0];
rz(-0.021447203530299195) q[1];
rx(5.6862249772952698) q[0];
measure q -> c;
