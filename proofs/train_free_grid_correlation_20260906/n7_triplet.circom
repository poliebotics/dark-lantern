pragma circom 2.2.3;

include "circomlib/circuits/bitify.circom";
include "circomlib/circuits/comparators.circom";
include "circomlib/circuits/poseidon.circom";

// N7 integer positive: exact 4x4 RGB cell-sum grids, signed per-channel Pearson bounds with S = 65536, mean over channels,
// three Poseidon commitments sharing one capture, tau = 1/8 with rounding guards. Specification: SPEC_FREEZE.json.

template GridCommit(role) {
    // 48 values of 26 bits each, packed nine per field word (6 words, the last holding 3), committed with the manifest halves,
    // a 128-bit nonce, the count 48 and a domain-separated role tag
    signal input v[48];
    signal input manifest_hi;
    signal input manifest_lo;
    signal input nonce;
    signal output out;
    component vb[48];
    for (var i = 0; i < 48; i++) {
        vb[i] = Num2Bits(26);
        vb[i].in <== v[i];
    }
    component nb = Num2Bits(128);
    nb.in <== nonce;
    signal p[6];
    for (var j = 0; j < 6; j++) {
        var acc = 0;
        for (var k = 0; k < 9; k++) {
            if (9 * j + k < 48) {
                acc += v[9 * j + k] * (1 << (26 * k));
            }
        }
        p[j] <== acc;
    }
    component h = Poseidon(11);
    h.inputs[0] <== manifest_hi;
    h.inputs[1] <== manifest_lo;
    h.inputs[2] <== nonce;
    h.inputs[3] <== 48;
    h.inputs[4] <== 4 * 5776403947341392372063893259620182327776817 + role;
    for (var j = 0; j < 6; j++) {
        h.inputs[5 + j] <== p[j];
    }
    out <== h.out;
}

template Moments() {
    // one channel: x[16], y[16] -> C = 16*Sxy - Sx*Sy, Vx = 16*Sxx - Sx^2, Vy = 16*Syy - Sy^2 (every product a constrained intermediate)
    signal input x[16];
    signal input y[16];
    signal output C;
    signal output Vx;
    signal output Vy;
    signal pxx[16];
    signal pyy[16];
    signal pxy[16];
    var sx = 0; var sy = 0; var sxx = 0; var syy = 0; var sxy = 0;
    for (var i = 0; i < 16; i++) {
        pxx[i] <== x[i] * x[i];
        pyy[i] <== y[i] * y[i];
        pxy[i] <== x[i] * y[i];
        sx += x[i]; sy += y[i]; sxx += pxx[i]; syy += pyy[i]; sxy += pxy[i];
    }
    signal Sx <== sx;
    signal Sy <== sy;
    signal sxsy <== Sx * Sy;
    signal sxsx <== Sx * Sx;
    signal sysy <== Sy * Sy;
    C <== 16 * sxy - sxsy;
    Vx <== 16 * sxx - sxsx;
    Vy <== 16 * syy - sysy;
}

template NonzeroInverse() {
    signal input v;
    signal input vinv;
    v * vinv === 1;
}

template ChannelQ() {
    // certifies q = floor(S*|rho|) for one channel: C = (1-2b) a, q^2 P <= S^2 a^2 < (q+1)^2 P with P = Vx*Vy; outputs the signed q
    signal input C;
    signal input Vx;
    signal input Vy;
    signal input b;
    signal input a;
    signal input q;
    signal output sq;
    b * (1 - b) === 0;
    signal ba <== b * a;
    C === a - 2 * ba;
    component ab = Num2Bits(60);
    ab.in <== a;
    component qb = Num2Bits(17);
    qb.in <== q;
    component qle = LessEqThan(17);
    qle.in[0] <== q;
    qle.in[1] <== 65536;
    qle.out === 1;
    signal P <== Vx * Vy;
    signal a2 <== a * a;
    signal S2a2 <== 4294967296 * a2;
    signal q2 <== q * q;
    signal q2P <== q2 * P;
    signal q1 <== q + 1;
    signal q12 <== q1 * q1;
    signal q12P <== q12 * P;
    signal slack1 <== S2a2 - q2P;
    component s1 = Num2Bits(152);
    s1.in <== slack1;
    signal slack2 <== q12P - S2a2 - 1;
    component s2 = Num2Bits(153);
    s2.in <== slack2;
    signal bq <== b * q;
    sq <== q - 2 * bq;
}

