#!/bin/bash
# Old Light bootstrap (Lambda gpu_1x_a100_sxm4, us-east-1, ZeeBeam mounted). Run on the box as ubuntu: bash box_bootstrap.sh
# Idempotent. Raw downloads go to the LOCAL disk; only pairs manifests, checkpoints and results go to the persistent filesystem,
# in the one NEW directory $OL_FS (nothing else on that filesystem is touched).
set -euo pipefail
K=${OL_KIT:-$(cd "$(dirname "$0")" && pwd)}          # this kit (rsynced from the development machine)
L=${OL_LOCAL:?set OL_LOCAL to a local work area for the raw downloads, the pairs and the pix2pixHD checkout}        # local disk work area
FS=${OL_FS:?set OL_FS to the output directory for checkpoints, results and logs}
UA="Mozilla/5.0 (X11; Linux x86_64) BOSUN-oldlight/1.0"
mkdir -p $L/raw2024 $L/raw2023 $L/logs $FS/logs $FS/results $FS/checkpoints
echo "== $(date -u +%FT%TZ) host $(hostname) $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"; df -h / "$FS" | tail -2
# 1. tools
if ! command -v aria2c >/dev/null; then sudo apt-get update -qq && sudo apt-get install -y -qq aria2 >/dev/null; fi
python3 -c "import torch, torchvision; print('torch', torch.__version__, 'tv', torchvision.__version__, 'cuda', torch.cuda.is_available(), torch.cuda.device_count())"
python3 -m pip install -q --user dominate 2>&1 | tail -1
# the Debian scikit-learn, scipy and scikit-image are built against numpy 1.x and fail beside the pip numpy 2.2.6: matching wheels into the user site
NP=$(python3 -c "import numpy; print(numpy.__version__)")
for m in scipy skimage; do python3 -c "import $m" 2>/dev/null || { python3 -m pip install -q --user --ignore-installed scikit-image "numpy==$NP" 2>&1 | tail -1; break; }; done
# the Debian h5py is built against numpy 1.x and fails to import beside the pip numpy 2.2.6: install a matching wheel into the user site (pip 22 has no --break-system-packages)
python3 -c "import h5py" 2>/dev/null || python3 -m pip install -q --user --ignore-installed --no-deps h5py 2>&1 | tail -1
python3 -c "import h5py, skimage, scipy, dominate, numpy, PIL; print('deps ok h5py', h5py.__version__, 'skimage', skimage.__version__, 'numpy', numpy.__version__)"
# 2. downloads (aria2 resumes; 2024: 7 large files split 16 ways each, 2023: 6,800 files, 48 in flight)
echo "== $(date -u +%FT%TZ) download 2024"
aria2c -q -c --user-agent="$UA" -j 4 -x 16 -s 16 -k 64M --file-allocation=none --auto-file-renaming=false --allow-overwrite=false \
  -d $L/raw2024 -i $K/urls_2024.txt --log=$L/logs/aria_2024.log --log-level=warn || true
echo "== $(date -u +%FT%TZ) download 2023"
aria2c -q -c --user-agent="$UA" -j 48 -x 2 -s 1 --file-allocation=none --auto-file-renaming=false --allow-overwrite=false \
  -d $L/raw2023 -i $K/urls_2023.txt --log=$L/logs/aria_2023.log --log-level=warn || true
echo "== $(date -u +%FT%TZ) downloaded: 2024 $(ls $L/raw2024 | wc -l) files, 2023 $(find $L/raw2023 -name '*.npy' | wc -l) files"; du -sh $L/raw2024 $L/raw2023 | tr '\n' ' '; echo
# 3. verify SHA-256 (parallel), record the result
echo "== $(date -u +%FT%TZ) verify"
(cd $L/raw2024 && sha256sum -c --quiet $K/sha_2024.txt > $L/logs/verify_2024.log 2>&1 && echo "2024 sha OK" || { echo "2024 SHA MISMATCH"; cat $L/logs/verify_2024.log | head; })
(cd $L/raw2023 && split -n l/16 $K/sha_2023.txt /tmp/sha_part_ && ls /tmp/sha_part_* | xargs -P 16 -I{} sha256sum -c --quiet {} > $L/logs/verify_2023.log 2>&1 && echo "2023 sha OK" || { echo "2023 SHA MISMATCH ($(wc -l < $L/logs/verify_2023.log) lines)"; head $L/logs/verify_2023.log; }; rm -f /tmp/sha_part_*)
# 4. pix2pixHD + the kit's modern-PyTorch patches (identical to the 6 September kitbootstrap.sh)
if [ ! -d $L/pix2pixHD ]; then git clone -q https://github.com/NVIDIA/pix2pixHD.git $L/pix2pixHD; fi
cd $L/pix2pixHD
python3 - <<'PY'
import pathlib, re
def patch(path, old, new):
    p = pathlib.Path(path); t = p.read_text()
    if old in t: p.write_text(t.replace(old, new)); print("patched", path, old[:40])
patch("models/networks.py", "torchvision.models.vgg19(pretrained=True)", "torchvision.models.vgg19(weights='IMAGENET1K_V1')")
for f in ("models/networks.py", "models/pix2pixHD_model.py"):
    p = pathlib.Path(f); t = p.read_text()
    if "F.upsample(" in t or "nn.functional.upsample(" in t:
        p.write_text(t.replace("F.upsample(", "F.interpolate(").replace("nn.functional.upsample(", "nn.functional.interpolate(")); print("upsample->interpolate", f)
for f in pathlib.Path(".").rglob("*.py"):
    t = f.read_text(); t2 = re.sub(r"np\.float\b(?!\d|_)", "float", t); t2 = re.sub(r"np\.int\b(?!\d|_)", "int", t2)
    if t2 != t: f.write_text(t2); print("np.float/int", f)
# Python 3.9 removed fractions.gcd (train.py uses it for the print/save frequency lcm): use math.gcd
patch("train.py", "import fractions", "import fractions, math")
patch("train.py", "fractions.gcd(a,b)", "math.gcd(a,b)")
PY
git -C $L/pix2pixHD rev-parse HEAD > $FS/logs/pix2pixHD_commit.txt
echo "== $(date -u +%FT%TZ) bootstrap done; pix2pixHD $(cat $FS/logs/pix2pixHD_commit.txt)"
