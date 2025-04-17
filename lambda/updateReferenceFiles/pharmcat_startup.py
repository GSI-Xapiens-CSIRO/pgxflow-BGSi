import base64
import bz2
import os

from launch_ec2 import launch_refupd_ec2

AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]

def update_pharmcat_preprocessor(pharmcat_version):
    with open("pharmcat_script.py", "rb") as file:
        compressed_pharmcat_script = base64.b64encode(
            bz2.compress(file.read())
        ).decode()
        
    with open("utils.py", "rb") as file:
        compressed_utils = base64.b64encode(
            bz2.compress(file.read())
        ).decode()

    ec2_startup = f"""
# Install dependencies
yum update -y
yum groupinstall -y "Development Tools"
yum install -y \
    python3 \
    python3-pip \
    awscli \
    gcc \
    make \
    zlib-devel \
    bzip2-devel \
    xz-devel \
    curl-devel \
    openssl-devel \
    wget
    
# Install boto3
pip install boto3

# Configure default region
export AWS_DEFAULT_REGION={AWS_DEFAULT_REGION}

mkdir -p /opt/pharmcat
cd /opt/pharmcat

# Copy contents of pharmcat script
cat > ./compressed_pharmcat.py << 'EOF'
{compressed_pharmcat_script}
EOF

# Copy contents of utils
cat > ./compressed_utils.py << 'EOF'
{compressed_utils}
EOF

cat > ./decompresser.py << 'EOF'
import base64
import bz2

with open("pharmcat.py", "wb") as output:
    output.write(bz2.decompress(base64.b64decode(input().encode())))
with open("utils.py", "wb") as output:
    output.write(bz2.decompress(base64.b64decode(input().encode())))
EOF
python3 decompresser.py

# Run the pharmcat script
sudo -E python3 pharmcat.py \
    --version '{pharmcat_version}'
"""