template N7IntegerTriplet() {
    signal input manifest_hi;
    signal input manifest_lo;
    signal input cap[48];
    signal input em[48];
    signal input mis[48];
    signal input nonce_cap;
    signal input nonce_em;
    signal input nonce_mis;
    signal input vinv_cap[3];
    signal input vinv_em[3];
    signal input vinv_mis[3];
    signal input b_m[3];
    signal input a_m[3];
    signal input q_m[3];
    signal input b_x[3];
    signal input a_x[3];
    signal input q_x[3];
    signal output C_capture;
    signal output C_matched;
    signal output C_mismatch;
    signal output z_matched;
    signal output z_mismatch;

    component mh = Num2Bits(128);
    mh.in <== manifest_hi;
    component ml = Num2Bits(128);
    ml.in <== manifest_lo;

    component gc = GridCommit(0);
    component ge = GridCommit(1);
    component gm = GridCommit(2);
    for (var i = 0; i < 48; i++) {
        gc.v[i] <== cap[i];
        ge.v[i] <== em[i];
        gm.v[i] <== mis[i];
    }
    gc.manifest_hi <== manifest_hi; gc.manifest_lo <== manifest_lo; gc.nonce <== nonce_cap;
    ge.manifest_hi <== manifest_hi; ge.manifest_lo <== manifest_lo; ge.nonce <== nonce_em;
    gm.manifest_hi <== manifest_hi; gm.manifest_lo <== manifest_lo; gm.nonce <== nonce_mis;
    C_capture <== gc.out;
    C_matched <== ge.out;
    C_mismatch <== gm.out;

    component mm[3];
    component mx[3];
    component nzc[3];
    component nze[3];
    component nzm[3];
    component cqm[3];
    component cqx[3];
    var Qm = 0;
    var Qx = 0;
    for (var c = 0; c < 3; c++) {
        mm[c] = Moments();
        mx[c] = Moments();
        for (var i = 0; i < 16; i++) {
            mm[c].x[i] <== cap[3 * i + c];
            mm[c].y[i] <== em[3 * i + c];
            mx[c].x[i] <== cap[3 * i + c];
            mx[c].y[i] <== mis[3 * i + c];
        }
        nzc[c] = NonzeroInverse(); nzc[c].v <== mm[c].Vx; nzc[c].vinv <== vinv_cap[c];
        nze[c] = NonzeroInverse(); nze[c].v <== mm[c].Vy; nze[c].vinv <== vinv_em[c];
        nzm[c] = NonzeroInverse(); nzm[c].v <== mx[c].Vy; nzm[c].vinv <== vinv_mis[c];
        cqm[c] = ChannelQ(); cqm[c].C <== mm[c].C; cqm[c].Vx <== mm[c].Vx; cqm[c].Vy <== mm[c].Vy; cqm[c].b <== b_m[c]; cqm[c].a <== a_m[c]; cqm[c].q <== q_m[c];
        cqx[c] = ChannelQ(); cqx[c].C <== mx[c].C; cqx[c].Vx <== mx[c].Vx; cqx[c].Vy <== mx[c].Vy; cqx[c].b <== b_x[c]; cqx[c].a <== a_x[c]; cqx[c].q <== q_x[c];
        Qm += cqm[c].sq;
        Qx += cqx[c].sq;
    }
    z_matched <== 196608 + Qm;
    z_mismatch <== 196608 + Qx;
    component zmb = Num2Bits(19);
    zmb.in <== z_matched;
    component zxb = Num2Bits(19);
    zxb.in <== z_mismatch;
    // guards: matched mean correlation above 1/8 and mismatch below 1/8 despite the 1/S rounding per channel
    component gm1 = LessEqThan(19);
    gm1.in[0] <== 221187;
    gm1.in[1] <== z_matched;
    gm1.out === 1;
    component gx1 = LessEqThan(19);
    gx1.in[0] <== z_mismatch;
    gx1.in[1] <== 221180;
    gx1.out === 1;
}

component main {public [manifest_hi, manifest_lo]} = N7IntegerTriplet();
