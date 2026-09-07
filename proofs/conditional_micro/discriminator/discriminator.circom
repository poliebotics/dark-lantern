pragma circom 2.2.3;

include "circomlib/circuits/bitify.circom";
include "circomlib/circuits/comparators.circom";
include "circomlib/circuits/poseidon.circom";


template PrivateTensorCommitment() {
    signal input context;
    signal input nonce;
    signal input values[224];
    signal output out;

    component nonceBits = Num2Bits(128);
    nonceBits.in <== nonce;

    signal packed[8];
    for (var word = 0; word < 8; word++) {
        var accumulator = 0;
        for (var slot = 0; slot < 31; slot++) {
            if (word * 31 + slot < 224) {
                accumulator += values[word * 31 + slot] * (1 << (8 * slot));
            }
        }
        packed[word] <== accumulator;
    }

    component digest = Poseidon(12);
    digest.inputs[0] <== context;
    digest.inputs[1] <== nonce;
    digest.inputs[2] <== 224;
    digest.inputs[3] <== 20260823;
    for (var word = 0; word < 8; word++) {
        digest.inputs[word + 4] <== packed[word];
    }
    out <== digest.out;
}


template BilinearScore() {
    signal input camera[4][16];
    signal input emission[3][16];
    signal output score;
    var W[4][3] = [[126,-120,-11],[73,124,-69],[-55,124,58],[-78,-111,127]];
    signal products[16][4][3];
    var accumulator = 0;
    for (var p = 0; p < 16; p++) {
        for (var c = 0; c < 4; c++) {
            for (var e = 0; e < 3; e++) {
                products[p][c][e] <== camera[c][p] * emission[e][p];
                accumulator += W[c][e] * products[p][c][e];
            }
        }
    }
    score <== 2147483648 + accumulator;
}

template ZeeBeamConditionalDiscriminator() {
    signal input context;
    signal input nonce;
    signal input cameraT[4][16];
    signal input cameraU[4][16];
    signal input emissionT[3][16];
    signal input emissionU[3][16];

    signal output commitment;
    signal output modelTag;
    signal output scoreTT;
    signal output scoreUU;
    signal output scoreTU;
    signal output scoreUT;
    signal output delta;
    signal output passed;

    modelTag <== 304195852289290939525100660671705491;
    component cameraTBits[4][16];
    component cameraUBits[4][16];
    component emissionTBits[3][16];
    component emissionUBits[3][16];
    for (var c = 0; c < 4; c++) {
        for (var p = 0; p < 16; p++) {
            cameraTBits[c][p] = Num2Bits(8);
            cameraUBits[c][p] = Num2Bits(8);
            cameraTBits[c][p].in <== cameraT[c][p];
            cameraUBits[c][p].in <== cameraU[c][p];
        }
    }
    for (var e = 0; e < 3; e++) {
        for (var p = 0; p < 16; p++) {
            emissionTBits[e][p] = Num2Bits(8);
            emissionUBits[e][p] = Num2Bits(8);
            emissionTBits[e][p].in <== emissionT[e][p];
            emissionUBits[e][p].in <== emissionU[e][p];
        }
    }

    component binding = PrivateTensorCommitment();
    binding.context <== context;
    binding.nonce <== nonce;
    var cursor = 0;
    for (var c = 0; c < 4; c++) {
        for (var p = 0; p < 16; p++) {
            binding.values[cursor] <== cameraT[c][p]; cursor++;
        }
    }
    for (var c = 0; c < 4; c++) {
        for (var p = 0; p < 16; p++) {
            binding.values[cursor] <== cameraU[c][p]; cursor++;
        }
    }
    for (var e = 0; e < 3; e++) {
        for (var p = 0; p < 16; p++) {
            binding.values[cursor] <== emissionT[e][p]; cursor++;
        }
    }
    for (var e = 0; e < 3; e++) {
        for (var p = 0; p < 16; p++) {
            binding.values[cursor] <== emissionU[e][p]; cursor++;
        }
    }
    commitment <== binding.out;

    component tt = BilinearScore();
    component uu = BilinearScore();
    component tu = BilinearScore();
    component ut = BilinearScore();
    for (var c = 0; c < 4; c++) {
        for (var p = 0; p < 16; p++) {
            tt.camera[c][p] <== cameraT[c][p];
            uu.camera[c][p] <== cameraU[c][p];
            tu.camera[c][p] <== cameraT[c][p];
            ut.camera[c][p] <== cameraU[c][p];
        }
    }
    for (var e = 0; e < 3; e++) {
        for (var p = 0; p < 16; p++) {
            tt.emission[e][p] <== emissionT[e][p];
            uu.emission[e][p] <== emissionU[e][p];
            tu.emission[e][p] <== emissionU[e][p];
            ut.emission[e][p] <== emissionT[e][p];
        }
    }
    scoreTT <== tt.score;
    scoreUU <== uu.score;
    scoreTU <== tu.score;
    scoreUT <== ut.score;
    delta <== tt.score + uu.score - tu.score - ut.score;
    component positive = LessEqThan(35);
    positive.in[0] <== 1;
    positive.in[1] <== delta;
    positive.out === 1;
    passed <== positive.out;
}

component main {public [context]} = ZeeBeamConditionalDiscriminator();
