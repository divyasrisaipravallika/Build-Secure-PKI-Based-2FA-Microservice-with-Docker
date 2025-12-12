#!/bin/bash
repo_url=https://github.com/divyasrisaipravallika/Build-Secure-PKI-Based-2FA-Microservice-with-Docker



# 1. Create commit_hash.txt
echo "[1] Extracting commit hash..."
git log -1 --format=%H > commit_hash.txt
echo "Commit Hash:"
cat commit_hash.txt
echo ""

# 2. Sign the commit hash with RSA-PSS-SHA256
echo "[2] Signing commit hash with student_private.pem..."
openssl dgst -sha256 -sigopt rsa_padding_mode:pss -sigopt rsa_pss_saltlen:32 -sign student_private.pem -out signature.bin commit_hash.txt
echo "signature.bin created"
echo ""


echo "signature.bin created"
echo ""

# 3. Encrypt signature with instructor_public.pem
echo "[3] Encrypting signature with instructor_public.pem..."
openssl pkeyutl -encrypt \
  -pubin -inkey instructor_public.pem \
  -in signature.bin \
  -out enc_sig.bin \
  -pkeyopt rsa_padding_mode:oaep \
  -pkeyopt rsa_oaep_md:sha256 \
  -pkeyopt rsa_mgf1_md:sha256

echo "enc_sig.bin created"
echo ""

# 4. Convert encrypted signature to Base64 single-line
echo "[4] Creating Base64 encrypted signature (enc_sig.b64)..."
base64 < enc_sig.bin | tr -d '\n' > enc_sig.b64
echo "Encrypted Commit Signature:"
cat enc_sig.b64
echo ""
echo ""

# 5. Create student public key in API format (one line with \n)
echo "[5] Converting student_public.pem to single line..."
awk '{printf "%s\\n",$0}' student_public.pem > student_public_api.txt

echo "Student Public Key (API Format):"
cat student_public_api.txt
echo ""
echo ""

# 6. Convert encrypted_seed to one line
echo "[6] Converting encrypted_seed.txt to single line..."
tr -d '\n' < encrypted_seed.txt > encrypted_seed_oneline.txt

echo "Encrypted Seed (single-line):"
cat encrypted_seed_oneline.txt
echo ""
echo ""

echo "Docker image URL for evaluation: divyasrivetsa/pki-2fa-service:latest"
echo "Docker Hub link: https://hub.docker.com/r/divyasrivetsa/pki-2fa-service/tags"